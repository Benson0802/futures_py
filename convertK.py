import pandas as pd
import os.path

class convertK():
    '''
    tick轉換為k棒
    '''
    def __init__(self, tick):
        self.datetime = tick['datetime']
        self.open = float(tick['open'])
        self.high = float(tick['high'])
        self.low = float(tick['low'])
        self.volume = int(tick['volume'])
        self.close = float(tick['close'])
        # 將tick轉換為DataFrame
        self.df = pd.DataFrame({'datetime': [self.datetime], 'open': [self.open], 'high': [self.high], 'low': [self.low], 'volume': [self.volume], 'close':[self.close]})
        # 轉換時間戳
        self.df['datetime'] = pd.to_datetime(self.df['datetime'], format='%Y-%m-%d %H:%M:%S.%f')
        # 設置時間戳為索引
        self.df.set_index('datetime', inplace=True)
    
    def convert_k_bar(self,time_unit):
        '''
        tick轉為k棒
        '''
        file_path = os.path.join('data', time_unit + '.csv')

        # 判斷文件是否為空或是沒文件則先創造DataFrame
        if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
            empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close'])
            empty_df.to_csv(file_path)

        # 讀取csv
        existing_df = pd.read_csv(file_path, index_col=0, parse_dates=True)

        # 排除重覆資料
        if len(existing_df) > 0 and existing_df.index[-1] == self.df.resample(time_unit).apply({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna().index[0]:
            print('Duplicate data. Skipping...')
            return False

        # 讀取新資料
        kbar = self.df.resample(time_unit).apply({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()

        # 合併現有資料並寫入csv
        new_df = pd.concat([existing_df, kbar])
        new_df.to_csv(file_path)

        print(kbar)
        return True