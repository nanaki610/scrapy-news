# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst

class YahooItem(scrapy.Item):
    """
    Yahooニュースのスクレイピングアイテム定義

    Attributes:
        title (scrapy.Field): ニュースのタイトル
        article_number (scrapy.Field): 記事の番号
        post_date (scrapy.Field): 投稿日
        url (scrapy.Field): 記事のURL
        article (scrapy.Field): 記事の本文
    """
    title = scrapy.Field(output_processor=TakeFirst())
    article_number = scrapy.Field(output_processor=TakeFirst())
    post_date = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    article = scrapy.Field(output_processor=TakeFirst())