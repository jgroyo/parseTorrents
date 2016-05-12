#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import urllib2
import random
import time
import sys
import operator
import codecs
from bs4 import BeautifulSoup
import locale

start_time = time.time()

try:
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
except:
    print "Exception: " + str(sys.exc_info()[0])

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

home_dir = 'series'
home_url = 'torrentes.no-ip.biz'
updateContent = ''


def get_magnet(url):
    try:
        request = urllib2.Request(url)
        request.add_header("Referer", "http://www.bricocine.com/")
        data = urllib2.urlopen(request).read()
        soup = BeautifulSoup(data, "html.parser")
#        print str(soup).decode('utf-8')
        for item in soup.findAll("a", {"class": "btn-primary"}):
            return item.get('href')
        return ''
    except: 
        print "Error getting magnet from " + url
        return ''


def get_torrent(url):
    try:
        request = urllib2.Request(url)
        request.add_header("Referer", "http://www.bricocine.com/")
        data = urllib2.urlopen(request).read()
        soup = BeautifulSoup(data, "html.parser")
        for item in soup.findAll("a", {"class": "btn-primary"}):
            return item.get('href')
        return ''
    except: 
        print "Error getting torrent file from " + url
        return ''


def get_serie(url):
    print
    print 'get_serie: ' + url + '\n---------'
    global updateContent
    try:
        web = urllib2.urlopen(url)
        data = web.read()
    except:
        print "Error while opening " + url
        return
    soup = BeautifulSoup(data, "html.parser")
    serie = ""
    for item in soup.findAll("h1", {"class": "post-title"}):
        serie = item.contents[0].strip()

    print
    #    print serie.encode('utf8') + ': ' + url.encode('utf8') + '\n----------'.encode('utf8')
    print serie + ': ' + url + '\n----------'

    folder_name = serie.replace(" ", "").replace(":", "").encode('ascii', 'ignore')
    folder_path = home_dir + '/' + folder_name
    file_name = folder_path + '/feed.rss'
    index_file_name = folder_path + '/index.html'

    mini_index_content = u'<!DOCTYPE html>\n<html>\n<head>\n'
    mini_index_content += u'<title>Feed para ' + serie + '</title>\n'
    mini_index_content += u'<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
    mini_index_content += u'<link rel="shortcut icon" href="../../favicon.ico">'
    mini_index_content += u'<style>a, a:link, a:visited, a:hover {color:#808080; text-decoration:none; ' \
                          u'font-family:\'Courier New\'; font-size:small;}</style>\n'
    mini_index_content += u'</head>\n<body>\n'
    mini_index_content += u'<h1>' + serie + '</h1>\n<a href="feed.rss">feed.rss</a><br><br>\n'

    feed_content = u'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
    feed_content += u'<title>Feed para ' + serie + '</title>\n'
    feed_content += u'<link>http://' + home_url + '/' + folder_path + '</link>\n'
    feed_content += '<ttl>30</ttl>\n<description>RSS feed for ' + serie + '</description>\n'

    items_found = False
    for item in soup.findAll("table", {"class": "table-series"}):
        tr_list = item.findAll("tr")
        for i in range(len(tr_list) - 1, -1, -1):
            items_found = True
            title = ''
            magnet = ''
            pub_date = ''
            it2 = tr_list[i]
            for it3 in it2.findAll("span", {"class": "title"}):
                title = it3.contents[0]
            for it4 in it2.findAll("a", {"id": "magnet"}):
                time.sleep(0.1)
                magnet = get_magnet(it4.get('href'))
            if magnet == "":
                for it4 in it2.findAll("a", {"id": "file"}):
                    time.sleep(0.1)
                    magnet = get_torrent(it4.get('href'))
            for it5 in it2.findAll("span", {"class": "metadata a"}):
                random_time = '{0}:{1}:{2}'.format(str(random.randint(0, 23)), str(random.randint(0, 59)), str(
                    random.randint(0, 59)))
                pub_date = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                         time.strptime(it5.contents[0] + random_time, " %d/%m/%Y %H:%M:%S"))
                pub_date = str(pub_date).decode('utf-8')
            try:
                mini_index_content += u'<a href="' + str(magnet) + '">' + title + ' (' + pub_date + ')</a><br>\n'
                feed_content += '<item>\n<title>' + title.strip() + '</title>\n'
                print title + ' (' + pub_date + '): ' + magnet
                feed_content += u'<link>' + str(magnet) + '</link>\n'
                feed_content += u'<pub_date>' + pub_date + '</pub_date>\n'
                feed_content += u'</item>\n'
            except:
                feed_content += u'</item>\n'
                print "Bad magnet or something..."
                print "Exception: " + str(sys.exc_info()[0])

    mini_index_content += u'</body>\n</html>\n'
    feed_content += '</channel>\n</rss>\n'
    if items_found:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        f = open(file_name, 'w')
        f.write(feed_content.encode('utf8'))
        f.close()
        f2 = open(index_file_name, 'w')
        f2.write(mini_index_content.encode('utf8'))
        f2.close()
        if sys.argv[1] == "update":
            updateContent += u'<a href="' + folder_name + '/index.html">' + serie + '</a><br>\n'


# Returns True if you have to continue inspecting
# which means full upgrade or changes in update
def check_for_changes(data):
    if sys.argv[1] != "update":
        return True
    old = ''
    ret_value = True
    try:
        f = open(home_dir + '/last_changes.txt', 'r')
        old = f.read()
        f.close()

        if old == data:
            ret_value = False
    finally:
        f = open(home_dir + '/last_changes.txt', 'w')
        f.write(data)
        f.close()
        return ret_value


