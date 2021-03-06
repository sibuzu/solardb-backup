# -*- coding: utf-8 -*-
 
import os
import sys
from firebase import firebase
from datetime import date, datetime, timedelta
import dateutil.parser
import pickle

firebaseDb = firebase.FirebaseApplication('https://solar-0.firebaseio.com', None)
firebaseRaw = firebase.FirebaseApplication('https://solar-2.firebaseio.com', None)
basepath = './data/'

def getRawdata(mydata, dt, rawdata):
    dataCount = 0
    mydata['rawdata'] = {}
    x1 = mydata['rawdata']
    for station, invs in rawdata.items():
        x1[station] = {}
        x2 = x1[station]
        for inv, dates in invs.items():
            x2[inv] = {}
            x3 = x2[inv]
            for date, raws in dates.items():
                if date == dt:
                    x3[dt] = raws
                    dataCount += 1
    return dataCount

def getPowerdata(mydata, dt, powerdata):
    dataCount = 0
    mydata['power'] = {}
    x1 = mydata['power']
    for station, dates in powerdata["power"].items():
        x1[station] = {}
        x2 = x1[station]
        for timestamp, data in dates.items():
            if timestamp == dt:
                x2[dt] = data
                dataCount += 1
    return dataCount

def getSunshine(mydata, dt, powerdata):
    dataCount = 0
    mydata['sunshine'] = {}
    x1 = mydata['sunshine']
    for station, dates in powerdata["sunshine"].items():
        x1[station] = {}
        x2 = x1[station]
        for timestamp, data in dates.items():
            if timestamp == dt:
                x2[dt] = data
                dataCount += 1
    return dataCount

def getAlarmlog(mydata, dt, powerdata):
    dataCount = 0
    mydata['alarmlog'] = {}
    x1 = mydata['alarmlog']
    for station, dates in powerdata["alarmlog"].items():
        x1[station] = {}
        x2 = x1[station]
        for timestamp, data in dates.items():
            tstr = timestamp[:4] + timestamp[5:7] + timestamp[8:10]
            if tstr == dt:
                x2[timestamp] = data
                dataCount += 1
    return dataCount

def clearRawdata(dt, rawdata):
    dataCount = 0
    dstr = "{}{:02}{:02}".format(dt.year, dt.month, dt.day)
    for station, invs in rawdata.items():
        for inv, items in invs.items():
            for dkey in list(items.keys()):
                if dkey < dstr:
                    del items[dkey]
                    dataCount += 1

    return dataCount

def clearSunshine(dt, powerdata):
    dataCount = 0
    dstr = "{}{:02}{:02}".format(dt.year, dt.month, dt.day)
    for station, items in powerdata["sunshine"].items():
        for dkey in list(items.keys()):
            if dkey < dstr:
                del items[dkey]
                dataCount += 1

    return dataCount

def clearAlarmlog(dt, powerdata):
    dataCount = 0
    dstr = "{}{:02}{:02}".format(dt.year, dt.month, dt.day)
    for station, items in powerdata["alarmlog"].items():
        for dkey in list(items.keys()):
            tstr = dkey[:4] + dkey[5:7] + dkey[8:10]
            if tstr < dstr:
                del items[dkey]
                dataCount += 1

    return dataCount

def clearPower(dt, powerdata):
    dataCount = 0
    dstr = "{}{:02}{:02}".format(dt.year, dt.month, dt.day)
    for station, items in powerdata["power"].items():
        for dkey, invs in items.items():
            if dkey < dstr:
                for ikey in list(invs.keys()):
                    if ikey!='total':
                        del invs[ikey]
                        dataCount += 1 
    return dataCount

if __name__ == '__main__':
    n = len(sys.argv)
    if n == 1:
        dt = datetime.today() - timedelta(days=1)
    elif n == 2:
        dt = dateutil.parser.parse(sys.argv[1])
    else:
        print("usage: solar_update.py [date]")
        print("  if date is not given, implying today")

    dstr = "{}{:02}{:02}".format(dt.year, dt.month, dt.day)
    print("{:%Y-%m-%d %H:%M:%S}: backup db of {}".format(datetime.now(),  dstr))

    rawdata = firebaseRaw.get('/', 'rawdata')
    powerdata = firebaseDb.get('/', '')

    dpath = basepath + dstr[:6]
    os.makedirs(dpath, exist_ok=True)
        
    mydata = {}
    n = getRawdata(mydata, dstr, rawdata)
    if n > 0:
        pklfile = dpath + '/' + dstr + '-rawdata.pkl' 
        with open(pklfile, 'wb') as fh:
            pickle.dump(mydata, fh)
    
    mydata = {}
    n = getPowerdata(mydata, dstr, powerdata)
    if n > 0:
        pklfile = dpath + '/' + dstr + '-powerdata.pkl' 
        with open(pklfile, 'wb') as fh:
            pickle.dump(mydata, fh)
    
    mydata = {}
    n = getSunshine(mydata, dstr, powerdata)
    if n > 0:
        pklfile = dpath + '/' + dstr + '-sunshine.pkl' 
        with open(pklfile, 'wb') as fh:
            pickle.dump(mydata, fh)
    
    mydata = {}
    n = getAlarmlog(mydata, dstr, powerdata)
    if n > 0:
        pklfile = dpath + '/' + dstr + '-alarmlog.pkl' 
        with open(pklfile, 'wb') as fh:
            pickle.dump(mydata, fh)

    # Clear Data
    power_dt = dt - timedelta(days=15)
    alarm_dt = dt - timedelta(days=3)
    sunshine_dt = dt - timedelta(days=15)
    rawdata_dt = dt - timedelta(days=3)

    n = clearRawdata(rawdata_dt, rawdata)
    # print(rawdata["正霆"]["inv01"].keys())
    if n > 0:
        firebaseRaw.put('/', 'rawdata', rawdata)

    n = clearSunshine(sunshine_dt, powerdata)
    if n > 0:
        firebaseDb.put('/', 'sunshine', powerdata["sunshine"])

    n = clearAlarmlog(alarm_dt, powerdata)
    if n > 0:
        firebaseDb.put('/', 'alarmlog', powerdata["alarmlog"])

    n = clearPower(power_dt, powerdata)
    if n > 0:
        firebaseDb.put('/', 'power', powerdata["power"])

    command = 'git add . && git commit -am "{}" && git push'.format(dstr)
    print(command)
    os.system(command)
