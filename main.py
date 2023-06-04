import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from cls.check_opening import check_opening
import json
from cls.convertK import convertK
from cls.tactics.aisle import aisle
import datetime
import globals
import pandas as pd
from cls.tactics.indicator import indicator

globals.initialize()
obj = check_opening()
year_mon = obj.get_year_mon()
globals.code = 'TXF' + str(year_mon['year']) + ('0' if len(str(year_mon['mon'])) == 1 else '') + str(year_mon['mon'])

with open('API_KEY.json', 'r') as f:
    json_data = json.load(f)
    api = sj.Shioaji()
    api.login(
        api_key=json_data['api_key'],
        secret_key=json_data['secret_key'],
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )
#開盤時間抓tick
api.quote.subscribe(
    api.Contracts.Futures.TXF[globals.code],
    quote_type = sj.constant.QuoteType.Tick,
    version = sj.constant.QuoteVersion.v1,
)
        
@api.on_tick_fop_v1()

def quote_callback(exchange:Exchange, tick:TickFOPv1):
    if tick.simtrade == True: return #避開試搓時間
    ck = convertK(tick,True)
    
    #最後一盤資料寫入csv
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    if current_time == datetime.time(hour=4, minute=59) or current_time == datetime.time(hour=13, minute=44):
        ck.write_tick("tick")
        #最後一盤資料寫入各分k
        if current_time == datetime.time(hour=5, minute=0) or current_time == datetime.time(hour=13, minute=45):
            df_tick = pd.read_csv('data/tick.csv', index_col='datetime')
            for index, row in df_tick.iterrows():
                globals.amount.append(row['close'])
                globals.volume += row['volume']
                        
            now = datetime.datetime.now()
            last_min  = now.strftime('%Y/%m/%d %H:%M:S')
            ck = convertK(tick,True)
            ck.write_1k_bar(last_min,globals.volume,globals.amount)
            ck.convert_k_bar('5Min')
            ck.convert_k_bar('15Min')
            ck.convert_k_bar('30Min')
            ck.convert_k_bar('60Min')
            ck.convert_day_k_bar()
    
    globals.now_min = ck.get_now_min()
    globals.tick_min = ck.get_tick_min()
    
    if globals.now_min == globals.tick_min: #現在的分鐘數與tick分鐘相符合就收集資料
        globals.volume += tick.volume
        if tick.close not in globals.amount: #排除重覆資料
            globals.amount.append(tick.close)
    else:
        ck.write_1k_bar(globals.tick_min,globals.volume,globals.amount)
        #策略判斷
        tactics = aisle(tick.close)
        tactics.run(5)
        # ord = indicator(tick.close)
        # ord.run(5)
        globals.now_min = None
        globals.amount.clear()
        globals.volume = tick.volume
        ck.convert_k_bar('5Min')
        ck.convert_k_bar('15Min')
        ck.convert_k_bar('30Min')
        ck.convert_k_bar('60Min')
        ck.convert_day_k_bar()

threading.Event().wait()
api.logout()