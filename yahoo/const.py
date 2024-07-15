"""
このファイルは、ウェブスクレイピングやデータベース接続などの様々な設定値を定義しています。

定義されている主な設定値:
- BASE_URL: スクレイピング対象のベースとなるURLです。
- TOP_PICS_URL: トップニュースのピックアップされた記事のURLです。
- item selector: スクレイピングした記事のタイトル、投稿日、URLを取得するためのCSSセレクタです。
- other selector: スクレイピング中に使用するCSSセレクタです。
- TIMEOUT: リクエストのタイムアウト時間（ミリ秒）です。
- SLACK_WEBHOOK_URL: SlackのWebhook URLです。slack通知用に使用します。
- TARGET_TODAY: 当日の記事のみを対象とするかどうかを指定します。
- LOG_LEVEL: ログの出力レベルです。
- LOG_FILE: ログファイルのパスです。
- CSV_FILE: CSVファイルのパスです。
- DB_TYPE: データベースの種類を指定します。SQLiteまたはMySQLを選択できます。
- SQLITE_PATH: SQLiteデータベースファイルのパスです。
- MYSQL_DB_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE: MySQLデータベース接続情報です。
- MYSQL_PATH: MySQLデータベース接続用のURLです。

環境変数からデータベース接続情報やSlackのWebhook URLを読み込むため、`.env`ファイルにこれらの値を設定しておく必要があります。
"""
from dotenv import load_dotenv
load_dotenv()

import os

#URL
BASE_URL = 'https://news.yahoo.co.jp'
TOP_PICS_URL = 'https://news.yahoo.co.jp/topics/top-picks'

##selector
#item selector
TITLE = 'div.newsFeed_item_title::text'
POST_DATE = 'time.newsFeed_item_date::text'
ARTICLE_LINK = 'a.newsFeed_item_link::attr(href)'

#other selector
ARTICLES_SELECTOR = 'li.newsFeed_item'
TOP_PICS_SELECTOR = 'div#uamods-topics'
TOTAL_ARTICLES_SELECTOR = 'span.eFboGc::text'
ARTICLE_SELECTOR = 'article[id*=uamods]'
LINK_TO_ARTICLE_SELECTOR = 'a.bxbqJP'
ARTICLE_CONTENT_SELECTOR = 'div.article_body *::text'
HEADLINE_CONTENT_SELECTOR = 'section.cOJYgv *::text'
NEXT_PAGE_SELECTOR = 'ul.jOUhIY > li:last-of-type > a::attr(href)'

TIMEOUT = 90000
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

#TARGET_TODAYがTrueの場合、当日の記事のみを対象とする。Falseの場合は全件取得する。
TARGET_TODAY = False

# ログの設定
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

#csvのファイル名
CSV_FILE = 'yahoo_news.csv'

#SQLiteかMYSQLかを選択
# DB_TYPE="MYSQL"
DB_TYPE="SQLITE"

#SQLiteのパス
DB_FILE = 'yahoo.db'
SQLITE_PATH = f"sqlite:///{DB_FILE}"
#MYSQLの接続情報
MYSQL_DB_USER = os.getenv('MYSQL_DB_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
MYSQL_PATH = f'mysql://{MYSQL_DB_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
