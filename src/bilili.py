import os
import sys
import threading

import requests
from urllib.parse import urlencode

import qrcode
from tkinter import Tk, Label
from PIL import ImageTk

import json
import pickle
import base64
from hashlib import md5
import winreg

from copy import deepcopy
from time import sleep, perf_counter, strftime, gmtime
from ctypes import windll
from tqdm import tqdm
from colorama import init

from io import StringIO
import dm_pb2 as dm


__all__ = ["print", "outputInit", "dictDisp",
           "dump", "load", "proxyServer", "loginQR", "retrieval",
           "multiDownload", "biliDownload", "staticDownload",
           "danmuDownload", "ccDownload", "ipLocate",
           "work_path", "base_path", "temp_path"]


work_path = os.getcwd()
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
temp_path = os.path.join(os.getenv('TEMP'), 'Bilili')
if not os.path.exists(temp_path):
    os.mkdir(temp_path)


appkey = [
    ('bca7e84c2d947ac6', '60698ba2f68e01ce44738920a0ffe768'),    # 登录
    ('iVGUTjsxvpLeuDCf', 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'),    # 取流
    ('1d8b6e7d45233436', '560c52ccd288fed045859ed18bffd973')     # 常规
    ]


# 重写保留字print，实现终端的彩色文本输出
_print = print
_print_flag = False
def print(*values, level=0, **kwargs):
    if _print_flag:
        sep = kwargs.get('sep', ' ')
        if level == 1: profix = '\033[1m'
        elif level == 2: profix = '\033[33m'
        elif level == 3: profix = '\033[31m'
        else: profix = ''
        _print(profix + sep.join(map(str, values)), **kwargs)
    else:
        _print(*values, **kwargs)


def outputInit():
    global _print_flag
    init(autoreset=True)
    _print_flag = True


def dictDisp(dic:dict):
    print(json.dumps(dic, indent=4, ensure_ascii=False, \
                     sort_keys=False, separators=(',',': ')))


def appsign(params:dict, appkey:str, appspec:str):
    params['appkey'] = appkey
    params = dict(sorted(params.items()))
    query = urlencode(params)
    sign = md5((query + appspec).encode()).hexdigest()
    params['sign'] = sign
    return  params


def dump(obj, path):
    tag = 'PY3bili'
    data = pickle.dumps(obj)
    b64 = base64.b64encode(data)
    with open(path, 'wb') as f:
        f.write(tag.encode() + b64)


def load(path):
    tag = 'PY3bili'
    with open(path, 'rb') as f:
        if f.read(7) == tag.encode():
            data = base64.b64decode(f.read())
            obj = pickle.loads(data)
        else:
            obj = None
    return obj


class proxyServer():
    
    def __init__(self):
        path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        self._regHandle = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, path)
        self._regQuery = lambda item_name: \
                          winreg.QueryValueEx(self._regHandle, item_name)[0]
        self.url = None
        self.update()

    def update(self):
        try:
            self.url = self._regQuery('ProxyServer')
        except FileNotFoundError:
            self.url = ''

    def __call__(self):
        try:
            enable = self._regQuery('ProxyEnable')
            if self.url and enable:
                return {"http": None, "https": 'http://%s' % self.url}
        except FileNotFoundError:
            pass
        return {"http": None, "https": None}

    def __del__(self):
        del self._regQuery
        winreg.CloseKey(self._regHandle)


Proxy = proxyServer()    # 检测系统代理


