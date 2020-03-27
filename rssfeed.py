import csv
import requests
import xml.etree.ElementTree as ET

def loadrss():
    # url of rss feed
    url = 'http://www.hindustantimes.com/rss/topnews/rssfeed.xml'

    # Create HTTP request for the given url
    res = requests.get(url)

    # saving content as xml file

    with open('newsreel.xml','wb') as f:
        f.write(res.content)


def parseXML(XMLfile):

    # create element tree object
    tree = ET.parse(XMLfile)

    # get Root element
    root  = tree.getroot()

    # create empty list for news items
    newsitems = []

    #iterate news item
    for item in root.findall('./channel/item'):

        # empty new dictionary
        news = {}

        # iterate child elements of item
        for child in item:
            # special checking for namespace object content:media
            if child.tag == '{http://search.yahoo.com/mrss/}content':
                news['media'] = child.attrib['url']
            else:
                news[child.tag] = child.text.encode('utf8')

                # append news dictionary to news items list
        newsitems.append(news)

        # return news items list
        return newsitems


def savetoCSV(newsItems,filename):
    # specifying the fields for csv file
    fields = ['guid', 'title', 'pubDate', 'description', 'link', 'media']

    # writing to csv file
    with open(filename, 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames=fields)

        # writing headers (field name )
        writer.writeheader()

        # writing data rows
        writer.writerows(newsItems)


def main():

    # load rss from web to update exsting xml
    loadrss()

    #parse  xml file
    newsitems = parseXML('newsreel.xml')

    # store news items in a csv file
    savetoCSV(newsitems,'topnews.csv')


if __name__ == '__main__':
        # calling main function
        main()












