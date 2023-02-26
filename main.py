import csv
import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from cls.check_opening import check_opening
import json
from cls.convertK import convertK

obj = check_opening()
flag = obj.check_date()
year_mon = obj.get_year_mon()
code = 'MXF' + str(year_mon['year']) + ('0' if len(str(year_mon['mon'])) == 1 else '') + str(year_mon['mon'])

# 登入
with open('API_KEY.json', 'r') as f:
    json_data = json.load(f)
    api = sj.Shioaji()
    api.login(
        api_key=json_data['api_key'],
        secret_key=json_data['secret_key'],
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )

#開盤時間抓tick
if flag is True:
    api.quote.subscribe(
        api.Contracts.Futures.MXF[code],
        quote_type = sj.constant.QuoteType.Tick,
        version = sj.constant.QuoteVersion.v1,
    )
    @api.on_tick_fop_v1()
    def quote_callback(exchange:Exchange, tick:TickFOPv1):
        ck = convertK(tick)
        # ck.convert_min_k_bar("1Min")
        # ck.convert_min_k_bar("5Min")
        # ck.convert_min_k_bar("60Min")
#非開盤時間抓歷史資料
else:
    #print("目前未開盤!")
    # kbars = api.kbars(
    #     contract=api.Contracts.Futures.MXF[code], 
    #     start='2023-01-02',
    #     end='2023-02-25',
    # )
    # ck = convertK(kbars)
    # ck.convert_min_k_bar('5Min')
    # ck.convert_min_k_bar('15Min')
    # ck.convert_min_k_bar('30Min')
    # ck.convert_min_k_bar('60Min')
    
#threading.Event().wait()

#api.logout()