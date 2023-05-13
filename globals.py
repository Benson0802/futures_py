def initialize(): 
    global has_thread #是否有子線程(繪圖子線程)
    global now_min #即時的分鐘
    global tick_min #tick的分鐘
    global volume #這一分鐘tick的累積量
    global amount #這一分鐘收集的tick收盤價
    global is_break #是否突破
    global code #台指期月份
    global is_backtest #是否回測
    global how #取幾根k棒
    global levels #支撐壓力
    
    has_thread = False
    now_min = None
    tick_min = None
    volume = 0
    amount = []
    is_break = False
    code = ''
    is_backtest = False
    how = 100
    levels = None