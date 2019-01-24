import rqdatac

rqdatac.init('****', '****', ('****', ****))
from rqdatac import *

import numpy as np
from datetime import datetime

# from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Spacer, Tabs, Panel
from bokeh.models.widgets import PreText, Select
from bokeh.plotting import figure

# 预储存行业字典
SHENWAN_INDUSTRY_MAP = {
    "801010.INDX": "农林牧渔",
    "801020.INDX": "采掘",
    "801030.INDX": "化工",
    "801040.INDX": "钢铁",
    "801050.INDX": "有色金属",
    "801080.INDX": "电子",
    "801110.INDX": "家用电器",
    "801120.INDX": "食品饮料",
    "801130.INDX": "纺织服装",
    "801140.INDX": "轻工制造",
    "801150.INDX": "医药生物",
    "801160.INDX": "公用事业",
    "801170.INDX": "交通运输",
    "801180.INDX": "房地产",
    "801200.INDX": "商业贸易",
    "801210.INDX": "休闲服务",
    "801230.INDX": "综合",
    "801710.INDX": "建筑材料",
    "801720.INDX": "建筑装饰",
    "801730.INDX": "电气设备",
    "801740.INDX": "国防军工",
    "801750.INDX": "计算机",
    "801760.INDX": "传媒",
    "801770.INDX": "通信",
    "801780.INDX": "银行",
    "801790.INDX": "非银金融",
    "801880.INDX": "汽车",
    "801890.INDX": "机械设备"
}

SHENWAN_INDUSTRY_MAP_ = {v: k for k, v in SHENWAN_INDUSTRY_MAP.items()}
DEFAULT_TICKERS = list(SHENWAN_INDUSTRY_MAP.values())

TOOLS = 'pan, wheel_zoom, box_zoom, box_select, lasso_select, reset'
LINE_ARGS = dict(color='#3A5785', line_color=None)