def list_series(url):
    #       shutil.rmtree(home_dir)
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)
    cont = True
    page = 1
    while cont:
        if sys.argv[1] == "full":
            print "\n\n-------------------\nPage: " + str(page) + "\n-------------------"
        cont = False
        try:
            request = urllib2.Request(url.format(page))
            web = urllib2.urlopen(request)
            data = urllib2.urlopen(url.format(page)).read()
        except urllib2.HTTPError, error:
            data = error.read()
        except:
            print "\nLast page: " + str(page)
            break

        if not check_for_changes(data):
            print "No changes\n---\n"
            return

        soup = BeautifulSoup(data, "html.parser")
        soup = soup.find("div", {"class": "quad-4-portrait"})
        limit = (100, 10)[sys.argv[1] == "update"]
        items = soup.findAll("div", {"class": "entry"})[0:limit]

        for item in items:
            if sys.argv[1] == "full":
                cont = True
            get_serie(item.a.get('href'))
        page += 1

        if sys.argv[1] == "update":
            # check for changes in update.html
            old = ''
            try:
                f = open(home_dir + '/update.html', 'r')
                f.readline()
                for line in f:
                    old += line
                f.close()
            except:
                print 'No previous update file'
            if old != updateContent.encode('utf-8'):
                # Actually write content
                f = open(home_dir + '/update.html', 'w')
                current_time = time.localtime()
                show_time = time.strftime('%d-%m-%Y %H:', current_time) + str(random.randint(0, 59)).zfill(2)
                muestra_time = u'<h2>Últimas series actualizadas (' + show_time.encode('utf8') + u')</h2>\n'
                f.write(muestra_time.encode('utf8'))
                f.write(updateContent.encode('utf8'))
                f.close()
                print '\nUpdate file written\n'
            else:
                print '\nNo need to update "update" file'


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def generate_index():
    index_content = u'<!DOCTYPE html>\n<html>\n<head>\n'
    index_content += u'<title>Index of feeds</title>\n'
    index_content += u'<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
    index_content += u'<link rel="shortcut icon" href="../favicon.ico">'
    index_content += u'<style>a, a:link, a:visited, a:hover {color:#808080; text-decoration:none; ' \
                     u'font-family:\'Courier New\'; font-size:small;}</style>\n'
    index_content += u'</head>\n<body>\n<h1>TorrentES</h1>\n'
    index_content += u'<!--#include virtual="update.html" -->\n'
    index_content += u'<h2>Series</h2>\n'

    dir_list = get_immediate_subdirectories(home_dir)
    tuple = []
    for base in dir_list:
        folder_name = home_dir + '/' + base
        try:
            f = open(folder_name + '/index.html', 'r')
            data = f.read()
            f.close()
            soup = BeautifulSoup(data, "html.parser")
            serie = soup.find("h1").get_text()
            tuple.append([serie, base])
        #            index_content += u'<a href="' + base + '/feed.rss">' + serie + '</a><br>\n'
        except:
            print 'File does not exist: ' + folder_name + '/index.html'

    tuple.sort(key=operator.itemgetter(0), cmp=locale.strcoll)
    for i in tuple:
        # index_content += u'<a href="' + i[1] + '/feed.rss">' + i[0] + '</a><br>\n'
        index_content += u'<a href="' + i[1] + '/index.html">' + i[0] + '</a><br>\n'

    index_content += u'<!--#include virtual="../analytics.html" -->\n'
    index_content += u'</body>\n</html>\n'
    index = open(home_dir + '/index.html', 'w')
    index.write(index_content.encode('utf8'))
    index.close()


# try:
if True:
    if len(sys.argv) != 2:
        print "Usage: " + sys.argv[0] + " <full/update/updateIndex>"
        sys.exit(0)

    current_time = time.localtime()
    show_time = time.strftime('%d-%m-%Y %H:%M:%S', current_time)
    print u'\n-----------\n' + show_time.encode('utf8') + u'\n' + sys.argv[1] + u'\n-----------'

    if len(sys.argv) == 2 and sys.argv[1] == "full":
        print "Full search...."
        list_series('http://www.bricocine.com/c/series/page/{0}/?orderby=title&order=asc')
    elif len(sys.argv) == 2 and sys.argv[1] == "update":
        print "Updating content...."
#        get_magnet('http://www.linksbrico.com/download.php?n=xATMg0CIz9mbvJHdgUGZg82ZlVnS&i==w2bxOcYwNXR&u===AI');
        get_serie('http://www.bricocine.com/14455/the-blacklist-temporada-3/');
#        get_serie('http://www.bricocine.com/15697/juego-de-tronos-temporada-6/');
        list_series('http://www.bricocine.com/c/series/')
    elif len(sys.argv) == 2 and sys.argv[1] == "updateIndex":
        print
    else:
        print "Usage: " + sys.argv[0] + " <full/update/updateIndex>"
        sys.exit(0)
# except Exception:
#   print(traceback.format_exc())
#   print "\nCurrent page was: " + page

# if time.strftime('%H', current_time) == "16":
#    get_serie('http://www.bricocine.com/13977/fear-the-walking-dead-temporada-1/');

print "\nGenerating index..."
generate_index()
print u'\nThe end...\n'
print("--- \nTook %s seconds\n ---" % (time.time() - start_time))

# raw_input()



