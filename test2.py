import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 假設有以下的Kpi線資料
k_lines = np.array([[1, 5], [2, 6], [3, 8], [4, 10], [5, 12], [6, 15]])

# 提取出收盤價
close_prices = k_lines[:, 1]

# 提取出時間序列，這裡假設每個K線的時間間隔都是一樣的
time_series = np.arange(len(close_prices)).reshape(-1, 1)

# 訓練線性回歸模型
reg = LinearRegression().fit(time_series, close_prices)

# 預測未來趨勢，這裡假設要預測未來5個時間點的趨勢
future_time_series = np.arange(len(close_prices), len(close_prices)+5).reshape(-1, 1)
future_close_prices = reg.predict(future_time_series)

# 繪製趨勢線
plt.plot(time_series, close_prices, label='close Prices')
plt.plot(np.concatenate((time_series, future_time_series)), np.concatenate((reg.predict(time_series), future_close_prices)), label='Trend Line')
plt.legend()
plt.show()