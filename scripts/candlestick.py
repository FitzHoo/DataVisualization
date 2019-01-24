import talib

import numpy as np
from math import pi
from datetime import datetime

import rqdatac

rqdatac.init('rice', 'rice', ('192.168.0.225', 16010))
from rqdatac import *

from bokeh.models import ColumnDataSource, HoverTool, Panel, CheckboxGroup, Select, DatePicker, TextInput, Button, Tabs
from bokeh.plotting import figure
# from bokeh.io import curdoc

from bokeh.palettes import Spectral6

from bokeh.layouts import row, column, widgetbox


def candlestick_plot():
    def obv_indicator(data):
        res = talib.OBV(data.close.values, data.volume.values)
        return res

    def rsi_indicator(data):
        res = talib.RSI(data.close.values, timeperiod=14)
        return res

    def cci_indicator(data):
        res = talib.CCI(data.high.values, data.low.values, data.close.values, timeperiod=14)
        return res

    def technical_indicator(data, indicator):
        if indicator == 'CCI':
            data['tech'] = cci_indicator(data)
        elif indicator == 'RSI':
            data['tech'] = rsi_indicator(data)
        else:
            data['tech'] = obv_indicator(data)
        return data

    def load_data(obid, start, end, freq='1d'):
        print('running....')
        data = get_price(obid, start, end, freqency=freq).reset_index()
        data['pct_change'] = data['close'].pct_change()
        # data.dropna(inplace=True)

        data['pct_change'] = data['pct_change'].apply(lambda x: str(round(x * 100, 2)) + '%')
        data['index'] = list(np.arange(len(data)))
        data['date'] = data['date'].apply(lambda x: x.strftime("%Y%m%d"))

        return data

    def moving_average(data, selection):
        selection_mapping = {k: int(k.split('_')[-1]) for k in selection}
        for k, v in selection_mapping.items():
            data[k] = data['close'].rolling(window=v).mean()
        return data

    def update_lines(attr, old, new):
        line_0.visible = 0 in average_selection.active
        line_1.visible = 1 in average_selection.active
        line_2.visible = 2 in average_selection.active
        line_3.visible = 3 in average_selection.active
        line_4.visible = 4 in average_selection.active
        line_5.visible = 5 in average_selection.active

    def update_plot(attr, old, new):
        indicator = indicator_selection.value
        new_data = technical_indicator(data, indicator)
        new_source = ColumnDataSource(new_data)

        source.data.update(new_source.data)

    def update_data():
        # global obid, start, end
        obid = order_book_id.value
        start = start_date.value
        end = end_date.value

        # 提取数据，均线根据选取与否进行添加
        new_data = load_data(obid, start, end)
        new_data_1 = moving_average(new_data, average_labels)
        new_data_2 = technical_indicator(new_data, indicator_selection.value)

        new_source = ColumnDataSource(new_data_2)
        new_source_1 = ColumnDataSource(new_data_1)
        source.data.update(new_source.data)
        source_1.data.update(new_source_1.data)

        inc = new_data.close >= new_data.open
        dec = new_data.close < new_data.open

        inc_source.data = inc_source.from_df(new_data_2.loc[inc])
        dec_source.data = dec_source.from_df(new_data_2.loc[dec])

        p.title.text = instruments(obid).symbol
        p.x_range.end = len(new_data) + 1
        p2.xaxis.major_label_overrides = {i: date for i, date in enumerate(new_data['date'])}

    today = datetime.now().date()

    average_labels = ["MA_5", "MA_10", "MA_20", 'MA_30', 'MA_60', 'MA_120']
    average_selection = CheckboxGroup(labels=average_labels, active=[0, 1, 2, 3, 4, 5, 6])

    indicator_selection = Select(title='TechnicalIndicator', value='RSI', options=['OBV', 'RSI', 'CCI'])

    order_book_id = TextInput(title='StockCode', value='002916.XSHE')
    symbol = instruments(order_book_id.value).symbol
    start_date = DatePicker(title="StartDate", value='2018-01-01', min_date='2015-01-01', max_date=today)
    end_date = DatePicker(title="EndDate", value=today, min_date=start_date.value, max_date=today)

    #     labels = [average_selection.labels[i] for i in average_selection.active]
    data = load_data(order_book_id.value, start_date.value, end_date.value)

    # 均线计算
    data_1 = moving_average(data, average_labels)  # 计算各种长度的均线

    # 技术指标计算
    data_2 = technical_indicator(data, indicator_selection.value)

    source = ColumnDataSource(data_2)
    source_1 = ColumnDataSource(data_1)

    inc = data.close >= data.open
    dec = data.open > data.close

    inc_source = ColumnDataSource(data_2.loc[inc])
    dec_source = ColumnDataSource(data_2.loc[dec])

    TOOLS = 'save, pan, box_zoom, reset, wheel_zoom'

    hover = HoverTool(tooltips=[('date', '@date'),
                                ('open', '@open'),
                                ('high', '@high'),
                                ('low', '@low'),
                                ('close', '@close'),
                                ('pct_change', "@pct_change")
                                ]
                      )

    length = len(data)
    p = figure(plot_width=1000, plot_height=500, title='{}'.format(symbol), tools=TOOLS, x_range=(0, length + 1))
    p.xaxis.visible = False  # 隐藏x-axis
    p.min_border_bottom = 0

    # 均线图
    line_0 = p.line(x='index', y='MA_5', source=source_1, color=Spectral6[5])
    line_1 = p.line(x='index', y='MA_10', source=source_1, color=Spectral6[4])
    line_2 = p.line(x='index', y='MA_20', source=source_1, color=Spectral6[3])
    line_3 = p.line(x='index', y='MA_30', source=source_1, color=Spectral6[2])
    line_4 = p.line(x='index', y='MA_60', source=source_1, color=Spectral6[1])
    line_5 = p.line(x='index', y='MA_120', source=source_1, color=Spectral6[0])

    p.segment(x0='index', y0='high', x1='index', y1='low', color='red', source=inc_source)
    p.segment(x0='index', y0='high', x1='index', y1='low', color='green', source=dec_source)
    p.vbar('index', 0.5, 'open', 'close', fill_color='red', line_color='red', source=inc_source, hover_fill_alpha=0.5)
    p.vbar('index', 0.5, 'open', 'close', fill_color='green', line_color='green', source=dec_source,
           hover_fill_alpha=0.5)

    p.add_tools(hover)

    p1 = figure(plot_width=p.plot_width, plot_height=200, x_range=p.x_range, toolbar_location=None)
    p1.vbar('index', 0.5, 0, 'volume', color='red', source=inc_source)
    p1.vbar('index', 0.5, 0, 'volume', color='green', source=dec_source)
    p1.xaxis.visible = False

    p2 = figure(plot_width=p.plot_width, plot_height=p1.plot_height, x_range=p.x_range, toolbar_location=None)
    p2.line(x='index', y='tech', source=source)

    p2.xaxis.major_label_overrides = {i: date for i, date in enumerate(data['date'])}
    p2.xaxis.major_label_orientation = pi / 4
    p2.min_border_bottom = 0

    button = Button(label="ClickToChange", button_type="success")
    button.on_click(update_data)
    average_selection.inline = True
    average_selection.width = 500
    average_selection.on_change('active', update_lines)
    indicator_selection.on_change('value', update_plot)
    widgets = column(row(order_book_id, start_date, end_date, button), row(indicator_selection, average_selection))

    layouts = column(widgets, p, p1, p2)

    # doc.add_root(pp)
    # make a layout
    tab = Panel(child=layouts, title='StockPrice')

    return tab


# tabs = Tabs(tabs=[candlestick_plot()])
# curdoc().add_root(tabs)


