import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import mplfinance as mpf
import matplotlib.patches as mpatches

idf = pd.read_csv('data/5Min.csv',index_col=0,parse_dates=True)
pkwargs=dict(type='candle')
fig, axes = mpf.plot(idf.iloc[0:20],returnfig=True,volume=True,
                     figsize=(11,8),panel_ratios=(3,1),
                     title='你的標題', **pkwargs,style='starsandstripes')
ax1 = axes[0]
ax2 = axes[2]
## define the colors and labels
colors = ["red","green","blue","Indigo"]
labels = ["Open", "High", "Low", "Close"]

def run_animation():
    ani_running = True

    def onClick(event):
        nonlocal ani_running
        
        if ani_running:
            ani.event_source.stop()
            ani_running = False
        else:
            ani.event_source.start()
            ani_running = True


    def animate(ival):
        if (20+ival) > len(idf):
            print('no more data to plot')
            ani.event_source.interval *= 3
            if ani.event_source.interval > 12000:
                exit()
            return

        data = idf.iloc[100+ival:(250+ival)]
        print(idf.iloc[ival+250])
        

        ## what to display in legend
        values = idf.iloc[ival+250][labels].to_list()
        legend_labels = [f"{l}: {str(v)}" for l,v in zip(labels,values)]
        handles = [mpatches.Patch(color=c, label=ll) for c,ll in zip(colors, legend_labels)]

        ax1.clear()
        ax2.clear()

        mpf.plot(data,ax=ax1,volume=ax2,**pkwargs,style='yahoo')

        ## add legend after plotting
        ax1.legend(handles=handles, loc=2)

    fig.canvas.mpl_connect('button_press_event', onClick)
    ani = animation.FuncAnimation(fig, animate, interval=240)
run_animation()
mpf.show()
