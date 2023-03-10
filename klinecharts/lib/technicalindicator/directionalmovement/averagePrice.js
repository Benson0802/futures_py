"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

/**
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at

 * http://www.apache.org/licenses/LICENSE-2.0

 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * 成交均线
 */
var _default = {
  name: 'AVP',
  shortName: 'AVP',
  series: 'price',
  precision: 2,
  plots: [{
    key: 'avp',
    title: 'AVP: ',
    type: 'line'
  }],
  calcTechnicalIndicator: function calcTechnicalIndicator(dataList) {
    var totalTurnover = 0;
    var totalVolume = 0;
    return dataList.map(function (kLineData) {
      var avp = {};
      var turnover = kLineData.turnover || 0;
      var volume = kLineData.volume || 0;
      totalTurnover += turnover;
      totalVolume += volume;

      if (totalVolume !== 0) {
        avp.avp = totalTurnover / totalVolume;
      }

      return avp;
    });
  }
};
exports.default = _default;