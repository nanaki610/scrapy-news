import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import pytz
from scrapy.selector import Selector

class NewsSpider(scrapy.Spider):
    name = 'news'
    
    def start_requests(self):
        yield scrapy.Request(
            'https://news.yahoo.co.jp/topics/top-picks',
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod("screenshot", path="start.png", full_page=True),
                    PageMethod('wait_for_selector', 'div#uamods-topics'),
                ],
                "callback": self.parse,
                "errback": self.errback,
            }
        )
    
    async def get_page_source(page):
        content = await page.content()
        return content

    # "月/日(曜日) hh:mm"形式の引数の日時をMMDDhhmm形式に変換する
    def convert_date(self, refDate):
        date = refDate.split('(')[0]
        time = refDate.split(')')[1].split()[0]
        # 1桁の場合は0埋めする
        month = date.split('/')[0].zfill(2)
        day = date.split('/')[1].zfill(2)
        hour = time.split(':')[0].zfill(2)
        minute = time.split(':')[1].zfill(2)
        return {'date': f'{month}{day}', 'time': f'{hour}{minute}'}
    
    #現在の日付をMMDD形式で取得する
    def get_today(self):
        today = datetime.now(pytz.timezone('Asia/Tokyo'))
        return today.strftime('%m%d')
            
    async def parse(self, response):
        page = response.meta['playwright_page']
        await page.close() # playwrigthのページを閉じる
        
        today = self.get_today() # 今日の日付を取得
        
        articles = response.css('li.newsFeed_item') # scrapyのセレクタで記事を取得
        for (index, article) in enumerate(articles):
            title = article.css('div.newsFeed_item_title::text').get() # タイトルを取得
            postDate = self.convert_date(article.css('time.newsFeed_item_date::text').get()) # 投稿日を取得
            url = article.css('a.newsFeed_item_link::attr(href)').get() # URLを取得
            
            #取得した投稿日が今日ではない場合は処理を終了
            # if postDate['date'] != today:
            #     break
            
            #記事のリンクに移動
            # article = scrapy.Request(
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'article#uamods-pickup'),
                        # PageMethod('click', '//a[contains(text(), "記事全文を読む")]', timeout=5000, wait_for='load'),
                        PageMethod('click', 'a.bxbqJP'),
                        PageMethod('screenshot', path=f"articledetail{index}.png", full_page=True),
                    ],
                    "callback": self.parse_article,
                    "errback": self.errback,
                }
            )

            # 取得したデータをyieldで返す
            yield {
                'title': title,
                'postDate': f"{postDate['date']}{postDate['time']}",
                'url': url,
                'article': article,
            }

    async def parse_article(self, response):
        page = response.meta['playwright_page']
        await page.close()
        
        #記事の内容を取得
        content = await page.content()
        selector = Selector(text=content)
        article = selector.css('article#uamods').get()
        return article
        

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()