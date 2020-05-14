#!/usr/bin/env python3

import os
import sys
import json
import threading

import requests
from tqdm import tqdm
from PicACG import pica

HELP = '''
exit, q 退出
help, h 帮助

token 获取当前Token
who 获取当前帐号信息
logout 退出登录
login [token] 通过Token登录
login [username] [password] 通过用户名和密码登录

init 获取图片服务器
init [url] 手动指定图片服务器

categories, c 获取分类信息
    q 返回
    [num] ([sort]) 列出漫画，列出后操作同下
info [id] 获取漫画信息
    q 返回
    [num] ([path]) 下载漫画，path默认为0
    l[a/ct] ([sort]) 列出与该漫画相同属性的漫画，sort默认为dd
    l[c/t] [categories/tags num] ([sort]) 列出与该漫画相同属性的漫画，sort默认为dd
favourite, f 获取收藏列表
    同下
list, l [a/c/t/ct] [name] ([dd/da/ld/vd]) 列出漫画
        a - 作者 c - 分类 t - 标签 ct 汉化组
        dd - 时间从新到旧 da - 时间从旧到新 ld - 喜爱排序 vd - 指名排序
    q 返回
    [num] 查看详情(等同于info)
    dp 下载该页的全部漫画，path智能选择(path默认为0，若此漫画只有一章，则会path=1)
    da 下载该列表中的全部漫画的所有章节，包含所有页，path智能选择(慎用)
    dpl 下载该页的全部漫画，path智能选择，但会将{title}解析为{listtitle}/{title}
    dal 下载该列表中的全部漫画的所有章节，包含所有页，path同上
    d [num] 下载指定漫画的全部章节，path智能选择
    d [num] [eps] ([path]) 下载指定漫画的指定章节，path默认为0
download, d [id] 下载漫画的所有章节
download, d [id] [eps] ([path]) 下载漫画的指定章节
'''

confFile = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'PicaPy.conf')
imageServer = ''

def command(comlist):
    if len(comlist) == 2:
        if comlist[1] == 'exit' or comlist[1] == 'q':
            sys.exit()
        elif comlist[1] == 'help' or comlist[1] == 'h':
            print(HELP)
        elif comlist[1] == 'token':
            print('当前 Token：\n' + p.token)
        elif comlist[1] == 'favourite' or comlist[1] == 'f':
            #getFavourite()
            getComicList(func = p.favourite, title = 'Favourite', name = 'Favourite')
        elif comlist[1] == 'who':
            who()
        elif comlist[1] == 'init':
            getImageServer()
        elif comlist[1] == 'logout':
            logout()
        elif comlist[1] == 'categories' or comlist[1] == 'c':
            getCategories()
        else:
            errorCommand()
    elif len(comlist) == 3:
        if comlist[1] == 'login':
            loginToken(comlist[2])
        elif comlist[1] == 'info':
            getEps(comlist[2])
        elif comlist[1] == 'init':
            imageServer = comlist[2]
            print('已将图片服务器设置为：' + comlist[2])
        elif comlist[1] == 'download' or comlist[1] == 'd':
            downloadComicAll(comlist[2])
        else:
            errorCommand()
    elif len(comlist) == 4:
        if comlist[1] == 'login':
            login(comlist[2], comlist[3])
        elif comlist[1] == 'download' or comlist[1] == 'd':
            downloadComic(comlist[2], comlist[3])
        if comlist[1] == 'list' or comlist[1] == 'l':
            getComicList(func = p.comicsList, args = {comlist[2]: comlist[3]}, name = comlist[3])
        else:
            errorCommand()
    elif len(comlist) == 5:
        if comlist[1] == 'download' or comlist[1] == 'd':
            downloadComic(comlist[2], comlist[3], comlist[4])
        if comlist[1] == 'list' or comlist[1] == 'l':
            getComicList(func = p.comicsList, args = {comlist[2]: comlist[3], 's': comlist[4]}, name = comlist[3])
        else:
            errorCommand()

def who():
    info = p.userInfo()
    if info['code'] == 200 and 'data' in info:
        print('欢迎您，{0}({1})！'.format(info['data']['user']['name'], info['data']['user']['email']))
        print('创建时间：' + info['data']['user']['created_at'])
    else:
        print('获取用户信息失败.')
        print(info)

