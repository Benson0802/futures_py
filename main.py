import shioaji as sj
from shioaji import TickFOPv1, Exchange
import threading
from cls.check_opening import check_opening
import json
from cls.convertK import convertK
from cls.order import order
import time

try: 
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

    now_min = ''
    tick_min = ''
    volume = 0
    has_order = False #是否有單
    amount = []
    #開盤時間抓tick
    if flag is True:
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
            global has_order
            global amount
            ck = convertK(tick,True)
            #寫入csv 比對用
            ck.write_tick("tick")
            now_min = ck.get_now_min(now_min)
            tick_min = ck.get_tick_min()
            if now_min > '05:01' and now_min < '08:45': return
            if now_min == tick_min:
                volume += tick.volume
                if tick.close in amount: return
                amount.append(tick.close)
                ord = order(tick.close,has_order,volume)
                #has_order = ord.strategy1()
                print('是否有單:'+str(has_order))
                #has_order = ord.strategy2()
                has_order = ord.strategy3()
                now_time = time.strftime("%H:%M", time.localtime())
                if now_time == "05:00" or now_time == "13:45":
                    print('5點')
                    print(volume)
                    print(amount)
                    if len(amount) > 0:
                        ck.write_1k_bar("05:00",volume,amount)
                        now_min = ''
                        amount.clear()
                        volume = 0
                        ck.convert_k_bar('5Min')
                        ck.convert_k_bar('15Min')
                        ck.convert_k_bar('30Min')
                        ck.convert_k_bar('60Min')
                        ck.convert_day_k_bar()
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
            
    #非開盤時間抓歷史資料
    else:
        kbars = api.kbars(
            contract=api.Contracts.Futures.MXF.MXFR1,
            start='2023-04-03',
            end='2023-04-08',
        )
        ck = convertK(kbars)
        ck.write_history_1k_bar()
        ck.convert_k_bar('5Min')
        ck.convert_k_bar('15Min')
        ck.convert_k_bar('30Min')
        ck.convert_k_bar('60Min')
        ck.convert_day_k_bar()
        
    if flag == True:
        threading.Event().wait()
        api.logout()
        
except Exception as err:
    print('5點')
    print(err)
    print(volume)
    print(amount)
    now_time = time.strftime("%H:%M", time.localtime())
    if now_time == "05:00" or now_time == "13:45":
        if len(amount) > 0:
            ck = convertK(amount[0])
            ck.write_1k_bar("05:00",volume,amount)
            now_min = ''
            amount.clear()
            volume = 0
            ck.convert_k_bar('5Min')
            ck.convert_k_bar('15Min')
            ck.convert_k_bar('30Min')
            ck.convert_k_bar('60Min')