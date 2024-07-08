"""
このファイルは、ウェブスクレイピングやデータベース接続などの様々な設定値を定義しています。

定義されている主な設定値:
- BASE_URL: スクレイピング対象のベースとなるURLです。
- TOP_PICS_URL: トップニュースのピックアップされた記事のURLです。
- TOP_PICS_SELECTOR, ARTICLE_SELECTOR, LINK_TO_ARTICLE_SELECTOR, ARTICLE_CONTENT_SELECTOR, NEXT_PAGE_SELECTOR: スクレイピング時に使用するCSSセレクタです。
- TIMEOUT: リクエストのタイムアウト時間（ミリ秒）です。
- SLACK_WEBHOOK_URL: SlackのWebhook URLです。通知用に使用します。
- SQLITE_PATH: SQLiteデータベースファイルのパスです。
- MYSQL_DB_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE: MySQLデータベース接続情報です。
- MYSQL_PATH: MySQLデータベース接続用のURLです。

環境変数からデータベース接続情報やSlackのWebhook URLを読み込むため、`.env`ファイルにこれらの値を設定しておく必要があります。
"""
from dotenv import load_dotenv
load_dotenv()

import os

BASE_URL = 'https://news.yahoo.co.jp'
TOP_PICS_URL = 'https://news.yahoo.co.jp/topics/top-picks'
TOP_PICS_SELECTOR = 'div#uamods-topics'
ARTICLE_SELECTOR = 'article[id*=uamods]'
LINK_TO_ARTICLE_SELECTOR = 'a.bxbqJP'
ARTICLE_CONTENT_SELECTOR = 'div.article_body *::text'
NEXT_PAGE_SELECTOR = 'ul.jOUhIY > li:last-of-type > a::attr(href)'
TIMEOUT = 90000
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
SQLITE_PATH = os.getenv('SQLITE_PATH')

# ログの設定
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

#MYSQLの接続情報
MYSQL_DB_USER = os.getenv('MYSQL_DB_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
MYSQL_PATH = f'mysql://{MYSQL_DB_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'

#SQLiteかMYSQLかを選択
# DB_TYPE="MYSQL"
DB_TYPE="SQLITE"