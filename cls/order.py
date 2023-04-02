import pandas as pd
import math
import csv
from datetime import datetime
import cls.notify as lineMeg

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
        df_trade = None
        df_15Min = self.df_15Min.iloc[-1]
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]
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
            if len(df_trade) > 0:
                if df_trade['type'] == 1: #多單/空單的處理
                    self.total_lot = 0
                    if df_trade['lot'] == 1: #有多單的處理
                        #收盤價 < 買進價格-10點 =>停損 或 格在高檔時停利
                        if (self.close < (df_trade['price'] - self.loss)) or (self.close >= h2 and self.close <= h3):
                            self.balance = ((df_trade['price'] - self.close)*50)-70 #計算賺賠
                            self.trade(-1,-1) #多單停損
                            self.has_order = False
                    elif df_trade['lot'] == -1: #空單的處理
                        #收盤價 > 放空價格+10點 停損 或 價格在低檔時停利
                        if (self.close > (df_trade['price'] + self.loss)) or (self.close <= l2 and self.close >= l3): 
                            self.balance = ((df_trade['price'] - self.close)*50)-70 #計算賺賠
                            self.trade(-1, 1) #空單回補
                            self.has_order = False
                            
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
        
        
    def trade(self,type,lot):
        '''
        買/回補 or 賣或放空
        type 1:進場 -1:出場
        lot 1:買 -1:賣
        '''
        now = datetime.now().strftime("%Y%m%d%H%M%S")
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