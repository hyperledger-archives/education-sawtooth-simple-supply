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
const parsing = require('../services/parsing')
const layout = require('../components/layout')
const MapWidget = require('../components/data')
const forms = require('../components/forms')

const transferSubmitter = state => e => {
  e.preventDefault()

  const recordId = _.get(state, 'record.record_id', '')
  const transferKeys = ['receiving_agent']
  const transfer = _.pick(state, transferKeys)

  api.post(`records/${recordId}/transfer`, transfer)
    .then(() => m.route.set(`/artworks/${recordId}`))
    .catch(api.alertError)
}

const updateSubmitter = state => e => {
  e.preventDefault()

  const recordId = _.get(state, 'record.record_id', '')
  const updateKeys = ['latitude', 'longitude']
  const update = _.pick(state, updateKeys)
  update.latitude = parsing.toInt(update.latitude)
  update.longitude = parsing.toInt(update.longitude)

  api.post(`records/${recordId}/update`, update)
    .then(() => m.route.set(`/artworks/${recordId}`))
    .catch(api.alertError)
}

const ArtworkDetailPage = {
  oninit(vnode) {
    api.get(`records/${vnode.attrs.recordId}`)
      .then(record => {vnode.state.record = record})
      .catch(api.alertError)
  },

  view (vnode) {
    const setter = forms.stateSetter(vnode.state)
    const recordId = _.get(vnode.state, 'record.record_id', '')
    const coordinates = _.get(vnode.state, 'record.locations', [])
    const created = new Date(
      _.get(_.minBy(coordinates, 'timestamp'), 'timestamp') * 1000).toString()
    const updated = new Date(
      _.get(_.maxBy(coordinates, 'timestamp'), 'timestamp') * 1000).toString()
    const owners = _.get(vnode.state, 'record.owners', [])
    const owner = _.get(_.maxBy(owners, 'timestamp'), 'agent_id', '')
    return [
      layout.title(recordId),
      m('.container',
        layout.row(layout.staticField('Owner', owner)),
        layout.row(layout.staticField('Created', created)),
        layout.row(layout.staticField('Updated', updated))),
      m(MapWidget, {
        coordinates: coordinates
      }),
      layout.row(
        (owner == api.getPublicKey())
        ? m('.update-form', [
          m('form', { onsubmit: updateSubmitter(vnode.state, recordId) },
          m('legend', 'Update Location'),
          layout.row([
            forms.group('Latitude', forms.field(setter('latitude'), {
              type: 'number',
              step: 'any',
              min: -90,
              max: 90,
            })),
            forms.group('Longitude', forms.field(setter('longitude'), {
              type: 'number',
              step: 'any',
              min: -180,
              max: 180,
            }))
          ]),
          m('.form-group',
            m('.row.justify-content-end.align-items-end',
              m('col-2',
                m('button.btn.btn-primary',
                  'Update Location')))))
          ])
        : ''),
      layout.row(
        (owner == api.getPublicKey())
        ? m('transfer-form', [
          m('form', { onsubmit: transferSubmitter(vnode.state, recordId) },
          m('legend', 'Transfer Ownership'),
          layout.row([
            forms.group('Public Key', forms.field(setter('receiving_agent'), {
              type: 'string'
            }))
          ]),
          m('.form-group',
            m('.row.justify-content-end.align-items-end',
              m('col-2',
                m('button.btn.btn-primary',
                  'Transfer Ownership')))))
          ])
        : '')
    ]
  }
}

module.exports = ArtworkDetailPage