class _QRWin(threading.Thread):

    def __init__(self, qr_img):
        super(_QRWin, self).__init__(name='QRcode_window')
        self.qr_img = qr_img
        self._win = None
        self._text = None
        self._quit = False
        self.start()

    def run(self):
        win = Tk()
        win.iconbitmap(os.path.join(base_path, 'bilili.ico'))
        win.title("Login bilibili")
        win.geometry('360x400')
        win.resizable(False, False)
        win.attributes('-topmost', True)
        win.config(background='#FAFAFA')
        qr_image = ImageTk.PhotoImage(self.qr_img)
        img = Label(win, image=qr_image, bg='#FFFFFF', \
                    bd=5, height=260, width=260, relief='solid')
        text = Label(win, text="请用哔哩哔哩移动端扫码登录", \
                          font=('微软雅黑',12, ''), \
                          fg='red', bg='#FAFAFA', height=1)
        img.pack(pady=32, side='bottom')
        text.pack(side='bottom')
        self._win = win
        self._text = text
        win.protocol('WM_DELETE_WINDOW', lambda: self.exit())
        win.deiconify()
        self._exit_hook()
        win.mainloop()

    def _exit_hook(self):
        self._win.after(500, self._exit_hook)
        if self._quit:
            self._win.destroy()
            del self._text, self._win

    def exit(self):
        if self.is_alive():
            self._quit = True

    def text(self, string):
        self._text.config(text=string)


class loginQR():
    
    def __init__(self):
        self.header = {
            'Host': 'passport.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
            'Accept': 'application/json'
            }
        self.proxy = {"http": None, "https": None}
        self.qr_url = None
        self.oauth_key = None
        self.cookies = requests.cookies.RequestsCookieJar()
        self.success = False
    
    def get(self):
        try:
            r = requests.get(\
                'https://passport.bilibili.com/qrcode/getLoginUrl', \
                params=appsign({}, *appkey[0]), proxies = self.proxy, \
                timeout=3)
        except:
            print("网络错误 (-200)\n", level=2)
            return
        if not r.ok:
            print("网络错误 (%i)\n" % r.status_code, level=2)
            return
        js = r.json()
        if js['code']:
            print("请求失败 (%i)\n" % js['code'], level=2)
            return
        self.qr_url = js['data']['url']
        self.oauth_key = js['data']['oauthKey']
        self.cookies.update(r.cookies)
        q = qrcode.QRCode(version=8, error_correction=qrcode.ERROR_CORRECT_Q, \
                          box_size=5)
        q.add_data(self.qr_url)
        q.make(fit=False)
        self.qr_img = q.make_image()
    
    def show(self, request_interval=1):
        global win_thread
        if self.qr_url ==None or self.oauth_key==None:
            return
        win_thread = _QRWin(self.qr_img)

        params = appsign({'oauthKey':self.oauth_key}, *appkey[0])
        scanned = 0
        while True:
            sleep(request_interval)
            try:
                r = requests.post(\
                    'https://passport.bilibili.com/qrcode/getLoginInfo', \
                    headers=self.header, \
                    data=params, \
                    cookies=self.cookies, \
                    proxies = self.proxy, \
                    timeout=3)
            except:
                print("网络错误 (-200)\n", level=2)
                break
            if not r.ok:
                print("网络错误 (%i)\n" % r.status_code, level=2)
                break
            js = r.json()
            if not js['status']:
            #-1：密钥错误；-2：密钥超时；-4：未扫描；-5：未确认
                if js['data'] == -4:
                    pass
                elif js['data'] == -5:
                    scanned += 1
                elif js['data'] == -1:
                    print("密钥错误\n", level=2)
                    break
                elif js['data'] == -2:
                    print("密钥已超时，请重新登录\n")
                    break
                else:
                    print("未知错误 (%s)\n" % js['data'], level=2)
                    break
            else:
                if js['code']:
                    print("登录失败 (%s)\n" % js['code'], level=2)
                else:
                    self.cookies.update(r.cookies)
                    self.success = True
                    print("登录成功！")
                break
            if scanned == 1:
                win_thread.text("已扫码...请在手机上确认登录")
            if not win_thread.is_alive():
                return
        win_thread.exit()


