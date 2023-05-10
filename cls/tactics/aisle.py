import pandas as pd
import math
import csv
from datetime import datetime
import cls.notify as lineMeg
import numpy as np
from scipy.stats import linregress
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import globals
import threading
from matplotlib.animation import FuncAnimation
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, LSTM, Dropout, Dense

class aisle():
    def __init__(self, close):
        self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime')
        self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
        self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
        self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime')
        self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
        self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
        self.df_trade = pd.read_csv('data/trade.csv', index_col='datetime')
        self.has_order = False
        if not self.df_trade.empty:
            if self.df_trade.iloc[-1]['type'] == 1:
                self.has_order = True
        self.close = int(close)
        self.loss = 20  # 損失幾點出場
        self.balance = 0  # 賺or賠 計算方式 => ((賣出部位-收盤部位)*50)-70手續費
        self.total_balance = self.df_trade['balance'].sum()  # 總賺賠
        self.levels = None
        
    def run(self, minute):
        '''
        上升通道及下降通道策略
        '''
        trend_line = self.get_trend_data(minute)
        data = self.get_trend_line(trend_line)
        is_breakout = self.has_breakout()
        print(self.levels)
        print(is_breakout)
        print('上線段預測價格:'+str(data['forecast_high']))
        print('下線段預測價格:'+str(data['forecast_low']))
        print('現價:'+str(self.close))
        if self.has_order == False:  # 目前沒單
            if data['trend'] == 0:  # 上空下多做價差
                print('盤整趨勢')
                # 上線段放空
                if self.close in range(data['forecast_high'], data['forecast_high']+10):
                    self.trade(1, -1)  # 買進空單
                    self.has_order = True
                # 下線段買多
                elif self.close in range(data['forecast_low'], data['forecast_low']+10):
                    self.trade(1, 1)  # 買進多單
                    self.has_order = True
                else:
                    print('條件不符合繼續等')
            elif data['trend'] == 1:  # 只有在低點買多
                print('上升趨勢')
                # 下線段買多
                if self.close in range(data['forecast_low'], data['forecast_low']+10):
                    self.trade(1, 1)  # 買進多單
                    self.has_order = True
            elif data['trend'] == 2:  # 只有在高點放空
                print('下降趨勢')
                # 上線段放空
                if self.close in range(data['forecast_high'], data['forecast_high']+10):
                    self.trade(1, -1)  # 買進空單
                    self.has_order = True
        else:  # 目前有單
            self.has_order = self.check_trend_loss(data)
        
        if globals.has_thread == False:
            thread = threading.Thread(
                target=self.draw_trend, args=(minute, trend_line))
            thread.start()
            globals.has_thread = True

    def get_trend_data(self, minute):
        '''
        取得目前趨勢資料
        '''
        df = None
        if minute == 1:
            self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime')
            df = self.df_1Min.tail(globals.how).reset_index(drop=False)
        elif minute == 5:
            self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
            df = self.df_5Min.tail(globals.how).reset_index(drop=False)
        elif minute == 15:
            self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
            df = self.df_15Min.tail(globals.how).reset_index(drop=False)
        elif minute == 30:
            self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime')
            df = self.df_30Min.tail(globals.how).reset_index(drop=False)
        elif minute == 60:
            self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
            df = self.df_60Min.tail(globals.how).reset_index(drop=False)
        elif minute == 1440:
            self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
            df = self.df_1day.tail(globals.how).reset_index(drop=False)

        # 線性回歸計算方式
        df_n = df.reset_index()
        reg_up = linregress(x=df_n.index, y=df_n.close)
        up_line = reg_up[1] + reg_up[0] * df_n.index
        df_temp_low = df_n[df_n["close"] < up_line]
        df_temp_high = df_n[df_n["close"] > up_line]

        while len(df_temp_low) >= 5:
            reg_low = linregress(x=df_temp_low.index, y=df_temp_low.close)
            up_line_low = (reg_low[1] + reg_low[0] *
                           pd.Series(df_n.index)).round().astype(int)
            df_temp_low = df_n[df_n["close"] < up_line_low]

        while len(df_temp_high) >= 5:
            reg_high = linregress(x=df_temp_high.index, y=df_temp_high.close)
            up_line_high = (reg_high[1] + reg_high[0] *
                            pd.Series(df_n.index)).round().astype(int)
            df_temp_high = df_n[df_n["close"] > up_line_high]

        df_n["low_trend"] = (reg_low[1] + reg_low[0] *
                             pd.Series(df_n.index)).round().astype(int)
        df_n["high_trend"] = (reg_high[1] + reg_high[0]
                              * pd.Series(df_n.index)).round().astype(int)
        
        #取得支撐壓力(方法1)
        #self.levels = self.detect_level_method_1(df)
        self.levels = self.detect_level_method_2(df)
        
        for _, level in self.levels:
            df_n["level"+str(level)] = level
        
        return df_n

    def has_breakout(self):
        '''
        檢測支壓，當前一根k低於支撐或壓力位且最後一根開盤價和收盤價低於該水平時返回true
        '''
        self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime')
        previous = self.df_1Min.iloc[-2]
        last = self.df_1Min.iloc[-1]
        for _, level in self.levels:
            cond1 = (previous['open'] < level) 
            cond2 = (last['open'] > level) and (last['low'] > level)
        return (cond1 and cond2)

    def detect_level_method_1(self,df):
        '''
        取得支撐壓力(方法1)
        '''
        levels = []
        for i in range(2,df.shape[0]-2):
            if self.is_support(df,i):
                l = df['low'][i]
                if self.is_far_from_level(l, levels, df):
                    levels.append((i,l))
            elif self.is_resistance(df,i):
                l = df['high'][i]
                if self.is_far_from_level(l, levels, df):
                    levels.append((i,l))
                
        return levels

    def detect_level_method_2(self,df):
        '''
        取得支撐壓力的方法2
        '''
        levels = []
        max_list = []
        min_list = []
        for i in range(5, len(df)-5):
            high_range = df['high'][i-5:i+4]
            current_max = high_range.max()
            if current_max not in max_list:
                max_list = []
            max_list.append(current_max)
            if len(max_list) == 5 and self.is_far_from_level(current_max, levels, df):
                levels.append((high_range.idxmax(), current_max))
            
            low_range = df['low'][i-5:i+5]
            current_min = low_range.min()
            if current_min not in min_list:
                min_list = []
            min_list.append(current_min)
            if len(min_list) == 5 and self.is_far_from_level(current_min, levels, df):
                levels.append((low_range.idxmin(), current_min))
        return levels

    def is_support(self,df,i):
        '''
        取得支撐
        '''
        cond1 = df['low'][i] < df['low'][i-1]   
        cond2 = df['low'][i] < df['low'][i+1]   
        cond3 = df['low'][i+1] < df['low'][i+2]   
        cond4 = df['low'][i-1] < df['low'][i-2]  
        return (cond1 and cond2 and cond3 and cond4) 

    def is_resistance(self,df,i): 
        '''
        取得壓力
        ''' 
        cond1 = df['high'][i] > df['high'][i-1]   
        cond2 = df['high'][i] > df['high'][i+1]   
        cond3 = df['high'][i+1] > df['high'][i+2]   
        cond4 = df['high'][i-1] > df['high'][i-2]  
        return (cond1 and cond2 and cond3 and cond4)

    def is_far_from_level(self , value, levels, df):
        '''
        判斷新的支壓存不存在
        '''
        ave =  np.mean(df['high'] - df['low'])    
        return np.sum([abs(value-level)<ave for _,level in levels])==0

    def get_trend_line(self, df_n):
        '''
        取得趨勢線
        '''
        trend = -1
        first_low = int(df_n["low_trend"].iloc[0])
        first_high = int(df_n["high_trend"].iloc[0])
        last_low = int(df_n["low_trend"].iloc[-1])
        last_high = int(df_n["high_trend"].iloc[-1])
        last_two_low = int(df_n["low_trend"].iloc[-2])
        last_two_high = int(df_n["high_trend"].iloc[-2])
        forecast_low = 0  # 預測下個趨勢線延伸的落點
        forecast_high = 0  # 預測下個趨勢線延伸的落點

        # 判斷趨勢
        # (上升趨勢，上下兩條線的最後一筆同時大於第一筆)
        if last_low > first_low and last_high > first_high:
            trend = 1
            forecast_low = last_low + (last_low - last_two_low)
            forecast_high = last_high + (last_high - last_two_high)
        # (下升趨勢，上下兩條線的最後一筆同時小於第一筆)
        elif last_low < first_low and last_high < first_high:
            trend = 2
            forecast_low = last_low - (last_two_low - last_low)
            forecast_high = last_high - (last_two_high - last_high)
        elif last_high <= first_high and last_low >= first_low:  # 盤整，上線段的最後一筆小於等於第一筆，下線段的最後一筆大於等於第一筆 呈現三角收斂或上下區間
            trend = 0
            forecast_low = last_low
            forecast_high = last_high

        return {"last_low": last_low, "last_high": last_high, 'forecast_low': forecast_low, 'forecast_high': forecast_high, 'trend': trend}

    def draw_trend(self,minute,df_n):
        '''
        繪製趨勢線
        '''
        fig, ax = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        def update(_):
            df_n = self.get_trend_data(minute)
            ax[0].clear()
            ax[1].clear()
            for _, level in self.levels:
                ax[0].plot(df_n["level"+str(level)],linestyle='dashed',label=str(level))
            ax[0].plot(df_n["close"])
            ax[0].plot(df_n["low_trend"])
            ax[0].plot(df_n["high_trend"])
            ax[0].set_title(str(globals.code)+"-"+str(minute)+'Min')
            ax[1].bar(df_n.index, df_n.volume, width=0.4)
            ax[1].set_title("Volume")
            
        ax[0].plot(df_n["close"])
        ax[0].plot(df_n["low_trend"])
        ax[0].plot(df_n["high_trend"])
        for _, level in self.levels:
                ax[0].plot(df_n["level"+str(level)],linestyle='dashed',label=str(level))
        ax[0].set_title(str(globals.code)+"-"+str(minute)+'Min')
        ax[1].bar(df_n.index, df_n.volume, width=0.4)
        ax[1].set_title("Volume")
        
        ani = FuncAnimation(fig, update, interval=600000)
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.total_balance = self.total_balance + self.balance
        with open('data/trade.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now, type, self.close, lot,
                            total_lot, self.balance, self.total_balance, 0])
            msg = self.lineMsgFormat(
                now, type, self.close, lot, total_lot, self.balance, self.total_balance)
            lineMeg.sendMessage(msg)

    def check_trend_loss(self, data):
        '''
        依趨勢線出場或停損
        '''
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]
            if len(df_trade) > 0:
                if df_trade['type'] == 1:  # 有單時
                    if df_trade['lot'] == 1:  # 有多單的處理
                        # 收盤價 < 買進價格-n點
                        if self.close <= (df_trade['price'] - self.loss):
                            self.balance = (
                                (self.close - df_trade['price'])*50)-70  # 計算賺賠
                            print('多單停損')
                            self.trade(-1, -1)  # 多單停損
                            return False

                        # 判斷趨勢停利
                        if data['trend'] == 0 or data['trend'] == 1:  # 盤整或上升趨勢則上線段停利
                            # 上線段停利(容許值上下五點)
                            if self.close in range(data['forecast_high']-5, data['forecast_high']+5):
                                self.balance = (
                                    (self.close - df_trade['price'])*50)-70  # 計算賺賠
                                print('多單停利-趨勢線上')
                                self.trade(-1, -1)  # 多單停利
                                return False

                    elif df_trade['lot'] == -1:  # 空單的處理
                        if (self.close >= (df_trade['price'] + self.loss)):
                            self.balance = (
                                (df_trade['price'] - self.close)*50)-70  # 計算賺賠
                            print('空單停損4')
                            self.trade(-1, 1)  # 空單回補
                            return False

                        # 判斷趨勢停利
                        if data['trend'] == 0 or data['trend'] == 2:  # 盤整或下降趨勢則下線段停利
                            # 下線段停利(容許值上下五點)
                            if self.close in range(data['forecast_low']-5, data['forecast_low']+5):
                                self.balance = (
                                    (df_trade['price'] - self.close)*50)-70  # 計算賺賠
                                print('空單停利-趨勢線')
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