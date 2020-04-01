import pandas as pd
import io
from requests import get
from numpy import exp, linspace, log
from scipy.optimize import curve_fit
from datetime import date
#import matplotlib.pylab 
import matplotlib.pyplot as plt
from itertools import izip


def gaussian(x, amp, cen, wid):
    return amp * exp(-(x-cen)**2 / wid)

def log_gaussian(x, amp, cen, wid):
    return log(gaussian(x, amp, cen, wid))

def cum_gaussian(x, amp, cen, wid):
    return gaussian(x, amp, cen, wid).cumsum()

def cum_log_gaussian(x, amp, cen, wid):
    return log(cum_gaussian(x, amp, cen, wid))

def set_bounds(ax,x,y):
    ax[0].set_xbound(*x)
    ax[0].set_ybound(*y)
    ax[1].set_xbound(*x)
    ax[1].set_ybound(1,y[1])


countries = ['UK', 'IT', 'FR', 'ES', 'US', 'CN']

params = [100, 0, 1000]
x = linspace(-60, 40, 101)

today = date.today()
f = lambda x: (x-today).dt.days
dateparse = lambda dates: [pd.datetime.strptime(d, '%d/%m/%Y') for d in dates]
data = pd.read_csv(
    io.StringIO(
        get("https://opendata.ecdc.europa.eu/covid19/casedistribution/csv/").content.decode('utf-8-sig')
        ),
    header=0,
    parse_dates=['dateRep'],
    date_parser=dateparse
    )

# r = get('https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide.xlsx', stream=True)
# 
# r.raw.decode_content = True  # decompress gzip or deflate responses
# data = pd.read_excel(r.raw)

data['DayN']=data.groupby(['geoId'])['dateRep'].apply(f)
data=data.sort_values(['DayN'])
data['TotalCases']=data.groupby(['geoId'])['cases'].cumsum()
data['TotalDeaths']=data.groupby(['geoId'])['deaths'].cumsum()


fig1, ax = plt.subplots(ncols=2, nrows=2)

x_bounds = [-50,20]


data.groupby(['DayN','geoId']).first()['TotalDeaths'].unstack()[countries].plot(marker='x', linewidth=0, title="Total Deaths", ax=ax[0,1])
data.groupby(['DayN','geoId']).first()['TotalDeaths'].unstack()[countries].plot(logy=True, marker='x', linewidth=0, title="Total Deaths", ax=ax[1,1])
data.groupby(['DayN','geoId']).first()['TotalCases'].unstack()[countries].plot(marker='x', linewidth=0, title="Total Cases", ax=ax[0,0])
data.groupby(['DayN','geoId']).first()['TotalCases'].unstack()[countries].plot(logy=True, marker='x', linewidth=0, title="Total Cases", ax=ax[1,0])

plt.show(block=False)
plt.pause(0.001)

colors = [line.get_color() for line in ax[0][0].lines]

for code, color in izip(countries, colors):
    try:
        res = next(x for x, val in enumerate(data[data.geoId==code].TotalDeaths) 
                                  if val > 10) - len(data[data.geoId==code].deaths)
        
        if code=='CN':
            cn_params, covars = curve_fit(cum_gaussian, data[data.geoId==code].DayN[res:], data[data.geoId==code].TotalDeaths[res:], p0=params, maxfev=10000)
            ax[0,1].plot(x-20,cum_gaussian(x-20, *cn_params), color=color, linestyle=':')
            ax[1,1].plot(x-20,cum_gaussian(x-20, *cn_params), color=color, linestyle=':')
        else:
            params, covars = curve_fit(cum_gaussian, data[data.geoId==code].DayN[res:], data[data.geoId==code].TotalDeaths[res:], p0=params, maxfev=10000)
            ax[0,1].plot(x[-80:],cum_gaussian(x[-80:], *params), color=color, linestyle=':')
            ax[1,1].plot(x[-80:],cum_gaussian(x[-80:], *params), color=color, linestyle=':')
        plt.draw()
        plt.pause(0.001)
    except RuntimeError:
        print "Couldn't fit Deaths for {}".format((code,))
    except StopIteration:
        print "not enough data to fit Deaths for {}".format((code,))

for code, color in izip(countries, colors):
    try:
        res = next(x for x, val in enumerate(data[data.geoId==code].TotalCases) 
                                  if val > 10) - len(data[data.geoId==code].cases)
                                  
        if code=='CN':
            cn_params, covars = curve_fit(cum_gaussian, data[data.geoId==code].DayN[res:], data[data.geoId==code].TotalCases[res:], p0=params, maxfev=10000)
            ax[0,0].plot(x-20,cum_gaussian(x-20, *cn_params), color=color, linestyle=':')
            ax[1,0].plot(x-20,cum_gaussian(x-20, *cn_params), color=color, linestyle=':')
        else:
            params, covars = curve_fit(cum_gaussian, data[data.geoId==code].DayN[res:], data[data.geoId==code].TotalCases[res:], p0=params, maxfev=10000)
            ax[0,0].plot(x[-80:],cum_gaussian(x[-80:], *params), color=color, linestyle=':')
            ax[1,0].plot(x[-80:],cum_gaussian(x[-80:], *params), color=color, linestyle=':')
        plt.draw()
        plt.pause(0.001)
    except RuntimeError:
        print "Couldn't fit for {}".format((code,))
    except StopIteration:
        print "not enough data to fit for {}".format((code,))

set_bounds([ax[0,0], ax[1,0]], x_bounds, [0, 500000])
set_bounds([ax[0,1], ax[1,1]], x_bounds, [0, 25000])
plt.pause(9999)