class retrieval():

    def __init__(self, sessdata):
        # Mozilla/5.0 (平台) 引擎版本 浏览器版本号
        self.header = {
            'Host': 'api.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
            'Accept': 'application/json',
            'Referer': 'https://www.bilibili.com/'
            }
        self.sess = sessdata

    def _dictCopy(self, src_dic, *keys):
        dst_dic = {}
        for key in keys:
            if not isinstance(key, str):
                continue
            dst_dic[key] = src_dic.get(key, None)
        return dst_dic

    def _keyWord(self, string):
        new_str = string.replace('<em class=\"keyword\">', '\033[33m')
        new_str = new_str.replace('</em>', '\033[0m')
        return new_str
    
    def _idParse(self, vid, flag=0):
        if isinstance(vid, int):
            if flag:
                params = {'avid':vid}
            else:
                params = {'aid':vid}
        else:
            params = {'bvid':vid}
        return params

    def _request(self, url, params, sign=2, timeout=3):
        try:
            r = requests.get(\
                url, \
                headers=self.header, \
                params=appsign(params, *appkey[sign]), \
                cookies=self.sess, \
                proxies=Proxy(), \
                timeout=3)
        except:
            return -200
        if not r.ok:
            return r.status_code 
        js = r.json()
        if js['code']:
            return js['code']
        else:
            return js.get('data', js.get('result', {'unkown_tag': None}))

    def c_user(self):
        data = self._request(\
            'https://api.bilibili.com/x/vip/web/user/info', {})
        if isinstance(data, int): return data
        return self._dictCopy(data, 'mid', \
                              'vip_type', 'vip_status', 'vip_due_date')
    
    def v_detail(self, vid):
        # raw
        data = self._request(\
            'https://api.bilibili.com/x/web-interface/view', \
            self._idParse(vid))
        return data

    def v_list(self, vid):
        # raw, vid->cid
        data = self._request(\
            'https://api.bilibili.com/x/player/pagelist', \
            self._idParse(vid))
        return data
    
    def p_search(self, key_word, search_type=0):
        params = {}
        if search_type == 0:
            params['search_type'] = 'media_bangumi'
        elif search_type == 1:
            params['search_type'] = 'media_ft'
        else:
            return
        params['keyword'] = key_word
        data = self._request(\
            'https://api.bilibili.com/x/web-interface/search/type', \
            params)
        if isinstance(data, int): return data
        if data['numResults'] == 0: return []
        results = []
        key_cols = ['title', 'org_title', 'cv', 'staff']
        for result in data['result']:
            res = self._dictCopy(\
                result, 'media_type', 'media_id', 'season_id', \
                'title', 'org_title', 'cv', 'staff', 'cover', \
                'areas', 'styles', 'desc', 'pubtime', 'season_type_name', \
                'media_score', 'index_show', 'goto_url')
            if result['badges'] == None:
                res['badges'] = ''
            else:
                res['badges'] = result['badges'][0]['text']
            #key_cols = result['hit_columns']
            for col in key_cols:
                res[col] = self._keyWord(res[col])
            eps = []
            if result['hit_epids']:
                for ep in result['eps']:
                    eps.append(self._keyWord(ep['title']))
            res['eps'] = eps
            results.append(res)
        return results

    def p_review(self, mid):
        data = self._request(\
            'https://api.bilibili.com/pgc/review/user', \
            {'media_id':mid})
        if isinstance(data, int): return data
        info = self._dictCopy(data['media'], 'season_id', 'title', \
                              'cover', 'rating', 'areas', 'type_name')
        return info

    def p_detail(self, sid):
        data = self._request(\
            'https://api.bilibili.com/pgc/view/web/season', \
            {'season_id':sid})
        if isinstance(data, int): return data
        info = self._dictCopy(\
            data, 'media_id', 'season_id', 'title', 'total', 'cover', \
            'evaluate', 'status', 'rating', 'stat', 'subtitle', 'series', \
            'areas', 'publish', 'record')
        info['copyright'] = data['rights']['copyright']
        seasons = []
        for season in data['seasons']:
            seasons.append(self._dictCopy(season, 'media_id', 'season_id', \
                                          'season_title', 'badge'))
        info['seasons'] = seasons
        return info
    
    def p_list(self, sid):
        data = self._request(\
            'https://api.bilibili.com/pgc/web/season/section', \
            {'season_id':sid})
        if isinstance(data, int): return data
        sections = []
        sections.append(data['main_section'])
        sections.extend(data['section'])
        eps = []; i = 1
        for section in sections:
            for ep in section['episodes']:
                _ep = self._dictCopy(ep, 'aid', 'cid', \
                                     'badge', 'status', 'cover')
                if ep['long_title']:
                    _ep['title'] = '%s %s' % (ep['title'], ep['long_title'])
                else:
                    _ep['title'] = ep['title']
                _ep['index'] = ep['title']
                _ep['epid'] = ep['id']
                eps.append(_ep)
                i += 1
        return eps

    def geturl(self, vid, cid, **kwargs):
        params = self._idParse(vid, flag=1)
        params['cid'] = cid
        params['qn'] = kwargs.get('qn', 0)
        params['fnval'] = kwargs.get('fnval', 16)
        params['fourk'] = kwargs.get('fourk', 0)
        data = self._request(\
            'https://api.bilibili.com/x/player/playurl', \
            params, sign=1)
        return data


