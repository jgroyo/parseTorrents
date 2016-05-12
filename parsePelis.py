#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import random
import time
import codecs
import sqlite3
import re
import os
import sys
import urllib
from mechanize import Browser
import urlparse

import torrent_data

from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")


import locale
try:
   locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
except:
   print "Exception: " + str(sys.exc_info()[0])


class MyOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15'


class ImdbRating:
    # title of the movie
    title = u''
    # IMDB URL of the movie
    url = u''
    # IMDB rating of the movie
    rating = u''
    # IMDB date of the movie
    date = u''
    # IMDB duration
    duration = u''
    # IMDB genres
    genres = u''

    # Did we find a result?
    found = False

    # constant
    BASE_URL = 'http://www.imdb.com'

    def __init__(self, title):
        self.title = title
        self._process()

    def _process(self):

        movie = '+'.join(self.title.split())
        movie = movie.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        movie = movie.replace('ñ', 'ñ').replace('¡', '')
        try:
            br = Browser()
            url = "%s/find?s=tt&q=%s" % (self.BASE_URL, movie.encode('ascii', 'ignore'))
            br.open(url)
        except:
            print u'IMDB Error trying to find ' + self.title
            return

        if re.search(r'/title/tt.*', br.geturl()):
            self.url = "%s://%s%s" % urlparse.urlparse(br.geturl())[:3]
            soup = BeautifulSoup(MyOpener().open(url).read())
        else:
            try:
                link = br.find_link(url_regex=re.compile(r'/title/tt.*'))
                res = br.follow_link(link)
                self.url = urlparse.urljoin(self.BASE_URL, link.url)
                soup = BeautifulSoup(res.read())
            except:
                pass

        try:
            self.title = soup.find('span', {"itemprop": "name"}).contents[0].strip().replace('"',"'")
            temp = soup.find('div', {"class": "star-box-giga-star"})
            if temp:
                self.rating = temp.contents[0].strip()
            self.found = True
            temp = soup.find('meta', {"itemprop": "datePublished"})
            if temp:
                self.date = temp.attrs['content']
            temp = soup.find('time', {"itemprop": "duration"})
            if temp:
                self.duration = temp.contents[0].replace('min', '').strip()
            is_first = True
            for x in soup.findAll('span', {"itemprop": "genre"}):
                if is_first:
                    is_first = False
                else:
                    self.genres += u', '
                self.genres += x.contents[0].strip()
        except:
            pass


# -----------------------------------
# Initial considerations
# -----------------------------------
home_dir = 'pelis'
torrents_dir = 'torrents'
home_url = 'torrentes.no-ip.biz'
conn = ''

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

start_time = time.time()

# -----------------------------------
# Connect to database, create it if it does not exist
# -----------------------------------
if not os.path.exists('pelis.db'):
    print "Create database"
    conn = sqlite3.connect('pelis.db')
    conn.execute('''CREATE TABLE PELIS
        (NOMBRE TEXT NOT NULL,
        CALIDAD TEXT NOT NULL,
        MAGNET  TEXT NOT NULL,
        TORRENT TEXT NOT NULL,
        FECHA   DATE,
        TAMANO  INTEGER,
        IMDB_NAME TEXT,
        IMDB_URL TEXT,
        IMDB_RATING TEXT,
        IMDB_DATE TEXT,
        IMDB_GENRE TEXT,
        IMDB_DURATION TEXT,
        PRIMARY KEY (NOMBRE, CALIDAD));''')
    print "DB created successfully"
    conn.close()


def get_magnet(url):
    try:
        request = urllib2.Request(url)
        request.add_header("Referer", "http://www.bricocine.com/")
        request.add_header("User-Agent",
                           "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36")
        web = urllib2.urlopen(request)
        data = web.read()
        web.close()
    except urllib2.HTTPError, error:
        data = error.read()
    soup = BeautifulSoup(data, "html.parser")
    link_node = soup.find('a', {"class": "btn-primary"})
    if link_node:
        return link_node.get('href')
    return u''


def get_torrent(url):
    try:
        request = urllib2.Request(url)
        request.add_header("Referer", "http://www.bricocine.com/")
        request.add_header("User-Agent",
                           "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36")
        web = urllib2.urlopen(request)
        data = web.read()
        web.close()
    except urllib2.HTTPError, error:
        data = error.read()
    soup = BeautifulSoup(data, "html.parser")
    return soup.find('a', {"class": "btn-primary"}).get('href')


