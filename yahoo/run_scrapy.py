import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.news import NewsSpider

# Yahooニュースのスパイダーを実行
process = CrawlerProcess(settings=get_project_settings())
process.crawl(NewsSpider)
process.start()