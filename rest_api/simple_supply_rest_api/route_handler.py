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

from aiohttp.web import json_response
import bcrypt
from Crypto.Cipher import AES
from itsdangerous import BadSignature
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from simple_supply_rest_api.errors import ApiBadRequest
from simple_supply_rest_api.errors import ApiNotFound
from simple_supply_rest_api.errors import ApiUnauthorized


LOGGER = logging.getLogger(__name__)


class RouteHandler(object):
    def __init__(self, loop, messenger, database):
        self._loop = loop
        self._messenger = messenger
        self._database = database

    async def authenticate(self, request):
        body = await decode_request(request)
        required_fields = ['public_key', 'password']
        validate_fields(required_fields, body)

        password = bytes(body.get('password'), 'utf-8')

        auth_info = await self._database.fetch_auth_resource(
            body.get('public_key'))
        if auth_info is None:
            raise ApiUnauthorized('No agent with that public key exists')

        hashed_password = auth_info.get('hashed_password')
        if not bcrypt.checkpw(password, bytes.fromhex(hashed_password)):
            raise ApiUnauthorized('Incorrect public key or password')

        token = generate_auth_token(
            request.app['secret_key'], body.get('public_key'))

        return json_response({'authorization': token})

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

        token = generate_auth_token(
            request.app['secret_key'], public_key)

        return json_response({'authorization': token})

    async def list_agents(self, _request):
        agent_list = await self._database.fetch_all_agent_resources()
        return json_response(agent_list)

    async def fetch_agent(self, request):
        public_key = request.match_info.get('agent_id', '')
        agent = await self._database.fetch_agent_resource(public_key)
        if agent is None:
            raise ApiNotFound(
                'Agent with public key {} was not found'.format(public_key))
        return json_response(agent)

    async def create_record(self, request):
        private_key = await self._authorize(request)

        body = await decode_request(request)
        required_fields = ['latitude', 'longitude', 'record_id']
        validate_fields(required_fields, body)

        await self._messenger.send_create_record_transaction(
            private_key=private_key,
            latitude=body.get('latitude'),
            longitude=body.get('longitude'),
            record_id=body.get('record_id'),
            timestamp=get_time())

        return json_response(
            {'data': 'Create record transaction submitted'})

    async def list_records(self, _request):
        record_list = await self._database.fetch_all_record_resources()
        return json_response(record_list)

    async def fetch_record(self, request):
        record_id = request.match_info.get('record_id', '')
        record = await self._database.fetch_record_resource(record_id)
        if record is None:
            raise ApiNotFound(
                'Record with the record id '
                '{} was not found'.format(record_id))
        return json_response(record)

    async def transfer_record(self, request):
        private_key = await self._authorize(request)

        body = await decode_request(request)
        required_fields = ['receiving_agent']
        validate_fields(required_fields, body)

        record_id = request.match_info.get('record_id', '')

        await self._messenger.send_transfer_record_transaction(
            private_key=private_key,
            receiving_agent=body['receiving_agent'],
            record_id=record_id,
            timestamp=get_time())

        return json_response(
            {'data': 'Transfer record transaction submitted'})

    async def update_record(self, request):
        private_key = await self._authorize(request)

        body = await decode_request(request)
        required_fields = ['latitude', 'longitude']
        validate_fields(required_fields, body)

        record_id = request.match_info.get('record_id', '')

        await self._messenger.send_update_record_transaction(
            private_key=private_key,
            latitude=body['latitude'],
            longitude=body['longitude'],
            record_id=record_id,
            timestamp=get_time())

        return json_response(
            {'data': 'Update record transaction submitted'})

    async def _authorize(self, request):
        token = request.headers.get('AUTHORIZATION')
        if token is None:
            raise ApiUnauthorized('No auth token provided')
        token_prefixes = ('Bearer', 'Token')
        for prefix in token_prefixes:
            if prefix in token:
                token = token.partition(prefix)[2].strip()
        try:
            token_dict = deserialize_auth_token(request.app['secret_key'],
                                                token)
        except BadSignature:
            raise ApiUnauthorized('Invalid auth token')
        public_key = token_dict.get('public_key')

        auth_resource = await self._database.fetch_auth_resource(public_key)
        if auth_resource is None:
            raise ApiUnauthorized('Token is not associated with an agent')
        return decrypt_private_key(request.app['aes_key'],
                                   public_key,
                                   auth_resource['encrypted_private_key'])


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


def decrypt_private_key(aes_key, public_key, encrypted_private_key):
    init_vector = bytes.fromhex(public_key[:32])
    cipher = AES.new(bytes.fromhex(aes_key), AES.MODE_CBC, init_vector)
    private_key = cipher.decrypt(bytes.fromhex(encrypted_private_key))
    return private_key


def hash_password(password):
    return bcrypt.hashpw(bytes(password, 'utf-8'), bcrypt.gensalt())


def get_time():
    dts = datetime.datetime.utcnow()
    return round(time.mktime(dts.timetuple()) + dts.microsecond/1e6)


def generate_auth_token(secret_key, public_key):
    serializer = Serializer(secret_key)
    token = serializer.dumps({'public_key': public_key})
    return token.decode('ascii')


def deserialize_auth_token(secret_key, token):
    serializer = Serializer(secret_key)
    return serializer.loads(token)
