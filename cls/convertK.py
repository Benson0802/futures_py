import pandas as pd
import os.path
import csv

class convertK():
    '''
    tick轉換為k棒
    '''
    def __init__(self, tick):
        # self.datetime = tick['datetime']
        # self.open = float(tick['open'])
        # self.high = float(tick['high'])
        # self.low = float(tick['low'])
        # self.volume = int(tick['volume'])
        # self.close = float(tick['close'])
        self.tick_path = 'data/tick.csv'
        self.min_path = 'data/1Min.csv'
        #self.tick = tick
        #self.write_tick()
    
    def write_tick(self):
        '''
        將k棒寫入csv
        '''
        
    def write_history(self):
        df = pd.DataFrame({**self.tick})
        df.ts = pd.to_datetime(df.ts)
        df.to_csv(self.min_path, mode='a', index=False, header=not os.path.exists(self.min_path))
        
    def convert_k_bar(self,time_unit):
        '''
        將歷史/即時1分k轉為n分(無法輸入日k，會有偏差)
        '''
        file_path = os.path.join('data', time_unit + '.csv')
        df = pd.read_csv(self.min_path)
        if(time_unit == "D"):
            print("待處理")
        else:
            df['ts'] = pd.to_datetime(df['ts'])
            df = df.set_index('ts')
            ohlc_dict = {
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }
            df_data = df.resample(rule=time_unit,label='right', closed='right').agg(ohlc_dict)
            df_data = df_data.dropna()
            df_data.to_csv(file_path)
        
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