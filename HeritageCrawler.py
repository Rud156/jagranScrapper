import requests
import hashlib
from re import sub
from lxml import html
from pymongo import MongoClient
from datetime import datetime

client = MongoClient()
dataBase = client.Heritage
collection = dataBase.places
collection.create_index('hash', background=True)
allLinks = set()


def get_links_from_list(linkList):
    for i in xrange(0, len(linkList)):
        if linkList[i][0] == '#':
            continue
        isFile = linkList[i].find("File:")
        if isFile == -1:
            actualLink = 'https://en.wikipedia.org' + linkList[i]
            if actualLink not in allLinks:
                allLinks.add(actualLink)
    print "Got " + str(len(allLinks)) + " links..."
    print ""


def get_link_from_general_list(link, xPath):
    try:
        page = requests.get(link)
        tree = html.fromstring(page.content)
        links = tree.xpath(xPath)
        get_links_from_list(links)
    except (requests.ConnectTimeout, requests.ConnectionError) as e:
        print "Error Occurred: " + str(e)
        write_logs_to_file(link, False, e)


def get_link_from_main_page(link):
    try:
        page = requests.get(link)
        tree = html.fromstring(page.content)
        links = tree.xpath('//div[@id="mw-content-text"]/table[1]/tr/td/a/@href')
        for i in xrange(0, len(links)):
            isFile = links[i].find("File:")
            if isFile == -1:
                actualLink = 'https://en.wikipedia.org' + links[i]
                if actualLink not in allLinks:
                    allLinks.add(actualLink)
        print "Got " + str(len(allLinks)) + " links..."
        print ""
    except (requests.ConnectTimeout, requests.ConnectionError) as e:
        print "Error Occurred: " + str(e)
        write_logs_to_file(link, False, e)


def get_info_from_page(link):
    # noinspection PyBroadException
    try:
        print "Getting Page: " + link
        try:
            page = requests.get(link)
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            print "Error Occurred: " + str(e)
            write_logs_to_file(link, False, e)
            return

        # TODO: Other Links Relevant to India
        tree = html.fromstring(page.content)
        pageTitle = tree.xpath('//h1[@id="firstHeading"]/text()')
        try:
            pageTitle = pageTitle[0].encode('utf-8')
        except IndexError:
            print "Index Error Occurred. Getting new heading"
            pageTitle = tree.xpath('//*[@id="firstHeading"]/i/text()')
            pageTitle = pageTitle[0].encode('utf-8')

        pageDescription_1 = tree.xpath('//div[@id="mw-content-text"]/p[1]/text()')
        pageDescription_2 = tree.xpath('//div[@id="mw-content-text"]/p[2]/text()')
        pageDescription = ""
        for i in xrange(0, len(pageDescription_1)):
            pageDescription += pageDescription_1[i].strip()
        pageDescription += "\n"
        for i in xrange(0, len(pageDescription_2)):
            pageDescription += pageDescription_2[i].strip()
        pageDescription = pageDescription.strip()
        pageDescription = pageDescription.encode('utf-8')

        imageXPath = "//img[contains(@src,'" + requests.utils.quote(pageTitle, safe='') + "')]/@src"
        imageURLs = tree.xpath(imageXPath)
        for i in xrange(0, len(imageURLs)):
            imageURLs[i] = 'https:' + imageURLs[i]
        pageURL = link

        tableHeadings = tree.xpath('//table[contains(@class, "infobox")]/tr[th and td]/th')
        tableData = tree.xpath('//table[contains(@class, "infobox")]/tr[th and td]/td')
        pageHash = hashlib.md5(pageTitle + pageDescription).hexdigest()

        dataSet = {
            'title': pageTitle,
            'description': pageDescription,
            'url': pageURL,
            'hash': pageHash,
            'image_links': imageURLs
        }
        table = {}
        for i in xrange(0, len(tableHeadings)):
            currentHeading = tableHeadings[i].text_content().strip()
            currentHeading = sub('[.]', '', currentHeading)

            currentData = tableData[i].text_content().strip()
            if currentHeading not in table:
                table[currentHeading] = currentData
        dataSet['table_content'] = table
        add_to_database(dataSet)
    except:
        write_logs_to_file(link, False, 'General Error')
        print "Error in page. Movin' on to next link..."


def add_to_database(dataSet):
    print "Adding " + dataSet['title'] + " to database..."
    dataHash = dataSet['hash']
    data = collection.find_one({'hash': dataHash})
    if data is not None:
        print "Page Already added!!!"
        print ""
        return
    collection.insert_one(dataSet)
    print "Data Added!!!"
    print ""


def write_logs_to_file(url, success, reason):
    fx = open("HeritageLogs.txt", "a")
    if success:
        fx.write("All feeds got and parsed. All complete for now..." + "\n")
    else:
        fx.write("Url: " + url + "\n")
        fx.write("Reason: " + reason + "\n")

    fx.write("Current Time: " + str(datetime.now().time()) + "\n")
    if success:
        fx.write("\n")
    fx.close()


if __name__ == '__main__':
    get_link_from_main_page("https://en.wikipedia.org/wiki/List_of_World_Heritage_Sites_in_India")
    get_link_from_general_list("https://en.wikipedia.org/wiki/Index_of_India-related_articles",
                               '//div[@id="mw-content-text"]/p/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_forts_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_museums_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/Pilgrimage_places_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki'
                               '/List_of_states_and_territories_of_India_by_number_of_places_of_worship',
                               '//*[@id="mw-content-text"]/table[2]/tr/td[2]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_national_parks_of_India',
                               '//*[@id="mw-content-text"]/table[2]/tr/td[1]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_national_parks_of_India',
                               '//*[@id="mw-content-text"]/table[2]/tr/td[5]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_lakes_of_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_waterfalls_of_India',
                               '//*[@id="mw-content-text"]/table/tr/td/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_beaches_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_Geographical_Indications_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[2]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_Geographical_Indications_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[4]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_botanical_gardens_in_India',
                               '//*[@id="mw-content-text"]/table[2]/tr/td[1]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_hill_stations_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_gates_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_zoos_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_aquaria_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[1]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_aquaria_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[2]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_forests_in_India',
                               '/*[@id="mw-content-text"]/table/tr/td[1]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_forests_in_India',
                               '/*[@id="mw-content-text"]/table/tr/td[3]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_forests_in_India',
                               '/*[@id="mw-content-text"]/table/tr/td[5]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_rivers_of_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_mountains_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[3]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_mountains_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_mountains_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[6]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_stadiums_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[2]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_stadiums_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[4]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_stadiums_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[5]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_stadiums_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[6]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_stadiums_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td[7]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/Wildlife_sanctuaries_of_India',
                               '//*[@id="mw-content-text"]/table/tr/td[2]/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_rock-cut_temples_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/List_of_mosques_in_India',
                               '//*[@id="mw-content-text"]/table/tr/td/a/@href')
    get_link_from_general_list('https://en.wikipedia.org/wiki/Hindu_pilgrimage_sites_in_India',
                               '//div[@id="mw-content-text"]//ul/li/a/@href')
    print 'All links accumulated...'
    for linkValue in allLinks:
        get_info_from_page(linkValue)
    print "Hella yes all done!!!"
    write_logs_to_file('', True, 'Wowser all complete...')
