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
from common_func import  post_slack, setup_logger
from scrapy import signals
from scrapy.signalmanager import dispatcher
from const import LOG_LEVEL, LOG_FILE

# ロガーの設定
# logger = setup_logger('news', 'scrapy.log', 'INFO')
logger = setup_logger('news', LOG_FILE, LOG_LEVEL)


#タイムゾーン設定
tokyo_timezone = pytz.timezone('Asia/Tokyo')

def spider_opened(spider): #スパイダーが開始したときに実行する関数
  """
  スパイダーが開始する際に実行される関数。
  スパイダーの開始時刻をログに記録します。

  Args:
    spider (Spider): 開始されたScrapyスパイダーのインスタンス。
  """
  start_time = datetime.now(tokyo_timezone).strftime('%Y/%m/%d %H:%M') #現在時刻(JST)をYYYYMMDDhhmm形式で取得
  logger.info(f"スクレイピング開始時刻: {start_time}")
  
def spider_closed(spider, reason): #スパイダーが終了したときに実行する関数
  """
  スパイダーが終了する際に実行される関数。
  スパイダーの終了時刻と終了理由をログに記録し、
  スクレイピングの結果をSlackに通知します。

  Args:
    spider (Spider): 終了したScrapyスパイダーのインスタンス。
    reason (str): スパイダーが終了した内容。
  """
  end_time = datetime.now(tokyo_timezone).strftime('%Y/%m/%d %H:%M')
  logger.info(f"[{reason}]スクレイピング終了時刻: {end_time}")
  
  slack_message = f"Yahoo Newsのスクレイピングが完了しました。\n掲載記事件数: {spider.total_articles}件/取得記事件数: {spider.fetch_count}件/登録記事件数: {spider.pass_count}件/本文取得スキップ件数: {spider.skip_count}/エラー件数: {spider.error_count}件\n"
  if spider.flag_use_csv:
    slack_message += f"csv登録済の記事件数: {spider.skip_csv_count}件\n"
  if spider.flag_use_DB:
    slack_message += f"DB登録済の記事件数: {spider.skip_DB_count}件\n"
  if spider.error_count > 0:
    slack_message += f"{spider.error_article_info}"
  post_slack(slack_message)

# Yahooニュースのスパイダーを実行
process = CrawlerProcess(settings = get_project_settings()) # Scrapyのプロジェクト設定を読み込み
dispatcher.connect(spider_opened, signal=signals.spider_opened) # スパイダーが開始したときに実行する関数を設定
dispatcher.connect(spider_closed, signal=signals.spider_closed) # スパイダーが終了したときに実行する関数を設定

process.crawl(NewsSpider) # NewsSpiderという名前のスパイダーを使用してクローリングプロセスを初期化
process.start() # クローリングプロセスを開始
