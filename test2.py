# #box
# import pandas as pd
# import numpy as np
# from sklearn.cluster import KMeans
# import plotly.graph_objects as go

# df = pd.read_csv('data/60Min.csv')
# df['datetime'] = pd.to_datetime(df['datetime'])
# df.set_index(['datetime'], inplace=True)
# df = df.tail(500)
# df_prices = np.array(df["close"])

# K = 9
# kmeans = KMeans(n_clusters=6).fit(df_prices.reshape(-1, 1))
# clusters = kmeans.predict(df_prices.reshape(-1, 1))

# # Create list to hold values, initialized with infinite values
# min_max_values = []
# # init for each cluster group
# for i in range(6):
#     # Add values for which no price could be greater or less
#     min_max_values.append([np.inf, -np.inf])
#     # Print initial values
#     print(min_max_values)
# # Get min/max for each cluster
# for i in range(len(df_prices)):
#     # Get cluster assigned to price
#     cluster = clusters[i]
#     # Compare for min value
#     if df_prices[i] < min_max_values[cluster][0]:
#         min_max_values[cluster][0] = df_prices[i]
#     # Compare for max value
#     if df_prices[i] > min_max_values[cluster][1]:
#         min_max_values[cluster][1] = df_prices[i]

# print("Initial Min/Max Values:\n", min_max_values)
# # Create container for combined values
# output = []
# # Sort based on cluster minimum
# s = sorted(min_max_values, key=lambda x: x[0])
# # For each cluster get average of
# for i, (_min, _max) in enumerate(s):
#     # Append min from first cluster
#     if i == 0:
#         output.append(_min)
#     # Append max from last cluster
#     if i == len(min_max_values) - 1:
#         output.append(_max)
#     # Append average from cluster and adjacent for all others
#     else:
#         output.append(sum([_max, s[i+1][0]]) / 2)

# pd.options.plotting.backend = 'plotly'
# colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo']

# fig = df.plot.scatter(
#     x=df.index,
#     y="close",
#     color=[colors[i] for i in clusters],
# )

# # Add horizontal lines
# for cluster_avg in output[1:-1]:
#     fig.add_hline(y=cluster_avg, line_width=1, line_color="blue")
  
# # Add a trace of the price for better clarity
# fig.add_trace(go.Trace(
#     x=df.index,
#     y=df['close'],
#     line_color="black",
#     line_width=1
# ))

# layout = go.Layout(
#     plot_bgcolor='#efefef',
#     showlegend=False,
#     # Font Families
#     font_family='Monospace',
#     font_color='#000000',
#     font_size=20,
#     xaxis=dict(
#         rangeslider=dict(
#             visible=False
#         ))
# )

# fig.update_layout(layout)
# # Display plot in local browser window
# fig.show()

# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# Define parameters
stock = 'TSM'  # Stock symbol or name
start_date = '2020-01-01'  # Start date of the time range
end_date = '2020-12-31'  # End date of the time range
interval = '1d'  # Interval of the data points
capital = 100000  # Initial capital
trade_amount = 0.1  # Trade amount or ratio
height_factor = 1.5  # Height factor for dynamic box height
width_factor = 1.2  # Width factor for dynamic box width
volume_threshold = 2  # Volume threshold for buy or sell signals

# Download data from Yahoo Finance
data = yf.download(stock, start=start_date, end=end_date, interval=interval)
data['Date'] = data.index  # Add a Date column

# Calculate the 20-day average volume
data['Avg_Volume'] = data['Volume'].rolling(20).mean()

# Initialize variables
box_height = None  # Box height
box_width = None  # Box width
box_top = None  # Box top
box_bottom = None  # Box bottom
position = None  # Position (long or short)
trade_price = None  # Trade price
trade_volume = None  # Trade volume
balance = capital  # Balance
profit = 0  # Profit
signals = []  # List of signals (buy or sell)
trades = []  # List of trades (entry or exit)

