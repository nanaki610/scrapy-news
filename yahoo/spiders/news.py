"""
Yahooニュースのトップピックスからニュース記事をスクレイピングするSpiderクラスを定義するモジュール。
"""
import asyncio
import os
import sys
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from common_func import get_this_year, setup_logger

# 現在のファイルのディレクトリパスを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# 親ディレクトリをsys.pathに追加
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    
from const import ARTICLE_LINK,  ARTICLES_SELECTOR, HEADLINE_CONTENT_SELECTOR, LOG_LEVEL, LOG_FILE, BASE_URL, POST_DATE, TARGET_TODAY, TITLE, TOP_PICS_URL, TOP_PICS_SELECTOR, ARTICLE_SELECTOR, LINK_TO_ARTICLE_SELECTOR, NEXT_PAGE_SELECTOR, ARTICLE_CONTENT_SELECTOR, TIMEOUT, TOTAL_ARTICLES_SELECTOR
from common_func import convert_date, get_today, list2str, post_slack
from items import YahooItem

# ロガーの設定
logger = setup_logger('news', LOG_FILE, LOG_LEVEL)


class NewsSpider(scrapy.Spider):
    """
    Yahooニュースのトップピックスからニュース記事をスクレイピングするSpiderクラス。
    
    スパイダーの動作：
    1. スパイダーは最初にYahooニュースのトップピックスページにアクセスし、ページのスクリーンショットを取得し、
       Yahooニュースのトップピックスページのセレクタがロードされるのを待つ。
    2. Yahooニュースのトップピックスページから各ニュース記事に対してリクエストを行い、記事の内容を取得する。
    3. 各ニュース記事のリンクがある場合は、リンクをクリックして記事の内容を取得する。
    4. 記事の内容を取得したら、記事のタイトル、記事番号、投稿日、URL、本文をItemLoaderに格納し、
       ItemLoaderを使ってデータを格納し、CSVファイルまたはデータベースに保存する。
    5. ページの最後までスクレイピングした後、次のページがある場合はリクエストを送信する。
    6. スクレイピングが完了したら、Slackにスクレイピングの結果を通知する。
    エラー発生時は、3回までリトライする。
    
    methods:
        start_requests: スパイダーの最初のリクエストを生成する。
        start_parse: Yahooニュースのトップピックスページのレスポンスを処理し、各ニュース記事に対してリクエストを行う。
        parse_headline: Yahooニュースのトップピックスページのニュース記事で、リンクがない記事の内容を取得する。
        parse_article: 個別のニュース記事ページのレスポンスを処理し、記事の内容を取得する。
        errback: リクエストが失敗した場合のエラーハンドリング。3回までリトライする。3回失敗した場合はエラー記事として保存する。
    
    Attributes:
        name (str): スパイダーの名前
        status (str): 進行中のステータス情報(メソッド名で管理)
        pass_count (int): 登録成功した記事数
        error_count (int): エラー記事数
        page_number (int): ページ番号
        article_number (int): 記事の番号
        flag_today_article (bool): 当日の記事かどうかのフラグ(const.pyのTARGET_TODAY参照)
        fetch_count (int): 現在の取得記事数
        error_article_info (str): slack通知用のエラー記事情報
        flag_use_csv (bool): CSVファイルを使用するかどうかのフラグ
        flag_use_DB (bool): データベースを使用するかどうかのフラグ
        skip_csv_count (int): CSVファイルに登録済の記事数
        skip_DB_count (int): データベースに登録済の記事数
    """
    name = 'news'
    status = ""
    pass_count = 0 # 取得記事数
    error_count = 0 # エラー記事数
    page_number = 1
    article_number = 1
    flag_today_article = True
    fetch_count = 0
    error_article_info = ""
    
    #pipelineクラスで使用
    flag_use_csv = False
    flag_use_DB = False
    skip_csv_count = 0
    skip_DB_count = 0

    def start_requests(self):
        """
        スパイダーの最初のリクエストを生成する。
        Yahooニュースのトップピックスページにアクセスし、ページのスクリーンショットを取得し、
        Yahooニュースのトップピックスページのセレクタがロードされるのを待つ。
        """
        self.status = "start_requests"
        logger.info(self.status)
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
        各ニュース記事の処理が完了したら、次のページがある場合はリクエストを送信する。

        :param response: ページのレスポンス
        """
        self.status = "start_parse"
        logger.info(self.status)
        self.total_articles = response.css(TOTAL_ARTICLES_SELECTOR).get().replace("件","") # 掲載記事数を取得
        logger.info(f"掲載記事件数: {self.total_articles}件")
        page = response.meta.get('playwright_page')
        if page:
            screenshot = await page.screenshot(path=f"SS/page{self.page_number}.png", full_page=True)
            await page.close() # Playwrightのページを閉じる
        
        today = get_today() # 今日の日付を取得
        
        articles = response.css(ARTICLES_SELECTOR) # Scrapyのセレクタで記事を取得
        for (index, article) in enumerate(articles):
            self.article_number = index + 1
            
            title = article.css(TITLE).get() # タイトルを取得
            article_number = f"{self.page_number}-{self.article_number}" # 記事番号を取得
            post_date = convert_date(article.css(POST_DATE).get()) # 投稿日を取得
            url = article.css(ARTICLE_LINK).get() # URLを取得
            
            # 取得した投稿日が今日ではない場合は処理を終了(TARGET_TODAYがTrueの場合のみ:const.py参照)
            if TARGET_TODAY and post_date['date'] != today:
                self.flag_today_article = False
                logger.info("前日の記事を取得したため終了します")
                break
            
            #年跨ぎを考慮
            if int(post_date['date']) <= int(today): #取得した記事の投稿日が今年の場合
                post_date = f"{get_this_year()}{post_date['date']}{post_date['time']}"
            else: #取得した記事の投稿日が昨年の場合
                post_date = f"{int(get_this_year())-1}{post_date['date']}{post_date['time']}"
                
            self.fetch_count += 1 # 現在の取得記事数をカウント
            logger.info(f"[start_parse]記事取得: {self.fetch_count}回目 記事番号: {article_number} タイトル: {title} 投稿日: {post_date} URL: {url}")
            
            # 記事のリンクに移動
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', ARTICLE_SELECTOR, timeout=TIMEOUT),
                    ],
                    'title': title,
                    'article_number': article_number,
                    'post_date': post_date,
                    'url': url,
                },
                callback=self.parse_headline,
                errback=self.errback,
                dont_filter=True,
            )
            await asyncio.sleep(10) # ページ遷移のために10秒待機
            
        # 次のページがある場合はリクエストを送信
        self.status = "start_parse_next_page"
        logger.info(self.status)
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
                dont_filter=True,
            )

    async def parse_headline(self, response):
        """
        Yahooニュースのトップピックスページのニュース記事で、詳細リンクがない記事の内容を取得する。
        リンクがある記事の場合は、リンクをクリックして次のparse_articleメソッドを呼び出す。

        :param response: ページのレスポンス
        """
        self.status = "parse_headline"
        logger.info(self.status)
        logger.info(f"[parse_headline]記事取得: {self.fetch_count}回目 記事番号: {response.meta['article_number']} タイトル: {response.meta['title']} 投稿日: {response.meta['post_date']} URL: {response.meta['url']}")
        page = response.meta.get('playwright_page')
        if page:
            await page.close() # Playwrightのページを閉じる
        
        # ページ内にLINK_TO_ARTICLE_SELECTORが存在するか確認
        if not response.css(LINK_TO_ARTICLE_SELECTOR):
            #存在しない場合は既に記事の詳細ページを開いているので、そのまま記事を取得
            article = response.css(HEADLINE_CONTENT_SELECTOR).get()
            # ItemLoaderを使ってデータを格納
            loader = ItemLoader(item=YahooItem(), response=response)
            loader.add_value('title', response.meta['title'])
            loader.add_value('article_number', response.meta['article_number'])
            loader.add_value('post_date', response.meta['post_date'])
            loader.add_value('url', response.meta['url'])
            loader.add_value('article', article)
            yield loader.load_item()
            self.pass_count += 1 # 取得成功した記事数をカウント
            
        else: # リンクがある場合はリンクをクリックして記事の内容を取得
            url = response.css(LINK_TO_ARTICLE_SELECTOR).attrib['href']
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # PageMethod('click', LINK_TO_ARTICLE_SELECTOR),
                        PageMethod('wait_for_selector', ARTICLE_SELECTOR, timeout=TIMEOUT),
                    ],
                    'title': response.meta['title'],
                    'article_number': response.meta['article_number'],
                    'post_date': response.meta['post_date'],
                    'url': response.meta['url'],
                },
                callback=self.parse_article,
                errback=self.errback,
                dont_filter=True,
            )

    async def parse_article(self, response):
        """
        個別のニュース記事ページのレスポンスを処理し、記事の内容を取得する。
        ただし、特殊な記事ページの場合は本文取得をスキップする。
        
        :param response: ページのレスポンス
        """
        self.status = "parse_article"
        logger.info(self.status)
        logger.info(f"[parse_article]記事取得: {self.fetch_count}回目 記事番号: {response.meta['article_number']} タイトル: {response.meta['title']} 投稿日: {response.meta['post_date']} URL: {response.meta['url']}")
        page = response.meta.get('playwright_page')
        # 記事の内容を取得する前にページのコンテンツを取得
        content = await page.content()
        selector = Selector(text=content)
        
        if page and selector.css(ARTICLE_CONTENT_SELECTOR): # 記事の内容を取得できるか確認
            # 記事の内容を取得。'article#uamods'は記事のHTML要素を指定するセレクタ
            try:
                article = selector.css(ARTICLE_CONTENT_SELECTOR).getall()
                article = list2str(article) # 記事の内容を文字列に変換
            except Exception as e:
                self.error_count += 1
                logger.warning("この記事のセレクターは特殊のため本文取得をスキップします",e)
                self.error_article_info += f"特殊な記事ページの為、本文取得をスキップしました\n{response.meta['url']}"
                article = "-"
                pass
        else:
            self.error_count += 1
            logger.warning("特殊な記事ページの為、本文取得をスキップします")
            self.error_article_info += f"特殊な記事ページの為、本文取得をスキップしました\n{response.meta['url']}"
            article = "-"
        await page.close()  # コンテンツ取得後にページを閉じる
        
        #記事の内容以外の情報をItemLoaderに格納
        loader = ItemLoader(item=YahooItem(), response=response)
        loader.add_value('title', response.meta['title'])
        loader.add_value('article_number', response.meta['article_number'])
        loader.add_value('post_date', response.meta['post_date'])
        loader.add_value('url', response.meta['url'])
        loader.add_value('article', article) # 記事の内容を格納
        yield loader.load_item() # ItemLoaderを使ってデータを格納
        self.pass_count += 1 # 取得成功した記事数をカウント

    async def errback(self, failure):
        """
        リクエストが失敗した場合のエラーハンドリング。
        ページのスクリーンショットを取得し、エラーメッセージをログに記録する。

        :param failure: 失敗したリクエストの情報
        """
        logger.info("errback")
        logger.info(f"[errback]記事取得: {self.fetch_count}回目 記事番号: {self.page_number}-{self.article_number} タイトル: {failure.request.meta.get('title')} 投稿日: {failure.request.meta.get('post_date')} URL: {failure.request.url}")
        page = failure.request.meta.get("playwright_page")
        if page:
            screenshot = await page.screenshot(path=f"SS/error{self.page_number}-{self.article_number}.png", full_page=True)
            await page.close()  # 失敗したページを閉じる

        # リトライ回数を取得
        max_retry_times = self.settings.get('RETRY_TIMES')
        retry_times = failure.request.meta.get('retry_times', 0)
        
        # エラーメッセージをログに記録
        logger.error(f"Request failed: {failure.request.url}, Reason: {failure.value}")
        
        if retry_times < max_retry_times:
            logger.info(f"エラー発生のためリトライします。URL: {failure.request.url}\nリトライ回数: {retry_times}/{max_retry_times}")
            retry_times += 1
            
            #statusによってscrapy.Requestのselectorとcallbackメソッドを変更
            if self.status == "start_requests":
                selector = TOP_PICS_SELECTOR
                callback = self.start_parse
            elif self.status == "start_parse":
                selector = ARTICLE_SELECTOR
                callback = self.parse_headline
            elif self.status == "start_parse_next_page":
                selector = TOP_PICS_SELECTOR
                callback = self.start_parse
            elif self.status == "parse_headline":
                selector = ARTICLE_SELECTOR
                callback = self.parse_article
            elif self.status == "parse_article":
                selector = ARTICLE_SELECTOR
                callback = self.parse_article
            
            yield scrapy.Request(
                failure.request.url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', selector, timeout=TIMEOUT),
                    ],
                    'title': failure.request.meta.get('title'),
                    'article_number': failure.request.meta.get('article_number'),
                    'post_date': failure.request.meta.get('post_date'),
                    'url': failure.request.url,
                    'retry_times': retry_times,
                },
                callback=callback,
                errback=self.errback,
                dont_filter=True,
            )
        else:
            self.error_article_info += f"取得失敗した記事: {failure.request.url}\n"
            logger.info(f"Yahoo Newsのスクレイピングに失敗した記事があります: {failure.request.url}")
            self.error_count += 1
            # ItemLoaderを使ってデータを格納。エラーが発生した場合はURL以外'Error'を格納。
            loader = ItemLoader(item=YahooItem(), response=failure.request)
            loader.add_value('title', 'Error')
            loader.add_value('article_number', 'Error')
            loader.add_value('post_date', 'Error')
            loader.add_value('url', failure.request.url)
            loader.add_value('article', 'Error')
            yield loader.load_item()
            retry_times = 0 # リトライ回数をリセット
