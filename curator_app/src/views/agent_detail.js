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
const _ = require('lodash')

const api = require('../services/api')
const layout = require('../components/layout')

/**
 * Displays information for a particular agent
 */
const AgentDetailPage = {
  oninit(vnode) {
    api.get(`agents/${vnode.attrs.publicKey}`)
      .then(agent => {vnode.state.agent = agent})
      .catch(api.alertError)
  },

  view (vnode) {
    const publicKey = _.get(vnode.state, 'agent.public_key', '')
    const timestamp = new Date(
      _.get(vnode.state, 'agent.timestamp', '') * 1000).toString()
    return [
      layout.title(_.get(vnode.state, 'agent.name', '')),
      m('.container',
        layout.row(layout.staticField('Public Key', publicKey)),
        layout.row(layout.staticField('Registered', timestamp)))
    ]
  }
}

module.exports = AgentDetailPage
