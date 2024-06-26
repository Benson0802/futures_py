from tradingpatterns.hard_data import generate_sample_df_with_pattern
from tradingpatterns.tradingpatterns import detect_head_shoulder
from tradingpatterns.tradingpatterns import detect_trendline
from tradingpatterns.tradingpatterns import detect_multiple_tops_bottoms
from tradingpatterns.tradingpatterns import calculate_support_resistance
from tradingpatterns.tradingpatterns import detect_triangle_pattern
from tradingpatterns.tradingpatterns import detect_wedge
from tradingpatterns.tradingpatterns import detect_channel
from tradingpatterns.tradingpatterns import detect_double_top_bottom
from tradingpatterns.tradingpatterns import detect_trendline
from tradingpatterns.tradingpatterns import find_pivots
import pandas as pd
import numpy as np

def get_pattern(df_n):
    '''
    detect_head_shoulder 頭肩頂和反頭肩頂：這些形態表明市場可能出現反轉，“頭”是最高點，“肩”是兩側略低的點。(判斷反轉可以用)
        head_shoulder_pattern會有head_shoulder_pattern會有Inverse Head and Shoulder(多)及Head and Shoulder(空)字串
    detect_multiple_tops_bottoms 多重頂部和底部：這些形態表明市場處於區間震盪狀態，多個高點和低點形成一個水平區間。(判斷區間可以用，但不好用)
        multiple_top_bottom_pattern會有Multiple Top(空)及Multiple Bottom(多)字串
    calculate_support_resistance 水平支撐和阻力：這些模式表明市場此前難以突破的關鍵水平。(判斷支壓可以用，但不好用)
    detect_triangle_pattern 上升和下降三角形模式：這些模式表明市場可能出現突破，上方趨勢線是阻力位，下方趨勢線是支撐位。(判斷型態可以用)
        triangle_pattern會有Ascending Triangle(上升)及Descending Triangle(下降)
    detect_wedge 楔形向上和向下：這些模式表明市場可能出現逆轉，趨勢線相互匯合。(可以用，判斷型態)
        wedge_pattern會有Wedge Up(上升)及Wedge Down(下降)
    detect_channel 上下通道：這些模式表明市場趨勢強勁，價格在明確的上下趨勢線內移動。(可以用，判斷通道向上向下)
        channel_pattern會出現Channel Up及Channel Down
    detect_double_top_bottom 雙頂和雙底：這些形態表明市場可能出現反轉，市場兩次觸及高點或低點，然後反轉。(可以用，判斷型態)
        double_pattern會出現Double Top及Double Bottom
    detect_trendline 趨勢線支撐和阻力：這些模式表明市場可能根據歷史價格行為經歷支撐或阻力的關鍵水平。(不能用，完全不準)
    find_pivots 尋找更高的高點和更低的低點(可以用但不好判斷)
    '''
    # df_n = detect_head_shoulder(df_n)
    # df_n = detect_multiple_tops_bottoms(df_n)
    # df_n = calculate_support_resistance(df_n) 棄用
    # df_n = detect_triangle_pattern(df_n)
    # df = pd.read_csv('data/60Min.csv', index_col='datetime')
    # df = detect_wedge(df)
    # df.reset_index(inplace=True)
    # df_n = pd.merge(df_n, df[["datetime", "wedge_pattern"]], on="datetime", how="left")
    df = pd.read_csv('data/60Min.csv', index_col='datetime')
    df = detect_channel(df)
    df.reset_index(inplace=True)
    df_n = pd.merge(df_n, df[["datetime", "channel_pattern"]], on="datetime", how="left")
    df_n = detect_double_top_bottom(df_n)
    # print(df_n)
    # exit()
    return df_n