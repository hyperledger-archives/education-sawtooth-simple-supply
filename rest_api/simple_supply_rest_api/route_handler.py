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
import datetime
from json.decoder import JSONDecodeError
import logging
import time

from aiohttp.web import HTTPNotImplemented
from aiohttp.web import json_response
import bcrypt
from Crypto.Cipher import AES
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from simple_supply_rest_api.errors import ApiBadRequest
from simple_supply_rest_api.errors import ApiInternalError


LOGGER = logging.getLogger(__name__)


class RouteHandler(object):
    def __init__(self, loop, messenger, database):
        self._loop = loop
        self._messenger = messenger
        self._database = database

    async def authorize(self, request):
        raise HTTPNotImplemented()

    async def create_agent(self, request):
        body = await decode_request(request)
        required_fields = ['name', 'password']
        validate_fields(required_fields, body)

        public_key, private_key = self._messenger.get_new_key_pair()

        await self._messenger.send_create_agent_transaction(
            private_key=private_key,
            name=body.get('name'),
            timestamp=get_time())

        encrypted_private_key = encrypt_private_key(
            request.app['aes_key'], public_key, private_key)
        hashed_password = hash_password(body.get('password'))

        await self._database.create_auth_entry(
            public_key, encrypted_private_key, hashed_password)

        agent = await self._database.fetch_agent_resource(public_key)
        if agent is None:
            raise ApiInternalError(
                'Transaction committed but not yet reported')
        authorization = generate_auth_token(
            request.app['secret_key'], public_key)

        response = {
            'authorization': authorization,
            'agent': agent
        }
        return json_response(response)

    async def list_agents(self, request):
        raise HTTPNotImplemented()

    async def fetch_agent(self, request):
        raise HTTPNotImplemented()

    async def create_record(self, request):
        raise HTTPNotImplemented()

    async def list_records(self, request):
        raise HTTPNotImplemented()

    async def fetch_record(self, request):
        raise HTTPNotImplemented()

    async def transfer_record(self, request):
        raise HTTPNotImplemented()

    async def update_record(self, request):
        raise HTTPNotImplemented()


async def decode_request(request):
    try:
        return await request.json()
    except JSONDecodeError:
        raise ApiBadRequest('Improper JSON format')


def validate_fields(required_fields, body):
    for field in required_fields:
        if body.get(field) is None:
            raise ApiBadRequest(
                "'{}' parameter is required".format(field))


def encrypt_private_key(aes_key, public_key, private_key):
    init_vector = bytes.fromhex(public_key[:32])
    cipher = AES.new(bytes.fromhex(aes_key), AES.MODE_CBC, init_vector)
    return cipher.encrypt(private_key)


def hash_password(password):
    return bcrypt.hashpw(bytes(password, 'utf-8'), bcrypt.gensalt())


def get_time():
    dts = datetime.datetime.utcnow()
    return round(time.mktime(dts.timetuple()) + dts.microsecond/1e6)


def generate_auth_token(secret_key, public_key):
    serializer = Serializer(secret_key)
    token = serializer.dumps({'public_key': public_key})
    return token.decode('ascii')
