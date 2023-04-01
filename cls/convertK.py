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
        o = pd.Series(df.iloc[0],dtype='int32')
        c = pd.Series(df.iloc[-1],dtype='int32')
        h = pd.Series(df.max(),dtype='int32')
        l = pd.Series(df.min(),dtype='int32')
        tick_min = pd.to_datetime(str(tick_min)+":00")
        volume = str(volume)
        file_exists = os.path.isfile(self.min_path)
        with open(self.min_path, 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
            writer.writerow([tick_min, o.item(), h.item(), l.item(), c.item(), volume])
            print("datetime: " + str(tick_min)+"open: " + str(o)+"high: " + str(h)+"low: " + str(l)+"close: " + str(c)+"volume: " + str(volume))
        return True
    
    def convert_day_k_bar(self):
        '''
        將歷史/即時60分k轉為日k
        '''
        #讀取日k最後一筆
        file_path = os.path.join('data', '1Day.csv')
        df_day = pd.read_csv(file_path, index_col='datetime')
        last_row = None
        last_index = None
        if not df_day.empty:
            last_row = df_day.iloc[-1]
            last_index = pd.to_datetime(last_row.name).date()
        #讀取一分k
        df_1k = pd.read_csv(self.min_path)
        df_1k['datetime'] = pd.to_datetime(df_1k['datetime'])
        index1440 = df_1k.loc[df_1k['datetime'].dt.time == pd.Timestamp('15:01:00').time()].index
        for idx in index1440:
            data = df_1k.iloc[idx:idx+1140]
            print(data)
            day = data.datetime.dt.date.iloc[-1]
            o = pd.Series(data['open'].iloc[0],dtype='int32')
            h = pd.Series(data['high'].max(),dtype='int32')
            l = pd.Series(data['low'].min(),dtype='int32')
            c = pd.Series(data['close'].iloc[-1],dtype='int32')
            v = data['volume'].sum()
            #如果日k已有資料則比對日k最後一筆進行替換，如果沒資料直接寫入
            if last_row is not None:
                if day == last_index:
                    df_day.index = pd.to_datetime(df_day.index).date
                    if last_index in df_day.index:
                        df_day.drop(labels=[last_index], inplace=True)
                        df_day.to_csv(file_path, index_label='datetime')

            with open(file_path, 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([day, o.item(), h.item(), l.item(), c.item(), v])
        
    def write_history_1k_bar(self):
        '''
        寫入1分k的歷史資料
        '''
        df_real = pd.DataFrame({**self.tick})
        df_real.ts = pd.to_datetime(df_real.ts)
        num_rows = sum(1 for line in open(self.min_path))
        df_1k = pd.read_csv(self.min_path, skiprows=num_rows-1, header=None, parse_dates=[0])
        df_1k.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
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
            if df_real.ts.isin([df_1k.iloc[-1]['datetime']]).any() is False:
                df_real = df_real.drop_duplicates(subset=['ts'], keep='last')
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
        把1分k轉為n分k，即時歷史共用
        '''
        current_time = int(datetime.now().time().strftime("%M"))
        # 讀取要轉換的檔案中最新的一筆k
        file_path = os.path.join('data', minutes + '.csv')
        df = pd.read_csv(file_path, index_col='datetime')
        last_row = None
        last_index = None
        if not df.empty:
            last_row = pd.read_csv(file_path, index_col='datetime').iloc[-1]
            last_index = pd.to_datetime(last_row.name)
        # 讀取1分k
        df_1k = pd.read_csv(self.min_path)
        df_1k['datetime'] = pd.to_datetime(df_1k['datetime'])
        df_1k.set_index('datetime', inplace=True)
        if set(['close', 'high', 'low', 'open', 'volume']).issubset(df_1k.columns):
            hlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            # 篩選08:45到15:00的資料
            if minutes == '30Min':
                df1 = df_1k.between_time('08:46', '13:45').resample(rule=minutes, offset='15min', closed='right', label='right').apply(hlc_dict).dropna()
            elif minutes == '60Min':
                df1 = df_1k.between_time('08:46', '13:45').resample(rule=minutes, offset='45min', closed='right', label='right').apply(hlc_dict).dropna()
            else:
                df1 = df_1k.between_time('08:46', '13:45').resample(rule=minutes, closed='right', label='right').apply(hlc_dict).dropna()
                
            # 篩選15:01到23:59以及00:01到05:00的資料
            df2 = pd.concat([df_1k.between_time('15:01', '23:59'), df_1k.between_time('00:00', '05:00')]).resample(rule=minutes, closed='right', label='right').apply(hlc_dict).dropna()
            resampled_df = df2.combine_first(df1)
            # 過濾掉 last_row 之前的資料
            if last_row.any():
                resampled_df = resampled_df.loc[last_index:]
                # 移除舊的lase資料
                df = pd.read_csv(file_path, index_col='datetime')
                last_index = pd.to_datetime(last_row.name)
                df.index = pd.to_datetime(df.index)
                df.drop(labels=[last_index.to_pydatetime()], inplace=True)
                df.to_csv(file_path, index_label='datetime')
            
            print('現在時間')
            print(current_time)
            resampled_df['open'] = pd.Series(resampled_df['open'],dtype='int32')
            resampled_df['high'] = pd.Series(resampled_df['high'],dtype='int32')
            resampled_df['low'] = pd.Series(resampled_df['low'],dtype='int32')
            resampled_df['close'] = pd.Series(resampled_df['close'],dtype='int32')
            resampled_df['volume'] = pd.Series(resampled_df['volume'],dtype='int32')
            print('轉為'+str(minutes))
            print('open:'+str(resampled_df['open'])+'high:'+str(resampled_df['high'])+'low:'+str(resampled_df['low'])+'close:'+str(resampled_df['close'])+'volume:'+str(resampled_df['volume']))
            resampled_df.to_csv(file_path, mode='a', header=False)
                
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