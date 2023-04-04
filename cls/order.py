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
    def __init__(self,close,has_order):
        self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
        self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
        self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
        self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime')
        self.has_order = has_order
        self.close = close
        self.loss = 10 #損失幾點出場
        self.balance = 0 #賺or賠 計算方式 => ((賣出部位-收盤部位)*50)-70手續費
        self.total_balance = self.df_trade['balance'].sum() #總賺賠
        self.total_lot = 0 #目前部位
        
    def strategy1(self):
        '''
        策略1:用前一筆15分k帶入波浪理論中的比率值來取得最高最低
        H2~H3放空或出場，突破h3或-10點出場
        L2~L3出掉或進場，跌破l3或-10點出場
        '''
        print('進入策略1:波浪理論')
        df_15Min = self.df_15Min.iloc[-1]
        h3 = math.ceil(df_15Min['high'] + (df_15Min['high'] - df_15Min['low']) * 4.236)
        l3 = math.floor(df_15Min['low'] - (df_15Min['high'] - df_15Min['low']) * 4.236)
        h2 = math.ceil(df_15Min['high'] + (df_15Min['high'] - df_15Min['low']) * 2.618)
        l2 = math.floor(df_15Min['low'] - (df_15Min['high'] - df_15Min['low']) * 2.618)
        h1 = math.ceil(df_15Min['high'] + (df_15Min['high'] - df_15Min['low']) * 1.618)
        l1 = math.floor(df_15Min['low'] - (df_15Min['high'] - df_15Min['low']) * 1.618)
        h = math.ceil(df_15Min['high'] + (df_15Min['high'] - df_15Min['low']) * 0.618)
        l = math.floor(df_15Min['low'] - (df_15Min['high'] - df_15Min['low']) * 0.618)
        #判斷有單或沒單
        if self.has_order is True: #有單的話判斷買進或放空，並比較現價是否達停損或決定是否出場
            self.has_order = self.check_loss(df_15Min)
                                        
        else: #沒單的話判斷現在價位是否達H2~H3或L2~L2來決定是否買進或放空
            if self.close >= h2 and self.close <= h3: #價格在高檔時
                self.total_lot = 1
                self.trade(1,-1) #買進空單
                self.has_order = True
            elif self.close <= l2 and self.close >= l3: #價格在低檔時
                self.total_lot = 1
                self.trade(1,1) #買進多單
                self.has_order = False
                
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
            self.has_order = self.check_loss(df_60Min)
        
        return self.has_order
     
    def check_loss(self,df):
        '''
        判斷停損及停利，依傳入的分k計算高低點停利
        '''
        h3 = math.ceil(df['high'] + (df['high'] - df['low']) * 4.236)
        l3 = math.floor(df['low'] - (df['high'] - df['low']) * 4.236)
        h2 = math.ceil(df['high'] + (df['high'] - df['low']) * 2.618)
        l2 = math.floor(df['low'] - (df['high'] - df['low']) * 2.618)
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]
            if len(df_trade) > 0:
                if df_trade['type'] == 1: #多單/空單的處理
                    self.total_lot = 0
                    if df_trade['lot'] == 1: #有多單的處理
                        #收盤價 < 買進價格-10點 =>停損 或 格在高檔時停利
                        if (self.close < (df_trade['price'] - self.loss)) or (self.close >= h2 and self.close <= h3):
                            self.balance = ((self.close - df_trade['price'])*50)-70 #計算賺賠
                            self.trade(-1,-1) #多單停損
                            return False
                    elif df_trade['lot'] == -1: #空單的處理
                        #收盤價 > 放空價格+10點 停損 或 價格在低檔時停利 
                        if (self.close > (df_trade['price'] + self.loss)) or (self.close <= l2 and self.close >= l3): 
                            self.balance = ((df_trade['price'] - self.close)*50)-70 #計算賺賠
                            self.trade(-1, 1) #空單回補
                            return False
                            
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

            # 判斷是否符合 2B 條件
            if self.close >= last_low:
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
            if self.close <= last_high:
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
        if lot > 0 :
            msg += '買'
        if lot < 0 :
            msg += '賣'
        if type == 1:
            msg += '進'
        if type == -1:
            msg += '出'
        msg += ' | '+str(price)
        if total_lot == 0:
            msg += ' | 平倉 | 收入:'
            msg += str(balance)
        
        msg += ' | 總盈餘:'
        msg += str(total_balance)

        return msg