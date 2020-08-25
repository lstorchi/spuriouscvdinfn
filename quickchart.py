import sys
import argparse
import datetime

import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--file", help="input csv file ", \
            required=True, type=str)
    
    args = parser.parse_args()
    
    filename = args.file

    df = pd.read_csv(filename)

    df = df.drop (["IdSensor", \
        "State", "Storico", "UTM_Est", "lat", \
        "DataStart", 'lng', 'location', 'Limit', "Utm_Nord"], axis=1)

    
    allinq = {}

    no2 = df[df["TypeOfSensor"] == "Biossido di Azoto"]
    allinq["NO2"] = no2
    o3 = df[df["TypeOfSensor"] == "Ozono"]
    allinq["O3"] = o3
    pm10 = df[df["TypeOfSensor"] == "PM10 (SM2005)"]
    allinq["PM10"] = pm10
    pm25 = df[df["TypeOfSensor"] == "Particelle sospese PM2.5"]
    allinq["PM2.5"] = pm25
    so2 = df[df["TypeOfSensor"] == "Biossido di Zolfo"]
    allinq["SO2"] = so2
    co = df[df["TypeOfSensor"] == "Monossido di Carbonio"]
    allinq["CO"] = co

    allinq_davg = {}
    for k in allinq:
        print("%5s has %10d values"%(k, allinq[k].shape[0]))
        allinq[k] = allinq[k].drop(["TypeOfSensor"], axis=1)
        print(allinq[k].head())

        values = []
        for i in range(allinq[k]["Value"].values.shape[0]):
            v = allinq[k]["Value"].values[i]
            v = v.replace(",", ".")
            values.append(float(v))

        dates = []
        for i in range(allinq[k]["Date"].values.shape[0]):
            d = allinq[k]["Date"].values[i].split()[0]
            ds = datetime.datetime.strptime(d,"%d/%m/%Y").date()
            dates.append(ds)

        if len(dates) != len(values):
            print("Error in size")
            exit(1)

        newdf = pd.DataFrame({'Date':dates,'Value':values})
        newdf['Date'] = pd.to_datetime(newdf.Date)
        newdf = newdf[newdf['Value'] >= 0.0]  
        allinq[k] = newdf.sort_values(by='Date')
        allinq[k]["Year"] = pd.DatetimeIndex(allinq[k]["Date"]).year

        print(allinq[k].head())

        lastdf = allinq[k].resample('d', on='Date').mean()
        allinq_davg[k] = lastdf
        
        print(allinq_davg[k].head())

        just2020 = allinq_davg[k][allinq_davg[k]["Year"] == 2020.0 ]

        x_values = just2020.index
        y_values = just2020["Value"]
        
        plt.clf()

        ax = plt.gca()
        formatter = mdates.DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(formatter)
        locator = mdates.MonthLocator()
        ax.xaxis.set_major_locator(locator)
        ax.set(xlabel="Date", ylabel="", \
            title= k + " values " )

        plt.plot(x_values, y_values, label=k)
        plt.savefig(k+'.png')

    max = -1
    kmax = ""
    for k in ["O3", "NO2", "PM10", "SO2", "CO"]:
        just2020 = allinq_davg[k][allinq_davg[k]["Year"] == 2020.0 ]
        print("%5s has %10d values"%(k, just2020.shape[0]))
        if max < just2020.shape[0]:
            kmax = k
        #print(just2020.index)
    
    just2020kmax = allinq_davg[k][allinq_davg[kmax]["Year"] == 2020.0 ]
    for d in just2020kmax.index: 
        print(d)