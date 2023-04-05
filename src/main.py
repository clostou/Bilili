import os
import json
from bilili import *
from merge import *
from time import strftime, localtime
from datetime import datetime, timedelta
from traceback import format_exc
from threading import Thread


name = 'Bilili'
version = '1.0'


def cutByLen(string, size, sep='\n'):
    cuts = []
    while size < len(string):
        cuts.append(string[: size])
        string = string[size: ]
    cuts.append(string)
    return sep.join(cuts)


def indexInput(raw_str, vaild_value):
    try:
        index = int(raw_str)
        if index not in vaild_value:
            raise ValueError
    except:
        index = -1
        print("输入的数值有误，请检查后重试")
    return index


def indexesInput(raw_str, max_value):
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


def failCheck(retrieval_ret):
    if isinstance(retrieval_ret, int):
        return True
    else:
        return False


def sessCheck(cookies):
    r = retrieval(cookies)
    ret = r.c_user()
    if isinstance(ret, int):
        if ret > 0: 
            #print("网络错误 (%i)\n" % ret)
            return 1
        else: 
            print("验证过期，请重新登录\n")
            return 0
    else:
        if ret['vip_type'] != 0 and ret['vip_status'] == 1:
            return 2
        else:
            return 1


def changeUser(user_name, cookies):
    global tag, f, r
    if f != None:
        f.refresh()
    state = sessCheck(cookies)
    if not state:
        tag = name
        r = retrieval(None)
        f = None
        login(user_name, new=True)
    else:
        if state == 2:
            tag = name + '(*%s)' % user_name
        else:
            tag = name + '(%s)' % user_name
        r = retrieval(cookies)
        f = favorite(user_name)


def login(user_name, new=False):
    cookies_path = os.path.join(temp_path, 'cookies_' + user_name)
    if new:
        l = loginQR()
        l.get()
        l.show()
        if l.success:
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
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
    ret = []; tab = " "*6
    for i, res in enumerate(results, 1):
        detail = r.p_detail(res['season_id'])
        if failCheck(detail): break
        
        ret.append(r._dictCopy(detail, 'media_id', 'season_id', 'title',
                               'total', 'cover'))
        if res['org_title']:
            org = "（%s）" % res['org_title']
        else:
            org = ""
        print("\033[44m%i\033[0m···%s%s" % (i, res['title'], org))
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
        if label != "未开播" and res['pubtime'] > 0:
            time = datetime(1970, 1, 1) + timedelta(hours=8, seconds=res['pubtime'])
            print(tab + "|    " + time.strftime("%Y年%m月%d日开播  ") + \
                  res['styles'])
        else:
            print(tab + "|    " + res['styles'])
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
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as fr:
                js = json.loads(fr.read())
            self.list = js.get(user, [])
        else:
            with open(self.path, 'w', encoding='utf-8') as fw:
                fw.write(json.dumps({}))
            self.list = []
        self.discard = set()

    def add(self, dic):
        if not isinstance(dic, dict): return
        dic['date'] = strftime('%Y.%m.%d', localtime())
        self.list.append(dic)
        self.refresh()
        print(" '%s' 已添加至收藏夹" % dic['title'])

    def delete(self, raw_str):
        ind = indexesInput(raw_str, len(self.list))
        i = 0; n = len(ind)
        while i < n:
            self.list[ind[i]] = None
            i += 1
        self.discard.update(ind)

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
        if self.discard:
            new_list = []
            i = 0; n = len(self.list)
            while i < n:
                if i not in self.discard:
                    new_list.append(self.list[i])
                i += 1
            self.discard.clear()
            self.list = new_list
        with open(self.path, 'r', encoding='utf-8') as fr:
            js = json.loads(fr.read())
        js[self.user] = self.list
        with open(self.path, 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(js))
    
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


