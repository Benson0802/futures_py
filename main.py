import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from cls.check_opening import check_opening
import json
from cls.convertK import convertK
from cls.order import order
import datetime


obj = check_opening()
year_mon = obj.get_year_mon()
code = 'MXF' + str(year_mon['year']) + ('0' if len(str(year_mon['mon'])) == 1 else '') + str(year_mon['mon'])
current_time = datetime.datetime.now().time().replace(microsecond=0)
now_min = ''
tick_min = ''
volume = 0
amount = []

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
    api.Contracts.Futures.MXF[code],
    quote_type = sj.constant.QuoteType.Tick,
    version = sj.constant.QuoteVersion.v1,
)
        
@api.on_tick_fop_v1()

def quote_callback(exchange:Exchange, tick:TickFOPv1):
    global now_min
    global tick_min
    global volume
    global amount

    if tick.simtrade == True: return #避開試搓時間
    ck = convertK(tick,True)
    #寫入csv 比對用
    ck.write_tick("tick")
    now_min = ck.get_now_min(now_min)
    tick_min = ck.get_tick_min()
    if now_min == tick_min: #現在的分鐘數與tick分鐘相符合
        volume += tick.volume
        if tick.close in amount: return #排除重覆資料(理論上不會有)
        amount.append(tick.close)
        ord = order(tick.close)
        ord.strategy1()
        #ord.strategy2()
        #ord.strategy3()
        if len(amount) > 0:
            ck.write_1k_bar(current_time,volume,amount)
            now_min = ''
            amount.clear()
            volume = 0
        else:
            ck.write_1k_bar(tick_min,volume,amount)
            now_min = ''
            amount.clear()
            amount.append(tick.close)
            volume = tick.volume
            ck.convert_k_bar('5Min')
            ck.convert_k_bar('15Min')
            ck.convert_k_bar('30Min')
            ck.convert_k_bar('60Min')
            ck.convert_day_k_bar()

threading.Event().wait()
api.logout()