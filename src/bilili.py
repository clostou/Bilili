import os
import sys
import threading

from urllib.parse import urlencode
import requests
from copy import deepcopy

import qrcode
from tkinter import Tk, Label
from PIL import ImageTk

import json
import pickle
import base64
from hashlib import md5

from time import sleep, perf_counter
from ctypes import windll
from tqdm import tqdm
#from colorama import init; init(autoreset=True)


__all__ = ["dictDisp", "dump", "load", "loginQR", "retrieval",
           "multiDownload", "biliDownload", "staticDownload",
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


class _QRWin(threading.Thread):

    def __init__(self, qr_img):
        super(_QRWin, self).__init__(name='QRcode_window')
        self.qr_img = qr_img
        self._win = None
        self._text = None
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
        win.protocol('WM_DELETE_WINDOW', lambda: sys.exit(0))
        win.deiconify()
        win.mainloop()

    def exit(self):
        if self.is_alive():
            self._win.destroy()

    def text(self, string):
        self._text.config(text=string)


class loginQR():
    
    def __init__(self):
        self.header = {
            'Host': 'passport.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
            'Accept': 'application/json'
            }
        self.qr_url = None
        self.oauth_key = None
        self.cookies = requests.cookies.RequestsCookieJar()
        self.success = False
    
    def get(self):
        try:
            r = requests.get(\
                'https://passport.bilibili.com/qrcode/getLoginUrl', \
                params=appsign({}, *appkey[0]), \
                timeout=3)
        except:
            print("网络错误 (-200)\n")
            return
        if not r.ok:
            print("网络错误 (%i)\n" % r.status_code)
            return
        js = r.json()
        if js['code']:
            print("请求失败 (%i)\n" % js['code'])
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
                    timeout=3)
            except:
                print("网络错误 (-200)\n")
                break
            if not r.ok:
                print("网络错误 (%i)\n" % r.status_code)
                break
            js = r.json()
            if not js['status']:
            #-1：密钥错误；-2：密钥超时；-4：未扫描；-5：未确认
                if js['data'] == -4:
                    pass
                elif js['data'] == -5:
                    scanned += 1
                elif js['data'] == -1:
                    print("密钥错误\n")
                    break
                elif js['data'] == -2:
                    print("密钥已超时，请重新登录\n")
                    break
                else:
                    print("未知错误 (%s)\n" % js['data'])
                    break
            else:
                if js['code']:
                    print("登录失败 (%s)\n" % js['code'])
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
        self.pos = initial
 
    def update(self, value):
        value += self.pos
        self.pos = min(max(0, value), self.total)

    def close(self):
        self.total = 0
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
        self._wait = 0
        if isinstance(url, list):
            self.url = url
        else:
            self.url = [url]
        self.kwargs = request_kwargs
        self.chunk_size = 1048576

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
        r = requests.get(self.url[0], **self.kwargs, timeout=3, stream=True)
        #r.raise_for_status()
        if not r.ok:
            print("Fail to request (%s)" % r.status_code)
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
                self.process.update(self.block[0])
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

    def _download(self, url_i, block_i, start, end):
        kwargs = deepcopy(self.kwargs)
        kwargs['headers']['Range'] = f'bytes={start}-{end}'
        f = self.temp_file[block_i - 1]
        with requests.get(self.url[url_i], **kwargs, timeout=15, stream=True) as r:
            with self.lock:
                try:
                    r.raise_for_status()
                except Exception as e:
                    print(repr(e))
                    return
                print(f"  Download thread of block-{block_i} start... ({r.headers['content-range']})")
            # 以下3行用于确保所有线程请求完毕后再开始下载
            self._wait += 1
            while self._stop:
                sleep(0.5)
            for chunk in r.iter_content(self.chunk_size):
                if chunk:
                    length = f.write(chunk)
                    f.flush()
                    with self.lock:
                        self.process.update(length)
                if self._abort:
                    break

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
            func()
        if self._started or self._exited: return
        self._started = True
        i = 1; j = 0
        while i <= self.num:
            temp_file = os.path.join(self.temp_dir, hex(self.block[-i] + 16))
            if os.path.exists(temp_file) and self.unfinished:
                resume_size = os.path.getsize(temp_file)
                start = self.block[-i] + resume_size
                self.temp_file.append(open(temp_file, 'ab+'))
            else:
                resume_size = 0
                start = self.block[-i]
                self.temp_file.append(open(temp_file, 'wb+'))
            end = self.block[- (i + 1)] - 1
            if start >= end + 1:
                i += 1; continue
            
            thread = threading.Thread(target=self._download, \
                                      name=f'thread-%s' % i, \
                                      args=(j, i, start, end))
            self.pool.append(thread)
            i += 1; j += 1
            if j >= len(self.url): j = 0
        for thread in self.pool:
            thread.start()
        if self.pool:
            self._monitor = threading.Thread(target=check, args=(self.exit, ))
            self._monitor.start()
            while self._wait < self.num:
                sleep(0.5)
            self.process.update(resume_size)
            self._stop = False
        else:
            self.exit()

    def join(self):
        self._monitor.join()

    def stop(self):
        self._abort = True

    def resume(self):
        if self._exited or not self._abort: return
        self._abort = False
        self._started = False
        self.unfinished = True
        self.pool = []
        self._close()
        self.temp_file = []
        self.start()

    def _close(self):
        for f in self.temp_file:
            f.close()
    
    def exit(self):
        if not self._started: return
        self._abort = True
        self._exited = True
        for p in self.pool:
            p.join()
        self.block[0] = self.process.pos
        self.process.close()
        total_size = 0
        for f in self.temp_file:
            total_size += f.tell()
        if self.block[0] >= self.block[1] or total_size >= self.block[1]:
            copy_unit_size = 32 * 1048576
            with open(self.path, 'wb') as fw:
                for fr in self.temp_file:
                    fr.seek(0)
                    while True:
                        copy_unit = fr.read(copy_unit_size)
                        if not copy_unit: break
                        fw.write(copy_unit)
            self._close()
            i = 1
            while i <= self.num:
                os.remove(os.path.join(self.temp_dir, hex(self.block[-i] + 16)))
                i += 1
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            if not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
            print("Download completed!\n")
        else:
            if self.is_partial:
                with open(self.index_file, 'wb') as f:
                    f.write(pickle.dumps(self.block))
            self._close()
            print("Exit!\n")

