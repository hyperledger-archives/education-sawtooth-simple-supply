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

import re
import logging
import math

import psycopg2
from sawtooth_sdk.protobuf.transaction_receipt_pb2 import StateChangeList

from simple_supply_addressing.addresser import AddressSpace
from simple_supply_addressing.addresser import NAMESPACE
from simple_supply_subscriber.decoding import deserialize_data


MAX_BLOCK_NUMBER = int(math.pow(2, 63)) - 1
NAMESPACE_REGEX = re.compile('^{}'.format(NAMESPACE))
LOGGER = logging.getLogger(__name__)


def get_events_handler(database):
    """Returns a events handler with a reference to a specific Database object.
    The handler takes a list of events and updates the Database appropriately.
    """
    return lambda events: _handle_events(database, events)


def _handle_events(database, events):
    block_num, block_id = _parse_new_block(events)
    try:
        is_duplicate = _resolve_if_forked(database, block_num, block_id)
        if not is_duplicate:
            _apply_state_changes(database, events, block_num, block_id)
        database.commit()
    except psycopg2.DatabaseError as err:
        LOGGER.exception('Unable to handle event: %s', err)
        database.rollback()


def _parse_new_block(events):
    try:
        block_attr = next(e.attributes for e in events
                          if e.event_type == 'sawtooth/block-commit')
    except StopIteration:
        return None, None

    block_num = int(next(a.value for a in block_attr if a.key == 'block_num'))
    block_id = next(a.value for a in block_attr if a.key == 'block_id')
    LOGGER.debug('Handling deltas for block: %s', block_id)
    return block_num, block_id


def _resolve_if_forked(database, block_num, block_id):
    existing_block = database.fetch_block(block_num)
    if existing_block is not None:
        if existing_block['block_id'] == block_id:
            return True  # this block is a duplicate
        LOGGER.info(
            'Fork detected: replacing %s (%s) with %s (%s)',
            existing_block['block_id'][:8],
            existing_block['block_num'],
            block_id[:8],
            block_num)
        database.drop_fork(block_num)
    return False


def _apply_state_changes(database, events, block_num, block_id):
    changes = _parse_state_changes(events)
    for change in changes:
        data_type, resources = deserialize_data(change.address, change.value)
        database.insert_block({'block_num': block_num, 'block_id': block_id})
        if data_type == AddressSpace.AGENT:
            _apply_agent_change(database, block_num, resources)
        elif data_type == AddressSpace.RECORD:
            _apply_record_change(database, block_num, resources)
        else:
            LOGGER.warning('Unsupported data type: %s', data_type)


def _parse_state_changes(events):
    try:
        change_data = next(e.data for e in events
                           if e.event_type == 'sawtooth/state-delta')
    except StopIteration:
        return []

    state_change_list = StateChangeList()
    state_change_list.ParseFromString(change_data)
    return [c for c in state_change_list.state_changes
            if NAMESPACE_REGEX.match(c.address)]


def _apply_agent_change(database, block_num, agents):
    for agent in agents:
        agent['start_block_num'] = block_num
        agent['end_block_num'] = MAX_BLOCK_NUMBER
        database.insert_agent(agent)


def _apply_record_change(database, block_num, records):
    for record in records:
        record['start_block_num'] = block_num
        record['end_block_num'] = MAX_BLOCK_NUMBER
        database.insert_record(record)
