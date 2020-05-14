#!/usr/bin/env python3

import os
import re

import hmac
import time
import json
import uuid
import urllib.parse

import requests
#from hyper.contrib import HTTP20Adapter

from requests.packages.urllib3.exceptions import InsecureRequestWarning	
#关闭安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class pica(object):
    
    def __init__(self, apiKey, apiSecret, token = '', channel = 1, quality = 'original', proxies = None, debug = False):
        '''
        :param apiKey: str 例：C69BAF41DA5ABD1FFEDC6D2FEA56B
        :param apiSecret: str 密钥：~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn
        :param token: str 用户Token 可留空
        :param channel: int 分流通道 可选：1、2、3
        :param quality: str 图片质量 可选：original、low、medium、high
        :param proxies: str 代理 默认无代理
        :param debug: bool Debug 默认关闭
        '''
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        self.token = token
        self.proxies = proxies
        self.debug = debug
        self.url = 'https://picaapi.picacomic.com/'
        self.header = {
            'Host': 'picaapi.picacomic.com',
            'authorization': token,
            'api-key': apiKey,
            'accept': 'application/vnd.picacomic.com.v1+json',
            'app-channel': str(channel),
            'time': '',
            'nonce': '',
            'signature': '',
            'app-version': '2.2.1.3.3.4',
            'app-uuid': 'defaultUuid',
            'image-quality': quality,
            'app-platform': 'android',
            'app-build-version': '45',
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/3.8.1'
        }

    def getSignature(self, path, method, timestamp, nonce):
        '''
        :param path: str 完整路径，如：https://picaapi.picacomic.com/users/profile
        :param method str 请求的方法 POST或GET
        :param timestamp str 时间戳(精确到秒)
        :param nonce str 32位随机数字字母，使用uuid去掉-实现
        '''
        raw = (path + str(timestamp) + nonce + method + self.apiKey).lower()
        signature = hmac.new(self.apiSecret.encode(), raw.encode(), 'sha256')
        return signature.hexdigest()

    def post(self, url, data=None):
        ts = str(int(time.time()))
        nonce = str(uuid.uuid4()).replace('-', '')
        self.header['time'] = ts
        self.header['nonce'] = nonce
        self.header['authorization'] = self.token
        self.header['signature'] = self.getSignature(url, 'POST', ts, nonce)
        headerTmp = self.header.copy()
        headerTmp.pop('authorization')
        headerTmp['content-type'] = 'application/json; charset=UTF-8'
        if self.debug:
            print(url)
            print(headerTmp)
        return requests.post(url=self.url + url, data=data, headers=headerTmp, verify=False, proxies=self.proxies)

    def get(self, url):
        ts = str(int(time.time()))
        nonce = str(uuid.uuid4()).replace('-', '')
        self.header['time'] = ts
        self.header['nonce'] = nonce
        self.header['authorization'] = self.token
        self.header['signature'] = self.getSignature(url, 'GET', ts, nonce)
        if self.debug:
            print(url)
            print(self.header)
        #s = requests.Session()
        #s.mount(self.url, HTTP20Adapter())
        #return s.get(url=self.url + url, headers=self.header, verify=False, proxies=self.proxies)
        return requests.get(url=self.url + url, headers=self.header, verify=False, proxies=self.proxies)

    def singin(self, email, password):
        try:
            token = self.post('auth/sign-in', json.dumps({'email':email, 'password':password})).json()
        except:
            return ''
        else:
            if token['code'] == 200:
                self.token = token['data']['token']
            return token['message']

    #个人信息
    def userInfo(self):
        #用户信息
        return self.get('users/profile').json()

    def favourite(self, page = '1', sort = 'dd'):
        #收藏夹
        return self.get('users/favourite?s={0}&page={1}'.format(sort, page)).json()

    def myComments(self, page = '1'):
        #我的评论
        return self.get('users/my-comments?page={0}'.format(page)).json()

    #广告和推荐
    def collections(self):
        #首页推荐
        return self.get('collections').json()

    def announcements(self, page = '1'):
        #公告
        return self.get('announcements?page={0}'.format(page)).json()

    def initapp(self):
        #应用初始化信息，包含部分分类、服务器地址和APP版本信息
        return self.get('init?platform=android').json()

    def banners(self):
        #首页banners广告
        return self.get('banners').json()

    #搜索和分类
    def keywords(self):
        #搜索建议关键词
        return self.get('keywords').json()

    def categories(self):
        #分类
        return self.get('categories').json()

    def advancedSearch(self, keyword, page = '1', sort = 'dd'):
        #高级搜索
        return self.post('comics/advanced-search?page={0}'.format(page), json.dumps({'keyword':keyword, 'sort':sort})).json()

    #游戏
    def gamesList(self, page = '1'):
        #游戏列表
        return self.get('games?page={0}'.format(page)).json()

    def games(self, id):
        #游戏信息
        return self.get('games/{0}'.format(id)).json()

    def gamesComments(self, id, page = '1'):
        #游戏评论
        return self.get('games/{0}/comments?page={1}'.format(id, page)).json()

    #漫画
    def comicsList(self, page = '1', c = None, t = None, a = None, f = None, s = None, ct = None, ca = None):
        #漫画分类列表
        #参数：page:页数 c:分类 t:标签 a:作者 --f:未知-- s:排序 ct:汉化组 --ca:未知--
        #sort可取：dd - 新到旧，da - 旧到新，ld - 最多爱心，vd - 最多绅士指名
        url = 'comics?page=' + page
        if c:
            url += '&c=' + urllib.parse.quote(c, safe='()')
        if t:
            url += '&t=' + urllib.parse.quote(t, safe='()')
        if a:
            url += '&a=' + urllib.parse.quote(a, safe='()')
        if f:
            url += '&f=' + urllib.parse.quote(f, safe='()')
        if s:
            url += '&s=' + urllib.parse.quote(s, safe='()')
        if ct:
            url += '&ct=' + urllib.parse.quote(ct, safe='()')
        if ca:
            url += '&ca=' + urllib.parse.quote(ca, safe='()')
        return self.get(url).json()

    def comicsInfo(self, id):
        #漫画信息
        return self.get('comics/{0}'.format(id)).json()

    def comicsComments(self, id, page = '1'):
        #漫画评论
        return self.get('comics/{0}/comments?page={1}'.format(id, page)).json()

    def commentsChildrens(self, id, page = '1'):
        #评论的回复（适用于漫画和游戏）
        return self.get('comments/{0}/childrens?page={1}'.format(id, page)).json()

    def comicsRecommendation(self, id):
        #相关推荐（看了这本子的人也在看）
        return self.get('comics/{0}/recommendation'.format(id)).json()

    def comicsEps(self, id, page = '1'):
        #漫画章节
        return self.get('comics/{0}/eps?page={1}'.format(id, page)).json()

    def comic(self, id, order, page = '1'):
        #漫画内容(包含图片地址)
        return self.get('comics/{0}/order/{1}/pages?page={2}'.format(id, order, page)).json()

    def comicsRandom(self):
        #随机漫画
        return self.get('comics/random').json()

    #排行榜
    def leaderboard(self, tt = 'H24', ct = 'VC'):
        #漫画排行
        #tt可取：H24 - 过去24小时，D7 - 过去7天，D30 -过去30天
        return self.get('comics/leaderboard?tt={0}&ct={1}'.format(tt, ct)).json()

    def knightLeaderboard(self):
        #骑士榜（用户上传数量排行）
        return self.get('comics/knight-leaderboard').json()
