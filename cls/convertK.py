import pandas as pd
import os.path
import csv
from datetime import datetime,timedelta
import time
import numpy as np

class convertK():
    '''
    tick轉換為k棒
    '''
    def __init__(self, tick, is_real=False):
        if is_real == True:
            self.datetime = pd.to_datetime(tick['datetime'])
            self.open = pd.Series(tick['open'],dtype='int32')
            self.high = pd.Series(tick['high'],dtype='int32')
            self.low = pd.Series(tick['low'],dtype='int32')
            self.volume = pd.Series(tick['volume'],dtype='int32')
            self.close = pd.Series(tick['close'],dtype='int32')
            self.amount = pd.Series(tick['amount'],dtype='int32')
        self.tick_path = 'data/tick.csv'
        self.min_path = 'data/1Min.csv'
        self.tick = tick
        
    def get_now_min(self,now):
        if now == '':
            return self.datetime.strftime('%Y/%m/%d %H:%M')
        else:
            return now
        
    def get_tick_min(self):
        return self.datetime.strftime('%Y/%m/%d %H:%M')
    
    def write_tick(self,time_unit):
        file_path = os.path.join('data', time_unit + '.csv')
        dict = {'datetime': self.datetime, 'open': self.open, 'high': self.high,'low': self.low, 'close': self.close, 'volume':self.volume}
        df = pd.DataFrame(dict)
        df.to_csv(file_path, mode='a', index=False, header=not os.path.exists(file_path))
    
    def write_1k_bar(self, tick_min, volume, amount):
        '''
        將tick寫入1分k
        '''
        df = pd.DataFrame(amount)
        o = df.iloc[0].to_string(index=False)
        c = df.iloc[-1].to_string(index=False)
        h = df.max().to_string(index=False)
        l = df.min().to_string(index=False)
        tick_min = str(tick_min)+":00"
        volume = str(volume)
        file_exists = os.path.isfile(self.min_path)
        with open(self.min_path, 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
            writer.writerow([tick_min, o, h, l, c, volume])
            print("datetime:"+tick_min)
            print("open:"+o)
            print("high:"+h)
            print("low:"+l)
            print("close:"+c)
            print("volume:"+volume)
        return True
    
    def convert_day_k_bar(self):
        '''
        將歷史/即時60分k轉為日k
        '''
        df = pd.read_csv('data/60Min.csv')
        df['datetime'] = pd.to_datetime(df['datetime'])
        index160000 = df.loc[df['datetime'].dt.time == pd.Timestamp('16:00:00').time()].index
        for idx in index160000:
            data = df.iloc[idx:idx+20]
            day = data.datetime.dt.date.iloc[-1]
            o = round(data['open'].iloc[0])
            h = round(data['high'].max())
            l = round(data['low'].min())
            c = round(data['close'].iloc[-1])
            v = data['volume'].sum()
            file_exists = os.path.isfile('data/1Day.csv')
            #查看是否有20筆資料，沒的話刪掉最後一筆日k
            if(len(data) == 20):               
                with open('data/1Day.csv', 'a', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    if not file_exists:
                        writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
                    writer.writerow([day, o, h, l, c, v])
        
    def write_history_1k_bar(self):
        '''
        寫入1分k的歷史資料
        '''
        df_real = pd.DataFrame({**self.tick})
        df_real.ts = pd.to_datetime(df_real.ts)
        num_rows = sum(1 for line in open(self.min_path))
        df_1k = pd.read_csv(self.min_path,skiprows=num_rows-1)
        df_1k['datetime'] = pd.to_datetime(df_1k['datetime'])
        # 沒任何資料時直接寫入
        if df_1k.empty and len(df_1k) == 0:
            o = pd.Series(df_real.Open,dtype='int32')
            h = pd.Series(df_real.High,dtype='int32')
            l = pd.Series(df_real.Low,dtype='int32')
            c = pd.Series(df_real.Close,dtype='int32')
            v = pd.Series(df_real.Volume,dtype='int32')
            dict = {'datetime': df_real.ts, 'open': o, 'high': h,'low': l, 'close': c, 'volume':v}
            df = pd.DataFrame(dict)
            df.to_csv(self.min_path, mode='a', index=False, header=not os.path.exists(self.min_path))
        else:
            #有資料時判斷最後一筆是否重覆再寫入
            if df_real.isin({'ts': [df_1k.iloc[-1]['datetime']]}) is False:
                o = pd.Series(df_real.Open,dtype='int32')
                h = pd.Series(df_real.High,dtype='int32')
                l = pd.Series(df_real.Low,dtype='int32')
                c = pd.Series(df_real.Close,dtype='int32')
                v = pd.Series(df_real.Volume,dtype='int32')
                dict = {'datetime': df_real.ts, 'open': o, 'high': h,'low': l, 'close': c, 'volume':v}
                df = pd.DataFrame(dict)
                df.to_csv(self.min_path, mode='a', index=False, header=not os.path.exists(self.min_path))
     
    def convert_k_bar(self,minutes):
        '''
        把1分k轉為5分k，即時歷史共用(5根1分k=1根5分k，所以抓取1-5，6-10依序壓縮，同時判斷是否已存在)
        '''
        # 判斷是否已經到轉換時間
        minute = int(minutes.replace('Min', ''))
        current_time = int(datetime.now().time().strftime("%M"))
        if minute == 5 and current_time % 5 != 0:
            return
        elif minute == 15 and current_time != 15:
            return
        elif minute == 30 and current_time != 30:
            return
        elif minute == 60 and current_time != 00:
            return
        file_path = os.path.join('data', minutes + '.csv')
        try:
            last_row = pd.read_csv(file_path, index_col='datetime').iloc[-1]
            last_index = pd.to_datetime(last_row.name)
            last_values = list(last_row.values)
        except:
            last_index = pd.to_datetime('1900-01-01')
            last_values = [None]*minute

        df_1k = pd.read_csv(self.min_path)
        df_1k['datetime'] = pd.to_datetime(df_1k['datetime'])
        df_1k.set_index('datetime', inplace=True)
        hlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        if set(['close', 'high', 'low', 'open', 'volume']).issubset(df_1k.columns):
            # 篩選08:46到15:00的資料
            df1 = df_1k.between_time('08:46', '15:00')
            df1 = df1[df1.index > last_index]  # 排除重複的資料
            # 篩選15:01到23:59以及00:01到05:00的資料
            #df2 = df_1k.between_time('15:01', '23:59').append(df_1k.between_time('00:01', '05:00'))
            df2 = pd.concat([df_1k.between_time('15:01', '23:59'), df_1k.between_time('00:01', '05:00')])
            df2 = df2[df2.index > last_index]  # 排除重複的資料
            resampled_df = pd.concat([df1, df2]).resample(minutes, closed='right', label='right').apply(hlc_dict).dropna()
            # 將讀取到的最後一筆資料加入到result之前
            if last_index in resampled_df.index:
                resampled_df.loc[last_index] = last_values
            result = resampled_df
            result.to_csv(file_path, mode='a', header=False, index_label='datetime')
                
    def convert_history_k_bar(self,time_unit):
        '''
        將歷史/即時1分k轉為n分
        '''
        # 先讀取5分k的csv最後一筆資料
        try:
            last_row = pd.read_csv('data/5Min.csv', index_col='datetime').iloc[-1]
            last_index = pd.to_datetime(last_row.name)
            last_values = list(last_row.values)
        except:
            last_index = pd.to_datetime('1900-01-01')
            last_values = [None]*5

        df_1k = pd.read_csv(self.min_path)
        df_1k['datetime'] = pd.to_datetime(df_1k['datetime'])
        df_1k.set_index('datetime', inplace=True)
        hlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        if set(['close', 'high', 'low', 'open', 'volume']).issubset(df_1k.columns):
            # 篩選08:46到13:45的資料
            df1 = df_1k.between_time('08:46', '13:45')
            df1 = df1[df1.index > last_index]  # 排除重複的資料
            # 篩選15:00到23:59以及00:00到05:00的資料
            #df2 = df_1k.between_time('15:00', '23:59').append(df_1k.between_time('00:00', '05:00'))
            df2 = pd.concat([df_1k.between_time('15:01', '23:59'), df_1k.between_time('00:01', '05:00')])
            df2 = df2[df2.index >= last_index]  # 排除重複的資料
            resampled_df1 = df1.resample('5Min', closed='right', label='right').apply(hlc_dict).dropna()
            resampled_df2 = df2.resample('5Min', closed='right', label='right').apply(hlc_dict).dropna()
            # 將讀取到的最後一筆資料加入到result之前
            if last_index in resampled_df1.index:
                resampled_df1.loc[last_index] = last_values
            elif last_index in resampled_df2.index:
                resampled_df2.loc[last_index] = last_values
            result = pd.concat([resampled_df1, resampled_df2])
            result.to_csv('data/5Min.csv', mode='a', header=not last_index == pd.to_datetime('1900-01-01').tz_localize('Asia/Taipei'), index_label='datetime')