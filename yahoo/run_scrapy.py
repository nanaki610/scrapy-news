"""
このスクリプトは、Scrapyフレームワークを使用してYahooニュースのスクレイピングを行うためのものです。
具体的には、以下の手順で動作します。

1. Scrapyのプロジェクト設定を読み込みます。
2. NewsSpiderという名前のスパイダーを使用してクローリングプロセスを初期化します。
3. クローリングプロセスを開始します。

このスクリプトを実行することで、NewsSpiderが定義するルールに従ってYahooニュースのデータを収集できます。
"""
from datetime import datetime
import pytz
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.news import NewsSpider
from common_func import  post_slack

# Yahooニュースのスパイダーを実行
process = CrawlerProcess(settings=get_project_settings())
process.crawl(NewsSpider)
process.start()

#現在時刻(JST)をYYYYMMDDhhmm形式で取得
tokyo_timezone = pytz.timezone('Asia/Tokyo')
now = datetime.now(tokyo_timezone).strftime('%Y%m%d%H%M')
post_slack(f"Yahoo Newsのスクレイピングが完了しました：{now}")