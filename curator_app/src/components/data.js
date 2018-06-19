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
const L = require('leaflet')

const MapWidget = {

  view (vnode) {
    return m('#map',  { style: "height:440px;" })
  },

  oncreate (vnode) {
    vnode.state.map = new L.map('map', {
      center: new L.LatLng(44.982853, -93.271967),
      zoom: 10
    })

    L.tileLayer( 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      subdomains: ['a','b','c']
    }).addTo(vnode.state.map)
  },

  onbeforeupdate (vnode, old) {
    // Coordinates exist and have changed
    return vnode.attrs.coordinates &&
      vnode.attrs.coordinates.length !== old.attrs.coordinates.length
  },

  onupdate (vnode) {
    const coordinates = _.sortBy(_.get(vnode.attrs, 'coordinates', []), 'timestamp')
    const latlngs = []
    coordinates.forEach(coord => {
      L.marker([
        coord.latitude / 1e6,
        coord.longitude / 1e6]).addTo(vnode.state.map),
      latlngs.push([coord.latitude / 1e6, coord.longitude / 1e6])
    })
    const path = L.polyline(latlngs).addTo(vnode.state.map)
    vnode.state.map.fitBounds(path.getBounds())
  }
}

module.exports = MapWidget
