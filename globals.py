def initialize(): 
    global has_thread #是否有子線程(繪圖子線程)
    global now_min #即時的分鐘
    global tick_min #tick的分鐘
    global volume #這一分鐘tick的累積量
    global amount #這一分鐘收集的tick收盤價
    global is_break #是否突破
    global code #台指期月份
    global direction #方向 1 做多  2做空
    global is_backtest #是否回測
    global how #取幾根k棒
    global levels #支撐壓力
    global aisle_type #判斷類型 1上通道 2下通道 3 最高壓力  4最低支撐  5次高壓力 6次低支撐
    global pattern
    global today
    has_thread = False
    now_min = None
    tick_min = None
    volume = 0
    amount = []
    is_break = False
    code = ''
    is_backtest = False
    how = 500
    levels = None
    direction = 0
    aisle_type = 0
    pattern = None
    today = None