def loginToken(token):
    p.token = token
    config['token'] = p.token
    with open(confFile, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4, ensure_ascii=False)
    print('正在尝试获取用户信息！')
    who()

def login(username, password):
    if p.singin(username, password) == 'success':
        config['token'] = p.token
        with open(confFile, 'w') as f:
            json.dump(config, f, sort_keys=True, indent=4, ensure_ascii=False)
        print('登录成功，正在获取用户信息！')
        who()
    else:
        print('登录失败，请检查您的用户名和密码是否正确.')

def logout(token):
    p.token = ''
    config['token'] = p.token
    with open(confFile, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)
    print('已经退出登录.')

def getComicInfo(id):
    info = p.comicsInfo(id)
    #print(info)
    if info['code'] == 200 and 'data' in info:
        if info['data']['comic']['finished']:
            finished = ' (完)'
        else:
            finished = ''
        print('[{0}] {1}{2}'.format('1', info['data']['comic']['title'], finished))
        print('描述：' + info['data']['comic']['description'])
        print('作者：{0} 章节：{1} 页数{2}'.format(info['data']['comic'].get('author', 'null'), info['data']['comic']['epsCount'], info['data']['comic']['pagesCount']))
        print('汉化组：' + info['data']['comic'].get('chineseTeam', 'null'))
        print('分类：' + ' '.join(info['data']['comic']['categories']))
        if info['data']['comic']['tags'] != []:
            print('标签：' + ' '.join(info['data']['comic']['tags']))
        print('喜爱：{0} 指名：{1} 浏览：{2}'.format(info['data']['comic']['likesCount'], info['data']['comic']['likesCount'], info['data']['comic']['totalViews']))
        print('创建时间：' + info['data']['comic']['created_at'])
        print('更新时间：' + info['data']['comic']['updated_at'])
        print('id：{0}\n'.format(info['data']['comic']['_id']))
    else:
        print('获取漫画信息失败.')
    return info

