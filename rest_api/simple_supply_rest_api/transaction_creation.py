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

import hashlib

from sawtooth_rest_api.protobuf import batch_pb2
from sawtooth_rest_api.protobuf import transaction_pb2

from simple_supply_addressing import addresser

from simple_supply_protobuf import payload_pb2


def make_create_agent_transaction(transaction_signer,
                                  batch_signer,
                                  name,
                                  timestamp):
    """Make a CreateAgentAction transaction and wrap it in a batch

    Args:
        transaction_signer (sawtooth_signing.Signer): The transaction key pair
        batch_signer (sawtooth_signing.Signer): The batch key pair
        name (str): The agent's name
        timestamp (int): Unix UTC timestamp of when the agent is created

    Returns:
        batch_pb2.Batch: The transaction wrapped in a batch

    """

    agent_address = addresser.get_agent_address(
        transaction_signer.get_public_key().as_hex())

    inputs = [agent_address]

    outputs = [agent_address]

    action = payload_pb2.CreateAgentAction(name=name)

    payload = payload_pb2.SimpleSupplyPayload(
        action=payload_pb2.SimpleSupplyPayload.CREATE_AGENT,
        create_agent=action,
        timestamp=timestamp)
    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer)


def make_create_record_transaction(transaction_signer,
                                   batch_signer,
                                   latitude,
                                   longitude,
                                   record_id,
                                   timestamp):
    """Make a CreateRecordAction transaction and wrap it in a batch

    Args:
        transaction_signer (sawtooth_signing.Signer): The transaction key pair
        batch_signer (sawtooth_signing.Signer): The batch key pair
        latitude (int): Initial latitude of the record
        longitude (int): Initial latitude of the record
        record_id (str): Unique ID of the record
        timestamp (int): Unix UTC timestamp of when the agent is created

    Returns:
        batch_pb2.Batch: The transaction wrapped in a batch
    """

    inputs = [
        addresser.get_agent_address(
            transaction_signer.get_public_key().as_hex()),
        addresser.get_record_address(record_id)
    ]

    outputs = [addresser.get_record_address(record_id)]

    action = payload_pb2.CreateRecordAction(
        record_id=record_id,
        latitude=latitude,
        longitude=longitude)

    payload = payload_pb2.SimpleSupplyPayload(
        action=payload_pb2.SimpleSupplyPayload.CREATE_RECORD,
        create_record=action,
        timestamp=timestamp)
    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer)


def make_transfer_record_transaction(transaction_signer,
                                     batch_signer,
                                     receiving_agent,
                                     record_id,
                                     timestamp):
    """Make a CreateRecordAction transaction and wrap it in a batch

    Args:
        transaction_signer (sawtooth_signing.Signer): The transaction key pair
        batch_signer (sawtooth_signing.Signer): The batch key pair
        receiving_agent (str): Public key of the agent receiving the record
        record_id (str): Unique ID of the record
        timestamp (int): Unix UTC timestamp of when the record is transferred

    Returns:
        batch_pb2.Batch: The transaction wrapped in a batch
    """
    sending_agent_address = addresser.get_agent_address(
        transaction_signer.get_public_key().as_hex())
    receiving_agent_address = addresser.get_agent_address(receiving_agent)
    record_address = addresser.get_record_address(record_id)

    inputs = [sending_agent_address, receiving_agent_address, record_address]

    outputs = [record_address]

    action = payload_pb2.TransferRecordAction(
        record_id=record_id,
        receiving_agent=receiving_agent)

    payload = payload_pb2.SimpleSupplyPayload(
        action=payload_pb2.SimpleSupplyPayload.TRANSFER_RECORD,
        transfer_record=action,
        timestamp=timestamp)
    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer)


def make_update_record_transaction(transaction_signer,
                                   batch_signer,
                                   latitude,
                                   longitude,
                                   record_id,
                                   timestamp):
    """Make a CreateRecordAction transaction and wrap it in a batch

    Args:
        transaction_signer (sawtooth_signing.Signer): The transaction key pair
        batch_signer (sawtooth_signing.Signer): The batch key pair
        latitude (int): Updated latitude of the location
        longitude (int): Updated longitude of the location
        record_id (str): Unique ID of the record
        timestamp (int): Unix UTC timestamp of when the record is updated

    Returns:
        batch_pb2.Batch: The transaction wrapped in a batch
    """
    agent_address = addresser.get_agent_address(
        transaction_signer.get_public_key().as_hex())
    record_address = addresser.get_record_address(record_id)

    inputs = [agent_address, record_address]

    outputs = [record_address]

    action = payload_pb2.UpdateRecordAction(
        record_id=record_id,
        latitude=latitude,
        longitude=longitude)

    payload = payload_pb2.SimpleSupplyPayload(
        action=payload_pb2.SimpleSupplyPayload.UPDATE_RECORD,
        update_record=action,
        timestamp=timestamp)
    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer)


def _make_batch(payload_bytes,
                inputs,
                outputs,
                transaction_signer,
                batch_signer):

    transaction_header = transaction_pb2.TransactionHeader(
        family_name=addresser.FAMILY_NAME,
        family_version=addresser.FAMILY_VERSION,
        inputs=inputs,
        outputs=outputs,
        signer_public_key=transaction_signer.get_public_key().as_hex(),
        batcher_public_key=batch_signer.get_public_key().as_hex(),
        dependencies=[],
        payload_sha512=hashlib.sha512(payload_bytes).hexdigest())
    transaction_header_bytes = transaction_header.SerializeToString()

    transaction = transaction_pb2.Transaction(
        header=transaction_header_bytes,
        header_signature=transaction_signer.sign(transaction_header_bytes),
        payload=payload_bytes)

    batch_header = batch_pb2.BatchHeader(
        signer_public_key=batch_signer.get_public_key().as_hex(),
        transaction_ids=[transaction.header_signature])
    batch_header_bytes = batch_header.SerializeToString()

    batch = batch_pb2.Batch(
        header=batch_header_bytes,
        header_signature=batch_signer.sign(batch_header_bytes),
        transactions=[transaction])

    return batch
