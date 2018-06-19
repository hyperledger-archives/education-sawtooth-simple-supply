/**
 * Copyright 2018 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ----------------------------------------------------------------------------
 */

'use strict'

const m = require('mithril')
const sortBy = require('lodash/sortBy')
const Table = require('../components/tables.js')
const api = require('../services/api')

const AgentList = {
  oninit (vnode) {
    vnode.state.agents = []

    const refresh = () => {
      api.get('agents').then((agents) => {
        vnode.state.agents = sortBy(agents, 'name')
      })
        .then(() => { vnode.state.refreshId = setTimeout(refresh, 2000) })
    }

    refresh()
  },

  onbeforeremove (vnode) {
    clearTimeout(vnode.state.refreshId)
  },

  view (vnode) {
    return [
      m('.agent-list',
        m(Table, {
          headers: [
            'Name',
            'Key'
          ],
          rows: vnode.state.agents
            .map((agent) => [
              m(`a[href=/agents/${agent.public_key}]`,
                { oncreate: m.route.link },
                agent.name),
              agent.public_key,
            ]),
          noRowsText: 'No agents found'
        })
      )
    ]
  }
}

module.exports = AgentList
