import pandas as pd
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
import cls.tools.trun_adam as adam
import cls.tools.get_sup_pre as suppre
import cls.tools.fibonacci as fib
import cls.tools.get_pattern as pattern
from sklearn.linear_model import LinearRegression
import time

class aisle():
    '''
    上通道及下通道+支撐壓力策略
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
        trend_line = self.get_trend_data(minute)
        data = self.get_trend_line(trend_line)
        print('支撐壓力 {}'.format(globals.levels))
        print('上線段預測價格:'+str(data['forecast_high']))
        print('下線段預測價格:'+str(data['forecast_low']))
        print('現價:'+str(self.close))
        print('is_break:'+str(globals.is_break))
        print('is_backtest:'+str(globals.is_backtest))
        print('aisle_type:'+str(globals.aisle_type))
        
        globals.is_break = True
        globals.is_backtest = True
        #改以支壓方式進出場
        level_keys = [key for key in trend_line.columns if key.startswith('level')]
        last_values = [trend_line[key].iloc[-1] for key in level_keys]
        if self.has_order == False:# 目前沒單
            for i in range(len(last_values)-1):
                if last_values[i] <= self.close <= last_values[i+1]:
                    lower_value = last_values[i]
                    upper_value = last_values[i+1]
                    time.sleep(10)
                    if globals.is_break == False and globals.is_backtest == False: #還沒突破/跌破訊號
                        if self.close <= lower_value or self.close >= upper_value: 
                            globals.is_break = True
                            break
                    else:
                        print('沒突破/跌破訊號~等待')
                    
                    if globals.is_break == True and globals.is_backtest == False: #已突破/跌破未回測
                        if self.close >= lower_value or self.close >= upper_value: 
                            globals.is_backtest = True
                            return
                    else:
                        print('已跌破低點未回測~等待')
                        
                    if globals.is_break == True and globals.is_backtest == True: #已突破/跌破已回測
                        if self.close in range(lower_value - 5, lower_value + 5):#低點做多
                            self.trade(1, 1)  # 買進多單
                            self.has_order = True #標記有單
                            self.break_reset()
                        elif self.close in range(upper_value - 5, upper_value + 5):#高點做空
                            self.trade(1, -1)  # 買進空單
                            self.has_order = True #標記有單
                            self.break_reset()
                    else:
                        print('已跌破+已回測但價格不符合~等待') 
                        
        else:  # 目前有單 
            self.has_order = self.check_trend_loss(data)
                
        # if self.has_order == False:# 目前沒單
        #     if data['trend'] == 0:  # 盤整 上空下多做價差
        #         print('盤整趨勢')
        #         if globals.is_break == False and globals.is_backtest == False: #還沒突破/跌破訊號
        #             if self.close > data['forecast_high']: #突破上通道等回測
        #                 self.break_set(True,2,1)
        #                 return
        #             elif self.close > globals.levels[-1]: #突破最高壓力線等回測
        #                 self.break_set(True,2,3)
        #                 return
        #             elif self.close > globals.levels[-2]: #突破次高壓力線等回測
        #                 self.break_set(True,2,5)
        #                 return
        #             elif self.close < data['forecast_low']: #跌破下通道等回測
        #                 self.break_set(True,1,2)
        #                 return
        #             elif self.close < globals.levels[0]: #跌破最低支撐線等回測
        #                 self.break_set(True,1,4)
        #                 return
        #             elif self.close < globals.levels[1]: #跌破最次低支撐線等回測
        #                 self.break_set(True,1,6)
        #                 return
        #             else:
        #                 print('沒突破/跌破訊號~等待')
        #         elif globals.is_break == True and globals.is_backtest == False: #已突破/跌破未回測
        #             if globals.direction == 2: #方向空 判斷是否回測
        #                 if globals.aisle_type == 1 and self.close in range(data['forecast_high'] - 5, data['forecast_high'] + 5):#上通道的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 elif globals.aisle_type == 3 and self.close in range(globals.levels[-1] - 5, globals.levels[-1] + 5):#最高壓力線的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 elif globals.aisle_type == 5 and self.close in range(globals.levels[-2] - 5, globals.levels[-2] + 5):#次高壓力線的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 else:
        #                     print('已突破高點未回測~等待')
        #             elif globals.direction == 1: #方向多 判斷是否回測
        #                 if globals.aisle_type == 2 and self.close in range(data['forecast_low'] - 5, data['forecast_low'] + 5):#下通道的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 elif globals.aisle_type == 4 and self.close in range(globals.levels[0] - 5, globals.levels[0] + 5):#最低支撐線的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 elif globals.aisle_type == 6 and self.close in range(globals.levels[1] - 5, globals.levels[1] + 5):#次低支撐線的上下5點當已回測
        #                     globals.is_backtest = True
        #                     return
        #                 else:
        #                     print('已跌破低點未回測~等待')
        #         elif globals.is_break == True and globals.is_backtest == True: #已突破/跌破已回測
        #             if globals.direction == 2: #方向空 判斷是否假突破已跌回
        #                 if globals.aisle_type == 1 and self.close < data['forecast_high']:
        #                     if np.isnan(data['head_shoulder_pattern']) == False or np.isnan(data['double_pattern']) == False:
        #                         self.trade(1, -1)  # 買進空單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 elif globals.aisle_type == 3 and self.close < globals.levels[-1]:
        #                     if np.isnan(data['head_shoulder_pattern']) == False or np.isnan(data['double_pattern']) == False:
        #                         self.trade(1, -1)  # 買進空單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 elif globals.aisle_type == 5 and self.close < globals.levels[-2]:
        #                     if np.isnan(data['head_shoulder_pattern']) == False or np.isnan(data['double_pattern']) == False:
        #                         self.trade(1, -1)  # 買進空單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 else:
        #                     print('已跌破+已回測但又站上去了~等待')
        #             elif globals.direction == 1: #方向多 判斷是否假跌破已站回
        #                 if globals.aisle_type == 2 and self.close > data['forecast_low']:#判斷是否站回下通道線
        #                     if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                         self.trade(1, 1)  # 買進多單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 elif globals.aisle_type == 4 and self.close > globals.levels[0]:#判斷是否站回最低支撐
        #                     if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                         self.trade(1, 1)  # 買進多單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 elif globals.aisle_type == 6 and self.close > globals.levels[1]:#判斷是否站回次低支撐
        #                     if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                         self.trade(1, 1)  # 買進多單
        #                         self.has_order = True #標記有單
        #                         self.break_reset()
        #                 else:
        #                     print('已突破+已回測但又跌回去了~等待')
        #     elif data['trend'] == 1:  # 趨勢多 只有在低點買多
        #         print('上升趨勢')
        #         if globals.is_break == False and globals.is_backtest == False: #還沒突破/跌破訊號
        #             if self.close < data['forecast_low']: #跌破下通道等回測
        #                 self.break_set(True,1,2)
        #                 return
        #             elif self.close < globals.levels[0]: #跌破最低支撐線等回測
        #                 self.break_set(True,1,4)
        #                 return
        #             elif self.close < globals.levels[1]: #跌破最次低支撐線等回測
        #                 self.break_set(True,1,6)
        #                 return
        #             else:
        #                 print('沒突破/跌破訊號~等待')
        #         elif globals.is_break == True and globals.is_backtest == False: #已突破/跌破未回測
        #             if globals.aisle_type == 2 and self.close in range(data['forecast_low'] - 5, data['forecast_low'] + 5):#下通道的上下5點當已回測
        #                 globals.is_backtest = True
        #                 return
        #             elif globals.aisle_type == 4 and self.close in range(globals.levels[0] - 5, globals.levels[0] + 5):#最低支撐線的上下5點當已回測
        #                 globals.is_backtest = True
        #                 return
        #             elif globals.aisle_type == 6 and self.close in range(globals.levels[1] - 5, globals.levels[1] + 5):#次低支撐線的上下5點當已回測
        #                 globals.is_backtest = True
        #                 return
        #             else:
        #                 print('已跌破低點未回測~等待')
        #         elif globals.is_break == True and globals.is_backtest == True: #已突破/跌破已回測
        #             if globals.aisle_type == 2 and self.close > data['forecast_low']:#判斷是否站回下通道線
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, 1)  # 買進多單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             elif globals.aisle_type == 4 and self.close > globals.levels[0]:#判斷是否站回最低支撐
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, 1)  # 買進多單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             elif globals.aisle_type == 6 and self.close > globals.levels[1]:#判斷是否站回次低支撐
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, 1)  # 買進多單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             else:
        #                 print('已突破+已回測但又跌回去了~等待')
        #     elif data['trend'] == 2:  # 只有在高點放空
        #         print('下降趨勢')
        #         if globals.is_break == False and globals.is_backtest == False: #還沒突破/跌破訊號
        #             if self.close > data['forecast_high']: #突破上通道等回測
        #                 self.break_set(True,2,1)
                        
        #                 return
        #             elif self.close > globals.levels[-1]: #突破最高壓力線等回測
        #                 self.break_set(True,2,3)
                        
        #                 return
        #             elif self.close > globals.levels[-2]: #突破次高壓力線等回測
        #                 self.break_set(True,2,5)
                        
        #                 return
        #             else:
        #                 print('沒突破/跌破訊號~等待')
        #         elif globals.is_break == True and globals.is_backtest == False: #已突破/跌破未回測
        #             if globals.aisle_type == 1 and self.close in range(data['forecast_high'] - 5, data['forecast_high'] + 5):#上通道的上下5點當已回測
        #                 globals.is_backtest = True
                        
        #                 return
        #             elif globals.aisle_type == 3 and self.close in range(globals.levels[-1] - 5, globals.levels[-1] + 5):#最高壓力線的上下5點當已回測
        #                 globals.is_backtest = True
                        
        #                 return
        #             elif globals.aisle_type == 5 and self.close in range(globals.levels[-2] - 5, globals.levels[-2] + 5):#次高壓力線的上下5點當已回測
        #                 globals.is_backtest = True
                        
        #                 return
        #             else:
        #                 print('已突破高點未回測~等待')
        #         elif globals.is_break == True and globals.is_backtest == True: #已突破/跌破已回測
        #             if globals.aisle_type == 1 and self.close < data['forecast_high']:
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, -1)  # 買進空單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             elif globals.aisle_type == 3 and self.close < globals.levels[-1]:
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, -1)  # 買進空單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             elif globals.aisle_type == 5 and self.close < globals.levels[-2]:
        #                 if data['head_shoulder_pattern'] != None or data['double_pattern'] != None:
        #                     self.trade(1, -1)  # 買進空單
        #                     self.has_order = True #標記有單
        #                     self.break_reset()
        #             else:
        #                 print('已跌破+已回測但又站上去了~等待')
        # else:  # 目前有單 
        #     self.has_order = self.check_trend_loss(data)
        
        if globals.has_thread == False:
            thread = threading.Thread(
                target=self.draw_trend, args=(minute, trend_line))
            thread.start()
            globals.has_thread = True
    
    def break_set(self, is_break,direction,aisle_type):
        '''
        is_break 是否突破 是:true 否:false
        direction 突破方向 1多 2空
        aisle_type 判斷的類型  1上通道 2下通道 3 最高壓力  4最低支撐  5次高壓力 6次低支撐
        '''
        globals.is_break = is_break
        globals.direction = direction
        globals.aisle_type = aisle_type
    
    def break_reset(self):
        globals.is_break = False #突破訊號復歸
        globals.is_backtest = False #回測訊號復歸
        globals.direction = 0 #方向復歸
        globals.aisle_type = 0 #比較類型復歸
    
    def get_trend_data(self, minute):
        '''
        取得目前趨勢資料
        '''
        df = None
        if minute == 1:
            df = self.df_1Min.tail(globals.how).reset_index(drop=False)
        elif minute == 5:
            df = self.df_5Min.tail(globals.how).reset_index(drop=False)
        elif minute == 15:
            df = self.df_15Min.tail(globals.how).reset_index(drop=False)
        elif minute == 30:
            df = self.df_30Min.tail(globals.how).reset_index(drop=False)
        elif minute == 60:
            df = self.df_60Min.tail(globals.how).reset_index(drop=False)
        elif minute == 1440:
            df = self.df_1day.tail(globals.how).reset_index(drop=False)

        df_n = df.reset_index()

        # 線性回歸計算方式
        reg_up = LinearRegression().fit(df_n.index.to_frame(), df_n["close"])
        up_line = reg_up.intercept_ + reg_up.coef_ * df_n.index
        df_temp_low = df_n[df_n["close"] < up_line]
        df_temp_high = df_n[df_n["close"] > up_line]

        while len(df_temp_low) >= 5:
            reg_low = LinearRegression().fit(df_temp_low.index.to_frame(), df_temp_low["close"])
            up_line_low = (reg_low.intercept_ + reg_low.coef_ * pd.Series(df_n.index)).round().astype(int)
            df_temp_low = df_n[df_n["close"] < up_line_low]

        while len(df_temp_high) >= 5:
            reg_high = LinearRegression().fit(df_temp_high.index.to_frame(), df_temp_high["close"])
            up_line_high = (reg_high.intercept_ + reg_high.coef_ * pd.Series(df_n.index)).round().astype(int)
            df_temp_high = df_n[df_n["close"] > up_line_high]

        df_n["low_trend"] = (reg_low.intercept_ + reg_low.coef_ * pd.Series(df_n.index)).round().astype(int)
        df_n["high_trend"] = (reg_high.intercept_ + reg_high.coef_ * pd.Series(df_n.index)).round().astype(int)
        
        # #取得支撐壓力
        # df['datetime'] = pd.to_datetime(df_n['datetime'])
        # df.set_index(['datetime'], inplace=True)
        # globals.levels = suppre.detect_level_method(df)

        # for level in globals.levels:
        #     df_n["level"+str(level)] = level

        globals.levels = fib.fibonacci(df)

        for level in globals.levels:
            df_n["level"+str(level)] = level
        
        #判斷型態
        df_n = pattern.get_pattern(df_n)
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
        if "head_shoulder_pattern" in df_n.columns:
            head_shoulder_pattern = df_n["head_shoulder_pattern"].iloc[-1]
        else:
            head_shoulder_pattern = None

        if "detect_double_top_bottom" in df_n.columns:
            detect_double_top_bottom = df_n["detect_double_top_bottom"].iloc[-1]
        else:
            detect_double_top_bottom = None
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

        return {
                "last_low": last_low, 
                "last_high": last_high, 
                'forecast_low': forecast_low, 
                'forecast_high': forecast_high, 
                'trend': trend,
                'head_shoulder_pattern': head_shoulder_pattern,
                'detect_double_top_bottom': detect_double_top_bottom
                }

    def draw_trend(self,minute,df_n):
        '''
        繪製趨勢線
        '''
        fig, ax = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        def update(_):
            df_n = self.get_trend_data(minute)
            ax[0].clear()
            ax[1].clear()
            for level in globals.levels:
                ax[0].plot(df_n["level"+str(level)],linestyle='dashed',label=str(level))
            ax[0].plot(df_n["close"])
            ax[0].plot(df_n["low_trend"])
            ax[0].plot(df_n["high_trend"])
            ax[0].set_title(str(globals.code)+"-"+str(minute)+'Min')
            ax[1].bar(df_n.index, df_n.volume, width=0.4)
            ax[1].set_title("Volume")
            # # 標記頭肩底
            # if "head_shoulder_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['head_shoulder_pattern'] == "Inverse Head and Shoulder"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='^', linestyle='None', markersize=8, color='red')
            
            # # 標記頭肩頂
            # if "head_shoulder_pattern" in df_n.columns:
            #     triangle_points = df_n[df_n['head_shoulder_pattern'] == "Head and Shoulder"]
            #     if not triangle_points.empty:
            #         ax[0].plot(triangle_points.index, triangle_points['close'], marker='v', linestyle='None', markersize=8, color='redgreen')
        
            # #標記區間底
            # if "multiple_top_bottom_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['multiple_top_bottom_pattern'] == "Multiple Bottom"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='-', linestyle='None', markersize=8, color='red')
        
            # #標記區間頂
            # if "multiple_top_bottom_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['multiple_top_bottom_pattern'] == "Multiple Top"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='-', linestyle='None', markersize=8, color='green')
        
            # #標記上升三角
            # if "triangle_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['triangle_pattern'] == "Ascending Triangle"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='2', linestyle='None', markersize=8, color='red')
        
            # #標記下袶三角
            # if "triangle_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['triangle_pattern'] == "Descending Triangle"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='1', linestyle='None', markersize=8, color='green')
       

            # #標記上升楔形
            # if "wedge_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['wedge_pattern'] == "Wedge Up"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='h', linestyle='None', markersize=8, color='red')
        
            # #標記下袶楔形
            # if "wedge_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['wedge_pattern'] == "Wedge Down"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='h', linestyle='None', markersize=8, color='green')
       
            # #標記上升通道
            # if "channel_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['channel_pattern'] == "Channel Up"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='d', linestyle='None', markersize=8, color='red')
        
            # #標記下袶通道
            # if "channel_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['channel_pattern'] == "Channel Down"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='d', linestyle='None', markersize=8, color='green')
       
            # #標記雙頂
            # if "double_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['double_pattern'] == "Double Top"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='*', linestyle='None', markersize=8, color='red')
            
            # #標記雙底
            # if "double_pattern" in df_n.columns:
            #     inverse_triangle_points = df_n[df_n['double_pattern'] == "Double Bottom"]
            #     if not inverse_triangle_points.empty:
            #         ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='*', linestyle='None', markersize=8, color='green')
        
        ax[0].plot(df_n["close"])
        ax[0].plot(df_n["low_trend"])
        ax[0].plot(df_n["high_trend"])
        for level in globals.levels:
            ax[0].plot(df_n["level"+str(level)],linestyle='dashed',label=str(level))
        ax[0].set_title(str(globals.code)+"-"+str(minute)+'Min')
        ax[1].bar(df_n.index, df_n.volume, width=0.4)
        ax[1].set_title("Volume")
        
    #     # 標記頭肩底
    #     if "head_shoulder_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['head_shoulder_pattern'] == "Inverse Head and Shoulder"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='^', linestyle='None', markersize=8, color='red')
        
    #     # 標記頭肩頂
    #     if "head_shoulder_pattern" in df_n.columns:
    #         triangle_points = df_n[df_n['head_shoulder_pattern'] == "Head and Shoulder"]
    #         if not triangle_points.empty:
    #             ax[0].plot(triangle_points.index, triangle_points['close'], marker='v', linestyle='None', markersize=8, color='green')
    
    #     #標記區間底
    #     if "multiple_top_bottom_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['multiple_top_bottom_pattern'] == "Multiple Bottom"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='-', linestyle='None', markersize=8, color='red')
       
    #     #標記區間頂
    #     if "multiple_top_bottom_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['multiple_top_bottom_pattern'] == "Multiple Top"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='-', linestyle='None', markersize=8, color='green')
    
    #     #標記上升三角
    #     if "triangle_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['triangle_pattern'] == "Ascending Triangle"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='2', linestyle='None', markersize=8, color='red')
       
    #     #標記下袶三角
    #     if "triangle_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['triangle_pattern'] == "Descending Triangle"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='1', linestyle='None', markersize=8, color='green')
    
    
    #     #標記上升楔形
    #     if "wedge_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['wedge_pattern'] == "Wedge Up"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='h', linestyle='None', markersize=8, color='red')
        
    #     #標記下袶楔形
    #     if "wedge_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['wedge_pattern'] == "Wedge Down"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='h', linestyle='None', markersize=8, color='green')
       
    #    #標記上升通道
    #     if "channel_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['channel_pattern'] == "Channel Up"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='d', linestyle='None', markersize=8, color='red')
        
    #     #標記下袶通道
    #     if "channel_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['channel_pattern'] == "Channel Down"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='d', linestyle='None', markersize=8, color='green')
       
    #     #標記雙頂
    #     if "double_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['double_pattern'] == "Double Top"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='*', linestyle='None', markersize=8, color='red')
        
    #     #標記雙底
    #     if "double_pattern" in df_n.columns:
    #         inverse_triangle_points = df_n[df_n['double_pattern'] == "Double Bottom"]
    #         if not inverse_triangle_points.empty:
    #             ax[0].plot(inverse_triangle_points.index, inverse_triangle_points['close'], marker='*', linestyle='None', markersize=8, color='green')
       
    
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
        依支壓出場停損
        '''
        if self.df_trade.empty is False:
            df_trade = self.df_trade.iloc[-1]

            if len(df_trade) > 0:
                if df_trade['type'] == 1:  # 有單時
                    if df_trade['lot'] == 1:  # 有多單的處理
                        # 收盤價 < 買進價格-n點
                        if self.close <= (df_trade['price'] - self.loss):
                            self.balance = ((self.close - df_trade['price'])*50)-70  # 計算賺賠
                            print('多單停損')
                            self.trade(-1, -1)  # 多單停損
                            return False

                        # 50點停利
                        if self.close >= (df_trade['price'] + 50):
                            self.balance = ((self.close - df_trade['price'])*50)-70  # 計算賺賠
                            print('多單停利')
                            self.trade(-1, -1)  # 多單停利
                            return False
                            

                    elif df_trade['lot'] == -1:  # 空單的處理
                        if (self.close >= (df_trade['price'] + self.loss)):
                            self.balance = ((df_trade['price'] - self.close)*50)-70  # 計算賺賠
                            print('空單停損')
                            self.trade(-1, 1)  # 空單回補
                            return False

                        if self.close <= (df_trade['price'] + 50):
                            self.balance = ((df_trade['price'] - self.close)*50)-70  # 計算賺賠
                            print('空單停利')
                            self.trade(-1, 1)  # 空單停利
                            return False

    # def check_trend_loss(self, data):
    #     '''
    #     依趨勢線出場或停損
    #     '''
    #     if self.df_trade.empty is False:
    #         df_trade = self.df_trade.iloc[-1]
    #         #取得翻亞當目標價
    #         df_60Min = self.df_60Min.tail(globals.how).reset_index(drop=False)
    #         last = df_60Min.iloc[-2]
    #         series = np.array(df_60Min['close'])
    #         exits = adam.flip_adam_exit(series)
    #         target = int(exits)
    #         print('亞當目標價:'+str(target))
    #         if len(df_trade) > 0:
    #             if df_trade['type'] == 1:  # 有單時
    #                 if df_trade['lot'] == 1:  # 有多單的處理
    #                     # 收盤價 < 買進價格-n點
    #                     if self.close <= (df_trade['price'] - self.loss):
    #                         self.balance = (
    #                             (self.close - df_trade['price'])*50)-70  # 計算賺賠
    #                         print('多單停損')
    #                         self.trade(-1, -1)  # 多單停損
    #                         return False

    #                     # 判斷趨勢停利
    #                     if data['trend'] == 0 or data['trend'] == 1:  # 盤整或上升趨勢則上線段停利
    #                         # 上線段停利(容許值上下五點)
    #                         if self.close in range(data['forecast_high']-5, data['forecast_high']+5):
    #                             self.balance = (
    #                                 (self.close - df_trade['price'])*50)-70  # 計算賺賠
    #                             print('多單停利-趨勢線上')
    #                             self.trade(-1, -1)  # 多單停利
    #                             return False
    #                         elif self.close >= target and last['volume'] > 15000:
    #                             self.balance = (
    #                                 (self.close - df_trade['price'])*50)-70  # 計算賺賠
    #                             print('多單停利-趨勢線上')
    #                             self.trade(-1, -1)  # 多單停利
    #                             return False

    #                 elif df_trade['lot'] == -1:  # 空單的處理
    #                     if (self.close >= (df_trade['price'] + self.loss)):
    #                         self.balance = (
    #                             (df_trade['price'] - self.close)*50)-70  # 計算賺賠
    #                         print('空單停損4')
    #                         self.trade(-1, 1)  # 空單回補
    #                         return False

    #                     # 判斷趨勢停利
    #                     if data['trend'] == 0 or data['trend'] == 2:  # 盤整或下降趨勢則下線段停利
    #                         # 下線段停利(容許值上下五點)
    #                         if self.close in range(data['forecast_low']-5, data['forecast_low']+5):
    #                             self.balance = (
    #                                 (df_trade['price'] - self.close)*50)-70  # 計算賺賠
    #                             print('空單停利-趨勢線')
    #                             self.trade(-1, 1)  # 空單停利
    #                             return False
    #                         elif self.close <= target and last['volume'] > 15000:
    #                             self.balance = (
    #                                 (df_trade['price'] - self.close)*50)-70  # 計算賺賠
    #                             print('空單停利-趨勢線')
    #                             self.trade(-1, 1)  # 空單停利
    #                             return False
                            
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