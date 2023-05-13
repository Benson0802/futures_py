import numpy as np
import pandas as pd
import globals

def detect_level_method_2(df):
    '''
    取得支撐壓力的方法2
    '''
    levels = []
    max_list = []
    min_list = []
    for i in range(5, len(df)-5):
        high_range = df['high'][i-5:i+4]
        current_max = high_range.max()
        if current_max not in max_list:
            max_list = []
        max_list.append(current_max)
        if len(max_list) == 5 and is_far_from_level(current_max, levels, df):
            levels.append((high_range.idxmax(), current_max))
            
        low_range = df['low'][i-5:i+5]
        current_min = low_range.min()
        if current_min not in min_list:
            min_list = []
        min_list.append(current_min)
        if len(min_list) == 5 and is_far_from_level(current_min, levels, df):
            levels.append((low_range.idxmin(), current_min))
            
    data = convert_arr_sort(levels)
    return data
    
def detect_level_method_1(df):
    '''
    取得支撐壓力(方法1)
    '''
    levels = []
    for i in range(2,df.shape[0]-2):
        if is_support(df,i):
            l = df['low'][i]
            if is_far_from_level(l, levels, df):
                levels.append((i,l))
        elif is_resistance(df,i):
            l = df['high'][i]
            if is_far_from_level(l, levels, df):
                levels.append((i,l))
        
    data = convert_arr_sort(levels)
    return data
    
def is_far_from_level(value, levels, df):
    '''
    判斷新的支壓存不存在
    '''
    ave =  np.mean(df['high'] - df['low'])    
    return np.sum([abs(value-level)<ave for _,level in levels])==0

def is_support(df,i):
    '''
    取得支撐
    '''
    cond1 = df['low'][i] < df['low'][i-1]   
    cond2 = df['low'][i] < df['low'][i+1]   
    cond3 = df['low'][i+1] < df['low'][i+2]   
    cond4 = df['low'][i-1] < df['low'][i-2]  
    return (cond1 and cond2 and cond3 and cond4) 

def is_resistance(df,i):
    '''
    取得壓力
    ''' 
    cond1 = df['high'][i] > df['high'][i-1]   
    cond2 = df['high'][i] > df['high'][i+1]   
    cond3 = df['high'][i+1] > df['high'][i+2]   
    cond4 = df['high'][i-1] > df['high'][i-2]  
    return (cond1 and cond2 and cond3 and cond4)

def convert_arr_sort(data):
    sorted_data = sorted(data, key=lambda x: x[1])  # 按第二个元素排序
    selected_data = sorted_data[:5]  # 选择前5个元素
    result = [x[1] for x in selected_data]  # 提取第二个元素
    return result

def has_breakout():
    '''
    判斷是否突破或跌破
    '''
    df = pd.read_csv('data/60Min.csv', index_col='datetime')
    previous = df.iloc[-2]
    last = df.iloc[-1]
    for level in globals.levels:
        cond1 = (previous['open'] < level) 
        cond2 = (last['open'] > level) and (last['low'] > level)
    return (cond1 and cond2)