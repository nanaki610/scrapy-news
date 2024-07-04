import asyncio
import scrapy
from scrapy_playwright.page import PageMethod

# Windows 以外のプラットフォームでは、デフォルトのイベントループポリシーを WindowsSelectorEventLoopPolicy に設定します
if asyncio.get_event_loop_policy() is not asyncio.WindowsSelectorEventLoopPolicy:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class NewsSpider(scrapy.Spider):
    name = 'news'
    
    def start_requests(self):
        yield scrapy.Request(
            'https://news.yahoo.co.jp/topics/top-picks',
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    # PageMethod("screenshot", path="start.png", full_page=True),  # ページ全体のスクリーンショットを撮影し、"start.png" という名前で保存します
                    PageMethod('wait_for_selector', 'div#uamods-topics'),  # 'div#uamods-topics' セレクタが表示されるまで待機します
                ]
            }
        )

    async def parse(self, response):
        print("クローリング実行")
        # playwirght で取得したページを response に変換します
        page = response.meta['playwright_page'] # Playwright のページオブジェクトを取得します
        # page.locator('div.newsFeed_item_title').click() # 記事のリンクをクリックします
        # page.get_by_text('記事全文を読む').click() # '記事全文を読む' ボタンをクリックします
        schreenshot = await page.screenshot(path="article.png", full_page=True) # ページ全体のスクリーンショットを撮影し、"article.png" という名前で保存します
        await page.close() # ページを閉じます
        
        # articles = page.locator('div#uamods-topics ul').all() # 記事のリストを取得します
        
        # for article in articles:
        #     print("クローリング実行中")
        #     yield {
        #         'title': article.locator('div.newsFeed_item_title').inner_text(),
        #     }