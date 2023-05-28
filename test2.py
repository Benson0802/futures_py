# import numpy as np
# import matplotlib.pyplot as plt
# import pandas as pd
# from talib import abstract

# # 函數功能：將頻域數據轉換成時序數據
# # bins爲頻域數據，n設置使用前多少個頻域數據，loop設置生成數據的長度
# def fft_combine(bins, n, loops=1):
#     length = int(len(bins) * loops)
#     data = np.zeros(length)
#     index = loops * np.arange(0, length, 1.0) / length * (2 * np.pi)
#     for k, p in enumerate(bins[:n]):
#         if k != 0 : p *= 2 # 除去直流成分之外, 其餘的係數都 * 2
#         data += np.real(p) * np.cos(k*index) # 餘弦成分的係數爲實數部分
#         data -= np.imag(p) * np.sin(k*index) # 正弦成分的係數爲負的虛數部分
#     return index, data

# def analyze_fft(dataform1):
#     lines = dataform1.shape[0]
#     # 生成隨機數
#     x = np.random.random(100)
#     y = np.fft.fft(x)
#     plt.subplot(2, 1, 1)
#     # plt.plot(x)
#     plt.plot(dataform1["ma5"])
#     #dft_a = np.fft.fft(dataform1["ma5"])

#     plt.subplot(2, 1, 2)
#     """
#     plt.plot(dft_a)
#     #plt.plot(y)
#     plt.xlabel('Freq (Hz)'), plt.ylabel(' ')
#     plt.show()"""
#     ts_log = np.log(dataform1["ma5"])
#     #ts_log = dataform1["ma5"]
#     #ts_diff = ts_log.diff(1)
#     ts_diff = ts_log
#     ts_diff = ts_diff.dropna()
#     fy = np.fft.fft(ts_diff)
#     conv1 = np.real(np.fft.ifft(fy))  # 逆變換
#     index, conv2 = fft_combine(fy / len(ts_diff), int(len(fy) / 2 - 1), 1.3)
#     ntotal = (len(ts_diff)/10 +2)*10

#     plt.plot(ts_diff)
#     plt.plot(conv1 - 0.5)
#     plt.plot(conv2 - 1)
#     plt.xticks(np.arange(1, ntotal, 5))
#     plt.grid( )
#     plt.show()
#     return 0


# df_60Min = pd.read_csv('data/60Min.csv', index_col='datetime')
# df = df_60Min.tail(500).reset_index(drop=False)
# sma5 = abstract.SMA(df['close'], 5)
# df['ma5'] = sma5
# analyze_fft(df)