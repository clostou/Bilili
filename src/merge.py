import os
import json
import shutil
import logging
import subprocess
from io import StringIO
from bilili import base_path
from danmaku2ass_light import Danmaku2ASS


__all__ = ['Convert']


def dirParse(dir_path):
    result = {}
    with open(os.path.join(dir_path, 'info.json'), 'r', encoding='utf-8') as f:
        result['title'] = json.load(f)['title']
    result['cover'] = ''
    result['eps'] = []
    for file in os.listdir(dir_path):
        path = os.path.join(dir_path, file)
        if os.path.isdir(path):
            try:
                with open(os.path.join(path, 'info.json'), 'r', encoding='utf-8') as f:
                    ep = {'title': json.load(f)['title']}
                ep['video'] = os.path.join(path, 'video.m4s')
                ep['audio'] = os.path.join(path, 'audio.m4s')
                danmu = os.path.join(path, 'danmaku.xml')
                ep['danmu'] = danmu if os.path.exists(danmu) else ''
                ep['cover'] = ''
                ep['subtitle'] = ''
                for ep_file in os.listdir(path):
                    cut = ep_file.split('.')
                    if cut[0] == 'cover':
                        ep['cover'] = os.path.join(path, ep_file)
                    elif cut[-1] == 'srt':
                        ep['subtitle'] = os.path.join(path, ep_file)
            except:
                pass
            else:
                result['eps'].append(ep)
        elif file.split('.')[0] == 'cover':
            result['cover'] = path
    return result


def fileMerge(file_dict, output):
    merger = os.path.join(base_path, 'm4sMerge')
    if file_dict.get('subtitle'):
        cmd = f'''{merger} "{file_dict["video"]}" "{file_dict["audio"]}" \
"{file_dict["cover"]}" "{file_dict["subtitle"]}" "{output}"'''
    else:
        cmd = f'''{merger} "{file_dict["video"]}" "{file_dict["audio"]}" \
"{file_dict["cover"]}" "{output}"'''
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout= subprocess.PIPE, \
                         stderr=subprocess.STDOUT, encoding='utf-8')
    out, err = p.communicate()
    return p.returncode


def xml2ass(xml_path, ass_path, config):
    # config: 0-字号 1-不透明度 2-底部空白 3-滚动时长 4-悬停时长 5-去除重叠字幕
    log_buffer = StringIO()
    logging.basicConfig(stream=log_buffer)
    Danmaku2ASS(xml_path, "autodetect", ass_path, 1080, 720,
                reserve_blank=int(720 * config[2]), font_size=int(config[0]), text_opacity=config[1],
                duration_marquee=config[3], duration_still=config[4], is_reduce_comments=config[5])
    log_buffer.close()


def copy_file(file1, file2, start=0, ending=-1, append=False, buffer=1024):
    if ending >= 0 and ending <= start:
        raise ValueError("invalid start-ending of read")
    mode = 'wb'
    if os.path.exists(file1):
        if append:
            mode = 'ab'
        else:
            os.remove(file1)
    if ending < 0:
        length = os.path.getsize(file2) - start
    else:
        length = min(os.path.getsize(file2), ending) - start
    with open(file2, 'rb') as f:
        f.seek(start)
        with open(file1, mode) as _f:
            while True:
                _f.write(f.read(buffer))
                length -= buffer
                if length <= 0:
                    break


def Convert(src_list, dst_path, dm_args=[23, 0.6, 0.667, 12.0, 6.0, 0], embed_cc=True):
    join = os.path.join
    for src in src_list:
        try:
            result = dirParse(src)
        except:
            print('目录 "%s" 解析失败，请检查文件是否缺失' % os.path.abspath(src))
            continue
        path = join(dst_path, result['title'])
        if os.path.exists(path):
            if not input('文件夹 "%s" 已经存在，是否覆盖 (y/n)？' % os.path.abspath(path)) in ['Y', 'y']:
                continue
            else:
                shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)
        print('创建目录 "%s"：' % result['title'])
        danmu_path = join(path, 'danmuAss')
        os.makedirs(danmu_path, exist_ok=True)
        if not embed_cc:
            cc_path = join(path, 'ccSrt')
            os.makedirs(cc_path, exist_ok=True)
        if result['cover']:
            copy_file(join(path, os.path.basename(result['cover'])), result['cover'])
        i = 0
        for ep in result['eps']:
            if not embed_cc and ep['subtitle']:
                file_copy(join(cc_path, '%s.srt' % ep['title']), ep['subtitle'])
                ep['subtitle'] = ''
            if fileMerge(ep, join(path, '%s.mp4' % ep['title'])) == 0:
                print('输出文件 "%s.mp4"' % ep['title'])
                i += 1
            else:
                print('文件缺失或已损坏 "%s"' % os.path.dirname(ep['video']))
            if ep['danmu']:
                xml2ass(ep['danmu'], join(danmu_path, '%s.ass' % ep['title']), dm_args)
        if not embed_cc and len(os.listdir(cc_path)) == 0:
            os.rmdir(cc_path)
        print("---总计%d个视频已合并\n" % i)


if __name__ == '__main__':
    Convert([r'.\dist\s_6333'], '.\\')
