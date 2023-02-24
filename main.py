import csv
import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from check_opening import check_opening
import os.path
import json
from convertK import convertK

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
        ck = convertK(tick)
        ck.convert_k_bar("1Min")
        ck.convert_k_bar("5Min")
        ck.convert_k_bar("15Min")
        ck.convert_k_bar("30Min")
        ck.convert_k_bar("60Min")
        ck.convert_k_bar("D")
        ck.convert_k_bar("W")
        ck.convert_k_bar("M")
        
        
threading.Event().wait()

api.logout()