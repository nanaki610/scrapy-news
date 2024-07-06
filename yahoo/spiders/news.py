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
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

class NewsSpider(scrapy.Spider):
    """
    Yahooニュースのトップピックスからニュース記事をスクレイピングするSpiderクラス。
    """
    name = 'news'
    TOP_PICS_URL = 'https://news.yahoo.co.jp/topics/top-picks'
    TOP_PICS_SELECTOR = 'div#uamods-topics'
    ARTICLE_SELECTOR_1 = 'article#uamods-pickup'
    ARTICLE_SELECTOR_2 = 'article#uamods'
    ARTICLE_CONTENT_SELECTOR = 'div.article_body *::text'
    
    def start_requests(self):
        """
        スパイダーの最初のリクエストを生成する。
        Yahooニュースのトップピックスページにアクセスし、ページのスクリーンショットを取得し、
        特定のセレクタがロードされるのを待つ。
        """
        yield scrapy.Request(
            self.TOP_PICS_URL,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod("screenshot", path="start.png", full_page=True),
                    PageMethod('wait_for_selector', self.TOP_PICS_SELECTOR),
                ],
            },
            callback=self.start_parse,
            errback=self.errback,
        )

    async def start_parse(self, response):
        """
        Yahooニュースのトップピックスページのレスポンスを処理し、各ニュース記事に対してリクエストを行う。

        :param response: ページのレスポンス
        """
        page = response.meta.get('playwright_page')
        if page:
            await page.close() # Playwrightのページを閉じる
        
        today = get_today() # 今日の日付を取得
        
        articles = response.css('li.newsFeed_item') # Scrapyのセレクタで記事を取得
        for (index, article) in enumerate(articles):
            title = article.css('div.newsFeed_item_title::text').get() # タイトルを取得
            postDate = convert_date(article.css('time.newsFeed_item_date::text').get()) # 投稿日を取得
            url = article.css('a.newsFeed_item_link::attr(href)').get() # URLを取得
            
            # 取得した投稿日が今日ではない場合は処理を終了
            if postDate['date'] != today:
                break
            
            # 記事のリンクに移動
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', self.ARTICLE_SELECTOR_1),
                        PageMethod('click', 'a.bxbqJP'),
                        PageMethod('wait_for_selector', self.ARTICLE_SELECTOR_2),
                        PageMethod('screenshot', path=f"SS/articledetail{index}.png", full_page=True),
                    ],
                    'title': title,
                    'postDate': f"{postDate['date']}{postDate['time']}",
                    'url': url,
                },
                callback=self.parse_article,
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
            await page.close()  # コンテンツ取得後にページを閉じる

            # 記事の内容を取得。'article#uamods'は記事のHTML要素を指定するセレクタ
            selector = Selector(text=content)
            article = selector.css(self.ARTICLE_CONTENT_SELECTOR).getall()

            # 全てのデータをまとめてyield
            yield {
                'title': response.meta['title'],
                'postDate': response.meta['postDate'],
                'url': response.meta['url'],
                'article': list2str(article)
            }

    async def errback(self, failure):
        """
        リクエストが失敗した場合のエラーハンドリング。

        :param failure: 失敗したリクエストの情報
        """
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()  # 失敗したページを閉じる

        # エラーメッセージをログに記録
        logger.error(f"Request failed: {failure.request.url}, Reason: {failure.value}")