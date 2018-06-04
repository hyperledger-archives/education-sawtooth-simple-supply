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

import enum
import hashlib


FAMILY_NAME = 'simple_supply'
FAMILY_VERSION = '0.1'
NAMESPACE = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[:6]
AGENT_PREFIX = '00'
RECORD_PREFIX = '01'


@enum.unique
class AddressSpace(enum.IntEnum):
    AGENT = 0
    RECORD = 1

    OTHER_FAMILY = 100


def get_agent_address(public_key):
    return NAMESPACE + AGENT_PREFIX + hashlib.sha512(
        public_key.encode('utf-8')).hexdigest()[:62]


def get_record_address(record_id):
    return NAMESPACE + RECORD_PREFIX + hashlib.sha512(
        record_id.encode('utf-8')).hexdigest()[:62]


def get_address_type(address):
    if address[:len(NAMESPACE)] != NAMESPACE:
        return AddressSpace.OTHER_FAMILY

    infix = address[6:8]

    if infix == '00':
        return AddressSpace.AGENT
    if infix == '01':
        return AddressSpace.RECORD

    return AddressSpace.OTHER_FAMILY
