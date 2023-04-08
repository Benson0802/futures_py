import pandas as pd
import math
import csv
from datetime import datetime
import cls.notify as lineMeg
import numpy as np

class order():
    '''
    建立在一口單的進出
    '''
    def __init__(self,close,has_order,volume):
        self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
        self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
        self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime')
        self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
        self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime')
        self.has_order = has_order
        self.close = int(close)
        self.volume = int(volume)
        self.loss = 10 #損失幾點出場
        self.balance = 0 #賺or賠 計算方式 => ((賣出部位-收盤部位)*50)-70手續費
        self.total_balance = self.df_trade['balance'].sum() #總賺賠
        self.total_lot = 0 #目前部位
        
    def strategy1(self):
        '''
        策略1:用前一日高低差帶入費波南希列數計算高低值
        '''
        print('進入策略1:費波南希列數')
        fc_data = self.fibonacci()
        print(fc_data)
        #判斷有單或沒單
        if self.has_order is True: #有單的話判斷出場
            self.has_order = self.check_loss()
        else: #沒單的話從前一日高點低點開始
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
        df_60Min = self.df_60Min.tail(100)
        trend = self.check_trend(df_60Min)
        trend = -1
        is_2b = self.check_2b(df_60Min,trend)
        
        if self.has_order is False: #沒單才進場
            if trend == 1: #上升趨勢買進
                if is_2b:
                    self.trade(1, 1) #買進多單
                    self.has_order = True
            elif trend == -1: #下降趨勢放空
                if is_2b:
                    self.trade(1, -1) #買進空單
                    self.has_order = True
            else:
                print('條件不成立繼續龜!')
        else:#有單判斷是否停損
            self.has_order = self.check_loss()
        
        return self.has_order
    
    def check_ps(self,minute):
        '''
        判斷各分k的支撐及壓力，依傳入的分鐘數來判斷，取20筆來判斷，常用的分鐘數為5分或60分
        '''
        how = 20
        df = None
        if minute == 5:
            df = self.df_5Min.tail(how)
        elif minute == 15:
            df = self.df_15Min.tail(how)
        elif minute == 30:
            df = self.df_30Min.tail(how)
        elif minute == 60:
            df = self.df_60Min.tail(how)
            
        # 取得最近一段時間內的最高和最低價格
        high = df['close'].max()
        low = df['close'].min()
        data = {'high':high,'low':low}
        
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
                        #滿足點h8回補，容許值10點
                        elif self.close in range(fc_data['h8']-10, fc_data['h8']):
                            self.balance = ((self.close - df_trade['price'])*50)-70 #計算賺賠
                            print('多單停利')
                            self.trade(-1,-1) #多單停利
                            return False
                        else:
                            print('等~~')
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
                            print('等~~')
                            return True
    def fibonacci(self):
        '''
        用前一日開盤價帶入費波南希列數取得各級價差
        '''
        df_1day = self.df_1day.iloc[-2]
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
        
    def check_2b(self,df_60Min,trend):
        '''
        2b法則判斷
        '''
        if trend == 0:
            return False

        if trend == 1:
            # 上升趨勢，用前一波的最低點作為判斷標準
            low_points = []
            low_flag = False
            last_low = 0
            for i in range(1, len(df_60Min)):
                if df_60Min['low'][i] < df_60Min['low'][i-1]:
                    low_flag = True
                    low_points.append(df_60Min['low'][i])
                elif df_60Min['low'][i] > df_60Min['low'][i-1] and low_flag:
                    # 當出現高點時，將 low_flag 設為 False
                    low_flag = False
                    # 取前一波的最低點
                    last_low = min(low_points)
                    # 重新初始化 low_points
                    low_points = []
                elif df_60Min['low'][i] == df_60Min['low'][i-1] and low_flag:
                    low_points.append(df_60Min['low'][i])
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
            for i in range(1, len(df_60Min)):
                if df_60Min['high'][i] > df_60Min['high'][i-1]:
                    high_flag = True
                    high_points.append(df_60Min['high'][i])
                elif df_60Min['high'][i] < df_60Min['high'][i-1] and high_flag:
                    # 當出現低點時，將 high_flag 設為 False
                    high_flag = False
                    # 取前一波的高點
                    last_high = max(high_points)
                    # 重新初始化 high_points
                    high_points = []
                elif df_60Min['high'][i] == df_60Min['high'][i-1] and high_flag:
                    high_points.append(df_60Min['high'][i])

            # 判斷是否符合 2B 條件
            print('下降趨勢放空')
            print('現價:'+str(self.close))
            print('前高+5:'+str(last_high+5))
            print('前高-5:'+str(last_high-5))
            if int(self.close) >= int(last_high-5) and int(self.close) <= int(last_high+5):
                return True

        return False
    
    def check_trend(self,df_60Min):
        '''
        判斷60K的趨勢，取100筆來判斷
        '''
        # 計算每波的最低點
        min_points = []
        min_price = float('inf')
        for i in range(len(df_60Min)):
            if df_60Min.iloc[i]['low'] < min_price:
                min_price = df_60Min.iloc[i]['low']
            if i > 0 and i < len(df_60Min)-1 and df_60Min.iloc[i-1]['low'] > df_60Min.iloc[i]['low'] < df_60Min.iloc[i+1]['low']:
                min_points.append((df_60Min.iloc[i], min_price))
        
        # 計算上升趨勢線
        x = [i for i in range(len(min_points))]
        y = [p[1] for p in min_points]
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        # 計算最新一根 K 棒的位置
        last_price = df_60Min.iloc[-1]['close']
        last_index = len(df_60Min) - 1

        # 計算上升趨勢線的值
        trend_value = p(last_index)

        # 判斷趨勢
        if last_price > trend_value:#目前為上升趨勢
            return 1
        elif last_price < trend_value:#目前為下降趨勢
            return -1
        else:#盤整
            return 0
            
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