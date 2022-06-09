
import string
from .parsed_news_model import ParsedNewsModel
import scrapy
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
import html2text
import logging
from scrapy.utils.log import configure_logging
import pandas as pd
from scrapy import signals
from pydispatch import dispatcher
import re
from bs4 import BeautifulSoup

class NewsSpider(scrapy.Spider):
    logging.basicConfig(
        filename='log.txt',
        format='%(levelname)s: %(message)s',
        level=logging.ERROR
    )        

    name = "news"
    allowed_domains = [
        "detik.com",
        "kompas.com",
        "tribunnews.com"
    ]
    start_urls = [
    #     # "https://www.detik.com/tag/bencana",
    #     "https://www.detik.com/tag/gempa",
    #     "https://www.detik.com/tag/banjir",
    #     "https://www.detik.com/tag/banjir-bandang",
    #     # "https://www.detik.com/tag/kemarau",
    #     "https://www.detik.com/tag/kekeringan",
    #     "https://www.detik.com/tag/kebakaran-hutan",
    #     # "https://www.detik.com/tag/cuaca-panas",
    #     # "https://www.detik.com/tag/awan-panas",
    #     "https://www.detik.com/tag/longsor",
    #     "https://www.detik.com/tag/angin-kencang",
    #     "https://www.detik.com/tag/puting-beliung",
    #     # "https://www.detik.com/tag/bencana-alam",
    #     "https://www.detik.com/tag/pergerakan-tanah",
    #     "https://www.detik.com/tag/pergeseran-tanah",
    #     "https://www.detik.com/tag/kebakaran",
        "https://www.detik.com/tag/erosi",
    #     "https://www.detik.com/tag/abrasi",
    #     # "https://www.detik.com/tag/tsunami",
    ]

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    interator = 0
    current_domain = ""
    current_subdomain = ""
    current_url = ""
    berita = []
    visited = []
    skipped_subdomain = ["travel", "20", "finance", "inet", "hot", "sport", "oto", "health", "food", "foto", "wolipop"]
    # 50
    def __init__(self, *a, **kw):
        super(NewsSpider, self).__init__(*a, **kw)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def preprocessing(self, berita):
        s = str(berita)
        s = s.replace('\n', ' ')
        s = s.replace('\r', ' ')
        tokens = [token for token in s.split(" ") if token != ""]
        
        T = [t for t in tokens]
        return ' '.join(T)



    def parse(self, response):
        parsing_url = urlparse(response.request.url)

        domain = parsing_url.netloc

        if self.current_url != response.request.url:
            self.current_url = response.request.url
            self.visited.clear()

        if (domain == "www.detik.com"):
            self.current_domain = domain
            for article in response.css("article"):
                link = article.css("a::attr(href)").extract_first()

                parsed_link = urlparse(link)
                self.current_subdomain = parsed_link.hostname.split('.')[0]

                if (self.current_subdomain not in self.skipped_subdomain) and \
                    ("edu" not in parsed_link.path) and \
                    ("foto-news" not in parsed_link.path):
                    yield response.follow(link, self.parse_detik)

            for navbutton in response.css('div.paging a'):
                
                currentIndexView = navbutton.css("a::text").extract_first()
                if currentIndexView != None:
                    if (currentIndexView.isnumeric() and (currentIndexView not in self.visited)):
                        self.visited.append(currentIndexView)
                        next_page = navbutton.css("a::attr(href)").extract_first()
                        
                        if next_page is not None and ("tv." not in next_page):
                            next_page = response.urljoin(next_page)
                            yield scrapy.Request(next_page, callback=self.parse, headers=self.headers)

                elif "next" in navbutton.css("a::attr(onclick)").extract_first():    
                    next_page = navbutton.css("a::attr(href)").extract_first()
                    if next_page is not None and ("tv." not in next_page):
                        self.interator += 1
                        next_page = response.urljoin(next_page)
                    yield scrapy.Request(next_page, callback=self.parse, headers=self.headers)


    def parse_detik(self, response):
            
        author = response.css("div.detail__author::text").extract_first()
        
        desc = ""

        title = response.css("h1.detail__title::text").extract_first()

        if title != None:
            date = response.css("div.detail__date::text").extract_first()
        else:
            title = response.css("h1.mt5::text").extract_first()
            date = response.css("div.date::text").extract_first()
            
        tempTitle = self.preprocessing(title)

        date = date
        date = date
 
        descBody = response.css('div.detail__body-text').extract()
        description = ((self.textParser(descBody[0]).replace("*","") + " "))
        
        if description != "" and title != "" and date != "":
            print('\n')
            print('\n')
            print('data inserted')
            print('\n')
            print('\n')
            data = [str(tempTitle), str(date), str(description), str(self.current_domain)]

            self.berita.append(data)

    def spider_closed(self, spider):
        print('\n')
        print('\n')
        print('kesini')
        print('\n')
        print('\n')
        writer = pd.DataFrame(self.berita, columns=['title', 'date', 'description', 'source'])
        writer.to_csv('scrapped_news.csv', index=False, sep=',')

    def textParser(self, text):
        # return text
        soup = BeautifulSoup(text, features='lxml')
        for table in soup.find_all("table", {'class':'linksisip'}): 
            table.decompose()

        for divTag in soup.find_all("div", {'class':'detail__body-tag'}): 
            divTag.decompose()

        for divVideo in soup.find_all("div", {'class':'sisip_video_ds'}): 
            divVideo.decompose()

        for divVideo1 in soup.find_all("div", {'class':'newlist-double'}):
            divVideo1.decompose()

        for divVideo2 in soup.find_all("iframe", {"class":"video20detik_0"}):
            divVideo2.decompose()

        for unusedStrong in soup.find_all("strong"):
            unusedStrong.decompose()

        converter = html2text.HTML2Text()
        converter.ignore_links = True

        return converter.handle(str(soup))
