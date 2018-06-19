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
# ------------------------------------------------------------------------------

import asyncio
import logging

import aiopg
import psycopg2
from psycopg2.extras import RealDictCursor


LATEST_BLOCK_NUM = """
SELECT max(block_num) FROM blocks
"""
LOGGER = logging.getLogger(__name__)


class Database(object):
    """Manages connection to the postgres database and makes async queries
    """
    def __init__(self, host, port, name, user, password, loop):
        self._dsn = 'dbname={} user={} password={} host={} port={}'.format(
            name, user, password, host, port)
        self._loop = loop
        self._conn = None

    async def connect(self, retries=5, initial_delay=1, backoff=2):
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
                self._conn = await aiopg.connect(
                    dsn=self._dsn, loop=self._loop, echo=True)
                LOGGER.info('Successfully connected to database')
                return

            except psycopg2.OperationalError:
                LOGGER.debug(
                    'Connection failed.'
                    ' Retrying connection (%s retries remaining)',
                    retries - attempt)
                await asyncio.sleep(delay)
                delay *= backoff

        self._conn = await aiopg.connect(
            dsn=self._dsn, loop=self._loop, echo=True)
        LOGGER.info('Successfully connected to database')

    def disconnect(self):
        """Closes connection to the database
        """
        self._conn.close()

    async def create_auth_entry(self,
                                public_key,
                                encrypted_private_key,
                                hashed_password):
        insert = """
        INSERT INTO auth (
            public_key,
            encrypted_private_key,
            hashed_password
        )
        VALUES ('{}', '{}', '{}');
        """.format(
            public_key,
            encrypted_private_key.hex(),
            hashed_password.hex())

        async with self._conn.cursor() as cursor:
            await cursor.execute(insert)

        self._conn.commit()

    async def fetch_agent_resource(self, public_key):
        fetch = """
        SELECT public_key, name, timestamp FROM agents
        WHERE public_key='{0}'
        AND ({1}) >= start_block_num
        AND ({1}) < end_block_num;
        """.format(public_key, LATEST_BLOCK_NUM)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchone()

    async def fetch_all_agent_resources(self):
        fetch = """
        SELECT public_key, name, timestamp FROM agents
        WHERE ({0}) >= start_block_num
        AND ({0}) < end_block_num;
        """.format(LATEST_BLOCK_NUM)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchall()

    async def fetch_auth_resource(self, public_key):
        fetch = """
        SELECT * FROM auth WHERE public_key='{}'
        """.format(public_key)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchone()

    async def fetch_record_resource(self, record_id):
        fetch_record = """
        SELECT record_id FROM records
        WHERE record_id='{0}'
        AND ({1}) >= start_block_num
        AND ({1}) < end_block_num;
        """.format(record_id, LATEST_BLOCK_NUM)

        fetch_record_locations = """
        SELECT latitude, longitude, timestamp FROM record_locations
        WHERE record_id='{0}'
        AND ({1}) >= start_block_num
        AND ({1}) < end_block_num;
        """.format(record_id, LATEST_BLOCK_NUM)

        fetch_record_owners = """
        SELECT agent_id, timestamp FROM record_owners
        WHERE record_id='{0}'
        AND ({1}) >= start_block_num
        AND ({1}) < end_block_num;
        """.format(record_id, LATEST_BLOCK_NUM)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                await cursor.execute(fetch_record)
                record = await cursor.fetchone()

                await cursor.execute(fetch_record_locations)
                record['locations'] = await cursor.fetchall()

                await cursor.execute(fetch_record_owners)
                record['owners'] = await cursor.fetchall()

                return record
            except TypeError:
                return None

    async def fetch_all_record_resources(self):
        fetch_records = """
        SELECT record_id FROM records
        WHERE ({0}) >= start_block_num
        AND ({0}) < end_block_num;
        """.format(LATEST_BLOCK_NUM)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                await cursor.execute(fetch_records)
                records = await cursor.fetchall()

                for record in records:
                    fetch_record_locations = """
                    SELECT latitude, longitude, timestamp
                    FROM record_locations
                    WHERE record_id='{0}'
                    AND ({1}) >= start_block_num
                    AND ({1}) < end_block_num;
                    """.format(record['record_id'], LATEST_BLOCK_NUM)

                    fetch_record_owners = """
                    SELECT agent_id, timestamp
                    FROM record_owners
                    WHERE record_id='{0}'
                    AND ({1}) >= start_block_num
                    AND ({1}) < end_block_num;
                    """.format(record['record_id'], LATEST_BLOCK_NUM)

                    await cursor.execute(fetch_record_locations)
                    record['locations'] = await cursor.fetchall()

                    await cursor.execute(fetch_record_owners)
                    record['owners'] = await cursor.fetchall()

                return records
            except TypeError:
                return []
