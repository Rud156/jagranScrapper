#!/usr/bin/env python2

import feedparser
import requests
import hashlib
import time
from lxml import html
from pymongo import MongoClient
from datetime import datetime

client = MongoClient()
dataBase = client.feedParser
collection = dataBase.feeds
allFeedLinks = []


def write_logs_to_file(url, success, reason):
    fx = open("JagranLogs.txt", "a")
    if success:
        fx.write("All feeds got and parsed. All complete for now..." + "\n")
    else:
        fx.write("Url: " + url + "\n")
        fx.write("Reason: " + reason + "\n")

    fx.write("Current Time: " + str(datetime.now().time()) + "\n")
    if success:
        fx.write("\n")
    fx.close()


def parse_feed(url):
    try:
        feed = feedparser.parse(url)
        entries = feed['entries']
        for value in entries:
            allFeedLinks.append(value.link)
    except:
        write_logs_to_file(url, False, "Error Parsing Feed")


def get_feed_links():
    try:
        page = requests.get('http://www.jagran.com/rss-hindi.html')
        tree = html.fromstring(page.content)
        urlList = tree.xpath('//table/tr/td/a/@href')
        filteredList = []
        for i in range(0, len(urlList)):
            if i % 2 == 0:
                filteredList.append(urlList[i])
        for url in filteredList:
            parse_feed(url)
        return True
    except Exception as e:
        write_logs_to_file("None", False, "Error In Connection")
        return False


def get_page(link):
    try:
        page = requests.get(link)
    except Exception as e:
        write_logs_to_file(link, False, "Connection Error")
        return "", [], "", "", "", False

    tree = html.fromstring(page.content)
    metaTitle = tree.xpath('//meta[@property="og:title"]/@content')
    metaKeywords = tree.xpath('//meta[@name="keywords"]/@content')
    body = tree.xpath('//div[@class="article-content"]/p/text()')
    title = tree.xpath('//section[@class="title"]/h1/text()')
    summary = tree.xpath('//div[@class="article-summery"]/text()')

    filteredBody = ""
    for item in body:
        filteredBody += item.encode('utf-8')

    if len(metaTitle) > 0:
        metaTitle = metaTitle[0].encode('utf-8')
    else:
        metaTitle = ''
    if len(summary) > 0:
        summary = summary[0].encode('utf-8')
    else:
        summary = ''
    if len(title) > 0:
        title = title[0].encode('utf-8')
    else:
        title = ''
    if len(metaKeywords) > 0:
        metaKeywords = metaKeywords[0].split(',')
    else:
        metaKeywords = []

    return metaTitle, metaKeywords, filteredBody, summary, title, True


def mongoCheck(hashValue, title, summary, metaTitle, metaKeywords, body, url, countValue):
    dataSet = {
        '_id': hashValue,
        'url': url,
        'title': title,
        'meta_title': metaTitle,
        'meta_keywords': metaKeywords,
        'body': body,
        'summary': summary
    }
    data = collection.find_one({'_id': hashValue})
    if data is not None:
        print 'Data Already Exists: ' + str(countValue)
        return

    collection.insert_one(dataSet)
    print 'Data Added: ' + str(countValue)


if __name__ == '__main__':
    print 'Service Started'
    retValue = get_feed_links()
    if retValue:
        print 'Got All Links'
        for i in range(0, len(allFeedLinks)):
            metaTitle, metaKeywords, body, summary, title, success = get_page(allFeedLinks[i])
            if success:
                hashValue = hashlib.md5(title + summary + metaTitle).hexdigest()
                mongoCheck(hashValue, title, summary, metaTitle, metaKeywords, body, allFeedLinks[i], i)
            else:
                print "Unable to get the reuqested page!!! Check Connection"
    else:
        print "Unable to get all links!!! Check Connection"
        write_logs_to_file("None", False, "Not Able to get any feeds. Check Connection...")
    print 'All Done. Wowser!!!!!!'
    write_logs_to_file("", True, "")
