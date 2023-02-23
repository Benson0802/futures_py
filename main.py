import csv
import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from check_opening import check_opening
import os.path
import json

obj = check_opening()
flag = obj.check_date()
year_mon = obj.get_year_mon()
code = 'MXF' + str(year_mon['year']) + ('0' if len(str(year_mon['mon'])) == 1 else '') + str(year_mon['mon'])
if flag is True:
    with open('API_KEY.json', 'r') as f:
        json_data = json.load(f)
    api = sj.Shioaji()
    api.login(
        api_key=json_data['api_key'],
        secret_key=json_data['secret_key'],
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )
    api.quote.subscribe(
        api.Contracts.Futures.MXF[code],
        quote_type = sj.constant.QuoteType.Tick,
        version = sj.constant.QuoteVersion.v1,
    )

    @api.on_tick_fop_v1()
    def quote_callback(exchange:Exchange, tick:TickFOPv1):
        file_exists = os.path.isfile('data/mydata.csv')
        with open('data/mydata.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                # 如果文件不存在，則寫入標題
                writer.writerow(['商品代碼', '時間', '開盤價', '標的物價格', '買盤成交總量(lot)', '賣盤成交總量(lot)', '均價', '成交價', '最高價(自開盤)', '最低價(自開盤)', '成交額(NTD)', '總成交額(NTD)', '成交量(lot)', '總成交量(lot)', '內外盤別(1: 內盤, 2: 外盤, 0: 無法判定)', '漲跌註記(1: 漲停, 2: 漲, 3: 平盤, 4: 跌, 5: 跌停)', '漲跌', '漲跌幅(%)', '試撮'])

            writer.writerow([str(tick['code']),tick['datetime'],float(tick['open']),float(tick['underlying_price']),int(tick['bid_side_total_vol']),int(tick['ask_side_total_vol']),float(tick['avg_price']),float(tick['close']),float(tick['high']),float(tick['low']),float(tick['amount']),float(tick['total_amount']),int(tick['volume']),int(tick['total_volume']),int(tick['tick_type']),int(tick['chg_type']),float(tick['price_chg']),float(tick['pct_chg']),int(tick['simtrade'])])
            print(tick)
            file.close()

threading.Event().wait()

api.logout()