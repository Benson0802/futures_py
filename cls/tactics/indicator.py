import pandas as pd
from talib import abstract
import globals
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from scipy.stats import linregress
import matplotlib
matplotlib.use('TkAgg')
import threading
from matplotlib.animation import FuncAnimation
import csv
import datetime
import cls.notify as lineMeg
import logging

class indicator():
    '''
    均線+技術指標
    '''
    def __init__(self, close):
        self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime',parse_dates=True)
        self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime',parse_dates=True)
        self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime',parse_dates=True)
        self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime',parse_dates=True)
        self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime',parse_dates=True)
        self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime',parse_dates=True)
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime',parse_dates=True)
        self.has_order = False
        if not self.df_trade.empty:
            if self.df_trade.iloc[-1]['type'] == 1:
                self.has_order = True
        self.close = int(close)
        self.loss = 20  # 損失幾點出場
        self.balance = 0  # 賺or賠 計算方式 => ((賣出部位-收盤部位)*50)-70手續費
        self.total_balance = self.df_trade['balance'].sum()  # 總賺賠
    
    def run(self, minute):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)
        df = None
        if minute == 1:
            df = self.df_1Min.tail(globals.how)
        elif minute == 5:
            df = self.df_5Min.tail(globals.how)
        elif minute == 15:
            df = self.df_15Min.tail(globals.how)
        elif minute == 30:
            df = self.df_30Min.tail(globals.how)
        elif minute == 60:
            df = self.df_60Min.tail(globals.how)
        elif minute == 1440:
            df = self.df_1day.tail(globals.how)

        df.rename(columns={'Turnover':'volume'}, inplace = True) 
        ema200 = abstract.SMA(df['close'], 200)
        ema200_slope = np.diff(ema200)  # 計算EMA60的斜率
        df_last = df.tail(1) #取最後1根k當型態判斷
        #多方k
        CDLDRAGONFLYDOJI = abstract.CDLDRAGONFLYDOJI(df_last['open'], df_last['high'], df_last['low'], df_last['close']) # T型十字
        CDLHAMMER = abstract.CDLHAMMER(df_last['open'], df_last['high'], df_last['low'], df_last['close'])#锤头
        #空方k
        CDLGRAVESTONEDOJI = abstract.CDLGRAVESTONEDOJI(df_last['open'], df_last['high'], df_last['low'], df_last['close']) # 墓碑十字/倒T十字
        CDLINVERTEDHAMMER = abstract.CDLINVERTEDHAMMER(df_last['open'], df_last['high'], df_last['low'], df_last['close']) # 倒锤头
        CDLSHOOTINGSTAR = abstract.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close']) #射击之星
        #多空共用k
        CDLHANGINGMAN = abstract.CDLHANGINGMAN(df_last['open'], df_last['high'], df_last['low'], df_last['close']) #上吊线
        CDLLONGLINE = abstract.CDLLONGLINE(df_last['open'], df_last['high'], df_last['low'], df_last['close'])#长蜡烛
        CDLMARUBOZU = abstract.CDLMARUBOZU(df_last['open'], df_last['high'], df_last['low'], df_last['close'])#實體k無上下引線
        
        if self.has_order == False:# 目前沒單
            #逆向策略抄底
            if (CDLDRAGONFLYDOJI != 0 or CDLHAMMER != 0 or CDLHANGINGMAN != 0 or CDLLONGLINE != 0 or CDLMARUBOZU != 0) and self.close < (int(ema200[-1])-100):
                print("買進多單")
                self.trade(1, 1)  # 買進多單
                self.has_order = True #標記有單
            #逆向策略摸頭
            elif (CDLGRAVESTONEDOJI !=0 or CDLINVERTEDHAMMER !=0 or CDLSHOOTINGSTAR != 0 or CDLHANGINGMAN != 0 or CDLLONGLINE != 0 or CDLMARUBOZU != 0) and self.close > (int(ema200[-1])+100):
                print("買進空單")
                self.trade(1, -1)  # 買進空單
                self.has_order = True #標記有單
            else:
                print('都不符合，等待')
            # #20dema斜率向上且穿過200 sema進多單
            # print(self.close)
            # print(int(ema200[-1]) -5)
            # print(int(ema200[-1]) +5)
            # print(int(ema200_slope[-1]))
            # if ema200_slope[-1] > 0 and self.close in range(int(ema200[-1])-5, int(ema200[-1]) +5):
            #     print("買進多單")
            #     self.trade(1, 1)  # 買進多單
            #     self.has_order = True #標記有單
            # #20dema斜率向下且穿過200 sema進空單
            # elif ema200_slope[-1] < 0 and self.close in range(int(ema200[-1])-5, int(ema200[-1]) +5):
            #     print("買進空單")
            #     self.trade(1, -1)  # 買進空單
            #     self.has_order = True #標記有單
            # else:
            #     print('都不符合，等待')
        else:
            self.has_order = self.check_trend_loss()
            
        if globals.has_thread == False:
            globals.has_thread = True
            thread = threading.Thread(
                target=self.draw_trend, args=(minute, df))
            thread.start()
        
    def draw_trend(self, minute, df):
        '''
        繪製趨勢線
        '''
        mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='binance', marketcolors=mc)
        kwargs = dict(type='candle', mav=(200), volume=True, figratio=(10, 8), figscale=1, title="5Min", style=s)
        fig, ax = mpf.plot(df, **kwargs, returnfig=True)
        
        def update(_):
            # 根據您設定的時間進行更新
            if minute == 1:
                updated_df = self.df_1Min.tail(globals.how)
            elif minute == 5:
                updated_df = self.df_5Min.tail(globals.how)
            elif minute == 15:
                updated_df = self.df_15Min.tail(globals.how)
            elif minute == 30:
                updated_df = self.df_30Min.tail(globals.how)
            elif minute == 60:
                updated_df = self.df_60Min.tail(globals.how)
            elif minute == 1440:
                updated_df = self.df_1day.tail(globals.how)
                
            # 清除現有的圖形並重新繪製更新後的資料
            ax.clear()
            mpf.plot(updated_df, **kwargs, ax=ax)
            
        ani = FuncAnimation(fig, update, interval=60000)
        plt.show()

    def trade(self, type, lot):
        '''
        買/回補 or 賣或放空
        type 1:進場 -1:出場
        lot 1:買 -1:賣
        '''
        if type == 1 and lot == 1:
            print('買多')
            total_lot = 1
        elif type == 1 and lot == -1:
            print('放空')
            total_lot = 1
        elif type == -1 and lot == 1:
            print('空單回補')
            total_lot = 0
        elif type == -1 and lot == -1:
            print('多單賣出')
            total_lot = 0
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.total_balance = self.total_balance + self.balance
        with open('data/trade.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now, type, self.close, lot,
                            total_lot, self.balance, self.total_balance, 0])
            msg = self.lineMsgFormat(
                now, type, self.close, lot, total_lot, self.balance, self.total_balance)
            lineMeg.sendMessage(msg)
            
    def check_trend_loss(self):
        '''
        依支壓出場停損
        '''
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]

            if len(df_trade) > 0:
                if df_trade['type'] == 1:  # 有單時
                    if df_trade['lot'] == 1:  # 有多單的處理
                        # 收盤價 < 買進價格-n點
                        if self.close <= (df_trade['price'] - self.loss):
                            logging.info("多單停損 close "+str(self.close)+"<="+str((df_trade['price'] - self.loss)))
                            self.balance = ((self.close - df_trade['price'])*50)-70  # 計算賺賠
                            print('多單停損')
                            self.trade(-1, -1)  # 多單停損
                            return False

                        # 50點停利
                        if self.close >= (df_trade['price'] + 50):
                            logging.info("多單停利 close"+str(self.close)+">="+str((df_trade['price'] + 50)))
                            self.balance = ((self.close - df_trade['price'])*50)-70  # 計算賺賠
                            print('多單停利')
                            self.trade(-1, -1)  # 多單停利
                            return False
                            

                    elif df_trade['lot'] == -1:  # 空單的處理
                        if (self.close >= (df_trade['price'] + self.loss)):
                            logging.info("空單停損 close "+str(self.close)+">="+str((df_trade['price'] + self.loss)))
                            self.balance = ((df_trade['price'] - self.close)*50)-70  # 計算賺賠
                            print('空單停損')
                            self.trade(-1, 1)  # 空單回補
                            return False

                        if self.close <= (df_trade['price'] - 50):
                            logging.info("空單停利 close "+str(self.close)+"<="+str((df_trade['price'] - 50)))
                            self.balance = ((df_trade['price'] - self.close)*50)-70  # 計算賺賠
                            print('空單停利')
                            self.trade(-1, 1)  # 空單停利
                            return False
    
    def lineMsgFormat(self,datetime,type,price,lot,total_lot,balance,total_balance):
        '''
        串接line訊息
        '''
        print(total_lot)
        msg = datetime+' | '
        if type == 1:
            msg += '買'
        if type == -1:
            msg += '賣'
        if lot == 1:
            msg += '進'
        if lot == -1 :
            msg += '出'
        msg += ' | '+str(price)
        if total_lot == 0:
            msg += ' 平倉 | 收入:'
            msg += str(balance)
        
        msg += ' | 總盈餘:'
        msg += str(total_balance)

        return msg