def getEps(id):
    comicInfo = getComicInfo(id)
    info = p.comicsEps(id)
    if info['code'] == 200 and 'data' in info:
        for eps in reversed(info['data']['eps']['docs']):
            print('[{0}] {1}'.format(eps['order'], eps['title']))
            print('更新时间：{0}\n'.format(eps['updated_at']))
        print('Page {0}/{1} Total {2}'.format(info['data']['eps']['page'], info['data']['eps']['pages'], info['data']['eps']['total']))
        print('输入 ↑/↓ 或 W/S 并回车换页，输入编号下载，输入 q 返回')
        while True:
            option = input('\033[0;32mComic > \033[0m')
            if option.isdecimal() and int(option) <= int(info['data']['eps']['total']) and int(option) >= 1:
                download(id, int(option), comicInfo['data']['comic']['title'])
                break
            elif option == '\x1b[A' or option.lower() == 'w':
                if info['data']['eps']['page'] == 1:
                    print('已经是第一页了.')
                else:
                    getFavourite(info['data']['eps']['page'] - 1)
                    break
            elif option == '\x1b[B' or option.lower() == 's':
                if info['data']['eps']['page'] == info['data']['eps']['pages']:
                    print('已经是最后一页了.')
                else:
                    getFavourite(info['data']['eps']['page'] + 1)
                    break
            elif option.split()[0].isdecimal() and int(option.split()[0]) <= int(info['data']['eps']['total']) and int(option.split()[0]) >= 1 and option.split()[1].isdecimal() and int(option.split()[1]) < len(config['path']) and int(option.split()[1]) >= 0:
                download(id, int(option.split()[0]), comicInfo['data']['comic']['title'], int(option.split()[1]))
                break
            elif option.lower() == 'la':
                getComicList(func = p.comicsList, args = {'a': comicInfo['data']['comic'].get('author', 'null')}, name = comicInfo['data']['comic'].get('author', 'null'))
                break
            elif option.lower() == 'lct':
                getComicList(func = p.comicsList, args = {'ct': comicInfo['data']['comic'].get('chineseTeam', 'null')}, name = comicInfo['data']['comic'].get('chineseTeam', 'null'))
                break
            elif option.split()[0].lower() == 'lc' and len(option.split()) == 2 and option.split()[1].isdecimal() and int(option.split()[1]) <= len(comicInfo['data']['comic']['categories']) and int(option.split()[1]) >= 1:
                getComicList(func = p.comicsList, args = {'c': comicInfo['data']['comic']['categories'][int(option.split()[1]) - 1]}, name = comicInfo['data']['comic']['categories'][int(option.split()[1]) - 1])
                break
            elif option.split()[0].lower() == 'lt' and len(option.split()) == 2 and option.split()[1].isdecimal() and int(option.split()[1]) <= len(comicInfo['data']['comic']['tags']) and int(option.split()[1]) >= 1:
                getComicList(func = p.comicsList, args = {'t': comicInfo['data']['comic']['tags'][int(option.split()[1]) - 1]}, name = comicInfo['data']['comic']['tags'][int(option.split()[1]) - 1])
                break
            elif option.split()[0].lower() == 'la' and len(option.split()) == 2 and option.split()[1] in ['dd', 'da', 'ld', 'vd']:
                getComicList(func = p.comicsList, args = {'a': comicInfo['data']['comic'].get('author', 'null'), 's': option.split()[1]}, name = comicInfo['data']['comic'].get('author', 'null'))
                break
            elif option.split()[0].lower() == 'lct' and len(option.split()) == 2 and option.split()[1] in ['dd', 'da', 'ld', 'vd']:
                getComicList(func = p.comicsList, args = {'ct': comicInfo['data']['comic'].get('chineseTeam', 'null'), 's': option.split()[1]}, name = comicInfo['data']['comic'].get('chineseTeam', 'null'))
                break
            elif option.split()[0].lower() == 'lc' and len(option.split()) == 3 and option.split()[1].isdecimal() and int(option.split()[1]) <= len(comicInfo['data']['comic']['categories']) and int(option.split()[1]) >= 1 and option.split()[2] in ['dd', 'da', 'ld', 'vd']:
                getComicList(func = p.comicsList, args = {'c': comicInfo['data']['comic']['categories'][int(option.split()[1]) - 1], 's': option.split()[2]}, name = comicInfo['data']['comic']['categories'][int(option.split()[1]) - 1])
                break
            elif option.split()[0].lower() == 'lt' and len(option.split()) == 3 and option.split()[1].isdecimal() and int(option.split()[1]) <= len(comicInfo['data']['comic']['tags']) and int(option.split()[1]) >= 1 and option.split()[2] in ['dd', 'da', 'ld', 'vd']:
                getComicList(func = p.comicsList, args = {'t': comicInfo['data']['comic']['tags'][int(option.split()[1]) - 1], 's': option.split()[2]}, name = comicInfo['data']['comic']['tags'][int(option.split()[1]) - 1])
                break
            elif option.lower() == 'q':
                break
            else:
                print('输入错误，请重新输入.')
    else:
        print('获取章节信息失败.')

def getCategories():
    info = p.categories()
    if info['code'] == 200 and 'data' in info:
        i = 0
        categoriesList = []
        for categories in info['data']['categories']:
            if 'active' not in categories:
                i += 1
                print('[{0}] {1}'.format(i, categories['title']))
                categoriesList.append(categories['title'])
        print('\n输入编号列出漫画，输入 q 返回')
        while True:
            option = input('\033[0;32mCategories > \033[0m')
            if option.isdecimal() and int(option) <= i and int(option) >= 1:
                getComicList(func = p.comicsList, args = {'c': categoriesList[int(option)-1]}, name = categoriesList[int(option)-1])
                break
            elif option.split()[0].isdecimal() and int(option.split()[0]) <= i and int(option.split()[0]) >= 1 and option.split()[1] in ['dd', 'da', 'ld', 'vd']:
                getComicList(func = p.comicsList, args = {'c': categoriesList[int(option.split()[0])-1], 's': option.split()[1]}, name = categoriesList[int(option.split()[0])-1])
                break
            elif option.lower() == 'q':
                break
            else:
                print('输入错误，请重新输入.')
    else:
        print('获取分类信息失败.')