def biliDownload(url, path, sessdata, process_bar=True):
    header = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
        }
    d = multiDownload(url, path, process_bar=process_bar, \
                      headers=header, params=appsign({}, *appkey[1]), cookies=sessdata)
    d.start()
    d.join()


def staticDownload(url, path):
    header = {
        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
        'Referer': 'https://www.bilibili.com/'
        }
    r = requests.get(\
        url, \
        headers=header, \
        timeout=3)
    r.raise_for_status()
    with open(path, 'wb') as f:
        f.write(r.content)


if __name__ == '__main__':
    #os.chdir(r'E:\我的文档\Python\python\bilibili')
    #path = r'.\0.mp4'
    #l = loginQR()
    #l.get()
    #l.show()
    
    #cookies = load('cookies_lgq')
    #r = retrieval(None)
    #dictDisp(r.p_search("夏目友人帐")[0])
    #dictDisp(r.p_search("地球脉动", search_type=1)[0])
    #dictDisp(r.p_search("过于慎重")[0])
    #dictDisp(r.p_search("妹妹")[0])
    #dictDisp(r.p_detail(28625))
    #dictDisp(r.p_list(28625))
    #dictDisp(r.p_review(28222736))
    #dictDisp(r.geturl(76392635, 130671984))
    #dictDisp(r.geturl(379104230, 107309283))    # 老视频不支持编码12
    
    #header = {
    #    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    #    'Referer': 'https://www.bilibili.com/'
    #    }
    #d = multiDownload(url, path, process_bar=True, headers=header, params=appsign({}, *appkey[1]), cookies=cookies)
    #d.start()
    #d.stop()
    #d.resume()
    #d.exit()
    pass

