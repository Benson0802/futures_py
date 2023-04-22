import pandas as pd
import math
import csv
from datetime import datetime
import cls.notify as lineMeg
import numpy as np
import time
from scipy.stats import linregress
import matplotlib.pyplot as plt

class order():
    '''
    建立在一口單的進出
    '''
    def __init__(self,close):
        self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime')
        self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
        self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
        self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime')
        self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
        self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime')
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime')
        self.has_order = False
        if not self.df_trade.empty:
            if self.df_trade.iloc[-1]['type'] == 1:
                self.has_order = True
        self.close = int(close)
        self.loss = 10 #損失幾點出場
        self.balance = 0 #賺or賠 計算方式 => ((賣出部位-收盤部位)*50)-70手續費
        self.total_balance = self.df_trade['balance'].sum() #總賺賠
        self.total_lot = 0 #目前部位
        self.how = 100 #取幾根k做判斷
        
    def strategy1(self):
        '''
        策略1:依傳入的頻率k棒帶入黃金分割率計算目標價
        '''
        print('進入策略1:黃金分割率')
        fc_data = self.fibonacci()
        print(fc_data)
        print('現價:'+str(self.close))
        #判斷有單或沒單
        if self.has_order == True: #有單的話判斷出場
            self.has_order = self.check_loss()
        else: #沒單的話從前一日高點低點開始
            # if is_burst == True:
            #前一日高點視為壓力(誤差容許值五點)
            if self.close in range(fc_data['h4']-5, fc_data['h4']):
                print('現價:'+str(self.close))
                print('高價-5:'+str(fc_data['h4']-5))
                print('高價:'+str(fc_data['h4']))
                self.total_lot = 1
                self.trade(1,-1) #買進空單
                self.has_order = True
            #空方最後防守區(誤差容許值五點)
            elif self.close in range(fc_data['h5']-5, fc_data['h5']):
                print('現價:'+str(self.close))
                print('高價-5:'+str(fc_data['h5']-5))
                print('高價:'+str(fc_data['h5']))
                self.total_lot = 1
                self.trade(1,-1) #買進空單
                self.has_order = True
            #多方滿足點(誤差容許值五點)
            elif self.close in range(fc_data['h8']-5, fc_data['h8']):
                print('現價:'+str(self.close))
                print('高價-5:'+str(fc_data['h8']-5))
                print('高價:'+str(fc_data['h8']))
                self.total_lot = 1
                self.trade(1,-1) #買進空單
                self.has_order = True
            #前一日最低點(誤差容許值五點)
            elif self.close in range(fc_data['l4'], fc_data['l4']+5):
                print('現價:'+str(self.close))
                print('低價:'+str(fc_data['l4']))
                print('低價+5:'+str(fc_data['l4']+5))
                self.total_lot = 1
                self.trade(1,1) #買進多單
                self.has_order = True
            #空方最後防守區(誤差容許值五點)
            elif self.close in range(fc_data['l5'], fc_data['l5']+5):
                print('現價:'+str(self.close))
                print('低價:'+str(fc_data['l5']))
                print('低價+5:'+str(fc_data['l5']+5))
                self.total_lot = 1
                self.trade(1,1) #買進多單
                self.has_order = True
            #空方滿足區(誤差容許值五點)
            elif self.close in range(fc_data['l8'], fc_data['l8']+5):
                print('現價:'+str(self.close))
                print('低價:'+str(fc_data['l8']))
                print('低價+5:'+str(fc_data['l8']+5))
                self.total_lot = 1
                self.trade(1,1) #買進多單
                self.has_order = True
                  
        return self.has_order
    
    def strategy2(self):
        '''
        道式理論123及2b法則，停損則是跌破上升趨勢或下降趨勢
        '''
        self.check_trend(1)
        exit()
        # trend = self.check_trend(60)
        # is_2b = self.check_2b(trend,60)
        # print('目前趨勢:'+str(trend))
        # print('是否2b:'+str(is_2b))
        # if self.has_order is False: #沒單才進場
        #     if trend == 1: #上升趨勢買進
        #         if is_2b: #符合2b
        #             self.trade(1, 1) #買進多單
        #             self.has_order = True
        #     elif trend == -1: #下降趨勢放空
        #         if is_2b: #符合2b
        #             self.trade(1, -1) #買進空單
        #             self.has_order = True
        #     else:
        #         print('條件不成立繼續龜!')
        # else:#有單判斷是否停損
        #     self.has_order = self.check_loss()
        
        # return self.has_order
    
    def strategy3(self):
        '''
        使用60k的支撐壓力判斷是否破底翻再進場
        '''
        if self.has_order is False: #沒單才進場
            ps = self.get_ps(60)
            if self.close in range(ps['high'], ps['high']+10):
                print('現價:'+str(self.close))
                print("h:"+str(ps['high']))
                print('hh:'+str(ps['high']+10))
                #睡一秒後判斷是否為假突破
                time.sleep(1)
                #is_fo = self.check_fo(5)
                #if is_fo == True:
                self.trade(1, -1) #買進空單
                self.has_order = True       
            elif self.close in range(ps['low']-10, ps['low']):
                print('現價:'+str(self.close))
                print("l:"+str(ps['low']-10))
                print('ll:'+str(ps['low']))
                #睡一秒後判斷是否為破底翻
                time.sleep(1)
                #is_bto = self.check_bto(5)
                #if is_bto == True:
                self.trade(1, 1) #買進多單
                self.has_order = True
            else:
                print('條件不成立繼續龜!')
                
        else:#有單判斷是否停損
            self.has_order = self.check_loss()
        return self.has_order
    
    def check_trend(self,minute):
        '''
        判斷趨勢
        '''
        df = None
        if minute == 1:
            df = self.df_1Min.tail(self.how).reset_index(drop=False)
        elif minute == 5:
            df = self.df_5Min.tail(self.how).reset_index(drop=False)
        elif minute == 15:
            df = self.df_15Min.tail(self.how).reset_index(drop=False)
        elif minute == 30:
            df = self.df_30Min.tail(self.how).reset_index(drop=False)
        elif minute == 60:
           df = self.df_60Min.tail(self.how).reset_index(drop=False)
           
        df_n = df.reset_index()
        reg_up = linregress(x = df_n.index,y = df_n.close)
        up_line = reg_up[1] + reg_up[0] * df_n.index
        df_temp_low = df_n[df_n["close"] < up_line]
        df_temp_high = df_n[df_n["close"] > up_line]

        while len(df_temp_low) >= 5 :
            reg_low = linregress(x = df_temp_low.index,y = df_temp_low.close)
            up_line_low = reg_low[1] + reg_low[0] * df_n.index
            df_temp_low = df_n[df_n["close"] < up_line_low]

        while len(df_temp_high) >= 5 :
            reg_high = linregress(x = df_temp_high.index,y = df_temp_high.close)
            up_line_high = reg_high[1] + reg_high[0] * df_n.index
            df_temp_high = df_n[df_n["close"] > up_line_high]

        df_n["low_trend"] = reg_low[1] + reg_low[0] * df_n.index
        df_n["high_trend"] = reg_high[1] + reg_high[0] * df_n.index
        
        plt.plot(df_n["close"])
        plt.plot(df_n["low_trend"])
        plt.plot(df_n["high_trend"])
        plt.title(str(minute)+'Min')
        plt.show()
        
        low_value = int(df_n["low_trend"].iloc[-1])
        high_value = int(df_n["high_trend"].iloc[-1])

        return {"low": low_value, "high": high_value}
    
    # def check_fo(self,minute):
    #     '''
    #     檢查是否發生假突破
    #     '''
    #     df = None
    #     if minute == 1:
    #         df = self.df_1Min.tail(self.how)
    #     elif minute == 5:
    #         df = self.df_5Min.tail(self.how)
    #     elif minute == 15:
    #         df = self.df_15Min.tail(self.how)
    #     elif minute == 30:
    #         df = self.df_30Min.tail(self.how)
    #     elif minute == 60:
    #         df = self.df_60Min.tail(self.how)
            
    #     # 計算均線及rsi
    #     df['ma'] = ta.trend.sma_indicator(df['close'], window=20)
    #     df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    #     # 判断是否为假突破
    #     if df['close'][0] > df['ma'][0] and df['close'][1] < df['ma'][1] and df['rsi'][1] > 70 and df['volume'][1] < df['volume'].rolling(20).mean()[1]:
    #         print('假突破')
    #         return True
    #     else:
    #         print('非假突破')
    #         return False
            
    # def check_bto(self,minute):
    #     '''
    #     檢查是否發生破底翻
    #     '''
    #     df = None
    #     if minute == 1:
    #         df = self.df_1Min.tail(self.how)
    #     elif minute == 5:
    #         df = self.df_5Min.tail(self.how)
    #     elif minute == 15:
    #         df = self.df_15Min.tail(self.how)
    #     elif minute == 30:
    #         df = self.df_30Min.tail(self.how)
    #     elif minute == 60:
    #         df = self.df_60Min.tail(self.how)
            
    #     # 計算均線及rsi
    #     df['ma'] = ta.trend.sma_indicator(df['close'], window=20)
    #     df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        
    #     #取前一筆收盤、均線、rsi
    #     last_close = df.iloc[-1]['close']
    #     last_ma = df.iloc[-1]['ma']
    #     last_rsi = df.iloc[-1]['rsi']
    #     if last_close > last_ma and last_rsi > 50:
    #         print('破底翻')
    #         return True
    #     else:
    #         print('沒破底翻')
    #         return False
        
    
    def get_ps(self,minute):
        '''
        取得各分k的支撐及壓力，依傳入的分鐘數來判斷，取20筆來判斷，常用的分鐘數為5分或60分
        '''
        df = None
        if minute == 5:
            df = self.df_5Min.tail(self.how)
        elif minute == 15:
            df = self.df_15Min.tail(self.how)
        elif minute == 30:
            df = self.df_30Min.tail(self.how)
        elif minute == 60:
            df = self.df_60Min.tail(self.how)
            
        # 取得最近一段時間內的最高和最低價格
        high = df['close'].max()
        low = df['close'].min()
        data = {'high':high,'low':low}
        print('現價:',self.close)
        print("壓力:", high)
        print("支撐:", low)
        return data
    
    def check_loss(self):
        '''
        判斷停損及停利，依傳入的分k計算高低點停利
        '''
        fc_data = self.fibonacci()
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]
            if len(df_trade) > 0:
                if df_trade['type'] == 1: #多單/空單的處理
                    self.total_lot = 0
                    if df_trade['lot'] == 1: #有多單的處理
                        #收盤價 < 買進價格-10點
                        if (self.close < (df_trade['price'] - self.loss)):
                            self.balance = ((self.close - df_trade['price'])*50)-70 #計算賺賠
                            print('多單停損')
                            self.trade(-1,-1) #多單停損
                            return False
                        #滿足點h7回補，容許值10點
                        elif self.close in range(fc_data['h7']-10, fc_data['h7']):
                            self.balance = ((self.close - df_trade['price'])*50)-70 #計算賺賠
                            print('多單停利')
                            self.trade(-1,-1) #多單停利
                            return False
                        else:
                            print('等~~')
                            return self.has_order
                    elif df_trade['lot'] == -1: #空單的處理
                        #收盤價 > 放空價格+10點停損 
                        if (self.close > (df_trade['price'] + self.loss)): 
                            self.balance = ((df_trade['price'] - self.close)*50)-70 #計算賺賠
                            print('空單停損')
                            self.trade(-1, 1) #空單回補
                            return False
                        # 滿足點l7回補，容許值10點
                        elif self.close in range(fc_data['l7'], fc_data['l7']+10):
                            self.balance = ((df_trade['price'] - self.close)*50)-70 #計算賺賠
                            print('空單停利')
                            self.trade(-1, 1) #空單停利
                            return False
                        else:
                            print('等~~'+str(self.has_order))
                            return self.has_order
    def fibonacci(self):
        '''
        用前一日開盤價帶入費波南希列數取得各級價差
        '''
        df_1day = self.df_1day.iloc[-1]
        ed = df_1day['high'] - df_1day['low'] #計算高低差
        data = {
            'h8':df_1day['high'] + ed * 1,#過高倍數1
            'h7':math.ceil(df_1day['high'] + ed * 0.75),#過高倍數0.75
            'h6':math.ceil(df_1day['high'] + ed * 0.5),#過高倍數0.5
            'h5':math.ceil(df_1day['high'] + ed * 0.382),#過高倍數0.382(空方最後防守點)
            'h4':df_1day['high'],#前一日最高點
            'h3':math.ceil(ed*0.764+df_1day['low']),#扭轉空翻多
            'h2':math.ceil(ed/3*2+df_1day['low']),#3分之2
            'h1':math.ceil(ed*0.618+df_1day['low']),#高點0.618(空方防守點)
            'un':math.ceil(ed*0.5+df_1day['low']),#中值(多空互換區)
            'l1':math.ceil(ed*0.382+df_1day['low']),#高點0.382(多方防守點)
            'l2':math.ceil(ed/3+df_1day['low']),#3分之1'
            'l3':math.ceil(ed*0.236+df_1day['low']),#扭轉多翻空
            'l4':df_1day['low'], #前一日最低點
            'l5':math.ceil(df_1day['low']-ed*0.382),#過低倍數0.382(多方最後防守點)
            'l6':math.ceil(df_1day['low']-ed*0.5),#過低倍數0.5
            'l7':math.ceil(df_1day['low']-ed*0.75),#過低倍數0.75
            'l8':df_1day['low']-ed*1 #過低倍數1  
        }
        
        return data
        
    def check_2b(self,trend,minute):
        '''
        2b法則判斷
        '''
        df = None
        if minute == 5:
            df = self.df_5Min.tail(self.how)
        elif minute == 15:
            df = self.df_15Min.tail(self.how)
        elif minute == 30:
            df = self.df_30Min.tail(self.how)
        elif minute == 60:
            df = self.df_60Min.tail(self.how)
            
        if trend == 0:
            return False

        if trend == 1:
            # 上升趨勢，用前一波的最低點作為判斷標準
            low_points = []
            low_flag = False
            last_low = 0
            for i in range(1, len(df)):
                if df['low'][i] < df['low'][i-1]:
                    low_flag = True
                    low_points.append(df['low'][i])
                elif df['low'][i] > df['low'][i-1] and low_flag:
                    # 當出現高點時，將 low_flag 設為 False
                    low_flag = False
                    # 取前一波的最低點
                    last_low = min(low_points)
                    # 重新初始化 low_points
                    low_points = []
                elif df['low'][i] == df['low'][i-1] and low_flag:
                    low_points.append(df['low'][i])
            print('上升趨勢做多')
            print('現價:'+str(self.close))
            print('前低+5:'+str(last_low+5))
            print('前高-5:'+str(last_low-5))
            # 判斷是否符合 2B 條件
            if self.close >= int(last_low+5) and self.close <= int(last_low-5):
                return True

        elif trend == -1:
            # 下降趨勢，用前一波的高點作為判斷標準
            high_points = []
            high_flag = False
            last_high = 0
            for i in range(1, len(df)):
                if df['high'][i] > df['high'][i-1]:
                    high_flag = True
                    high_points.append(df['high'][i])
                elif df['high'][i] < df['high'][i-1] and high_flag:
                    # 當出現低點時，將 high_flag 設為 False
                    high_flag = False
                    # 取前一波的高點
                    last_high = max(high_points)
                    # 重新初始化 high_points
                    high_points = []
                elif df['high'][i] == df['high'][i-1] and high_flag:
                    high_points.append(df['high'][i])

            # 判斷是否符合 2B 條件
            print('下降趨勢放空')
            print('現價:'+str(self.close))
            print('前高+5:'+str(last_high+5))
            print('前高-5:'+str(last_high-5))
            if int(self.close) >= int(last_high-5) and int(self.close) <= int(last_high+5):
                return True

        return False
            
    def trade(self,type,lot):
        '''
        買/回補 or 賣或放空
        type 1:進場 -1:出場
        lot 1:買 -1:賣
        '''
        if type == 1 and lot == 1:
            print('買多')
        elif type == 1 and lot == -1:
            print('放空')
        elif type == -1 and lot == 1:
            print('空單回補')
        elif type == -1 and lot == -1:
            print('多單賣出')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total_balance = self.total_balance + self.balance
        with open('data/trade.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now, type, self.close, lot, self.total_lot, self.balance, self.total_balance,0])
            msg = self.lineMsgFormat(now, type, self.close, lot, self.total_lot, self.balance, self.total_balance)
            lineMeg.sendMessage(msg)
            
    def lineMsgFormat(self,datetime,type,price,lot,total_lot,balance,total_balance):
        '''
        串接line訊息
        '''
        msg = datetime+' | '
        if type == 1:
            msg += '買'
        if type == -1:
            msg += '賣'
        if lot == 1:
            msg += '多'
        if lot == -1 :
            msg += '空'
        msg += ' | '+str(price)
        if total_lot == 0:
            msg += ' | 平倉 | 收入:'
            msg += str(balance)
        
        msg += ' | 總盈餘:'
        msg += str(total_balance)

        return msg