# Bilili�����й���
![](https://img.shields.io/badge/FileVer.-1.1.4-orange) ![](https://img.shields.io/badge/Python-3.x-blue) ![](https://img.shields.io/badge/LICENSE-GPLv3-green)
## ���
Bilili������������һ������Python3����������API�������й��ߡ�����Ŀʵ����Bվ�����Ӱ�ӵ�PGC����Ƶ�Ķ��̱߳������أ���֧����Ƶ�������˺Ź���ͼ򵥵��ղؼй��ܡ�

����󲿷ֵ�API�ӿڲο�����ƪ�ĵ���[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)
>**ע�⣺  
>����Ŀ����ѧϰ������̼������Լ����˲���֮�ã�������ɵ�һ�к����ʹ���߱��˳е�**

## Ŀ¼˵��
* src: Դ�����ļ������г������Ϊmain.py
* dist : ���ʾ������������ֱ��ʹ�õ�exe����

## ������
**1. login [new] \{user_name}**

    ͨ���û���(user_name)��¼�����˺�
    ��ѡ�ֶ� new���������˺Ų�����

    ע��ĳЩ��Ƶ�ķ��ʡ�����(��߻�������)������ҪBվ�˺Ż���Ա�˺ŵĵ�¼

**2. search bangumi | ft \{key_word}**

    ��Bվ�����Ӱ�ӷ������йؼ���(key_word)���������������������Ϊ��б�  
    bangumi���������  
    ��ft��Ӱ�ӷ���  

**3. favorite**

    �򵥵��ղؼй��ܣ����˺Ű�
    + add {search_result_id}������������ж�Ӧ���(search_result_id)����Ƶ��ӵ��ղؼ���
        ʾ����
            ��һ������Ϊ��search ft ���򡱣�������20����������1-20
            �ѵڶ���������������������뵱ǰ�˺ŵ��ղؼ�:
                favorite add 2
            ע����������һ��ֻ�����һ����Ƶ
    + delete {favorite_id}��ɾ���ղؼ��ж�Ӧ��ŷ�Χ(favorite_id)����Ƶ
        ʾ����
            �����ղؼ�����12����Ƶ�����1-12
            ɾ����2����Ƶ��
                favorite delete 2
            ��ɾ����2��3��4��6����Ƶ��
                favorite delete 2-4,6
            ��ɾ����3��5�������4����Ƶ��
                favorite delete 3,5,9-
    + list���г��ղؼ��е�ȫ����Ƶ��������ǰ�ղؼ�����Ϊ��б�

**4. download {list_id | 's'+season_id} [-path {save_path}] [-auto] [-only_danmu]**

    ���ػ�б��б��Ϊlist_id����Ƶ
    ��һ���� list_id | 's'+season_id��
        list_id�����ػ�б��б��Ϊlist_id����Ƶ
            ʾ����
                1.��һ������Ϊ��search bangumi re0����������6�����
                  ���ص�һ�������Re0�ڶ���ǰ�롱��
                      download 1
                2.��һ������Ϊ��favorite list�����ղؼ�����2����Ƶ
                  ���ص�2����Ƶ��
                      download 2
        ��'s'+season_id������ssid��Ϊseason_id����Ƶ
            ʾ����
                ����ssid��Ϊ28625�ķ��磺
                    download s28625
    ��ѡ���� -path {save_path}��
        �����ļ�����·��Ϊsave_path
    ��ѡ���� -auto��
        �Զ�ѡ������Ƶ��ʽ�������ȣ�Ĭ��h.265/1080p/192k��
    ��ѡ���� -only_danmu��
        �����ػ���µ�Ļ

    ע����������Ƶ���ܲ�֧��h.265���롣��δ����video.m4s��Ƶ�ļ����뽫video_codec_id��ֵ��Ϊ7

**5. clear**

    ����������л�������(��¼��¼���ղؼ�)

**6. debug \{python_code}**

    �������һ����ִ��python���룬�����ڵ���

**7. help**

    �鿴�������

**8. about**

    ��ʾ��������Ϣ

**9. version**

    ��ʾ����汾

**10. exit**

    �˳�����

## ���
�������ص��ļ�������������׿��WIN10�ͻ������ƣ�Ϊdash��ʽ������Ƶ�Ƿֿ��������ļ������ϲ���ο��ҵ���һ����Ŀm4sMerge[^1]��
>*�����Ŀ��ʼ�Ľ��磬������Ρ�ʹ��-����-�Ľ������Ѿ��Ƚϳ��졣�����һ�û�����ᵽGitHub�ϣ�~~������ʱ��ͰѰ�����~~��*

* ֪�����ӣ��ں��ϲ�����������ӣ���[������Bվ���ص����Ե���Ƶ����Ƶ�ϲ���һ��? - ֪��](https://www.zhihu.com/question/354969536/answer/1270358138)
[^1]: ֱ��ʹ��ǰ��Ҫ��ģʽ�ļ� Bilili_amdtool.pat �ŵ��ϲ����߰�װĿ¼�µ� pattern �ļ���
