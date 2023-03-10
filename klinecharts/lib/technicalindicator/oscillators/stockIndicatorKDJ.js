"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _calcHnLn = _interopRequireDefault(require("../calcHnLn"));

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
 * KDJ
 *
 * 当日K值=2/3×前一日K值+1/3×当日RSV
 * 当日D值=2/3×前一日D值+1/3×当日K值
 * 若无前一日K 值与D值，则可分别用50来代替。
 * J值=3*当日K值-2*当日D值
 */
var _default = {
  name: 'KDJ',
  shortName: 'KDJ',
  calcParams: [9, 3, 3],
  plots: [{
    key: 'k',
    title: 'K: ',
    type: 'line'
  }, {
    key: 'd',
    title: 'D: ',
    type: 'line'
  }, {
    key: 'j',
    title: 'J: ',
    type: 'line'
  }],
  calcTechnicalIndicator: function calcTechnicalIndicator(dataList, _ref) {
    var params = _ref.params;
    var result = [];
    dataList.forEach(function (kLineData, i) {
      var kdj = {};
      var close = kLineData.close;

      if (i >= params[0] - 1) {
        var lhn = (0, _calcHnLn.default)(dataList.slice(i - (params[0] - 1), i + 1));
        var ln = lhn.ln;
        var hn = lhn.hn;
        var hnSubLn = hn - ln;
        var rsv = (close - ln) / (hnSubLn === 0 ? 1 : hnSubLn) * 100;
        kdj.k = ((params[1] - 1) * (result[i - 1].k || 50) + rsv) / params[1];
        kdj.d = ((params[2] - 1) * (result[i - 1].d || 50) + kdj.k) / params[2];
        kdj.j = 3.0 * kdj.k - 2.0 * kdj.d;
      }

      result.push(kdj);
    });
    return result;
  }
};
exports.default = _default;