def get_torrent_file(torrent_url):
    file_name = ''
    try:
        file_name = torrent_url.split('/')[-1]
        urllib.urlretrieve(torrent_url, torrents_dir + '/' + file_name)
    except:
        return None
    return file_name


def get_peli(url, calidad):
    try:
        request = urllib2.Request(url)
        request.add_header("Referer", "http://www.bricocine.com/")
        request.add_header("User-Agent",
                           "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36")
        web = urllib2.urlopen(request)
        data = web.read()
        web.close()
    except urllib2.HTTPError, error:
        data = error.read()
    except:
        print "Error while opening " + url
        print "Exception: " + str(sys.exc_info()[0])
        return ""

    print
    soup = BeautifulSoup(data, "html.parser")
    try:
        peli = u'' + soup.find("h1", {"class": "post-title"}).contents[0].split('[')[0].strip()
    except:
        print 'Error parsing url: ' + url
        return
    # print peli.encode('utf8') + ': ' + url.encode('utf8') + '\n----------'.encode('utf8')
    print peli.encode('ascii', 'ignore') + ': ' + url + '\n----------'

    magnet = torrent = ''
    tamano = 0

    for item in soup.findAll("table", {"class": "table-series"}):
        tr_list = item.findAll("tr")
        for i in range(len(tr_list) - 1, -1, -1):
            # imdb = ImdbRating(peli.encode('utf-8'))
            imdb = ImdbRating(peli)
            if imdb.found:
                print u'IMDB: {0} ({1}) - {2}: {3}'.format(imdb.title, imdb.rating, imdb.date, imdb.url)
            pub_date = ''
            it2 = tr_list[i]
            title = it2.find('span', {"class": "title"}).contents[0]
            magnet_node = it2.find('a', {"id": "magnet"})
            if magnet_node:
                magnet = get_magnet(magnet_node.get('href'))
            torrent_node = it2.find('a', {"id": "file"})
            if torrent_node:
                torrent = get_torrent(torrent_node.get('href'))
                if torrent:
                    torrent_file = get_torrent_file(torrent)
                if torrent_file:
                    tamano = torrent_data.get_tamano(torrents_dir + '/' + torrent_file)
            date_node = it2.find("span", {"class": "metadata a"})
            if date_node:
                random_time = '{0}:{1}:{2}'.format(str(random.randint(0, 23)), str(random.randint(0, 59)),
                                                   str(random.randint(0, 59)))
                pub_date = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                         time.strptime(date_node.contents[0] + random_time, " %d/%m/%Y %H:%M:%S"))
            else:
                if imdb.found and imdb.date:
                    random_time = '{0}:{1}:{2}'.format(str(random.randint(0, 23)), str(random.randint(0, 59)),
                                                       str(random.randint(0, 59)))
                    try:
                        pub_date = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                                 time.strptime(imdb.date + ' ' + random_time, "%Y-%m-%d %H:%M:%S"))
                    except:
                        pub_date = "Wed, 01 Jan 1901 00:00:00 +0000"
                else:
                    pub_date = "Wed, 01 Jan 1901 00:00:00 +0000"

            try:
                pub_date = str(pub_date).decode('utf-8')
                print peli + ' (' + pub_date + '): ' + magnet
                stmt = 'INSERT INTO PELIS (' \
                       'NOMBRE, ' \
                       'CALIDAD, ' \
                       'MAGNET, ' \
                       'TORRENT, ' \
                       'FECHA, ' \
                       'TAMANO,' \
                       'IMDB_NAME, ' \
                       'IMDB_URL, ' \
                       'IMDB_RATING, ' \
                       'IMDB_DATE, ' \
                       'IMDB_GENRE, ' \
                       'IMDB_DURATION) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}", ' \
                       '"{10}", "{11}")'.format(peli, calidad, magnet, torrent, pub_date, str(tamano),
                        imdb.title, imdb.url, imdb.rating, imdb.date, imdb.genres, imdb.duration)
                conn.execute(stmt)
                conn.commit()
            except:
                print u"Bad magnet or something at film: " + peli
                print "Exception: " + str(sys.exc_info()[0])
                return peli

    return peli


