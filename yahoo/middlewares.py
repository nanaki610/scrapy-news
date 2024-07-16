# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import scrapy
from scrapy_playwright.page import PageMethod

from common_func import post_slack
from yahoo.const import ARTICLE_SELECTOR, TIMEOUT, TOP_PICS_SELECTOR, TOP_PICS_URL
from spiders.news import NewsSpider

class YahooSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class YahooDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

class ScrapyRetryMiddleware:
    """
    スクレイピング中に発生したエラーをSlackに通知するミドルウェア。

    このミドルウェアは、スクレイピングプロセス中に発生したエラーを捕捉し、
    設定されたSlackチャンネルにエラー情報を送信します。エラー情報には、
    エラーの内容、現在のリトライ回数、設定された最大リトライ回数、
    およびエラーが発生したURLが含まれます。

    Attributes:
        crawler (Crawler): ScrapyのCrawlerインスタンス。シグナルの接続に使用されます。

    Methods:
        from_crawler(cls, crawler): クラスメソッド。Crawlerインスタンスを受け取り、インスタンスを初期化してシグナルを接続します。
        spider_error(self, failure, response, spider): エラーが発生した際に呼び出されるメソッド。エラー情報をSlackに通知します。
    """
    retry_times = 0
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_error, signal=signals.spider_error)
        return s

    def spider_error(self, failure, response, spider):
        print("spider_error")
        max_retry_times = spider.settings.get('RETRY_TIMES')
        #現在のリトライ回数を取得
        # retry_times = response.meta.get('retry_times')
        
        if self.retry_times < max_retry_times:
            self.retry_times += 1
            post_slack(f"スクレイピング中にエラーが発生し為リトライします。エラー内容: {failure.getErrorMessage()}\nリトライ回数: {self.retry_times}/{max_retry_times}\nURL: {response.url}")
            spider.logger.info(f"Retrying ({self.retry_times}/{max_retry_times}) for {response.url}")
            
            #statusによってscrapy.Requestのselectorとcallbackメソッドを変更
            if spider.status == "start_requests":
                selector = TOP_PICS_SELECTOR
                callback = spider.start_parse
            elif spider.status == "start_parse":
                selector = ARTICLE_SELECTOR
                callback = spider.parse_headline
            elif spider.status == "start_parse_next_page":
                selector = TOP_PICS_SELECTOR
                callback = spider.start_parse
            elif spider.status == "parse_headline":
                selector = ARTICLE_SELECTOR
                callback = spider.parse_article
            elif spider.status == "parse_article":
                selector = ARTICLE_SELECTOR
                callback = spider.parse_article
            
            #リトライするためのリクエストを作成
            return scrapy.Request(
                TOP_PICS_URL,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', selector, timeout=TIMEOUT),
                    ],
                    # 'title': response.meta['title'],
                    # 'article_number': response.meta['article_number'],
                    # 'post_date': response.meta['post_date'],
                    # 'url': response.url,
                    'retry_times': self.retry_times,
                },
                callback=NewsSpider.start_parse,
                errback=NewsSpider.errback,
                dont_filter=True,
            )

        else:
            post_slack(f"スクレイピング中にエラーが発生したため終了します。エラー内容: {failure.getErrorMessage()}\nリトライ回数: {self.retry_times}/{max_retry_times}\nURL: {response.url}")
            spider.logger.error(f"Giving up on {response.url} after {self.retry_times} retries")
            
