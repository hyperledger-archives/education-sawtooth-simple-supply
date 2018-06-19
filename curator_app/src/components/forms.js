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

/**
 * Convenience function for returning partial onValue functions
 */
const stateSetter = state => key => value => { state[key] = value }

/**
 * Returns a labeled form group
 */
const group = (label, ...contents) => {
  return m('.form-group', [
    m('label', label),
    contents
  ])
}

/**
 * Returns a bare input field suitable for use in a form group.
 * Passes its value to a callback, and defaults to required.
 */
const field = (onValue, attrs = null) => {
  const defaults = {
    required: true,
    oninput: m.withAttr('value', onValue)
  }

  return m('input.form-control.mb-1', _.assign(defaults, attrs))
}

/**
 * Returns a labeled input field which passes its value to a callback
 */
const input = (type, onValue, label, required = true) => {
  return group(label, field(onValue, { type, required }))
}

const textInput = _.partial(input, 'text')
const passwordInput = _.partial(input, 'password')

module.exports = {
    group,
    field,
    stateSetter,
    textInput,
    passwordInput
}