def download(sid, select_id, output_path, auto_format=False, only_danmu=False):

    def vParse(dash):
        v_type = {}
        n = len(dash); i = 0
        while i < n:
            vq_list = v_type.setdefault(dash[i]['codecid'], [])
            vq_list.append(dash[i]['id'])
            i += 1
        for vc in v_type:
            v_type[vc].sort(reverse=True)
        vc_list = list(v_type)
        vc_list.sort(reverse=True)
        return vc_list, v_type
    
    def aParse(dash):
        aq_list = []
        n = len(dash); i = 0
        while i < n:
            aq_list.append(dash[i]['id'])
            i += 1
        aq_list.sort(reverse=True)
        return aq_list
    
    def next(value, sorted_list):
        i = 0; n = len(sorted_list)
        while i < n:
            if sorted_list[i] < value:
                return sorted_list[i]
            i += 1
        return sorted_list[-1]
    
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
    dir_path = join(output_path, 's_%s' % sid)
    os.makedirs(dir_path, exist_ok=True)
    with open(join(dir_path, 'info.json'), 'w', encoding='utf-8') as fw:
        fw.write(json.dumps(info, ensure_ascii=False))
    staticDownload(info['cover'], join(dir_path, 'cover.%s' % info['cover'].split('.')[-1]))
    
    slist = r.p_list(sid)
    if failCheck(slist): return
    if len(slist) > 1:
        print("\n" + "-"*19 + " episode selection " + "-"*19)
        i = 0
        for item in slist:
            i += 1
            ind = str(i)
            string = " "*(5-len(ind)) + ind + ": " + item['title']
            if item['badge']:
                string += "（%s）" % item['badge']
            print(string)
        raw = input("\---episodes(e.g.1-%d,%d): " % (i - 1, i))
        index = indexesInput(raw, i)
        if len(index) == 0:
            return
        eps = []
        i = 0; n = len(index)
        while i < n:
            eps.append(slist[index[i]])
            i += 1
    else:
        n = len(slist)
        eps = slist

    info = r.geturl(eps[0]['aid'], eps[0]['cid'], is_pgc=True, fnval=2192, fourk=1)    # 最高4K分辨率
    if failCheck(info): return
    vc_list = {13: 'av01(AV1)', 12: 'hev1(H.265)/flv', 7: 'avc1(H.264)'}
    aq_list = {30280: '192K', 30232: '132K', 30216: '64K'}
    support_vc, v_type = vParse(info['dash']['video'])
    support_aq = aParse(info['dash']['audio'])

    if only_danmu:
        print("\n" + "-"*20 + " download config " + "-"*20)
        print(f"\n    0: 保留全部弹幕\n    ...\n    8: 默认屏蔽等级(推荐)\n    ...\n    10: 最高屏蔽等级")
        raw = input("\---danmu_block_level(0-10): ")
        dm = indexInput(raw, range(11))
        if dm < 0: return
    elif auto_format:
        if 12 in support_vc:
            vc = 12
        else:
            vc = support_vc[-1]
        access_vq = v_type[vc]
        vq = min(access_vq[0], 112)
        aq = support_aq[0]
        dm = 8
        print(f"\nAuto configuration:\n  video_codec_id: {vc}\n  video_quality_id: {vq}\n  audio_quality_id: {aq}\n  danmu_block_level: {dm}")
    else:
        print("\n" + "-"*20 + " download config " + "-"*20)
        for i in support_vc:
            print(f"    {i}: {vc_list[i]}")
        raw = input("\---video_codec_id: ")
        vc = indexInput(raw, support_vc)
        if vc < 0: return
        access_vq = v_type[vc]
        for i in range(len(info['accept_quality'])):
            if info['accept_quality'][i] not in access_vq:
                print(f"    {info['accept_quality'][i]}: {info['accept_description'][i]}（会员）")
            else:
                print(f"    {info['accept_quality'][i]}: {info['accept_description'][i]}")
        raw = input("\---video_quality_id: ")
        vq = indexInput(raw, access_vq)
        if vq < 0: return
        for i in support_aq:
            print(f"    {i}: {aq_list[i]}")
        raw = input("\---audio_quality_id: ")
        aq = indexInput(raw, support_aq)
        if aq < 0: return
        print(f"    0: 保留全部弹幕\n    ...\n    8: 默认屏蔽等级(推荐)\n    ...\n    10: 最高屏蔽等级")
        raw = input("\---danmu_block_level(0-10): ")
        dm = indexInput(raw, range(11))
        if dm < 0: return

    print("\nStarting multi-thread download...")
    i = 0
    for ep in eps:
        path = join(dir_path, ep['index'])
        if not os.path.exists(path):
            os.mkdir(path)
        with open(join(path, 'info.json'), 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(ep, ensure_ascii=False))
        staticDownload(ep['cover'], join(path, 'cover.%s' % ep['cover'].split('.')[-1]))
        
        if only_danmu:
            # 仅下载弹幕
            ret = danmuDownload(ep['cid'], join(path, 'danmaku.xml'), \
                                level=dm, cookies=r.sess)
            if failCheck(ret):
                print("%d: 更新失败" % i + 1)
            else:
                print(f"{i+1}: 保留{ret[0]} / 总共{ret[1]}\n")
                i += 1
            continue
        else:
            dmDown = Thread(target=danmuDownload, \
                            args=(ep['cid'], join(path, 'danmaku.xml')), \
                            kwargs={'level': dm, 'cookies': r.sess})
            ccDown = Thread(target=ccDownload, \
                            args=(ep['aid'], ep['cid'], path), \
                            kwargs={'cookies': r.sess})
            dmDown.start()
            ccDown.start()
        
        info = r.geturl(ep['aid'], ep['cid'], is_pgc=True, fnval=2192, fourk=1)
        if failCheck(info): continue
        dash = info['dash']
        ret_v = False; ret_a = False
        
        not_exist = True
        for dic in dash['video']:
            if dic['id'] == vq  and dic['codecid'] == vc:
                ret_v = biliDownload(dic, \
                                     join(path, 'video.m4s'), r.sess)
                not_exist = False
                break
        if not_exist:
            support_vc, v_type = vParse(dash['video'])
            _vc = vc; _vq = vq
            if _vc not in support_vc: _vc = next(_vc, support_vc)
            if _vq not in v_type[_vc]: _vq = next(_vq, v_type[_vc])
            for dic in dash['video']:
                if dic['id'] == _vq and dic['codecid'] == _vc:
                    ret_v = biliDownload(dic, \
                                         join(path, 'video.m4s'), r.sess)
                    break
        
        not_exist = True
        for dic in dash['audio']:
            if dic['id'] == aq:
                ret_a = biliDownload(dic, \
                                     join(path, 'audio.m4s'), r.sess)
                not_exist = False
                break
        if not_exist:
            support_aq = aParse(dash['audio'])
            _aq = next(aq, support_aq)
            for dic in dash['audio']:
                if dic['id'] == _aq:
                    ret_a = biliDownload(dic, \
                                            join(path, 'audio.m4s'), r.sess)
                    break
        #staticDownload('https://comment.bilibili.com/%s.xml' % ep['cid'], \
        #               join(path, 'danmaku.xml'))
        if ret_v and ret_a: i += 1

    m.add(dir_path)
    print(" %i 个文件下载完成（总共：%i，失败：%i）\n" % (i, n, n - i))


