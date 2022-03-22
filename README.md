# Bilili命令行工具
![](https://img.shields.io/badge/Build-success-yellow) ![](https://img.shields.io/badge/Version-1.0-orange) ![](https://img.shields.io/badge/Python-3.x-blue) ![](https://img.shields.io/badge/LICENSE-GPLv3-green)
## 简介
Bilili（哔哩哩）是一个基于Python3和哔哩哔哩API的命令行工具。该项目实现了B站番剧和影视等PGC类视频的多线程本地下载，还支持视频搜索、账号管理和简单的收藏夹功能。

程序大部分的API接口参考了这篇文档：[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)
>**注意：  
>该项目仅供学习交流编程技术、以及个人测试之用，可能造成的一切后果由使用者本人承担**

## 目录说明
* src: 源代码文件，其中程序入口为main.py
* dist : 打包示例，包含可以直接使用的exe程序

## 命令行
**1. login [new] \{user_name}**

    通过用户名(user_name)登录已有账号
    可选字段 new：创建新账号并保存

    注：某些视频的访问、下载(或高画质下载)可能需要B站账号或大会员账号的登录

**2. search bangumi | ft \{key_word}**

    在B站番剧或影视分区进行关键词(key_word)搜索，并将搜索结果设置为活动列表  
    bangumi：番剧分区  
    或ft：影视分区  

**3. favorite**

    简单的收藏夹功能，与账号绑定
    + add {search_result_id}：将搜索结果中对应编号(search_result_id)的视频添加到收藏夹中
        示例：
            上一条命令为“search ft 地球”，返回了20条结果，编号1-20
            把第二条结果“地球脉动”放入当前账号的收藏夹:
                favorite add 2
            注：该条命令一次只能添加一个视频
    + delete {favorite_id}：删除收藏夹中对应编号范围(favorite_id)的视频
        示例：
            现在收藏夹中有12个视频，编号1-12
            删除第2个视频：
                favorite delete 2
            或删除第2、3、4、6个视频：
                favorite delete 2-4,6
            或删除第3、5个和最后4个视频：
                favorite delete 3,5,9-
    + list：列出收藏夹中的全部视频，并将当前收藏夹设置为活动列表

**4. download {list_id | 's'+season_id} [-path {save_path}] [-auto]**

    下载活动列表中编号为list_id的视频
    第一参数 list_id | 's'+season_id：
        list_id：下载活动列表中编号为list_id的视频
            示例：
                1.上一条命令为“search bangumi re0”，返回了6条结果
                  下载第一条结果“Re0第二季前半”：
                      download 1
                2.上一条命令为“favorite list”，收藏夹中有2个视频
                  下载第2个视频：
                      download 2
        或's'+season_id：下载ssid号为season_id的视频
            示例：
                下载ssid号为28625的番剧：
                    download s28625
    可选参数 -path {save_path}：
        设置文件下载路径为save_path
    可选参数 -auto：
        自动选择音视频格式和清晰度（默认h.265/1080p/192k）

    注：部分老视频可能不支持h.265编码。若未下载video.m4s视频文件，请将video_codec_id的值设为7

**5. clear**

    清除本地所有缓存数据(登录记录和收藏夹)

**6. debug \{python_code}**

    向程序发送一条可执行python代码，仅用于调试

**7. help**

    查看命令帮助

**8. about**

    显示软件相关信息

**9. version**

    显示软件版本

**10. exit**

    退出程序

## 相关
程序下载的文件与哔哩哔哩安卓和WIN10客户端类似，为dash格式（音视频是分开的两个文件），合并请参考我的另一个项目m4sMerge[^1]。  
>*这个项目开始的较早，经过多次“使用-反馈-改进”，已经比较成熟。不过我还没把它搬到GitHub上，~~后面有时间就把搬上来~~。*

* 知乎链接（内含合并软件下载链接）：[怎样把B站下载到电脑的视频跟音频合并在一起? - 知乎](https://www.zhihu.com/question/354969536/answer/1270358138)
[^1]: 直接使用前需要把模式文件 Bilili.pat 放到合并工具安装目录下的 pattern 文件夹