class _tqdmLike():

    def __init__(self, total, initial):
        self.total = total
        self.init = initial
        self.n = initial
 
    def update(self, value):
        value += self.n
        self.n = min(max(0, value), self.total)

    def reset(self):
        self.n = self.init
    
    def refresh(self):
        pass

    def close(self):
        self.total = 0
        self.init = 0
        self.update(0)


class multiDownload():

    def __init__(self, url, dst, threading_num=-1, process_bar=False,
                 **request_kwargs):
        self.lock = threading.Lock()
        self.pool = []
        self.num = threading_num
        self._started = False
        self._abort = False
        self._exited = False
        self._stop = True
        self._connectNum = 0
        self.success = False
        self.error_info = ''
        if isinstance(url, list):
            self.url = url
        else:
            self.url = [url]
        self.kwargs = request_kwargs
        self.chunk_size = 524288    # 512KB

        self.path = dst
        target_dir = os.path.dirname(dst)
        filename = os.path.basename(dst)
        os.makedirs(target_dir, exist_ok=True)
        self.temp_dir = os.path.join(target_dir, 'download_temp')
        self.index_file = os.path.join(self.temp_dir, \
                                       md5(filename.encode()).hexdigest())
        if not os.path.exists(self.temp_dir): os.mkdir(self.temp_dir)
        windll.kernel32.SetFileAttributesW(self.temp_dir, 0x2)
        self.temp_file = []
        
        header = self.kwargs.get('headers', {})
        header['Range'] = 'bytes=0-'
        self.kwargs['headers'] = header
        try:
            error_code = -200
            r = requests.get(self.url[0], **self.kwargs, timeout=3, stream=True)
            error_code = r.status_code
            r.raise_for_status()
        except Exception as e:
            self.error_info = repr(e)
            print("Fail to request (%s)\n" % error_code)
            self._exited = True
            return
        if r.status_code == 206:
            self.is_partial = True
        else:
            self.is_partial = False
        self.file_size = int(r.headers['content-length'])
        
        if process_bar:
            self.process = tqdm(total=self.file_size, initial=0, \
                                unit='B', unit_scale=True, leave=False, \
                                desc=filename)
        else:
            self.process = _tqdmLike(self.file_size, 0)
        
        self.unfinished = False
        if self.is_partial:
            # 检查文件名和文件大小区分指针文件
            if os.path.exists(self.index_file):
                with open(self.index_file, 'rb') as f:
                    record = pickle.loads(f.read())
                    if record[1] == self.file_size:
                        self.unfinished = True
            if self.unfinished:
                self.block = record
                self.num = len(self.block) - 2
            else:
                self.block = [0, self.file_size]
                if self.num <= 0:
                    self.num = int((self.file_size/33554432)**0.4) + 1
                block_size = self.file_size / self.num
                i = 1
                while i <= self.num:
                    self.block.append(self.file_size - round(i*block_size))
                    i += 1
        else:
            self.block = [0, self.file_size, 0]
            self.num = 1

        print(f"\rConnected to '%s' || Download as '%s' [size: %.1fMB / thread: %i / resumable: %s]" % (\
              requests.utils.urlparse(self.url[0])[1], \
              self.path, \
              self.file_size / 1048576, \
              self.num, \
              self.is_partial))

    def _downThread(self, url_i, block_i, retry=2):
        
        def download(url, kwargs, file):
            with requests.get(url, **kwargs, timeout=3, stream=True) as r:
                r.raise_for_status()
                if self._stop:
                    with self.lock:
                        print(f"  Download thread of block-{block_i} starts... ({r.headers['content-range']})")
                # 以下3行用于确保所有线程连接完毕后再开始下载
                self._connectNum += 1
                while self._stop:
                    sleep(0.5)
                for chunk in r.iter_content(self.chunk_size):
                    if chunk:
                        length = file.write(chunk)
                        file.flush()
                        with self.lock:
                            self.process.update(length)
                    if self._abort:
                        break
        
        kwargs = deepcopy(self.kwargs)
        temp_file = os.path.join(self.temp_dir, hex(self.block[-block_i] + 16))
        with self.lock:
            self.temp_file.append(temp_file)
        i = 0
        if self.is_partial:
            file = open(temp_file, 'ab')
            if self.unfinished and os.path.exists(temp_file):
                resume_size = os.path.getsize(temp_file)
            else:
                resume_size = 0
            start = self.block[-block_i] + resume_size
            end = self.block[- (block_i + 1)] - 1
            self.process.n += resume_size
            if start > end:
                self._connectNum += 1
            else:
                while i <= retry:
                    kwargs['headers']['Range'] = f'bytes={start}-{end}'
                    try:
                        download(self.url[url_i], kwargs, file)
                    except Exception as e:
                        self.error_info = repr(e)
                    start = self.block[-block_i] + os.path.getsize(temp_file)
                    if start > end or self._abort:
                        break
                    sleep(1)
                    i += 1
                if self._stop and i > retry:
                    self._connectNum += 1
        else:
            file = open(temp_file, 'wb')
            kwargs['headers']['Range'] = f'bytes=0-'
            while i <= retry:
                file.seek(0)
                with self.lock:
                    self.process.reset()
                try:
                    download(self.url[url_i], kwargs, file)
                except Exception as e:
                    self.error_info = repr(e)
                if os.path.getsize(temp_file) >= self.file_size or self._abort:
                    break
                sleep(1)
                i += 1
        file.close()

    def start(self):
        
        def check(func):
            while True:
                count = 0
                for p in self.pool:
                    if p.is_alive():
                        count += 1
                if count == 0:
                    break
                else:
                    sleep(1)
            if not self._abort:
                func()

        if self._started or self._exited: return
        self._started = True
        i = 1; j = 0
        while i <= self.num:
            thread = threading.Thread(target=self._downThread, \
                                      name='downThread-%s' % i, \
                                      args=(j, i, 3))
            self.pool.append(thread)
            i += 1; j += 1
            if j >= len(self.url): j = 0
        for thread in self.pool:
            thread.start()
        if self.pool:
            self._monitor = threading.Thread(target=check, args=(self.exit, ))
            self._monitor.start()
            while self._connectNum < self.num:
                if self._exited:
                    return
                sleep(0.5)
            self.process.refresh()
            self._stop = False
        else:
            self.exit()

    def join(self):
        if not self._started or self._abort: return
        self._monitor.join()

    def stop(self):
        if not self.is_partial: return
        self._abort = True

    def resume(self):
        if self._exited or not self._abort: return
        self._abort = False
        self._started = False
        self.process.n = 0
        self.pool.clear()
        self.temp_file.clear()
        self.start()
    
    def exit(self):
        if not self._started: return
        self._abort = True
        self._exited = True
        for p in self.pool:
            p.join()
        self.block[0] = self.process.n
        self.process.close()
        if self.block[0] >= self.block[1]:
            copy_unit_size = 32 * 1048576    # 32MB
            with open(self.path, 'wb') as fw:
                for f in self.temp_file:
                    with open(f, 'rb') as fr:
                        while True:
                            copy_unit = fr.read(copy_unit_size)
                            if not copy_unit: break
                            fw.write(copy_unit)
                    os.remove(f)
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            if not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
            print("Download completed!\n")
            self.success = True
        else:
            if self.is_partial:
                with open(self.index_file, 'wb') as f:
                    f.write(pickle.dumps(self.block))
            print("Exit!\n")
            self.success = False


