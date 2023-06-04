#支撐壓力
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import plotly.graph_objects as go

df = pd.read_csv('data/60Min.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df.set_index(['datetime'], inplace=True)
df = df.tail(500)
df_prices = np.array(df["close"])

K = 9
kmeans = KMeans(n_clusters=6).fit(df_prices.reshape(-1, 1))
clusters = kmeans.predict(df_prices.reshape(-1, 1))

# Create list to hold values, initialized with infinite values
min_max_values = []
# init for each cluster group
for i in range(6):
    # Add values for which no price could be greater or less
    min_max_values.append([np.inf, -np.inf])
    # Print initial values
    print(min_max_values)
# Get min/max for each cluster
for i in range(len(df_prices)):
    # Get cluster assigned to price
    cluster = clusters[i]
    # Compare for min value
    if df_prices[i] < min_max_values[cluster][0]:
        min_max_values[cluster][0] = df_prices[i]
    # Compare for max value
    if df_prices[i] > min_max_values[cluster][1]:
        min_max_values[cluster][1] = df_prices[i]

print("Initial Min/Max Values:\n", min_max_values)
# Create container for combined values
output = []
# Sort based on cluster minimum
s = sorted(min_max_values, key=lambda x: x[0])
# For each cluster get average of
for i, (_min, _max) in enumerate(s):
    # Append min from first cluster
    if i == 0:
        output.append(_min)
    # Append max from last cluster
    if i == len(min_max_values) - 1:
        output.append(_max)
    # Append average from cluster and adjacent for all others
    else:
        output.append(sum([_max, s[i+1][0]]) / 2)

pd.options.plotting.backend = 'plotly'
colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo']

fig = df.plot.scatter(
    x=df.index,
    y="close",
    color=[colors[i] for i in clusters],
)

# Add horizontal lines
for cluster_avg in output[1:-1]:
    fig.add_hline(y=cluster_avg, line_width=1, line_color="blue")
    
# Add a trace of the price for better clarity
fig.add_trace(go.Trace(
    x=df.index,
    y=df['close'],
    line_color="black",
    line_width=1
))

layout = go.Layout(
    plot_bgcolor='#efefef',
    showlegend=False,
    # Font Families
    font_family='Monospace',
    font_color='#000000',
    font_size=20,
    xaxis=dict(
        rangeslider=dict(
            visible=False
        ))
)

fig.update_layout(layout)
# Display plot in local browser window
fig.show()