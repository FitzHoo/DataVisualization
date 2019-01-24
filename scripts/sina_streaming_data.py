import re
import requests
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Spacer
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.plotting import figure
from bokeh.layouts import row, column

source = ColumnDataSource(dict(time=[], low=[], high=[], open=[], last=[]))
source_1 = ColumnDataSource(dict(low=[], high=[], open=[], last=[], volume=[], value=[]))
source_2 = ColumnDataSource(dict(ask_bid_price=[], ask_bid_volume=[], index=[]))

fig = figure(x_axis_type='datetime', plot_width=1000, plot_height=500)
fig.line(x="time", y="last", color="navy", line_width=2, source=source)
# fig.background_fill_color = "black"

columns_1 = [TableColumn(field='open', title='开盘价'),
             TableColumn(field='last', title='最新价'),
             TableColumn(field='high', title='最高价'),
             TableColumn(field='low', title='最低价'),
             TableColumn(field='volume', title='成交量(手)'),
             TableColumn(field='value', title='成交金额(万元)')]

columns_2 = [TableColumn(field='index', title='明细'),
             TableColumn(field='ask_bid_price', title='五档委托价'),
             TableColumn(field='ask_bid_volume', title='五档委托量')]

data_table_1 = DataTable(source=source_1, columns=columns_1, width=fig.plot_width, height=50)
data_table_2 = DataTable(source=source_2, columns=columns_2, height=fig.plot_height, width=300)

layout = column(row(data_table_1, Spacer(height=data_table_1.height, width=data_table_2.width)), row(fig, data_table_2))

url = "http://hq.sinajs.cn/list={}".format('sz002916')


def get_streaming_data():
    original_data = requests.get(url).text
    data = re.findall(r'"(.*?)"', original_data)[0].split(',')

    symbol = data[0]
    # date = datetime.strptime(data[-3], '%Y-%m-%d').date()
    time = datetime.strptime(data[-2], '%H:%M:%S').time()
    # dt = datetime.combine(date, time)
    open = float(data[1])
    last = float(data[3])
    high = float(data[4])
    low = float(data[5])
    volume = int(float(data[8]) / 100)  # 手
    value = round(float(data[9]) / 10000, 2)  # 万元

    temp = data[10: 30]
    index = ['卖五', '卖四', '卖三', '卖二', '卖一', '买一', '买二', '买三', '买四', '买五']
    _ask_bid_volume = [float(j) for i, j in enumerate(temp) if i % 2 == 0]
    ask_bid_volume = _ask_bid_volume[5:][::-1] + _ask_bid_volume[:5]
    _ask_bid_price = [float(j) for i, j in enumerate(temp) if i % 2 != 0]
    ask_bid_price = _ask_bid_price[5:][::-1] + _ask_bid_price[:5]  # 从卖五到买五

    return symbol, time, open, last, high, low, volume, value, ask_bid_price, ask_bid_volume, index


def update():
    symbol, time, open, last, high, low, volume, value, ask_bid_price, ask_bid_volume, index = get_streaming_data()
    print(time, open, last, high, low, volume, value)

    fig.title.text = symbol
    new_data = dict(time=[time], open=[open], last=[last], high=[high], low=[low])
    new_data_1 = dict(open=[open], last=[last], high=[high], low=[low], volume=[volume], value=[value])
    new_data_2 = dict(ask_bid_price=ask_bid_price, ask_bid_volume=ask_bid_volume, index=index)
    source.stream(new_data, rollover=fig.plot_width)
    source_1.data.update(new_data_1)
    source_2.data.update(new_data_2)


curdoc().add_root(layout)
curdoc().add_periodic_callback(update, 500)  # 每秒更新一次
