import os
import json
from bilili import *
from colorama import init
from datetime import datetime, timedelta


name = 'Bilili'
version = '1.0'


def cutByLen(string, size, sep='\n'):
    cuts = []
    while size < len(string):
        cuts.append(string[: size])
        string = string[size: ]
    cuts.append(string)
    return sep.join(cuts)


def indexInput(raw_str, max_value):
    raw = raw_str.split(',')
    index = []
    for item in raw:
        try:
            item_cut = item.split('-')
            cut_num = len(item_cut)
            if cut_num == 1:
                start = int(item) - 1
                if start < 0 or start >= max_value:
                    raise ValueError
                index.append(start)
            elif cut_num == 2:
                if item_cut[0]:
                    start = int(item_cut[0]) - 1
                    if start < 0:
                        raise ValueError
                else:
                    start = 0
                if item_cut[1]:
                    end = int(item_cut[1])
                    if end > max_value:
                        raise ValueError
                else:
                    end = max_value
                index.extend(list(range(start, end)))
            else:
                raise ValueError
        except:
            index = []
            print("输入的数值有误，请检查后重试")
    return index


def changeUser(user_name, cookies):
    global tag, f, r
    if f != None:
        f.save()
    tag = name + '(%s)' % user_name
    r = retrieval(cookies)
    f = favorite(user_name)


def failCheck(retrieval_ret):
    if isinstance(retrieval_ret, int):
        if retrieval_ret > 0: 
            print("网络错误 (%i)\n" % retrieval_ret)
        else: 
            print("服务器拒绝请求 (%i)\n" % retrieval_ret)
        return True
    else:
        return False


def login(user_name, new=False):
    cookies_path = os.path.join(temp_path, 'cookies_' + user_name)
    if new:
        l = loginQR()
        l.get()
        l.show()
        if l.success:
            dump(l.cookies, cookies_path)
            changeUser(user_name, l.cookies)
        else:
            pass
    else:
        if os.path.exists(cookies_path):
            changeUser(user_name, load(cookies_path))
        else:
            print("用户 %s 不存在" % user_name)


class select():
    
    def __init__(self):
        self.list = []
        self.status = -1

    def get(self, select_id, required_status=0):
        target = None
        length = len(self.list)
        if required_status != self.status and required_status != 0:
            print("无可索引对象，已取消对'%s'的引用" % select_id)
        elif select_id < 1 or select_id > length:
            if length == 0:
                print("索引值不合法（取值范围：空）" )
            elif length == 1:
                print("索引值不合法（取值范围：1）" )
            else:
                print("索引值不合法（取值范围：1 - %i）" % length)
        else:
            target = self.list[select_id - 1]
        return target

    def set(self, new_list, status):
        self.list = new_list
        self.status = status


def search(key_word, search_type=0):
    def form(string, src_sep, dst_sep, cut_len, cut_sep):
        cuts = string.split(src_sep)
        for i in range(len(cuts)):
            cuts[i] = cutByLen(cuts[i], cut_len, cut_sep)
        return dst_sep.join(cuts)
    
    if search_type == 0:
        cata = "番剧"
    elif search_type == 1:
        cata = "影视"
    else:
        print("未知查询范围：%i，请检查后重试\n" % search_type)
        return
    print("正在B站%s分区搜索关键词：\"%s\"......" % (cata, key_word), end=' ')
    results = r.p_search(key_word, search_type)
    if failCheck(results): return
    if results:
        print("总计%i个条目：\n" % len(results))
    else:
        print("无相关结果\n")
        return
    ret = []; tab = " "*12
    for i, res in enumerate(results, 1):
        detail = r.p_detail(res['season_id'])
        
        ret.append(r._dictCopy(detail, 'media_id', 'season_id', 'title',
                               'total', 'cover'))
        if res['org_title']:
            org = "（%s）" % res['org_title']
        else:
            org = ""
        print("\033[44m%i\033[0m······%s%s" % (i, res['title'], org))
        for ep in res['eps']:
            print(tab + " ·" + ep)
        print(tab + "|" + "-"*94)
        if res['badges']:
            print(tab + "|" + " "*(90-2*len(res['badges'])) + \
                  "[%s]" % res['badges'])
        else:
            print(tab + "|")
        if detail['publish']['is_finish']:
            label = "已完结"
        elif detail['publish']['is_started']:
            label = "连载中"
        else:
            label = "未开播"
        print(tab + "|    " +res['season_type_name'] + " " + label + \
              " " + res['index_show'])
        if res['media_score']['user_count'] > 0:
            score = "评分 \033[31m%s\033[0m" % res['media_score']['score']
        else:
            score = "暂无评分"
        print(tab + "|" + " "*74 + score)
        print(tab + "|")
        print(tab + "|")
        time = datetime(1970, 1, 1) + timedelta(hours=8, seconds=res['pubtime'])
        print(tab + "|    " + time.strftime("%Y年%m月%d日开播  ") + \
              res['styles'])
        print(tab + "|    " + detail['subtitle'])
        print(tab + "|")
        print(tab + "|" + "-"*94)
        print(tab + "|")
        print(tab + "|  md号（media id）：%i" % res['media_id'])
        print(tab + "|  ss号（season id）：%i" % res['season_id'])
        print(tab + "|  封面链接：" + res['cover'])
        print(tab + "|  播放页跳转链接：" + res['goto_url'])
        print(tab + "|")
        print(tab + "|")
        seq = "\n" + tab + "|    "
        if res['cv']:
            print(tab + "|  CAST：")
            cast = res['cv'].replace("\n", seq)
            cast = cast.replace("、", seq)
            print(tab + "|    " + cast)
            print(tab + "|")
        if res['staff']:
            print(tab + "|  Staff：")
            print(tab + "|    " + res['staff'].replace("\n", seq))
            print(tab + "|")
        print(tab + "|  简介：")
        print(tab + "|      ", \
              form(detail['evaluate'], '\n', seq + "  ", 44, seq))
        print(tab + "|")
        print(tab + "|\n")
    s.set(ret, 1)
    print("#活动的列表：'%s'的搜索结果\n" % key_word)