def getComicList(func, args = {}, page = '1', title = 'Comics', name = 'Comics'):
    args['page'] = str(page)
    #print(func, args , page)
    info = func(**args)
    if info['code'] == 200 and 'data' in info:
        print('漫画列表：' + name + '\n')
        i = 0
        for comic in info['data']['comics']['docs']:
            i += 1
            if comic['finished']:
                finished = ' (完)'
            else:
                finished = ''
            print('[{0}] {1}{2}'.format(str(i), comic['title'], finished))
            print('作者：{0} 章节：{1} 页数{2}'.format(comic.get('author', 'null'), comic['epsCount'], comic['pagesCount']))
            print('分类：' + ' '.join(comic['categories']))
            print('喜爱：{0} 指名：{1} 浏览：{2}\n'.format(comic['likesCount'], comic['likesCount'], comic['totalViews']))
        print('Page {0}/{1} Total {2}'.format(info['data']['comics']['page'], info['data']['comics']['pages'], info['data']['comics']['total']))
        print('输入 ↑/↓ 或 W/S 并回车换页，输入编号查看详情，输入 d [编号] [章节] 下载，输入 q 返回')
        while True:
            option = input('\033[0;32m' + title + ' > \033[0m')
            if option.isdecimal() and int(option) <= i and int(option) >= 1:
                getEps(info['data']['comics']['docs'][int(option) - 1]['_id'])
                break
            elif option == '\x1b[A' or option.lower() == 'w':
                if info['data']['comics']['page'] == 1:
                    print('已经是第一页了.')
                else:
                    getComicList(func = func, args = args, page = info['data']['comics']['page'] - 1, title = title, name = name)
                    break
            elif option == '\x1b[B' or option.lower() == 's':
                if info['data']['comics']['page'] == info['data']['comics']['pages']:
                    print('已经是最后一页了.')
                else:
                    getComicList(func = func, args = args, page = info['data']['comics']['page'] + 1, title = title, name = name)
                    break
            elif option.lower() == 'dp':
                if input('您确定要该页全部漫画吗？[Y/n]').lower() == 'y':
                    for comic in info['data']['comics']['docs']:
                        print('\n\n标题：' + comic['title'])
                        if comic['epsCount'] == 1:
                            download(comic['_id'], '1', comic['title'], 1, yes=True)
                        else:
                            downloadComicAll(comic['_id'], comic['title'])
                    break
                else:
                    print('取消下载.')
            elif option.lower() == 'da':
                if input('您确定要列表(包含所有页)全部漫画吗？[Y/n]').lower() == 'y':
                    print('正在获取漫画列表...')
                    comicList = []
                    for page in range(int(info['data']['comics']['pages'])):
                        if page > 0:
                            args['page'] = str(page+1)
                            info = func(**args)
                        comicList += info['data']['comics']['docs']
                    #print(comicList)
                    for comic in comicList:
                        print('\n\n标题：' + comic['title'])
                        if comic['epsCount'] == 1:
                            download(comic['_id'], '1', comic['title'], 1, yes=True)
                        else:
                            downloadComicAll(comic['_id'], comic['title'])
                    break
                else:
                    print('取消下载.')
            elif option.lower() == 'dpl':
                if input('您确定要该页全部漫画吗？[Y/n]').lower() == 'y':
                    for comic in info['data']['comics']['docs']:
                        print('\n\n标题：' + comic['title'])
                        if comic['epsCount'] == 1:
                            download(comic['_id'], '1', comic['title'], 1, yes=True, pathAdd=name.replace('/', '_')+'/')
                        else:
                            downloadComicAll(comic['_id'], comic['title'])
                    break
                else:
                    print('取消下载.')
            elif option.lower() == 'dal':
                if input('您确定要列表(包含所有页)全部漫画吗？[Y/n]').lower() == 'y':
                    print('正在获取漫画列表...')
                    comicList = []
                    for page in range(int(info['data']['comics']['pages'])):
                        if page > 0:
                            args['page'] = str(page+1)
                            info = func(**args)
                        comicList += info['data']['comics']['docs']
                    #print(comicList)
                    for comic in comicList:
                        print('\n\n标题：' + comic['title'])
                        if comic['epsCount'] == 1:
                            download(comic['_id'], '1', comic['title'], 1, yes=True, pathAdd=name.replace('/', '_')+'/')
                        else:
                            downloadComicAll(comic['_id'], comic['title'])
                    break
                else:
                    print('取消下载.')
            elif option.split()[0].lower() == 'd' and len(option.split()) == 2:
                if info['data']['comics']['docs'][int(option.split()[1]) - 1]['epsCount'] == 1:
                    download(info['data']['comics']['docs'][int(option.split()[1]) - 1]['_id'], '1', info['data']['comics']['docs'][int(option.split()[1]) - 1]['title'], 1)
                else:
                    downloadComicAll(info['data']['comics']['docs'][int(option.split()[1]) - 1]['_id'], info['data']['comics']['docs'][int(option.split()[1]) - 1]['title'])
                break
            elif option.split()[0].lower() == 'd' and len(option.split()) == 3:
                download(info['data']['comics']['docs'][int(option.split()[1]) - 1]['_id'], option.split()[2], info['data']['comics']['docs'][int(option.split()[1]) - 1]['title'])
                break
            elif option.split()[0].lower() == 'd' and len(option.split()) == 4 and option.split()[3].isdecimal() and int(option.split()[3]) < len(config['path']) and int(option.split()[3]) >= 0:
                download(info['data']['comics']['docs'][int(option.split()[1]) - 1]['_id'], option.split()[2], info['data']['comics']['docs'][int(option.split()[1]) - 1]['title'], int(option.split()[3]))
                break
            elif option.lower() == 'q':
                break
            else:
                print('输入错误，请重新输入.')
    else:
        print('获取漫画列表失败.')

