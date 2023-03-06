import pandas as pd
import os.path
import csv
from datetime import datetime,timedelta

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
        #df.drop_duplicates(inplace = True)
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
            if(len(data) < 20):
                dd = pd.read_csv('data/1Day.csv')
                dd.update(dd.drop(dd.index[-1]))
                
            with open('data/1Day.csv', 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
                writer.writerow([day, o, h, l, c, v])
        
    def convert_k_bar(self,time_unit):
        '''
        將歷史/即時1分k轉為n分
        '''
        file_path = os.path.join('data', time_unit + '.csv')
        df = pd.read_csv(self.min_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['open'] = pd.to_numeric(df['open'], downcast='integer')
        df['high'] = pd.to_numeric(df['high'], downcast='integer')
        df['low'] = pd.to_numeric(df['low'], downcast='integer')
        df['close'] = pd.to_numeric(df['close'], downcast='integer')
        df['volume'] = pd.to_numeric(df['volume'], downcast='integer')
        df = df.set_index('datetime')
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        df_data = df.resample(rule=time_unit,label='right', closed='right').agg(ohlc_dict)
        df_data = df_data.dropna()
        df_data.to_csv(file_path)
        print(df_data)
            
            
    # def convert_k_bar(self,time_unit):
    #     '''
    #     tick轉為k棒
    #     '''
    #     # 將tick轉換為DataFrame
    #     self.df = pd.DataFrame({'Open': [self.open], 'ts': [self.datetime], 'High': [self.high] , 'Volume': [self.volume], 'Low': [self.low], 'Amount': [self.low], 'Close':[self.close]})
    #     # 轉換時間戳
    #     self.df['datetime'] = pd.to_datetime(self.df['ts'], format='%Y-%m-%d %H:%M:%S.%f')
    #     # 設置時間戳為索引
    #     self.df.set_index('datetime', inplace=True)
    #     file_path = os.path.join('data', time_unit + '.csv')
        
    #     # 判斷文件是否為空或是沒文件則先創造DataFrame
    #     if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
    #         empty_df = pd.DataFrame(columns=['Open', 'ts', 'High', 'Volume', 'Low', 'Amount','Close'])
    #         empty_df.to_csv(file_path)

    #     # 讀取csv
    #     existing_df = pd.read_csv(file_path, index_col=0, parse_dates=True)

    #     # 排除重覆資料
    #     if len(existing_df) > 0 and existing_df.index[-1] == self.df.resample(time_unit).apply({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna().index[0]:
    #         print('Duplicate data. Skipping...')
    #         return False

    #     # 讀取新資料
    #     kbar = self.df.resample(time_unit).apply({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()

    #     # 合併現有資料並寫入csv
    #     new_df = pd.concat([existing_df, kbar])
    #     new_df.to_csv(file_path)

    #     print(kbar)
    #     return True