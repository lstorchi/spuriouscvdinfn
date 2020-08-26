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
    parser.add_argument("-f","--file", help="input poullants csv file ", \
            required=True, type=str)
    parser.add_argument("-c","--filecases", help="input cases csv file ", \
            required=False, type=str, default="")

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
            if type(v) == str:
                v = v.replace(",", ".")
                if k == "CO":
                    values.append(float(v)*1000.0)
                else:
                    values.append(float(v))
            else:
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
    aqidata = ["O3", "NO2", "PM10", "SO2", "CO"]
    normv = {"O3":100.0, "NO2":90.0, "PM10":50.0, "SO2":125, "CO":10000}
    for k in aqidata:
        just2020 = allinq_davg[k][allinq_davg[k]["Year"] == 2020.0 ]
        print("%5s has %10d values"%(k, just2020.shape[0]))
        if max < just2020.shape[0]:
            kmax = k
        #print(just2020.index)
    
    just2020kmax = allinq_davg[k][allinq_davg[kmax]["Year"] == 2020.0 ]
    aqi = {}
    for d in just2020kmax.index: 
        print(d)
        alldatain = True
        cmax = []
        for k in aqidata:
            just2020 = allinq_davg[k][allinq_davg[k]["Year"] == 2020.0 ]
            try:
                print(" ", k, " => %8.4f"%(just2020.loc[d]["Value"]), end = "")
                cmax.append(just2020.loc[d]["Value"]/normv[k])
            except KeyError as ke:
                print(" ", k, " => NaN", end = "")
                alldata = False
        print()

        if alldatain:
            aqi[d] = np.max (cmax) * 50.0
            
    plt.clf()

    x_values = list(aqi.keys())
    y_values = list(aqi.values())

    ax = plt.gca()
    formatter = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(formatter)
    locator = mdates.MonthLocator()
    ax.xaxis.set_major_locator(locator)
    ax.set(xlabel="Date", ylabel="", \
        title= "AQI values " )

    plt.plot(x_values, y_values, label="AQI")
    plt.savefig('aqi.png')

    if args.filecases != "":
        cdf = pd.read_csv(args.filecases)

        dates = []
        for i in range(cdf["Date"].values.shape[0]):
            d = cdf["Date"].values[i].split("T")[0]
            ds = datetime.datetime.strptime(d,"%Y-%m-%d").date()
            dates.append(ds)
        
        totcases = []
        for i in range(cdf["Total Cases"].values.shape[0]):
            tc = float(cdf["Total Cases"].values[i])
            totcases.append(tc)
        
        ndf = pd.DataFrame({"Date":dates, "Total_Cases":totcases})
        ndf = ndf.sort_values(by="Date")
        
        newcases = []
        prev = 0.0
        for i, r in ndf.iterrows():
            nc = r["Total_Cases"] - prev
            newcases.append(nc)
            prev = r["Total_Cases"]
            
        ndf["New_Cases"] = newcases
            
        #print(ndf)
        
        idx = 0
        allinqvalues = []
        for i, r in ndf.iterrows():
            d = r["Date"]
            nc = r["New_Cases"]
            tc = r["Total_Cases"]
            inqvalues = {}
            for k in aqidata:
                just2020 = allinq_davg[k][allinq_davg[k]["Year"] == 2020.0 ]
                
                try:
                    value = just2020.loc[d, :]["Value"]
                except KeyError as ke:
                    value = -1.0
                inqvalues[k] = value
                
            allinqvalues.append(inqvalues)
            print(idx, nc, inqvalues["PM10"])
            idx += 1
            #print(inqvalues)
            
        """
        plt.clf()
        x_values = ndf["Dates"].values
        y_values = ndf["New_Cases"].values
 

        ax = plt.gca()
        formatter = mdates.DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(formatter)
        locator = mdates.MonthLocator()
        ax.xaxis.set_major_locator(locator)
        ax.set(xlabel="Date", ylabel="", \
            title= "New cases" )

        plt.plot(x_values, y_values, label=k)
        plt.show()
        """



