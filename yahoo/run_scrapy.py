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

#現在時刻(JST)をYYYYMMDDhhmm形式で取得
tokyo_timezone = pytz.timezone('Asia/Tokyo')
start_time = datetime.now(tokyo_timezone).strftime('%Y/%m/%d %H:%M')
print(f"スクレイピング開始時刻: {start_time}")

# Yahooニュースのスパイダーを実行
process = CrawlerProcess(settings=get_project_settings())
process.crawl(NewsSpider)
process.start()

end_time = datetime.now(tokyo_timezone).strftime('%Y/%m/%d %H:%M')
exect_time = (datetime.now() - datetime.strptime(start_time, '%Y/%m/%d %H:%M')).seconds / 60 # 経過時間(分)

print(f"スクレイピング終了時刻: {end_time}")
post_slack(f"Yahoo Newsのスクレイピングが完了しました。実行時間:{exect_time}分")