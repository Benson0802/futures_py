import math

def fibonacci(df):
    highest_swing = -1
    lowest_swing = -1
        

    for i in range(1,df.shape[0]-1):
        if df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i+1] and (highest_swing == -1 or df['high'][i] > df['high'][highest_swing]):
            highest_swing = i

        if df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i+1] and (lowest_swing == -1 or df['low'][i] < df['low'][lowest_swing]):
            lowest_swing = i
     

    ratios = [0, 0.236, 0.382, 0.5 , 0.618, 0.786,1]
    colors = ["black","r","g","b","cyan","magenta","yellow"]
    levels = []

    max_level = df['high'][highest_swing]
    min_level = df['low'][lowest_swing]

    for ratio in ratios:
        if highest_swing > lowest_swing: # Uptrend
            levels.append(math.ceil(max_level - (max_level-min_level)*ratio))
        else: # Downtrend
            levels.append(math.ceil(min_level + (max_level-min_level)*ratio))
        
    result = sorted(levels)
    return result