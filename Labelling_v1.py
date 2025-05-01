# %%

import numpy as np
from tqdm import tqdm

import pandas as pd
import warnings
from sqlalchemy import create_engine, text
from datetime import datetime, date
import matplotlib.pyplot as plt


# %%


def auto_labeling(data_list, timestamp_list, w):
    labels = np.zeros(len(data_list))
    FP = data_list[0]
    x_H = data_list[0]
    HT = timestamp_list[0]
    x_L = data_list[0]
    LT = timestamp_list[0]
    Cid = 0
    FP_N = 0
    for i in range(len(data_list)):
        if data_list[i] > FP + data_list[0] * w:
            x_H = data_list[i]
            HT = timestamp_list[i]
            FP_N = i
            Cid = 1
            break
        if data_list[i] < FP - data_list[0] * w:
            x_L = data_list[i]
            LT = timestamp_list[i]
            FP_N = i
            Cid = -1
            break
    for i in tqdm(range(FP_N, len(data_list))):
        if Cid > 0:
            if data_list[i] > x_H:
                x_H = data_list[i]
                HT = timestamp_list[i]
            if data_list[i] < x_H - x_H * w and LT < HT:
                for j in range(len(data_list)):
                    if timestamp_list[j] > LT and timestamp_list[j] <= HT:
                        labels[j] = 1
                x_L = data_list[i]
                LT = timestamp_list[i]
                Cid = -1
        if Cid < 0:
            if data_list[i] < x_L:
                x_L = data_list[i]
                LT = timestamp_list[i]
            if data_list[i] > x_L + x_L * w and HT <= LT:
                for j in range(len(data_list)):
                    if timestamp_list[j] > HT and timestamp_list[j] <= LT:
                        labels[j] = -1
                x_H = data_list[i]
                HT = timestamp_list[i]
                Cid = 1
    # Post-processing
    labels[0] = labels[1]
    labels = np.where(labels == 0, Cid, labels)
    assert len(labels) == len(timestamp_list)
    timestamp2label_dict = {timestamp_list[i]: labels[i] for i in range(len(timestamp_list))}
    return labels, timestamp2label_dict


def plot_ts_with_trend_and_financial_extremes(ax, Date_list, Cls_list, trend_labels, x_interval):
    x = [i for i in range(len(Date_list))]
    for i in range(len(trend_labels) - 1):
        j = i
        while j < len(trend_labels) - 2 and trend_labels[j] == trend_labels[j + 1]:
            j = j + 1
        if trend_labels[j - 1] == -1:
            color = 'orange'
        elif trend_labels[j - 1] == 1:
            color = 'skyblue'
        else:
            color = 'white'
        ax.plot(x[i:j+1], Cls_list[i:j+1], color)
    ax.set_xlabel('Date')
    ax.set_ylabel("Price")
    x_sampled = []
    for i in x:
        if i % x_interval == 0:
            x_sampled.append(i)
    x = x_sampled
    xtick = [Date_list[i] for i in x]
    ax.set_xticks(x)
    ax.set_xticklabels(xtick)
    for xtick in ax.get_xticklabels():
        xtick.set_rotation(0)
    return ax



# %%

# Database connection
engine = create_engine(
    "postgresql+psycopg://postgres:Nefertiti7@192.168.116.64/postgres?application_name=Python_App_Results_Summary",
    isolation_level="SERIALIZABLE", connect_args={'sslmode': "disable"})
            
# %%

ticker='DE'
exchange='NYSE'
p_date='2020-01-01'

params = {'symbol': ticker, 'exchange': exchange, 'p_date': p_date} 

query="""SELECT pricehistory.datetime, pricehistory.symbol::text, pricehistory.exchange::text, pricehistory.open, pricehistory.high, pricehistory.low, pricehistory.close, pricehistory.volume from pricehistory
                      WHERE pricehistory.symbol::text = %(symbol)s::text
                      
                      AND pricehistory.datetime::date > %(p_date)s::date """

with engine.connect() as con:                                                                         
    df = pd.read_sql(query, con, parse_dates={"datetime": {"format": "%y-%m-%d"}}, params=params) 


df.sort_values(by='datetime', ascending=True, inplace=True)
df

# %%



#stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sz399300")
df['date'] = df['datetime'].astype(str)
#stock_zh_index_daily_df = stock_zh_index_daily_df[stock_zh_index_daily_df['date'] >= '2005-04-08']
Date_list = df['date'].values.tolist()
Cls_list = df['close'].values.tolist()
for w in [0.05, 0.08, 0.1, 0.15, 0.2]:
    trend_labels, _ = auto_labeling(Cls_list, Date_list, w)
    fig = plt.figure(figsize=(15, 5), dpi=300)
    ax = plt.gca()
    ax = plot_ts_with_trend_and_financial_extremes(ax, Date_list, Cls_list, trend_labels, x_interval=300)
    title = "Trend Labeling of CSI 300 with w={}%".format(w*100)
    ax.set_title(title)
    plt.savefig('figures/' + '{}.png'.format(title))
    
    
    
# %%