def sw_industry_analysis():

    def nix(val, lst):
        return [x for x in lst if x != val]

    def get_data(ticker_1, ticker_2, start='20180101', end=datetime.today().date()):
        df = get_price([ticker_1, ticker_2], start, end, fields='close')
        df['t1_returns'] = np.log(df[ticker_1]).diff()
        df['t2_returns'] = np.log(df[ticker_2]).diff()
        return df.dropna().reset_index()

    def get_hhist_data(data):
        hhist, hedges = np.histogram(data['t1_returns'], bins=20)
        hzeros = np.zeros_like(hhist)
        hhist_data = {'left': hedges[:-1], 'right': hedges[1:], 'bottom': hzeros,
                      'top': hhist, 'top_1': hzeros, 'top_2': hzeros}
        return hhist_data

    def get_vhist_data(data):
        vhist, vedges = np.histogram(data['t2_returns'], bins=20)
        vzeros = np.zeros_like(vhist)
        vhist_data = {'left': vzeros, 'right': vhist, 'bottom': vedges[:-1],
                      'top': vedges[1:], 'right_1': vzeros, 'right_2': vzeros}
        return vhist_data

    def ticker1_change(attr, old, new):
        ticker_2.options = nix(new, DEFAULT_TICKERS)
        update()

    def ticker2_change(attr, old, new):
        ticker_1.options = nix(new, DEFAULT_TICKERS)
        update()

    def update():
        global df
        ticker_1_name, ticker_2_name = SHENWAN_INDUSTRY_MAP_[ticker_1.value], SHENWAN_INDUSTRY_MAP_[ticker_2.value]
        df = get_data(ticker_1_name, ticker_2_name)

        source.data.update(dict(x=df['t1_returns'], y=df['t2_returns'], x_p=df[ticker_1_name],
                                y_p=df[ticker_2_name], date=df['date']))

        hhist_data_dict = get_hhist_data(df)
        source_hhist.data.update(hhist_data_dict)
        hmax = max(source_hhist.data['top']) * 1.1
        ph.y_range.update(start=-hmax, end=hmax)
        print('ph.y_range', ph.y_range.end)

        vhist_data_dict = get_vhist_data(df)
        source_vhist.data.update(vhist_data_dict)
        vmax = max(source_vhist.data['right']) * 1.1
        pv.x_range.update(start=vmax, end=-vmax)
        print('pv.x_range', pv.x_range.end)
        print(20 * '=')

        update_stats(df, ticker_1_name, ticker_2_name)

        corr.title.text = "{} vs. {}".format(ticker_1.value, ticker_2.value)
        ts1.title.text = ticker_1.value
        ts2.title.text = ticker_2.value

    def udpate_selection(attr, old, new):
        inds = new  # 选定的数据对应的索引
        length = len(df)
        if 0 < len(inds) < length:
            neg_inds = [s for s in range(length) if s not in inds]  # 未选定数据点的对应索引
            _, hedges = np.histogram(df['t1_returns'], bins=20)
            _, vedges = np.histogram(df['t2_returns'], bins=20)

            new_hhist_df = df['t1_returns']
            new_vhist_df = df['t2_returns']

            hhist1, _ = np.histogram(new_hhist_df.iloc[inds], bins=hedges)
            hhist2, _ = np.histogram(new_hhist_df.iloc[neg_inds], bins=hedges)

            vhist1, _ = np.histogram(new_vhist_df.iloc[inds], bins=vedges)
            vhist2, _ = np.histogram(new_vhist_df.iloc[neg_inds], bins=vedges)

            source_hhist.patch({'top_1': [(slice(None), hhist1)], 'top_2': [(slice(None), -hhist2)]})
            source_vhist.patch({'right_1': [(slice(None), vhist1)], 'right_2': [(slice(None), -vhist2)]})

    def update_stats(data, t1, t2):
        stats_indicator = data[[t1, t2, 't1_returns', 't2_returns']].describe()
        ticker_1_name, ticker_2_name = ticker_1.value, ticker_2.value
        stats_indicator.columns = [ticker_1_name, ticker_2_name, ticker_1_name + '收益率', ticker_2_name + '收益率']
        stats.text = str(stats_indicator)

    # Set Up Widgets
    stats = PreText(text='', width=700)
    ticker_1 = Select(value='非银金融', options=nix('食品饮料', DEFAULT_TICKERS))
    ticker_2 = Select(value='食品饮料', options=nix('非银金融', DEFAULT_TICKERS))

    # Callback
    ticker_1.on_change('value', ticker1_change)
    ticker_2.on_change('value', ticker2_change)

    # Construct DataSource
    source = ColumnDataSource(data=dict(x=[], y=[], x_p=[], y_p=[], date=[]))
    source_hhist = ColumnDataSource(data=dict(left=[], right=[], bottom=[], top=[], top_1=[], top_2=[]))
    source_vhist = ColumnDataSource(data=dict(left=[], right=[], bottom=[], top=[], right_1=[], right_2=[]))

    # 收益率散点图
    corr = figure(plot_width=500, plot_height=500, tools=TOOLS)
    r = corr.scatter(x='x', y='y', size=2, source=source, selection_color='orange', alpha=0.6,
                     nonselection_alpha=0.1, selection_alpha=0.4)

    # 添加横轴直方图
    hmax = 40
    ph = figure(toolbar_location=None, plot_width=corr.plot_width, plot_height=200, y_range=(-hmax, hmax),
                min_border=10, min_border_left=None, y_axis_location='left', x_axis_location='above')
    ph.quad(bottom='bottom', top='top', left='left', right='right', color='white', line_color="#3A5785",
            source=source_hhist)
    ph.quad(bottom='bottom', top='top_1', left='left', right='right', alpha=0.5, source=source_hhist, **LINE_ARGS)
    ph.quad(bottom='bottom', top='top_2', left='left', right='right', alpha=0.1, source=source_hhist, **LINE_ARGS)

    ph.xgrid.grid_line_color = None
    ph.yaxis.major_label_orientation = np.pi / 4
    ph.background_fill_color = '#fafafa'

    # 添加纵轴直方图
    vmax = 40
    pv = figure(toolbar_location=None, plot_height=corr.plot_height, plot_width=200, x_range=(vmax, -vmax),
                min_border=10, min_border_left=None, y_axis_location='left')
    pv.quad(bottom='bottom', top='top', left='left', right='right', color='white', line_color="#3A5785",
            source=source_vhist)
    pv.quad(bottom='bottom', top='top', left='left', right='right_1', alpha=0.5, source=source_vhist, **LINE_ARGS)
    pv.quad(bottom='bottom', top='top', left='left', right='right_2', alpha=0.1, source=source_vhist, **LINE_ARGS)

    # 股价时间序列图
    ts1 = figure(plot_width=900, plot_height=200, tools=TOOLS, x_axis_type='datetime', active_drag='box_select',
                 toolbar_location='above')
    ts1.line('date', 'x_p', source=source)
    ts1.circle('date', 'x_p', size=1, source=source, color=None, selection_color='orange')

    ts2 = figure(plot_width=ts1.plot_width, plot_height=ts1.plot_height, tools=TOOLS, x_axis_type='datetime',
                 active_drag='box_select', toolbar_location='above')
    ts2.x_range = ts1.x_range
    ts2.line('date', 'y_p', source=source)
    ts2.circle('date', 'y_p', size=1, source=source, color=None, selection_color='orange')

    # 初始化数据
    update()

    r.data_source.selected.on_change('indices', udpate_selection)

    widgets = column(ticker_1, ticker_2, widgetbox(stats))
    layout_1 = column(row(Spacer(width=200, height=200), ph), row(pv, corr, widgets))

    layout_2 = column(layout_1, ts1, ts2)

    tab = Panel(child=layout_2, title='IndustryAnalysis')

    return tab

# tabs = Tabs(tabs=[sw_industry_analysis()])
# curdoc().add_root(tabs)