def biliDownload(url_dic, path, sessdata, process_bar=True):
    header = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
        }
    url_list= [url_dic['base_url']] + url_dic['backup_url']
    i = 0; end_i = len(url_list) - 1
    while True:
        d = multiDownload(url_list[i], path, process_bar=process_bar, \
                          headers=header, params=appsign({}, *appkey[1]), \
                          proxies=Proxy(), cookies=sessdata)
        d.start()
        d.join()
        if d.success or i == end_i: break
        print("Changing download link ...")
        i += 1
    return d.success


def staticDownload(url, path=None, params={}):
    header = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
        }
    r = requests.get(\
        url, \
        headers=header, \
        params=params, \
        proxies=Proxy(), \
        timeout=3)
    r.raise_for_status()
    if path:
        with open(path, 'wb') as f:
            f.write(r.content)
        return
    else:
        return r.content


def _xmlEscape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
           .replace('"', '&quot;').replace("'", '&apos;')


def danmuDownload(cid, path, level=3, flag=0b000, cookies=None, retry=3):
    header = {
        'Host': 'api.bilibili.com',
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
    }
    params = {'type': 1, 'oid': cid, 'segment_index': 1}
    url = 'https://api.bilibili.com/x/v2/dm/web/seg.so'
    proxy = Proxy()
    if flag == 0:
        if level < 0 or level > 10:
            print("Invalid level value (0-10)")
            return
        filt = lambda d: True if d.weight>level else False
    else:
        # bit0:保护 bit1:直播 bit2:高赞
        if flag < 0:
            print("Invalid flag value (>=0)")
            return
        filt = lambda d: True if d.attr&flag>0 else False
    proto = dm.DmSegMobileReply()
    buf = StringIO()
    count_all = 0; count = 0
    while True:
        try:
            r = requests.get(\
                url, \
                params=params, \
                headers=header, \
                cookies=cookies, \
                proxies=proxy, \
                timeout=3)
            r.raise_for_status()
        except:
            if retry:
                retry -= 1
                continue
            else:
                return ()
        proto.ParseFromString(r.content)
        seg_n = len(proto.elems)
        if seg_n > 0:
            params['segment_index'] += 1
            count_all += seg_n
        else:
            break
        i =  0
        while i < seg_n:
            d = proto.elems[i]
            if filt(d):
                p = ','.join(\
                    map(str, (d.progress/1000, d.mode, d.fontsize, d.color, \
                              d.ctime, d.pool, d.midHash, d.idStr, d.weight)))
                c = _xmlEscape(d.content.encode().decode())
                buf.write(f'<d p="{p}">{c}</d>') 
                #buf.write(f'<d p="{d.progress/1000},{d.mode},{d.fontsize},{d.color},{d.ctime},{d.pool},{d.midHash},{d.idStr},{d.weight}">{d.content.encode().decode()}</d>')
                count += 1
            i += 1
    with open(path, 'w', encoding='utf-8') as fw:
        if flag != 0:
            fw.write(f'''<?xml version="1.0" encoding="UTF-8"?><i>\
<chatserver>chat.bilibili.com</chatserver><chatid>{cid}</chatid>\
<count>{count}</count><segment>{params['segment_index']-1}</segment>\
<level>0</level><flag>{flag}</flag><state>0</state>''')
        else:
            fw.write(f'''<?xml version="1.0" encoding="UTF-8"?><i>\
<chatserver>chat.bilibili.com</chatserver><chatid>{cid}</chatid>\
<count>{count}</count><segment>{params['segment_index']-1}</segment>\
<level>{level}</level><flag>{flag}</flag><state>0</state>''')
        fw.write(buf.getvalue())
        fw.write('</i>')
    buf.close()
    return count, count_all


