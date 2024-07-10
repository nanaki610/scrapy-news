import os
import sys
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from common_func import setup_logger

# 現在のファイルのディレクトリパスを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# 親ディレクトリをsys.pathに追加
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    
from const import LOG_LEVEL, LOG_FILE, BASE_URL, TOP_PICS_URL, TOP_PICS_SELECTOR, ARTICLE_SELECTOR, LINK_TO_ARTICLE_SELECTOR, NEXT_PAGE_SELECTOR, ARTICLE_CONTENT_SELECTOR, TIMEOUT
from common_func import convert_date, get_today, list2str, post_slack
from items import YahooItem

# ロガーの設定
# logger = setup_logger('news', 'scrapy.log', 'INFO')
logger = setup_logger('news', LOG_FILE, LOG_LEVEL)

class NewsSpider(scrapy.Spider):
    """
    Yahooニュースのトップピックスからニュース記事をスクレイピングするSpiderクラス。
    """
    name = 'news'
    pass_count = 0 # 取得記事数
    error_count = 0 # エラー記事数
    page_number = 1
    article_number = 1
    flag_today_article = True

    def start_requests(self):
        """
        スパイダーの最初のリクエストを生成する。
        Yahooニュースのトップピックスページにアクセスし、ページのスクリーンショットを取得し、
        Yahooニュースのトップピックスページのセレクタがロードされるのを待つ。
        """
        yield scrapy.Request(
            TOP_PICS_URL,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod("screenshot", path="start.png", full_page=True),
                    PageMethod('wait_for_selector', TOP_PICS_SELECTOR, timeout=TIMEOUT),
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
        logger.info("start_parse")
        page = response.meta.get('playwright_page')
        if page:
            screenshot = await page.screenshot(path=f"SS/page{self.page_number}.png", full_page=True)
        await page.close() # Playwrightのページを閉じる
        
        today = get_today() # 今日の日付を取得
        
        articles = response.css('li.newsFeed_item') # Scrapyのセレクタで記事を取得
        for (index, article) in enumerate(articles):
            self.article_number = index + 1
            
            title = article.css('div.newsFeed_item_title::text').get() # タイトルを取得
            article_number = f"{self.page_number}-{self.article_number}" # 記事番号を取得
            post_date = convert_date(article.css('time.newsFeed_item_date::text').get()) # 投稿日を取得
            url = article.css('a.newsFeed_item_link::attr(href)').get() # URLを取得
            
            # 取得した投稿日が今日ではない場合は処理を終了
            # if post_date['date'] != today:
            #     self.flag_today_article = False
            #     break
            
            # 記事のリンクに移動
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', ARTICLE_SELECTOR, timeout=TIMEOUT),
                        PageMethod('click', LINK_TO_ARTICLE_SELECTOR),
                        PageMethod('wait_for_selector', ARTICLE_SELECTOR, timeout=TIMEOUT),
                    ],
                    'title': title,
                    'article_number': article_number,
                    'post_date': f"{post_date['date']}{post_date['time']}",
                    'url': url,
                },
                callback=self.parse_article,
                errback=self.errback,
            )
            
        # 次のページがある場合はリクエストを送信
        next_page_selector = response.css(NEXT_PAGE_SELECTOR).get()
        if next_page_selector and self.flag_today_article:
            self.page_number += 1
            next_url = BASE_URL + next_page_selector
            yield scrapy.Request(
                next_url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods' : [
                        PageMethod('wait_for_selector', TOP_PICS_SELECTOR, timeout=TIMEOUT),
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
        logger.info("parse_article")
        page = response.meta.get('playwright_page')
        
        if page:
            # 記事の内容を取得する前にページのコンテンツを取得
            content = await page.content()

            # 記事の内容を取得。'article#uamods'は記事のHTML要素を指定するセレクタ
            selector = Selector(text=content)
            try:
                article = selector.css(ARTICLE_CONTENT_SELECTOR).getall()
                article = list2str(article)
            except Exception as e:
                logger.warning("この記事のセレクターは特殊のため本文取得をスキップします",e)
                article = "-"
                pass
                
            # ItemLoaderを使ってデータを格納
            loader = ItemLoader(item=YahooItem(), response=response)
            loader.add_value('title', response.meta['title'])
            loader.add_value('article_number', response.meta['article_number'])
            loader.add_value('post_date', response.meta['post_date'])
            loader.add_value('url', response.meta['url'])
            loader.add_value('article', article)
            yield loader.load_item()
            
            self.pass_count += 1 # 取得記事数をカウント
        await page.close()  # コンテンツ取得後にページを閉じる

    async def errback(self, failure):
        """
        リクエストが失敗した場合のエラーハンドリング。
        ページのスクリーンショットを取得し、エラーメッセージをログに記録する。

        :param failure: 失敗したリクエストの情報
        """
        logger.info("errback")
        page = failure.request.meta.get("playwright_page")
        if page:
            screenshot = await page.screenshot(path=f"SS/error{self.page_number}-{self.article_number}.png", full_page=True)
        await page.close()  # 失敗したページを閉じる

        # エラーメッセージをログに記録
        logger.error(f"Request failed: {failure.request.url}, Reason: {failure.value}")
        
        # ItemLoaderを使ってデータを格納。エラーが発生した場合はURL以外'Error'を格納。
        loader = ItemLoader(item=YahooItem(), response=failure.request)
        loader.add_value('title', 'Error')
        loader.add_value('article_number', 'Error')
        loader.add_value('post_date', 'Error')
        loader.add_value('url', failure.request.url)
        loader.add_value('article', 'Error')
        yield loader.load_item()
        
        post_slack(f"Yahoo Newsのスクレイピングに失敗した記事があります：{failure.request.url}")
        self.error_count += 1 # エラー記事数をカウント