def downloadComic(id, eps, path = '0'):
    if path.isdecimal() and int(path) < len(config['path']) and int(path) >= 0:
        info = p.comicsInfo(id)
        if info['code'] == 200 and 'data' in info:
            epsInfo = p.comicsEps(id)
            if epsInfo['code'] == 200 and 'data' in epsInfo:
                if eps.isdecimal() and int(eps) <= epsInfo['data']['eps']['total'] and int(eps) >= 1:
                    download(id, eps, info['data']['comic']['title'], int(path))
                else:
                    print('您输入的章节不存在.')
            else:
                print('获取章节信息失败.')
        else:
            print('获取漫画信息失败，请检查id是否正确.')
    else:
        print('您输入的 path 参数无效.')

def downloadComicAll(id, title = '', pathAdd = ''):
    if title == '':
        title = getComicInfo(id)['data']['comic']['title']
    info = p.comicsEps(id)
    if info['code'] == 200 and 'data' in info:
        print('正在获取章节列表...')
        epsList = []
        for page in range(int(info['data']['eps']['pages'])):
            if page > 0:
                info = p.comicsEps(id, str(page+1))
            epsList += info['data']['eps']['docs']
        epsList.sort(key=lambda x: x['order'])
        #print(epsList)
        for eps in epsList:
            print('\n[{0}] {1}'.format(eps['order'], eps['title']))
            print('更新时间：{0}'.format(eps['updated_at']))
            download(id, str(eps['order']), title, yes=True, pathAdd=pathAdd)
    else:
        print('获取章节信息失败.')

def download(id, eps, title, path = 0, yes = False, pathAdd = ''):
    '''
    :param id: str 漫画ID
    :param eps: str 章节
    :param title: str 漫画标题
    :param path: int path list 的编号 可选0或1
    :param yes: bool 若为 True 则不进行确认
    :param pathAdd: str 在解析path时在{title}前添加的字符串
    '''
    info = p.comic(id, eps)
    if info['code'] == 200 and 'data' in info:
        if yes or input('您确定要下载 {0} 的章节{1} ：{2} 吗？[Y/n]'.format(title, eps, info['data']['ep']['title'])).lower() == 'y':
            print('正在获取下载列表...')
            downloadList = []
            for page in range(int(info['data']['pages']['pages'])):
                if page > 0:
                    info = p.comic(id, eps, str(page+1))
                for comicList in info['data']['pages']['docs']:
                    downloadList.append({'name': comicList['media']['originalName'], 'path': comicList['media']['path']})
            if len(downloadList) == info['data']['pages']['total']:
                print('开始下载...')
                #print(downloadList)
                if not os.path.isdir(os.path.dirname(config['path'][path].format(title = pathAdd + title.replace('/', '_'), eps = info['data']['ep']['title'].replace('/', '_'), name = '', number = ''))):
                    os.makedirs(os.path.dirname(config['path'][path].format(title = pathAdd + title.replace('/', '_'), eps = info['data']['ep']['title'].replace('/', '_'), name = '', number = '')))
                if config['multithreading']:
                    global downloadCreator
                    global con
                    global pbar
                    downloadCreator = downloadProducer(downloadList, title, info['data']['ep']['title'], path, pathAdd)
                    con = threading.Condition()
                    #此处使用 threading.Condition() 而非 threading.Lock() 是因为要阻塞主线程
                    #运行流程为：
                    #主线程调用generator，generator创建子线程，
                    #主线程在创建指定数目的子线程后使用with获取锁，进入循环，立即进入waiting池并释放锁，
                    #每个子线程执行完毕后获取锁（防止同时调用generator），并调用generator创建新的线程后释放，从而实现线程数不变，
                    #最后，当generator中的任务全部完成后，子线程再调用generator时会进入循环并使用notify()通知位于waiting池中的主进程，
                    #主进程收到通知停止阻塞并判断当前的线程数，从而确定目前是否所有子线程均已结束，如果不是，则继续等待，
                    #当最后一个子线程处理完毕后，调用generator通知主线程，主线程确认已经无任何子线程，结束循环，with释放锁，执行下面的语句
                    pbar = tqdm(total=len(downloadList))
                    for i in range(config['multithreading']):
                        next(downloadCreator)
                    with con:
                        while threading.active_count() > 2:
                            #此处 > 2 是因为tqdm会创建一个线程
                            con.wait()
                        pbar.close()
                else:
                    i = 0
                    for pic in tqdm(downloadList):
                        i += 1
                        r = requests.get(url=imageServer + pic['path'], headers={'accept-encoding': 'gzip', 'user-agent': 'okhttp/3.8.1'}, verify=False, proxies=p.proxies)
                        filename = config['path'][path].format(title = pathAdd + title.replace('/', '_'), eps = info['data']['ep']['title'].replace('/', '_'), name = pic['name'].replace('/', '_'), number = str(i))
                        with open(filename, 'wb') as fd:
                            for chunk in r.iter_content(1024):
                                fd.write(chunk)
            else:
                print('获取下载列表失败.')
        else:
            print('取消下载.')
    else:
        print('获取下载链接失败.')

