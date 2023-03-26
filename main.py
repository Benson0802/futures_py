import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from cls.check_opening import check_opening
import json
from cls.convertK import convertK
import time

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
    
    now_min = ''
    tick_min = ''
    volume = 0
    amount = []
    @api.on_tick_fop_v1()
    def quote_callback(exchange:Exchange, tick:TickFOPv1):
        global now_min
        global tick_min
        global volume
        ck = convertK(tick,True)
        #寫入csv 比對用
        ck.write_tick("tick")
        now_min = ck.get_now_min(now_min)
        tick_min = ck.get_tick_min()
        if now_min > '05:01' and now_min < '08:45': return
        now_time = time.strftime("%H:%M", time.localtime())
        if now_min == tick_min or now_time == "05:00" or now_time == "13:45":
            print('收集1分鐘內的tick資料')
            volume += tick.volume
            if tick.close in amount: return
            amount.append(tick.close)
            if now_time == "05:00" or now_time == "13:45":
                print('轉為1分k')
                ck.write_1k_bar("05:00",volume,amount)
                now_min = ''
                amount.clear()
                volume = 0
                ck.convert_k_bar('5Min')
                ck.convert_k_bar('15Min')
                ck.convert_k_bar('30Min')
                ck.convert_k_bar('60Min')
        else:
            print('轉為1分k')
            ck.write_1k_bar(tick_min,volume,amount)
            now_min = ''
            amount.clear()
            amount.append(tick.close)
            volume = tick.volume
            ck.convert_k_bar('5Min')
            ck.convert_k_bar('15Min')
            ck.convert_k_bar('30Min')
            ck.convert_k_bar('60Min')
        
#非開盤時間抓歷史資料
else:
    kbars = api.kbars(
        contract=api.Contracts.Futures.MXF.MXFR1,
        start='2023-03-20',
        end='2023-03-25',
    )
    ck = convertK(kbars)
    #ck.write_history_1k_bar()
    #ck.convert_k_bar('5Min')
    #ck.convert_k_bar('15Min')
    #ck.convert_k_bar('30Min')
    #ck.convert_k_bar('60Min')
    ck.convert_day_k_bar()
    
# threading.Event().wait()
# api.logout()