# Loop through the data
for i in range(len(data)):
    date = data['Date'][i]  # Current date
    open_price = data['Open'][i]  # Current open price
    high_price = data['High'][i]  # Current high price
    low_price = data['Low'][i]  # Current low price
    close_price = data['Close'][i]  # Current close price
    volume = data['Volume'][i]  # Current volume

    if box_height is None:  # If no box height is set, use the first day's range as the initial box height
        box_height = high_price - low_price

    if box_width is None:  # If no box width is set, use 1 as the initial box width
        box_width = 1

    if box_top is None:  # If no box top is set, use the first day's high as the initial box top
        box_top = high_price

    if box_bottom is None:  # If no box bottom is set, use the first day's low as the initial box bottom
        box_bottom = low_price

    if position is None:  # If no position is set, use 'short' as the initial position
        position = 'short'

    signal = None  # Initialize signal as None

    if position == 'short':  # If in a short position, look for buy signals

        if volume > volume_threshold * data['Avg_Volume'][i]:  # If volume exceeds the threshold

            if high_price > box_top:  # If high price breaks above the box top

                signal = 'buy'  # Generate a buy signal

                trade_price = max(open_price, box_top)  # Set trade price as the maximum of open price and box top

                trade_volume = int(balance * trade_amount / trade_price)  # Set trade volume as a fraction of balance

                balance -= trade_volume * trade_price  # Deduct trade amount from balance

                position = 'long'  # Switch to long position

                box_height *= height_factor  # Update box height by multiplying with height factor

                box_width *= width_factor  # Update box width by multiplying with width factor

                box_top += box_height  # Update box top by adding box height

                box_bottom += box_height  # Update box bottom by adding box height

    elif position == 'long':  # If in a long position, look for sell signals

        if volume > volume_threshold * data['Avg_Volume'][i]:  # If volume exceeds the threshold

            if low_price < box_bottom:  # If low price breaks below the box bottom

                signal = 'sell'  # Generate a sell signal

                trade_price = min(open_price, box_bottom)  # Set trade price as the minimum of open price and box bottom

                trade_volume = int(balance * trade_amount / trade_price)  # Set trade volume as a fraction of balance

                balance += trade_volume * trade_price  # Add trade amount to balance

                profit += trade_volume * (trade_price - trades[-1][2])  # Calculate profit from the last entry trade

                position = 'short'  # Switch to short position

                box_height *= height_factor  # Update box height by multiplying with height factor

                box_width *= width_factor  # Update box width by multiplying with width factor

                box_top -= box_height  # Update box top by subtracting box height

                box_bottom -= box_height  # Update box bottom by subtracting box height

    if signal is not None:  # If a signal is generated, record it in the signals list
        signals.append((date, signal, trade_price, trade_volume))

    if signal == 'buy':  # If a buy signal is generated, record it as an entry trade in the trades list
        trades.append((date, 'entry', trade_price, trade_volume))

    if signal == 'sell':  # If a sell signal is generated, record it as an exit trade in the trades list
        trades.append((date, 'exit', trade_price, trade_volume))

# Print results
print('Final balance:', balance)
print('Total profit:', profit)
print('Number of signals:', len(signals))
print('Number of trades:', len(trades))

# Plot results
plt.figure(figsize=(12, 8))
plt.plot(data['Date'], data['Close'], label='Close Price')
plt.plot(data['Date'], data['Avg_Volume'], label='Average Volume')
for signal in signals:
    if signal[1] == 'buy':
        plt.scatter(signal[0], signal[2], color='green', marker='^', label='Buy Signal')
    elif signal[1] == 'sell':
        plt.scatter(signal[0], signal[2], color='red', marker='v', label='Sell Signal')
plt.legend()
plt.title('Darvas Box Trading Strategy for ' + stock)
plt.xlabel('Date')
plt.ylabel('Price/Volume')
plt.show()