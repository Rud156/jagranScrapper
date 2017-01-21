import feedparser
import requests
import hashlib
import time
from lxml import html
from pymongo import MongoClient

client = MongoClient()
dataBase = client.feedParser
collection = dataBase.feeds

allFeedLinks = []


def parse_feed(url):
    feed = feedparser.parse(url)
    entries = feed['entries']
    for value in entries:
        allFeedLinks.append(value.link)


def get_feedLinks():
    page  = requests.get('http://www.jagran.com/rss-hindi.html')
    tree = html.fromstring(page.content)
    urlList = tree.xpath('//table/tr/td/a/@href')
    filteredList = []
    for i in range(0, len(urlList)):
        if i % 2 == 0:
            filteredList.append(urlList[i])
    for url in filteredList:
        parse_feed(url)


def get_page(link):
    page = requests.get(link)
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
        title  = title[0].encode('utf-8')
    else:
        title = ''
    if len(metaKeywords) > 0:
        metaKeywords = metaKeywords[0].split(',')
    else:
        metaKeywords = []

    return  metaTitle, metaKeywords, filteredBody, summary, title


def mongoCheck(hashValue, title, summary, metaTitle, metaKeywords, body, countValue):
    dataSet = {
        '_id': hashValue,
        'title': title,
        'meta_title': metaTitle,
        'meta_keywords': metaKeywords,
        'body': body,
        'summary': summary
    }
    data = collection.find_one({'_id': hashValue})
    if data != None:
        print 'Data Already Exists: ' + str(countValue)
        return
    collection.insert_one(dataSet)
    print 'Data Added: ' + str(countValue)


if __name__ == '__main__':
    while(true):
        print 'Service Started'
        get_feedLinks()
        print 'Got All Links'
        for i in range(0, len(allFeedLinks)):
            metaTitle, metaKeywords, body, summary, title = get_page(allFeedLinks[i])
            hashValue = hashlib.md5(title + summary + metaTitle).hexdigest()
            mongoCheck(hashValue, title, summary, metaTitle, metaKeywords, body, i)
        print 'All Done. Wowser!!!!!!'
        time.sleep(600)


