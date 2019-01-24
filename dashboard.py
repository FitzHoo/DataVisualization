from scripts.candlestick import candlestick_plot
from scripts.industry_analysis import sw_industry_analysis

from bokeh.io import curdoc
from bokeh.models import Tabs


tab_1 = candlestick_plot()
tab_2 = sw_industry_analysis()

tabs = Tabs(tabs=[tab_1, tab_2])
curdoc().add_root(tabs)