def _ccList2srt(cclist, **font_args):
    
    def timeTrans(time):
        cut = str(time).partition('.')
        intTime = strftime('%H:%M:%S', gmtime(time))
        digits = len(cut[2])
        if digits == 0: decTime = '000'
        elif digits == 1: decTime = cut[2] + '00'
        elif digits == 2: decTime = cut[2] + '0'
        else: decTime = cut[2]
        return f'{intTime}.{decTime}'
    
    fn = font_args.get('fn')
    fs = font_args.get('fs', 14)
    fc = font_args.get('fc')
    if fn != None:
        head = r'{\fn%s\fs%s}' % (fn, fs)
    else:
        head = r'{\fs%s}' % fs
    if fc != None:
        head = '<font color=%s>' % fc + head
    buf = StringIO()
    for i, line in enumerate(cclist):
        tag = f"{i+1}\n{timeTrans(line['from'])} --> {timeTrans(line['to'])}\n"
        _line = tag + head + line['content'] + '\n\n'
        buf.write(_line)
    return buf


def ccDownload(aid, cid, path, cookies=None):
    header = {
        'Host': 'api.bilibili.com',
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
    }
    params = {'aid': aid, 'cid': cid}
    url = 'https://api.bilibili.com/x/web-interface/view'
    try:
        r = requests.get(url, \
                         params=params, \
                         headers = header, \
                         cookies=cookies, \
                         proxies=Proxy(), \
                         timeout=3)
    except:
        return -200
    if not r.ok:
        return r.status_code
    js = r.json()
    if js['code']:
        return js['code']
    subtitles = js['data']['subtitle']['list']
    if len(subtitles) == 0:
        return 0
    for item in subtitles:
        subtitle_data = json.loads(staticDownload(item['subtitle_url']))
        srt_data = _ccList2srt(subtitle_data['body'])
        _path = os.path.join(path, '%s.srt' % item['lan'])
        with open(_path, 'w', encoding='utf-8') as f:
            f.write(srt_data.getvalue())
    return 0


