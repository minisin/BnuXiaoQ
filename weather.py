#-*- encoding: utf-8 -*-

import webapp2
from google.appengine.api import memcache
from func import *
import json

def validate(c):
    if c == 'w':
        return True
    return False

def answerNow():
    w = db.GqlQuery('SELECT * FROM Weather WHERE day = :1', 0).get()
    s = '当前天气状况：\n'
    s += '温度：' + w.temp + '\n'
    s += '风力：' + w.wind + '\n'
    s += '着装建议：' + w.desc + '\n'
    s += '\n'
    return s

def answerNext(d):
    w = db.GqlQuery('SELECT * FROM Weather WHERE day = :1', d).get()
    s = w.temp + '， ' + w.desc + '\n'
    return s

def answer(ToUserName, FromUserName, CreateTime, MsgType, Content):
    Content = memcache.get(key = 'weather')
    if not Content:
        Content = ''
        Content += answerNow()
        Content += '未来五天预报：\n'
        for i in range(1, 6):
            Content += answerNext(i)
        w = db.GqlQuery('SELECT * FROM Weather WHERE day = :1', 0).get()
        Content += '\n更新时间：'
        Content += (w.updateTime + datetime.timedelta(hours = 8)).strftime('%m月%d日 %H:%M')
        memcache.add(key = 'weather', value = Content, time = 600)
    return genTextXml(ToUserName, FromUserName, CreateTime, MsgType, Content)

def getOrCreateWeatherByDay(d):
    w = db.GqlQuery('SELECT * FROM Weather WHERE day = :1', d).get()
    if not w:
        w = Weather()
        w.day = d
        w.save()
    return w

def updateFive():
    url = 'http://m.weather.com.cn/data/101010200.html'
    res = urlfetch.fetch(url).content
    j = json.loads(res)
    j = j['weatherinfo']
    temp = list()
    temp.append(j['temp1'])
    temp.append(j['temp2'])
    temp.append(j['temp3'])
    temp.append(j['temp4'])
    temp.append(j['temp5'])
    desc = list()
    desc.append(j['weather1'])
    desc.append(j['weather2'])
    desc.append(j['weather3'])
    desc.append(j['weather4'])
    desc.append(j['weather5'])
    for i in range(0, 5):
        w = getOrCreateWeatherByDay(i + 1)
        w.temp = temp[i]
        w.desc = desc[i]
        w.save()
    w = getOrCreateWeatherByDay(0)
    w.desc = j['index_d']
    w.save()

def updateNow():
    url = 'http://www.weather.com.cn/data/sk/101010200.html'
    res = urlfetch.fetch(url).content
    j = json.loads(res)
    j = j['weatherinfo']
    temp = j['temp'] + '℃'
    wind = j['WS'] + j['WD']
    w = getOrCreateWeatherByDay(0)
    w.temp = temp
    w.wind = wind
    w.save()

class FetchHandler(webapp2.RequestHandler):
    def get(self):
        updateFive()
        updateNow()

app = webapp2.WSGIApplication([
    ('/weather/fetch', FetchHandler)
], debug = True)