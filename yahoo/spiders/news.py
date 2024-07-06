import os
import sys
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
import logging

# 現在のファイルのディレクトリパスを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# 親ディレクトリをsys.pathに追加
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    
from date_util import convert_date, get_today
from str_util import list2str

# ロガーの設定
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.ERROR)

class NewsSpider(scrapy.Spider):
    """
    Yahooニュースのトップピックスからニュース記事をスクレイピングするSpiderクラス。
    """
    name = 'news'
    BASE_URL = 'https://news.yahoo.co.jp'
    TOP_PICS_URL = 'https://news.yahoo.co.jp/topics/top-picks'
    TOP_PICS_SELECTOR = 'div#uamods-topics'
    ARTICLE_SELECTOR = 'article[id*=uamods]'
    ARTICLE_CONTENT_SELECTOR = 'div.article_body *::text'
    NEXT_PAGE_SELECTOR = 'ul.jOUhIY > li:last-of-type > a::attr(href)'
    TIMEOUT = 90000
    page_number = 1
    article_number = 1
    
    def start_requests(self):
        """
        スパイダーの最初のリクエストを生成する。
        Yahooニュースのトップピックスページにアクセスし、ページのスクリーンショットを取得し、
        Yahooニュースのトップピックスページのセレクタがロードされるのを待つ。
        """
        yield scrapy.Request(
            self.TOP_PICS_URL,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod("screenshot", path="start.png", full_page=True),
                    PageMethod('wait_for_selector', self.TOP_PICS_SELECTOR, timeout=self.TIMEOUT),
                ],
            },
            callback=self.start_parse,
            errback=self.errback,
        )

    async def start_parse(self, response):
        """
        Yahooニュースのトップピックスページのレスポンスを処理し、各ニュース記事に対してリクエストを行う。
        また、次のページがある場合はリクエストを送信する。

        :param response: ページのレスポンス
        """
        print("start_parse")
        page = response.meta.get('playwright_page')
        if page:
            screenshot = await page.screenshot(path=f"SS/page{self.page_number}.png", full_page=True)
            await page.close() # Playwrightのページを閉じる
        
        today = get_today() # 今日の日付を取得
        
        articles = response.css('li.newsFeed_item') # Scrapyのセレクタで記事を取得
        for (index, article) in enumerate(articles):
            self.article_number = index + 1
            
            title = article.css('div.newsFeed_item_title::text').get() # タイトルを取得
            post_date = convert_date(article.css('time.newsFeed_item_date::text').get()) # 投稿日を取得
            url = article.css('a.newsFeed_item_link::attr(href)').get() # URLを取得
            
            # 取得した投稿日が今日ではない場合は処理を終了
            # if post_date['date'] != today:
            #     break
            
            # 記事のリンクに移動
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', self.ARTICLE_SELECTOR, timeout=self.TIMEOUT),
                        PageMethod('click', 'a.bxbqJP'),
                        PageMethod('wait_for_selector', self.ARTICLE_SELECTOR, timeout=self.TIMEOUT),
                        # PageMethod('screenshot', path=f"SS/articledetail{self.page_number}-{self.article_number}.png", full_page=True),
                    ],
                    'title': title,
                    'post_date': f"{post_date['date']}{post_date['time']}",
                    'url': url,
                },
                callback=self.parse_article,
                errback=self.errback,
            )
            
        # 次のページがある場合はリクエストを送信
        next_page_selector = response.css(self.NEXT_PAGE_SELECTOR).get()
        if next_page_selector:
            self.page_number += 1
            next_url = self.BASE_URL + next_page_selector
            yield scrapy.Request(
                next_url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods' : [
                        PageMethod('wait_for_selector', self.TOP_PICS_SELECTOR, timeout=self.TIMEOUT),
                    ],
                },
                callback=self.start_parse,
                errback=self.errback,
            )

    async def parse_article(self, response):
        """
        個別のニュース記事ページのレスポンスを処理し、記事の内容を取得する。

        :param response: ページのレスポンス
        :return: 記事のHTMLコンテンツ
        """
        print("parse_article")
        page = response.meta.get('playwright_page')
        
        if page:
            # 記事の内容を取得する前にページのコンテンツを取得
            content = await page.content()
            await page.close()  # コンテンツ取得後にページを閉じる

            # 記事の内容を取得。'article#uamods'は記事のHTML要素を指定するセレクタ
            selector = Selector(text=content)
            article = selector.css(self.ARTICLE_CONTENT_SELECTOR).getall()

            # 全てのデータをまとめてyield
            yield {
                'title': response.meta['title'],
                'article_number': f"{self.page_number}-{self.article_number}",
                'post_date': response.meta['post_date'],
                'url': response.meta['url'],
                'article': list2str(article)
            }

    async def errback(self, failure):
        """
        リクエストが失敗した場合のエラーハンドリング。
        ページのスクリーンショットを取得し、エラーメッセージをログに記録する。

        :param failure: 失敗したリクエストの情報
        """
        print("errback")
        page = failure.request.meta.get("playwright_page")
        if page:
            screenshot = await page.screenshot(path=f"SS/error{self.page_number}-{self.article_number}.png", full_page=True)
            await page.close()  # 失敗したページを閉じる

        # エラーメッセージをログに記録
        # logger.error(f"Request failed: {failure.request.url}, Reason: {failure.value}")
        print(f"Request failed: {failure.request.url}, Reason: {failure.value}")