class favorite():

    def __init__(self, user):
        self.user = user
        self.path = os.path.join(temp_path, 'favorite.json')
        if os.path.exists(path):
            with open(self.path, 'r', encoding='utf-8') as fr:
                js = json.loads(fr.read())
            self.list = js.get(user, [])
        else:
            with open(self.path, 'w', encoding='utf-8') as fw:
                fw.write(json.dumps({}))
            self.list = []
        self.discard = []

    def add(self, dic):
        dic['date'] = strftime('%Y.%m.%d', localtime())
        self.list.append(dic)
        self.save()
        print(" '%s' 已添加至收藏夹" % dic['title'])

    def delete(self, raw_str):
        ind = indexInput(raw_str, len(self.list))
        i = 0; n = len(ind)
        while i < n:
            self.list[i] = None
            i += 1
        self.discard.extend(ind)

    def get(self, index):
        ret = {}
        index -= 1
        if index < 0 or index >= len(self.list):
            print("输入的数值有误，请检查后重试")
        elif self.list[index] == None:
            print("无法获取已经删除的项")
        else:
            ret.update(self.list[index])
            ret.pop('date')
        return ret

    def refresh(self):
        if len(self.discard) > 0:
            new_list = []
            i = 0; n = len(self.list)
            j = self.discard.pop(0)
            while i < n:
                if i == j:
                    j = self.discard.pop(0)
                else:
                    new_list.append(self.list[i])
                i += 1
            self.list = new_list
    
    def disp(self):
        self.refresh()
        print("\n" + "-"*16 + "我的收藏夹（编号/剧集名/收藏日期）" + "-"*16)
        if self.list:
            for i, dic in enumerate(self.list, 1):
                i = str(i)
                print(" "*(5-len(i)) + i + ":  %s (%s)" % \
                    (dic['title'], dic['date']))
        else:
            print(" "*3 + "（空）")
        print("-"*66 + "\n")
        s.set(self.list, 2)
        print("#活动的列表：%s的收藏夹\n" % self.user)

    def save(self):
        self.refresh()
        with open(self.path, 'r', encoding='utf-8') as fr:
            js = json.loads(fr.read())
        js[self.user] = self.list
        with open(self.path, 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(js))


def download(sid, select_id, dir_path, auto_format=False):
    if sid:
        detail = r.p_detail(sid)
        if failCheck(detail): return
        info = r._dictCopy(detail, 'media_id', 'season_id', \
                           'title', 'total', 'cover')
        print("ssid: %s ---> %s" % (sid, detail['title']))
    else:
        info = s.get(select_id)
        if not info: return
        sid = info['season_id']
    join = os.path.join
    dir_path = join(dir_path, 's_%s' % sid)
    os.makedirs(dir_path, exist_ok=True)
    with open(join(dir_path, 'info.json'), 'w', encoding='utf-8') as fw:
        fw.write(json.dumps(info, ensure_ascii=False))
    staticDownload(info['cover'], join(dir_path, 'cover.jpg'))
    
    slist = r.p_list(sid)
    if failCheck(slist): return
    print("\n" + "-"*20 + " episode selection " + "-"*20)
    i = 1
    for item in slist:
        index = str(i)
        string = " "*(5-len(index)) + index + ": " + item['title']
        if item['badge']:
            string += "（%s）" % item['badge']
        print(string)
        i += 1
    raw = input("---episodes(e.g.1-%i,%i): " % (i-3, i-1))
    index = indexInput(raw, i - 1)
    if len(index) == 0:
        return
    eps = []
    i = 0; n = len(index)
    while i < n:
        eps.append(slist[index[i]])
        i += 1

    info = r.geturl(eps[0]['aid'], eps[0]['cid'], fnval=2256, fourk=1)
    if failCheck(info): return
    if auto_format:
        vc = 12
        vq = min(max(info['accept_quality']), 80)
        aq = max([a['id'] for a in info['dash']['audio']])
    else:
        print("\n" + "-"*20 + " format selection " + "-"*20)
        print("    12: hev1(H.265)\n    7: avc1(H.264)")
        vc = int(input("---video_codec_id: "))
        for i in range(len(info['accept_quality'])):
            print(f"    {info['accept_quality'][i]}: {info['accept_description'][i]}")
        vq = int(input("---video_quality_id: "))
        print("    30280: 192K\n    30232: 132K\n    30216: 64K")
        aq = int(input("---audio_quality_id: "))

    print("\nStarting multi-thread download...")
    i = 0
    for ep in eps:
        path = join(dir_path, ep['index'])
        if not os.path.exists(path):
            os.mkdir(path)
        with open(join(path, 'info.json'), 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(ep, ensure_ascii=False))
        info = r.geturl(ep['aid'], ep['cid'], fnval=16)
        if failCheck(info):
            continue
        else: dash = info['dash']
        for dic in dash['video']:
            if dic['codecid'] == vc and dic['id'] == vq:
                biliDownload(dic['base_url'], \
                             join(path, 'video.m4s'), r.sess)
                break
        for dic in dash['audio']:
            if dic['id'] == aq:
                biliDownload(dic['base_url'], \
                             join(path, 'audio.m4s'), r.sess)
                break
        staticDownload('https://comment.bilibili.com/%s.xml' % ep['cid'], \
                       join(path, 'danmaku.xml'))
        i += 1
    
    print(" %i 个视频下载完成（总共：%i，失败：%i）\n" % (i, n, n - i))


