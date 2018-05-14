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


LOGGER = logging.getLogger(__name__)


CREATE_BLOCK_STMTS = """
CREATE TABLE IF NOT EXISTS blocks (
    block_num  integer PRIMARY KEY,
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
    start_block_num  integer,
    end_block_num    integer
);
"""


CREATE_RECORD_LOCATION_STMTS = """
CREATE TABLE IF NOT EXISTS record_locations (
    id               bigserial PRIMARY KEY,
    record_id        varchar,
    latitude         numeric(9,6),
    longitude        numeric(9,6),
    timestamp        integer,
    start_block_num  integer,
    end_block_num    integer
);
"""


CREATE_RECORD_OWNER_STMTS = """
CREATE TABLE IF NOT EXISTS record_owners (
    id               bigserial PRIMARY KEY,
    record_id        varchar,
    agent_id         varchar,
    timestamp        integer,
    start_block_num  integer,
    end_block_num    integer
);
"""


CREATE_AGENT_STMTS = """
CREATE TABLE IF NOT EXISTS agents (
    id               bigserial PRIMARY KEY,
    public_key       varchar,
    name             varchar,
    timestamp        integer,
    start_block_num  integer,
    end_block_num    integer
);
"""


class Database(object):
    """Simple object for managing a connection to a postgres database
    """
    def __init__(self, host, port, name, user, password):
        self._host = host
        self._port = port
        self._name = name
        self._user = user
        self._password = password
        self._conn = None

    def connect(self, retries=5, initial_delay=1, backoff=2):
        """Initializes a connection to the database
        """
        LOGGER.info('Connecting to database: %s:%s', self._host, self._port)

        delay = initial_delay
        for attempt in range(retries):
            try:
                self._conn = psycopg2.connect(
                    dbname=self._name,
                    host=self._host,
                    port=self._port,
                    user=self._user,
                    password=self._password)

            except psycopg2.OperationalError:
                LOGGER.debug(
                    'Connection failed.'
                    ' Retrying connection (%s retries remaining)',
                    retries - attempt)
                time.sleep(delay)
                delay *= backoff

            else:
                break

        else:
            self._conn = psycopg2.connect(
                dbname=self._name,
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password)

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
