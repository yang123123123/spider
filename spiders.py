# 该爬虫项目是为了爬取 https://alpha.wallhaven.cc/ 网站上部分分辨率的部分图片保存到本地，并将url和tag存入到mysql数据库，采用了多线程的方式进行爬取

import requests
from lxml import etree
import os
import threading
import Threadpool
import pymysql


# 连接数据库
db = pymysql.connect("120.79.146.112", "wangjing", "Wwj3113776.", "wallpaper", charset="utf8")
cur = db.cursor()
# 获取数据库里所有的tag
sql = "select name from wall_app_tag"
cur.execute(sql)
tags = list(cur.fetchall())
tag_lists = []
# 将获取到的tag存放到tag_lists的列表中
for tag in tags:
    tag_lists.append(tag[0])
cur.close()
db.close()

lock = threading.Lock()

# 实例化Threadpool，创建一个能存放50个线程的线程池
pool = Threadpool.Threadpool(50)

# 根据url获得网页html代码
def get_lxml_etree_element(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    return etree.HTML(response.text)

# 若目录不存在就新建目录，并调到该目录下
def mkdir(path):
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)
    os.chdir(path)

# 下载图片和图片tag并入库的函数
def download(page, path, pool):
    # 获取html并用xpath解析
    try:
        selector = get_lxml_etree_element(
            'https://alpha.wallhaven.cc/search?q=&categories=111&purity=100&resolutions={}&sorting=favorites&order=desc&page={}'.format(path,
                page))
        # 获取图片id存放到wallpaper_id列表中
        wallpaper_id = selector.xpath('//div[@id="thumbs"]/section/ul//li/figure/@data-wallpaper-id')

        # 每一个线程获取一个db的连接
        try:
            db = pymysql.connect("120.79.146.112", "wangjing", "Wwj3113776.", "wallpaper", charset="utf8")
            db.autocommit(True)
            cur = db.cursor()

            # 遍历id的列表
            for id in wallpaper_id:
                print(id)
                # 爬取图片
                try:
                    response = requests.get('https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.jpg'.format(id))

                    # 存到本地并将url存到数据库
                    with open('photo{}.jpg'.format(id), 'wb+') as f:
                        f.write(response.content)
                    try:
                        sql1 = "insert into wall_app_img(ImgId, ImgUrl, ImgRatio) values({},'photo{}.jpg','{}')".format(id, id, path)
                        cur.execute(sql1)
                    except:
                        print('插入id为{}的图片失败'.format(id))
                    # 爬取图片tag并入库，若获取tag失败，将该图片从数据库中删除
                    try:
                        selector_tag = get_lxml_etree_element('https://alpha.wallhaven.cc/wallpaper/{}'.format(id))
                        # 获取一张图片的所有tag存放到列表中
                        tag_list = selector_tag.xpath('//ul[@id="tags"]//li/a/text()')

                        for tag in tag_list:
                            tag_id = len(tag_lists)+1
                            # 判断列表中是否已有该tag，若没有，添加该tag到tag列表中
                            if tag not in tag_lists:
                                # 因为多线程同时对tag_list进行操作，容易出现死锁，需要加锁来避免
                                lock.acquire()
                                tag_lists.append(tag)
                                lock.release()
                                # 将tag插入到数据库
                                try:
                                    sql2 = "insert into wall_app_tag(TagId, name) values({},'{}')".format(tag_id, tag)
                                    sql3 = "insert into wall_app_photo_tag(ImgId, TagId) values({},{})".format(id, tag_id)
                                    cur.execute(sql2)
                                    cur.execute(sql3)
                                except:
                                    print('插入id为{}的图片tag失败'.format(id))
                    except:
                        print('获取id为{}的图片tag失败'.format(id))
                        del_sql = "delete from wall_app_img where ImgId={}".format(id)
                        cur.execute(del_sql)
                except:
                    print('获取id为{}的图片失败'.format(id))

            cur.close()
            db.close()
        except:
            print('数据库连接异常')
    except:
        print('第{}页获取失败'.format(page))
    pool.addThread()

# 需要爬取的分辨率的字典，对应的value为该分辨率的图片总页数
path_dic = {
    '1280x800': 95,
    '1280x960': 41,
    '1600x900': 100,#130
    '1600x1000': 35,
    '1600x1200': 100,#245
    '1920x1080': 100,#3658
    '1920x1200': 100,#1492
    '1920x1440': 37,
    '2560x1440': 100,#370
    '2560x1600': 100,#579
    '2560x1920': 15,
}

# 主函数，从pool中取出线程并激活线程
def main(path):
    mkdir(path)
    for page in range(1, path_dic[path]+1):
        t = pool.getThread()(target=download, args=(page, path, pool))
        t.start()

# 调用函数
main('1280x960')
