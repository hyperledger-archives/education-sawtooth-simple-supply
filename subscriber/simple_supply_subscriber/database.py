# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import logging
import time

import psycopg2
from psycopg2.extras import RealDictCursor


LOGGER = logging.getLogger(__name__)


CREATE_BLOCK_STMTS = """
CREATE TABLE IF NOT EXISTS blocks (
    block_num  bigint PRIMARY KEY,
    block_id   varchar
);
"""


CREATE_AUTH_STMTS = """
CREATE TABLE IF NOT EXISTS auth (
    public_key            varchar PRIMARY KEY,
    hashed_password       varchar,
    encrypted_private_key varchar
)
"""


CREATE_RECORD_STMTS = """
CREATE TABLE IF NOT EXISTS records (
    record_id        varchar PRIMARY KEY,
    start_block_num  bigint,
    end_block_num    bigint
);
"""


CREATE_RECORD_LOCATION_STMTS = """
CREATE TABLE IF NOT EXISTS record_locations (
    id               bigserial PRIMARY KEY,
    record_id        varchar,
    latitude         numeric(9,6),
    longitude        numeric(9,6),
    timestamp        bigint,
    start_block_num  bigint,
    end_block_num    bigint
);
"""


CREATE_RECORD_OWNER_STMTS = """
CREATE TABLE IF NOT EXISTS record_owners (
    id               bigserial PRIMARY KEY,
    record_id        varchar,
    agent_id         varchar,
    timestamp        bigint,
    start_block_num  bigint,
    end_block_num    bigint
);
"""


CREATE_AGENT_STMTS = """
CREATE TABLE IF NOT EXISTS agents (
    id               bigserial PRIMARY KEY,
    public_key       varchar,
    name             varchar,
    timestamp        bigint,
    start_block_num  bigint,
    end_block_num    bigint
);
"""


class Database(object):
    """Simple object for managing a connection to a postgres database
    """
    def __init__(self, dsn):
        self._dsn = dsn
        self._conn = None

    def connect(self, retries=5, initial_delay=1, backoff=2):
        """Initializes a connection to the database

        Args:
            retries (int): Number of times to retry the connection
            initial_delay (int): Number of seconds wait between reconnects
            backoff (int): Multiplies the delay after each retry
        """
        LOGGER.info('Connecting to database')

        delay = initial_delay
        for attempt in range(retries):
            try:
                self._conn = psycopg2.connect(self._dsn)
                LOGGER.info('Successfully connected to database')
                return

            except psycopg2.OperationalError:
                LOGGER.debug(
                    'Connection failed.'
                    ' Retrying connection (%s retries remaining)',
                    retries - attempt)
                time.sleep(delay)
                delay *= backoff

        self._conn = psycopg2.connect(self._dsn)
        LOGGER.info('Successfully connected to database')

    def create_tables(self):
        """Creates the Simple Supply tables
        """
        with self._conn.cursor() as cursor:
            LOGGER.debug('Creating table: blocks')
            cursor.execute(CREATE_BLOCK_STMTS)

            LOGGER.debug('Creating table: auth')
            cursor.execute(CREATE_AUTH_STMTS)

            LOGGER.debug('Creating table: records')
            cursor.execute(CREATE_RECORD_STMTS)

            LOGGER.debug('Creating table: record_locations')
            cursor.execute(CREATE_RECORD_LOCATION_STMTS)

            LOGGER.debug('Creating table: record_owners')
            cursor.execute(CREATE_RECORD_OWNER_STMTS)

            LOGGER.debug('Creating table: agents')
            cursor.execute(CREATE_AGENT_STMTS)

        self._conn.commit()

    def disconnect(self):
        """Closes the connection to the database
        """
        LOGGER.info('Disconnecting from database')
        if self._conn is not None:
            self._conn.close()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def drop_fork(self, block_num):
        """Deletes all resources from a particular block_num
        """
        delete_agents = """
        DELETE FROM agents WHERE start_block_num >= {}
        """.format(block_num)
        update_agents = """
        UPDATE agents SET end_block_num = null
        WHERE end_block_num >= {}
        """.format(block_num)

        delete_record_locations = """
        DELETE FROM record_owners WHERE record_id =
        (SELECT record_id FROM records WHERE start_block_num >= {})
        """.format(block_num)
        delete_record_owners = """
        DELETE FROM record_owners WHERE record_id =
        (SELECT record_id FROM records WHERE start_block_num >= {})
        """.format(block_num)
        delete_records = """
        DELETE FROM records WHERE start_block_num >= {}
        """.format(block_num)
        update_records = """
        UPDATE records SET end_block_num = null
        WHERE end_block_num >= {}
        """.format(block_num)

        delete_blocks = """
        DELETE FROM blocks WHERE block_num >= {}
        """.format(block_num)

        with self._conn.cursor() as cursor:
            cursor.execute(delete_agents)
            cursor.execute(update_agents)
            cursor.execute(delete_record_locations)
            cursor.execute(delete_record_owners)
            cursor.execute(delete_records)
            cursor.execute(update_records)
            cursor.execute(delete_blocks)

    def fetch_last_known_blocks(self, count):
        """Fetches the specified number of most recent blocks
        """
        fetch = """
        SELECT block_num, block_id FROM blocks
        ORDER BY block_num DESC LIMIT {}
        """.format(count)

        with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(fetch)
            blocks = cursor.fetchall()

        return blocks

    def fetch_block(self, block_num):
        fetch = """
        SELECT block_num, block_id FROM blocks WHERE block_num = {}
        """.format(block_num)

        with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(fetch)
            block = cursor.fetchone()

        return block

    def insert_block(self, block_dict):
        insert = """
        INSERT INTO blocks (
        block_num,
        block_id)
        VALUES ('{}', '{}');
        """.format(
            block_dict['block_num'],
            block_dict['block_id'])

        with self._conn.cursor() as cursor:
            cursor.execute(insert)

    def insert_agent(self, agent_dict):
        insert = """
        INSERT INTO agents (
        public_key,
        name,
        timestamp,
        start_block_num,
        end_block_num)
        VALUES ('{}', '{}', '{}', '{}', '{}');
        """.format(
            agent_dict['public_key'],
            agent_dict['name'],
            agent_dict['timestamp'],
            agent_dict['start_block_num'],
            agent_dict['end_block_num'])

        with self._conn.cursor() as cursor:
            cursor.execute(insert)