class utils():

    def __init__(self):
        pass

    def doc_about(self):
        with open(os.path.join(base_path, 'helpDoc.txt'), \
                  'r', encoding='utf-8') as f:
            print(f.read(103))

    def doc_help(self):
        with open(os.path.join(base_path, 'helpDoc.txt'), \
                  'r', encoding='utf-8') as f:
            f.seek(243)
            print(f.read())

    def clear_temp(self):
        if os.path.exists(temp_path):
            for name in os.listdir(temp_path):
                os.remove(os.path.join(temp_path, name))
            os.rmdir(temp_path)
        print("缓存已清理！")


def mainLoop():
    prompt = ' > '
    while True:
        raw = input(tag + prompt)
        cut = raw.split(' ')
        if cut[0] == 'search':
            try:
                if cut[1] == 'bangumi':
                    search_type = 0
                elif cut[1] == 'ft':
                    search_type = 1
                else:
                    raise Exception
                key_word = cut[2]
            except:
                print("用法：search bangumi | ft {key_word}")
                continue
            search(key_word, search_type)
        elif cut[0] == 'favorite':
            if f == None:
                print("请登录后再使用收藏夹功能")
                continue
            try:
                if cut[1] == 'list':
                    f.disp()
                elif cut[1] == 'add':
                    try:
                        no = int(cut[2])
                    except:
                        print("用法：favorite add {search_result_id}")
                        continue
                    f.add(s.get(no, 1))
                elif cut[1] == 'delete':
                    try:
                        no_raw = cut[2]
                    except:
                        print("用法：favorite delete {favorite_id}")
                        continue
                    f.delete(no_raw)
                else:
                    raise Exception
            except:
                print("用法：favorite list | add | delete [parameter]")
                continue
        elif cut[0] == 'download':
            try:
                if cut[1][0] == 's':
                    sid = int(cut[1][1: ])
                    no = 0
                else:
                    sid = 0
                    no = int(cut[1])
                path = work_path
                auto = False
                i = 2; n = len(cut)
                while i < n:
                    if cut[i] == '-path':
                        path = cut[i + 1]
                        i += 1
                    elif cut[i] == '-auto':
                        auto = True
                    else:
                        raise Exception
                    i += 1
            except:
                print("用法：download {list_id | 's'+season_id} [-path {save_path}] [-auto]")
                continue
            download(sid, no, path, auto)
        elif cut[0] == 'login':
            try:
                if cut[1] == 'new':
                    new = True
                    user = cut[2]
                else:
                    new = False
                    user = cut[1]
            except:
                print("用法：login [new] {user_name}")
                continue
            login(user, new)
        elif cut[0] == 'help':
            u.doc_help()
        elif cut[0] == 'about':
            u.doc_about()
        elif cut[0] == 'version':
            print("\n", version, "\n", sep='')
        elif cut[0] == 'exit':
            break
        elif cut[0] == 'debug':
            try:
                exec(' '.join(cut[1: ]))
            except Exception as e:
                print(repr(e))
        elif cut[0] == 'clear':
            u.clear_temp()
        else:
            print("未知指令，请输入help查看帮助")


if __name__ == '__main__':
    #os.chdir(work_path)
    tag = name
    r = retrieval(None)
    s = select()
    f = None
    u = utils()
    print("="*96 + "\n\n" + " "*32 + "Bilili（哔哩哩）B站视频下载工具\n\n" + "="*96)
    init(autoreset=True)
    mainLoop()
