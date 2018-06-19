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

const Table = {
  oninit (vnode) {
    if (!vnode.attrs.noRowsText) {
      vnode.attrs.noRowsText = 'No rows available'
    }
  },

  view (vnode) {
    return [
      m('table.table',
        m('thead',
          m('tr',
            vnode.attrs.headers.map((header) => m('th', header)))),
        m('tbody',
          vnode.attrs.rows.length > 0
          ? vnode.attrs.rows
              .map((row) =>
                m('tr',
                  row.map((col) => m('td', col))))
          : m('tr',
              m('td.text-center', { colSpan: vnode.attrs.headers.length },
                vnode.attrs.noRowsText))
        )
      )
    ]
  }
}

module.exports = Table