def downloadProducer(downloadList, title, epsTitle, path, pathAdd):
    number = 0
    for pic in downloadList:
        number += 1
        t = threading.Thread(target=downloadThread, args=(pic, title, epsTitle, number, path, pathAdd))
        t.start()
        yield
    while True:
        con.notify()
        yield

def downloadThread(pic, title, epsTitle, number, path, pathAdd):
    r = requests.get(url=imageServer + pic['path'], headers={'accept-encoding': 'gzip', 'user-agent': 'okhttp/3.8.1'}, verify=False, proxies=p.proxies)
    filename = config['path'][path].format(title = pathAdd + title.replace('/', '_'), eps = epsTitle.replace('/', '_'), name = pic['name'].replace('/', '_'), number = str(number))
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(1024):
            fd.write(chunk)
    con.acquire()
    try:
        next(downloadCreator)
        pbar.update(1)
    finally:
        con.release()

def errorCommand():
    print('命令格式错误，输入 help 获取帮助.')

def getImageServer():
    global imageServer
    info = p.initapp()
    if info['code'] == 200 and 'data' in info:
        imageServer = info['data']['imageServer']
        print('获取图片服务器成功！\n当前图片服务器为：' + imageServer)
    else:
        print('获取图片服务器失败，请输入 init 重试，或输入 init + 地址 手动指定图片服务器.')

if __name__ == '__main__':
    if os.path.isfile(confFile):
        with open(confFile, 'r') as f:
            config = json.load(f)
    else:
        config = {'apiKey': '', 'apiSecret': '', 'channel': '1', 'path': ['/sdcard/Pica/{title}/{eps}/{name}', '/sdcard/Pica/{title}/{name}'], 'proxies': None, 'quality': 'original', 'token': '', multithreading: False}
        #path 可选格式
        #{title}：漫画标题
        #{eps}：章节标题
        #{name}：原文件名(推荐)
        #{number}：文件名(按顺序从1开始，不包含拓展名)
        #例：/sdcard/Pica/{title}/{eps}/{name}
        #   /sdcard/Pica/{title}/{eps}/{number}.png
        #   /sdcard/Pica/{title}-{eps}/{name}
        #注意：必须将{title}放在/后，因为在漫画列表中选择dal时，会将{title}解析为'列表名称/{title}'
        #channel 可选：1、2、3
        #quality 可选：original、low、medium、high
    p = pica(config['apiKey'], config['apiSecret'], config['token'], config['channel'], config['quality'], config['proxies'], False)
    getImageServer()
    if len(sys.argv) == 1:
        print('\n提示：输入 help 获取帮助.')
        while True:
            command(['PicaPy'] + input('\033[0;32mPicaPy > \033[0m').split(' '))
    else:
        command(sys.argv)