class merge():
    
    def __init__(self):
        self.merge_list = []
    
    def add(self, dir_path):
        if dir_path not in self.merge_list:
            self.merge_list.append(dir_path)
    
    def convert(self, target, output_path, keep_subtitle=False):
        if target:
            Convert([target], output_path, embed_cc=not keep_subtitle)
        elif self.merge_list:
            Convert(self.merge_list, output_path, embed_cc=not keep_subtitle)
        else:
            print("没有需要合并的文件")


class utils():

    def __init__(self):
        pass

    def doc_about(self):
        with open(os.path.join(base_path, 'helpDoc.txt'), \
                  'r', encoding='utf-8') as f:
            print(f.read(121))

    def doc_help(self):
        with open(os.path.join(base_path, 'helpDoc.txt'), \
                  'r', encoding='utf-8') as f:
            f.seek(260)
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
        print(tag + prompt, end='', level=1)
        raw = input()
        cut = raw.split(' ')
        if cut[0] == 'search':
            try:
                if cut[1] == 'bangumi':
                    search_type = 0
                elif cut[1] == 'ft':
                    search_type = 1
                else:
                    raise Exception
                key_word = ' '.join(cut[2: ])
            except:
                print("用法：search bangumi | ft {key_word}")
                continue
            search(key_word, search_type)
        elif cut[0] == 'favorite' or cut[0] == 'f':
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
        elif cut[0] == 'download' or cut[0] == 'd':
            try:
                if cut[1][0] == 's':
                    sid = int(cut[1][1: ])
                    no = 0
                else:
                    sid = 0
                    no = int(cut[1])
                path = work_path
                auto = False; only = False
                i = 2; n = len(cut)
                while i < n:
                    if cut[i] == '-path':
                        path = cut[i + 1]
                        i += 1
                    elif cut[i] == '-auto':
                        auto = True
                    elif cut[i] == '-update_danmu':
                        only = True
                    else:
                        raise Exception
                    i += 1
            except:
                print("用法：download {list_id | 's'+season_id} [-path {save_path}] [-auto] [-update_danmu]")
                continue
            download(sid, no, path, auto, only)
        elif cut[0] == 'merge':
            try:
                target = None
                path = work_path
                keep_subtitle = False
                if len(cut) > 1:
                    i = 1; n = len(cut)
                    if os.path.exists(cut[1]):
                        target = cut[1]
                        i += 1
                    while i < n:
                        if cut[i] == '-path':
                            path = cut[i + 1]
                            i += 1
                        elif cut[i] == '-keep_subtitle':
                            keep_subtitle = True
                        else:
                            raise Exception
                        i += 1
            except:
                print("用法：merge [{target}] [-path {save_path}] [-keep_subtitle]")
                continue
            m.convert(target, path, keep_subtitle)
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
    os.chdir(work_path)
    tag = name
    r = retrieval(None)
    s = select()
    m = merge()
    f = None
    u = utils()
    print("="*96 + "\n\n" + " "*32 + "Bilili（哔哩哩）B站视频下载工具\n\n" + "="*96)
    outputInit()
    try:
        mainLoop()
    except:
        print(format_exc(), level=3)
        input("\n请按任意键退出...")