def list_pelis(url, calidad):
    #       shutil.rmtree(home_dir)
    cont = True
    page = 1
    last_peli = ''

    while cont:
        if sys.argv[1] == "full":
            print "\n\n-------------------\nPage: " + str(page) + "\n-------------------"
        cont = False
        try:
            request = urllib2.Request(url.format(page))
            request.add_header("Referer", "http://www.bricocine.com/")
            request.add_header("User-Agent",
                               "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36")
            web = urllib2.urlopen(request)
            data = web.read()
            web.close()
        except urllib2.HTTPError, error:
            data = error.read()
        except:
            print "\nLast page(" + calidad + "): " + str(page)
            print "url Error: " + url.format(page)
            print "Exception: " + str(sys.exc_info()[0])
            print "urllib2.urlopen(" + url.format(page) + ")"
            break

        if sys.argv[1] == "update":
            try:
                f = open('last_' + calidad, 'r')
                last_peli = f.readline()
                f.close()
            except:
                print "File last_" + calidad + "does not exist."
                print "Exception: " + str(sys.exc_info()[0])

        soup = BeautifulSoup(data, "html.parser")
        soup = soup.find("div", {"class": "quad-4-portrait"})
        limit = (100, 6)[sys.argv[1] == "update"]
        entries = []
        try:
            entries = soup.findAll("div", {"class": "entry"})
        except:
            print url.format(page)
            print u"Error in " + str(calidad) + ", page: " + str(page)

        is_first = True
        for item in entries[0:limit]:
            if sys.argv[1] == "full":
                cont = True
            peli = get_peli(item.a.get('href'), calidad)
            if sys.argv[1] == "update":
                if is_first:
                    f = open('last_' + calidad, 'w')
                    f.write(peli)
                    f.close()
                    is_first = False
                if peli == last_peli:
                    return
        page += 1


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def generate_index():
    index_content = u'<!DOCTYPE html>\n<html>\n<head>\n'
    index_content += u'<title>Index of films</title>\n'
    index_content += u'<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
    index_content += u'<link rel="shortcut icon" href="../favicon.ico">'
    index_content += u'<script src="../sorttable.js"></script>'
    index_content += u'<style>\n' \
                     u'a, a:link, a:visited, a:hover {color:#808080; text-decoration:none; ' \
                     u'font-family:\'Courier New\'; font-size:small;} \n' \
                     u'table.sortable th:not(.sorttable_sorted):not(.sorttable_sorted_reverse):not(.sorttable_nosort):after ' \
                     u'{content: " ▾ ▴";}\n ' \
                     u'table { border-collapse: collapse; }' \
                     u'</style>\n'
    index_content += u'</head>\n<body>\n<h1>TorrentES</h1>\n'
    index_content += u'<h2>Pelis</h2>\n'
    index_content += u'<a href="feed.rss">feed.rss</a><br>\n'

    index_content += u'<!--#include virtual="update.html" -->\n'

    index_content += u'<br>\n'

    cur = conn.cursor()
    cur.execute("select nombre, fecha from pelis order by datetime(fecha) desc limit 1;")
    data = cur.fetchone()
    index_content += u"Última actualización: " + str(data[0]) + " (" + str(data[1])+ ")<br>"
    print u"Última actualización: " + str(data) + "<br>"
    cur.close()

    cur = conn.cursor()
    cur.execute("select count(*) from PELIS")
    data = cur.fetchone()[0]
    index_content += str(data) + u" películas encontradas.<br>"
    print str(data) + u" películas encontradas.<br>"
    cur.close()

    index_content += u'<table class="sortable" border>\n'
    index_content += u'<tr>' \
                     u'<th>Título</th>' \
                     u'<th class="sorttable_numeric">IMDb#</th>' \
                     u'<th>Calidad</th>' \
                     u'<th>Estreno</th>' \
                     u'<th class="sorttable_numeric">Tamaño (MB)</th>' \
                     u'<th class="sorttable_numeric">Duración (min)</th>' \
                     u'<th>Género</th>' \
                     u'<th class="sorttable_nosort">IMDb</th>' \
                     u'<th class="sorttable_nosort">Torrent</th>' \
                     u'<th class="sorttable_nosort">Magnet</th>' \
                     u'</tr>\n'

    # titulo, nota, calidad, fecha añadido, fecha estreno, tamaño, enlace imdb (con icono), torrent, magnet
    cur = conn.cursor()
    cur.execute("select * from PELIS order by rowid desc")
    for row in cur.fetchall():
        new_line = u'<tr>'
        new_line += '<td><b>{0}</b></td>'.format(row[0])
        #for row_name in  'IMDB_RATING' 'CALIDAD' 'IMDB_DATE':
        for row_name in (8, 1, 9):
            new_line += '<td>{0}</td>'.format(row[row_name])
        tamano = row[5] / 1024 / 1024
        new_line += '<td>{0}</td>'.format(tamano)
        new_line += '<td>{0}</td>'.format(row[11])
        new_line += '<td>{0}</td>'.format(row[10])
        new_line += '<td><a href="{0}">IMDb</a></td>'.format(row[7])
        new_line += '<td><a href="{0}">torrent</a></td>'.format(row[3])
        new_line += '<td><a href="{0}">magnet</a></td>'.format(row[2])
        new_line += u'</tr>'
        index_content += new_line

    cur.close()
    # cur.execute("select * from PELIS order by rowid")


    index_content += u'</table>\n'
    index_content += u'<!--#include virtual="../analytics.html" -->\n'
    index_content += u'</body>\n</html>\n'
    index = open(home_dir + '/index.html', 'w')
    index.write(index_content.encode('utf8'))
    index.close()


