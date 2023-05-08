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
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Conv1D, MaxPooling1D, Flatten
import os.path

class aisle():
    '''
    建立在一口單的進出
    '''

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

    def run(self, minute):
        '''
        上升通道及下降通道策略
        '''
        trend_line = self.get_trend_data(minute)
        data = self.get_trend_line(trend_line)
        power_k = self.power_kbar(30)  # 加入能量k棒的判斷
        print(power_k)
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
                elif self.close in range(power_k['ll'] - 5, power_k['ll'] + 5):  # 買進多單
                    self.trade(1, 1)  # 買進多單
                    self.has_order = True
                elif self.close in range(power_k['hh'] - 5, power_k['hh'] + 5):  # 買進空單
                    self.trade(1, -1)  # 買進空單
                    self.has_order = True
                else:
                    print('條件不符合繼續等')
            elif data['trend'] == 1:  # 只有在低點買多
                print('上升趨勢')
                # 下線段買多
                if self.close in range(data['forecast_low'], data['forecast_low']+10):
                    self.trade(1, 1)  # 買進多單
                    self.has_order = True
                elif self.close in range(power_k['ll']-5, power_k['ll']+5):  # 買進多單
                    self.trade(1, 1)  # 買進多單
                    self.has_order = True
            elif data['trend'] == 2:  # 只有在高點放空
                print('下降趨勢')
                # 上線段放空
                if self.close in range(data['forecast_high'], data['forecast_high']+10):
                    self.trade(1, -1)  # 買進空單
                    self.has_order = True
                elif self.close in range(power_k['hh']-5, power_k['hh']+5):  # 買進空單
                    self.trade(1, -1)  # 買進空單
                    self.has_order = True
        else:  # 目前有單
            self.has_order = self.check_trend_loss(data, minute, power_k)

        # 預測下個60k
        forecast = self.forecast(minute)
        with open('data/forecast.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([trend_line.iloc[-1]['datetime'],forecast])
        print('預測下個時間點:'+str(forecast))
        
        if globals.has_thread == False:
            thread = threading.Thread(
                target=self.draw_trend, args=(minute, trend_line))
            thread.start()
            globals.has_thread = True

    def power_kbar(self, minute):
        '''
        能量K棒計算
        '''
        df = None
        if minute == 1:
            self.df_1Min = pd.read_csv('data/1Min.csv', index_col='datetime')
            df = self.df_1Min.iloc[-2]
        elif minute == 5:
            self.df_5Min = pd.read_csv('data/5Min.csv', index_col='datetime')
            df = self.df_5Min.iloc[-2]
        elif minute == 15:
            self.df_15Min = pd.read_csv('data/15Min.csv', index_col='datetime')
            df = self.df_15Min.iloc[-2]
        elif minute == 30:
            self.df_30Min = pd.read_csv('data/30Min.csv', index_col='datetime')
            df = self.df_30Min.iloc[-2]
        elif minute == 60:
            self.df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
            df = self.df_60Min.iloc[-2]
        elif minute == 1440:
            self.df_1day = pd.read_csv('data/1Day.csv', index_col='datetime')
            df = self.df_1day.iloc[-2]

        volume = float(str(df['volume'])[0] + '.' + str(df['volume'])[1:]) if int(
            str(df['volume'])[0]) < 6 else float('0.' + str(df['volume']))
        power = math.ceil((df['high'] - df['low']) * volume)
        hh = math.ceil(df['high'] + power)
        h = math.ceil(df['close'] + power)
        l = math.ceil(df['close'] - power)
        ll = math.ceil(df['low'] - power)
        op_h = math.ceil(df['low'] + power)
        op_l = math.ceil(df['high'] - power)
        # return {"量能:":power ,"頂:": hh, "高": h, '低':l,'底':ll ,'反轉高點': op_h,'反轉低點':op_l}
        return {"power:": power, "hh": hh, "h": h, 'l': l, 'll': ll, 'op_h': op_h, 'op_l': op_l}

    def forecast(self,minute):
        df = None
        if minute == 1:
            df = pd.read_csv('data/1Min.csv')
        elif minute == 5:
            df = pd.read_csv('data/5Min.csv')
        elif minute == 15:
            df = pd.read_csv('data/15Min.csv')
        elif minute == 30:
            df = pd.read_csv('data/30Min.csv')
        elif minute == 60:
            df = pd.read_csv('data/60Min.csv')
        elif minute == 1440:
            df = pd.read_csv('data/1Day.csv')
        # 將日期欄位轉換為datetime型態
        df['datetime'] = pd.to_datetime(df['datetime'])

        # 將datetime欄位設為index
        df = df.set_index('datetime')
        # 訓練集和測試集的比例
        train_size = 0.8

        # 將資料集分割為訓練集和測試集
        train_df = df[:int(len(df)*train_size)]
        test_df = df[int(len(df)*train_size):]

        # 轉換資料集格式
        def create_dataset(X, y, time_steps=1):
            Xs, ys = [], []
            for i in range(len(X) - time_steps):
                v = X.iloc[i:(i + time_steps)].values
                Xs.append(v)
                ys.append(y.iloc[i + time_steps])
            return np.array(Xs), np.array(ys)

        # 設定時間步長
        TIME_STEPS = 3

        # 將訓練集和測試集轉換為X和y格式
        X_train, y_train = create_dataset(train_df, train_df['close'], TIME_STEPS)
        X_test, y_test = create_dataset(test_df, test_df['close'], TIME_STEPS)

        # 使用MinMaxScaler進行標準化
        scaler = MinMaxScaler()
        X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
        X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)

        # 建立模型
        model = Sequential()
        model.add(Conv1D(filters=64, kernel_size=2, activation='relu', input_shape=(TIME_STEPS, X_train.shape[2])))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Flatten())
        model.add(Dense(50, activation='relu'))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')

        # 訓練模型
        model.fit(X_train, y_train, epochs=50, batch_size=16, verbose=1)

        # 使用訓練好的模型進行預測
        last_data = df.iloc[-TIME_STEPS:]
        last_data_scaled = scaler.transform(last_data.values.reshape(-1, 1)).reshape(1, TIME_STEPS, last_data.shape[1])
        result = math.ceil(model.predict(last_data_scaled)[0][0])
        return result
        
        
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
        
        # 黃金分割率
        # fib = self.fibonacci(minute)
        # print(fib)
        # df_n["h_809"] = fib['h_809']
        # df_n["h_618"] = fib['h_618']
        # df_n["h_500"] = fib['h_500']
        # df_n["h_382"] = fib['h_382']
        # df_n["h_191"] = fib['h_191']
        # df_n["l_191"] = fib['l_191']
        # df_n["l_382"] = fib['l_382']
        # df_n["l_500"] = fib['l_500']
        # df_n["l_618"] = fib['l_618']
        # df_n["l_809"] = fib['l_809']

        # 能量k棒
        # power_k = self.power_kbar(1440)
        # print(power_k)
        # df_n['hh'] = power_k['hh']
        # df_n['h'] = power_k['h']
        # df_n['l'] = power_k['l']
        # df_n['ll'] = power_k['ll']
        # df_n['op_h'] = power_k['op_h']
        # df_n['op_l'] = power_k['op_l']

        return df_n

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
            ax[0].plot(df_n["close"])
            ax[0].plot(df_n["low_trend"])
            ax[0].plot(df_n["high_trend"])
            # ax[0].plot(df_n['hh'])
            # ax[0].plot(df_n['h'])
            # ax[0].plot(df_n['l'])
            # ax[0].plot(df_n['ll'])
            # ax[0].plot(df_n['op_h'])
            # ax[0].plot(df_n['op_l'])
            # ax[0].plot(df_n["h_809"])
            # ax[0].plot(df_n["h_618"])
            # ax[0].plot(df_n["h_500"])
            # ax[0].plot(df_n["h_382"])
            # ax[0].plot(df_n["h_191"])
            # ax[0].plot(df_n["l_191"])
            # ax[0].plot(df_n["l_382"])
            # ax[0].plot(df_n["l_500"])
            # ax[0].plot(df_n["l_618"])
            # ax[0].plot(df_n["l_809"])
            ax[0].set_title(str(globals.code)+"-"+str(minute)+'Min')
            ax[1].bar(df_n.index, df_n.volume, width=0.4)
            ax[1].set_title("Volume")
            
        ax[0].plot(df_n["close"])
        ax[0].plot(df_n["low_trend"])
        ax[0].plot(df_n["high_trend"])
        # ax[0].plot(df_n['hh'])
        # ax[0].plot(df_n['h'])
        # ax[0].plot(df_n['l'])
        # ax[0].plot(df_n['ll'])
        # ax[0].plot(df_n['op_h'])
        # ax[0].plot(df_n['op_l'])
        # ax[0].plot(df_n["h_809"])
        # ax[0].plot(df_n["h_618"])
        # ax[0].plot(df_n["h_500"])
        # ax[0].plot(df_n["h_382"])
        # ax[0].plot(df_n["h_191"])
        # ax[0].plot(df_n["l_191"])
        # ax[0].plot(df_n["l_382"])
        # ax[0].plot(df_n["l_500"])
        # ax[0].plot(df_n["l_618"])
        # ax[0].plot(df_n["l_809"])
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

    def check_trend_loss(self, data, minute, power_k):
        '''
        依趨勢線出場或停損
        '''
        if self.df_trade.empty is False:
            # 改用能量k棒判斷停利點
            # fib = self.fibonacci(minute)
            # print(fib)
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
                            # 能量k棒計算出來的高點
                            elif self.close >= power_k['hh'] or self.close in range(power_k['h'], power_k['hh']):
                                self.balance = (
                                    (self.close - df_trade['price'])*50)-70  # 計算賺賠
                                print('多單停利-能量k棒範圍')
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
                            # 能量k棒計算出來的低點
                            elif self.close <= power_k['ll'] or self.close in range(power_k['l'], power_k['ll']):
                                self.balance = (
                                    (df_trade['price'] - self.close)*50)-70  # 計算賺賠
                                print('空單停利-能量k棒')
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