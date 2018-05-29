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

from aiohttp.web import HTTPNotImplemented


class RouteHandler(object):
    def __init__(self, loop, messenger, database):
        self._loop = loop
        self._messenger = messenger
        self._database = database

    async def authorize(self, request):
        raise HTTPNotImplemented()

    async def create_agent(self, request):
        raise HTTPNotImplemented()

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
