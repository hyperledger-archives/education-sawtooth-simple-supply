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
import sys
import time
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError

from sawtooth_cli.rest_client import RestClient

from sawtooth_rest_api.protobuf import batch_pb2

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory

from simple_supply_rest_api import transaction_creation


def make_key():
    context = create_context('secp256k1')
    private_key = context.new_random_private_key()
    signer = CryptoFactory(context).new_signer(private_key)
    return signer


REST_URL = 'rest-api:8008'
BATCH_KEY = make_key()
LOGGER = logging.getLogger(__name__)


class SimpleSupplyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wait_for_rest_apis([REST_URL])
        cls.client = SimpleSupplyClient(REST_URL)
        cls.signer1 = make_key()
        cls.signer2 = make_key()

    def test_00_timestamp(self):
        """ Tests the timestamp validation rules.

        Notes:
            timestamp validation rules:
                - The timestamp must be less than the current time
        """
        self.assertEqual(
            self.client.create_agent(
                key=self.signer1,
                name='alice',
                timestamp=sys.maxsize)[0]['status'],
            "INVALID",
            "Invalid timestamp")

    def test_01_create_agent(self):
        """ Tests the CreateAgentAction validation rules.

        Notes:
            CreateAgentAction validation rules:
                - The public_key must be unique for all accounts
        """

        self.assertEqual(
            self.client.create_agent(
                key=self.signer1,
                name='alice',
                timestamp=1)[0]['status'],
            "COMMITTED")

        self.assertEqual(
            self.client.create_agent(
                key=self.signer1,
                name='alice',
                timestamp=2)[0]['status'],
            "INVALID",
            "Account with the public key {} already exists".format(
                self.signer1.get_public_key().as_hex()))

        self.assertEqual(
            self.client.create_agent(
                key=self.signer2,
                name='alice',
                timestamp=1)[0]['status'],
            "COMMITTED")

class SimpleSupplyClient(object):

    def __init__(self, url):
        self._client = RestClient(base_url="http://{}".format(url))

    def create_agent(self, key, name, timestamp):
        batch = transaction_creation.make_create_agent_transaction(
            transaction_signer=key,
            batch_signer=BATCH_KEY,
            name=name,
            timestamp=timestamp)
        batch_id = batch.header_signature
        batch_list = batch_pb2.BatchList(batches=[batch])
        self._client.send_batches(batch_list)
        return self._client.get_statuses([batch_id], wait=10)


def wait_until_status(url, status_code=200, tries=5):
    """Pause the program until the given url returns the required status.

    Args:
        url (str): The url to query.
        status_code (int, optional): The required status code
        tries (int, optional): The number of attempts to request the url for
            the given status. Defaults to 5.
    Raises:
        AssertionError: If the status is not received in the given number of
            tries.
    """

    attempts = tries
    while attempts > 0:
        try:
            response = urlopen(url)
            if response.getcode() == status_code:
                return

        except HTTPError as err:
            if err.code == status_code:
                return

            LOGGER.debug('failed to read url: %s', str(err))
        except URLError as err:
            LOGGER.debug('failed to read url: %s', str(err))

        sleep_time = (tries - attempts + 1) * 2
        LOGGER.debug('Retrying in %s secs', sleep_time)
        time.sleep(sleep_time)

        attempts -= 1

    raise AssertionError(
        "{} is not available within {} attempts".format(url, tries))


def wait_for_rest_apis(endpoints, tries=5):
    """Pause the program until all the given REST API endpoints are available.

    Args:
        endpoints (list of str): A list of host:port strings.
        tries (int, optional): The number of attempts to request the url for
            availability.
    """

    for endpoint in endpoints:
        http = 'http://'
        url = endpoint if endpoint.startswith(http) else http + endpoint
        wait_until_status(
            '{}/blocks'.format(url),
            status_code=200,
            tries=tries)