# -----------------------------------
# Main
# -----------------------------------
if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <full/update/updateIndex>"
    sys.exit(0)

#get_peli(u"http://www.bricocine.com/1916/iron-man-3-2013-bdrip/", u"blueray")
#get_peli(u"http://www.bricocine.com/8178/el-secreto-de-sus-ojos-2009-dvdrip/", u"dvdrip")

try:
    conn = sqlite3.connect('pelis.db')
    print "Database opened successfully"
    # conn.execute('INSERT INTO PELIS (NOMBRE, CALIDAD, MAGNET, TORRENT, FECHA, IMDB_RATING, IMDB_DATE, IMDB_URL) VALUES ("test", "blueray", "magnet:?xt=test", "torrent:?SAdr", "Wed, 28 Oct 2015 12:47:46 +0000", "5.5", "2015-06-26", "http://www.imdb.com/title/tt3667648/?ref_=fn_tt_tt_1")')
    current_time = time.localtime()
    show_time = time.strftime('%d-%m-%Y %H:%M:%S', current_time)
    print u'\n-----------\n' + show_time.encode('utf8') + u'\n' + sys.argv[1] + u'\n-----------'

    if len(sys.argv) == 2 and sys.argv[1] == "full":
        print "Full search...."
        # list_pelis('http://www.bricocine.com/c/bluray-rip/page/{0}/?orderby=title&order=asc', 'bluray')
        list_pelis('http://www.bricocine.com/c/3d/page/{0}/', '3d')
        list_pelis('http://www.bricocine.com/c/bluray-rip/page/{0}/', 'bluray')
        list_pelis('http://www.bricocine.com/c/dvdrip/page/{0}/', 'DVDRip')
        list_pelis('http://www.bricocine.com/c/hd-microhd/page/{0}/', 'hd-microhd')
    elif len(sys.argv) == 2 and sys.argv[1] == "update":
        print "Updating content...."
        list_pelis('http://www.bricocine.com/c/bluray-rip/', 'bluray')
        list_pelis('http://www.bricocine.com/c/dvdrip/', 'DVDRip')
        list_pelis('http://www.bricocine.com/c/hd-microhd/', 'hd-microhd')
        list_pelis('http://www.bricocine.com/c/3d/', '3d')
    elif len(sys.argv) == 2 and sys.argv[1] == "updateIndex":
        print
    else:
        print "Usage: " + sys.argv[0] + " <full/update/updateIndex>"
        conn.close()
        sys.exit(0)

    print "\nGenerating index..."
    generate_index()
# except:
#    print "General Exception: " + str(sys.exc_info()[0])
finally:
    conn.close()
    print u'\nThe end...'
    print("--- Took %s seconds ---" % (time.time() - start_time))

# raw_input()