def ipLocate():
    print("---ip地理位置查询......", end='')
    try:
        error_code = -200
        r = requests.get('https://api.bilibili.com/x/web-interface/zone', \
                         proxies=Proxy(), \
                         timeout=3)
        error_code = r.status_code
        r.raise_for_status()
    except Exception as e:
        print(f"失败\n    {error_code}): {repr(e)}\n")
    else:
        js = r.json()
        if js['code']:
            print(f"失败\n{js['code']}):    {js['message']}\n")
        else:
            print("成功")
            dictDisp(js['data'])


if __name__ == '__main__':
    #os.chdir(r'E:\我的文档\Bilibili\PGC下载')
    #path = r'.\0.mp4'
    #l = loginQR()
    #l.get()
    #l.show()
    
    cookies = load(r'.\dist\data_bak\cookies_lgq')
    r = retrieval(cookies)
    #dictDisp(r.p_search("夏目友人帐")[0])
    #dictDisp(r.p_search("地球脉动", search_type=1)[0])
    #dictDisp(r.p_search("过于慎重")[0])
    #dictDisp(r.p_search("妹妹")[0])
    #dictDisp(r.p_detail(28625))
    #dictDisp(r.p_list(28625))
    #dictDisp(r.p_review(28222736))
    #dictDisp(r.geturl(76392635, 130671984))
    #dictDisp(r.geturl(379104230, 107309283))    # 老视频不支持编码12
    
    #dictDisp(r.p_detail(28595))
    #dictDisp(r.p_review(28222693))
    #dictDisp(r.p_list(28595))
    #dictDisp(r.geturl(74758770, 127992675))
    
    #header = {
    #    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    #    'Referer': 'https://www.bilibili.com/'
    #    }
    #d = multiDownload(url, path, process_bar=True, headers=header, params=appsign({}, *appkey[1]), cookies=cookies)
    #d.start()
    #d.stop()
    #d.resume()
    #d.exit()

    #danmuDownload(29611963, 'danmu.xml')
    #danmuDownload(29611963, 'danmu.xml', level=6)
    #danmuDownload(29611963, 'danmu.xml', flag=0b101)

    #r = retrieval(None)
    #dictDisp(r.p_detail(41472))
    #dictDisp(r.p_list(41472))
    #ccDownload(937955841, 567929070, r'.\')

    #ipLocate()
    pass

