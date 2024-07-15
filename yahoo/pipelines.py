# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Article, Session
from common_func import setup_logger
from const import LOG_LEVEL, LOG_FILE

# ロガーの設定
logger = setup_logger('news', LOG_FILE, LOG_LEVEL)

class CsvPipeline:
    """
    スクレイピングしたアイテムをCSVファイルに保存するパイプラインです。

    このパイプラインは、スパイダーの開始時にCSVファイルを開き、
    記事のタイトル、記事番号、投稿日、URL、本文を含む各アイテムを書き込みます。
    ただし、urlがすでにファイルに存在する場合、アイテムは無視されます。
    """

    def open_spider(self, spider):
        """
        CSVファイルを開き、ヘッダーを書き込みます (新規作成の場合)。
        """
        spider.flag_use_csv = True
        
        self.file = open("yahoo_news.csv", "a+", newline='', encoding='utf-8')
        self.file.seek(0)
        self.existing_urls = set(line.split(',')[3].strip() for line in self.file.readlines())
        
        # 新規作成の場合、ヘッダーを書き込む
        if self.file.tell() == 0:
            self.file.write("title,article_number,post_date,url,article\n")
        
    def close_spider(self, spider):
        """
        CSVファイルを閉じます。
        """
        self.file.close()
        
    def process_item(self, item, spider):
        """
        各アイテムを処理し、CSVファイルに書き込みます。
        ただし、urlがすでにファイルに存在する場合、アイテムは無視されます。
        """
        # 重複チェック
        if item.get('url') in self.existing_urls:
            logger.warning(f"[csv]取得した記事は既に保存済のためスキップします。リンク: {item.get('url')}")
            spider.skip_csv_count += 1
            return item

        # アイテムを書き込む
        line = f"{item.get('title')},{item.get('article_number')},{item.get('post_date')},{item.get('url')},{item.get('article')}\n"
        self.file.write(line)
        logger.info(f"[csv]記事が正常に保存されました。リンク: {item.get('url')}")
        self.existing_urls.add(item.get('url'))  # 重複チェック用にURLを追加
        return item
    
# class SQLitePipeline:
#     """
#     スクレイピングしたアイテムをSQLiteデータベースに保存するパイプラインです。

#     このパイプラインは、スパイダーの開始時にSQLiteデータベースへの接続を開き、
#     記事用のテーブルが存在しない場合は作成します。このパイプラインによって処理された
#     各アイテムは、記事テーブルに挿入されます。同じURLを持つアイテムがデータベースに
#     既に存在する場合、挿入は無視されます。これにより、各記事が一度だけ保存されることが保証されます。
#     """
#     def open_spider(self, spider):
#         """
#         SQLiteデータベース接続を開き、記事テーブルが存在しない場合は作成します。
#         """
#         self.connection = sqlite3.connect("yahoo_news.db")
#         self.cursor = self.connection.cursor()
#         self.cursor.execute("""
#             CREATE TABLE IF NOT EXISTS articles (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT,
#                 article_number TEXT,
#                 post_date TEXT,
#                 url TEXT UNIQUE,
#                 article TEXT
#             )
#         """)

#     def close_spider(self, spider):
#         """
#         変更をコミットし、SQLiteデータベース接続を閉じます。
#         """
#         self.connection.commit()
#         self.connection.close()

#     def process_item(self, item, spider):
#         """
#         各アイテムを処理し、データベースの記事テーブルに挿入します。
#         同じURLを持つアイテムが既に存在する場合、挿入は無視されます。
#         """
#         self.cursor.execute("""
#             INSERT OR IGNORE INTO articles (title, article_number, post_date, url, article) VALUES (?, ?, ?, ?, ?)
#         """, (
#             item.get('title'),
#             item.get('article_number'),
#             item.get('post_date'),
#             item.get('url'),
#             item.get('article')
#         ))
#         return item
    
class SQLAlchemyPipeline:
    """
    スクレイピングしたアイテムをSQAchemyを使用してデータベースに保存するパイプラインです。
    
    このパイプラインは、スパイダーの開始時にデータベースセッションを開き、
    記事用のテーブルが存在しない場合は作成します。このパイプラインによって処理された
    各アイテムは、記事テーブルに挿入されます。同じURLを持つアイテムがデータベースに
    既に存在する場合、挿入は無視されます。これにより、各記事が一度だけ保存されることが保証されます。
    """
    skip_DB_count = 0
    flag_use_DB = False
    
    def open_spider(self, spider):
        """
        データベースセッションを開き、記事テーブルが存在しない場合は作成します。
        """
        spider.flag_use_DB = True
        try:
            self.session = Session()
            Base.metadata.create_all(bind=self.session.get_bind())
        except SQLAlchemyError as e:
            logger.error(f"データベース接続エラー: {e}")
            raise e  # スパイダーの実行を停止するためにエラーを伝播させる

    def close_spider(self, spider):
        """
        変更をコミットし、データベースセッションを閉じます。
        """
        self.session.close()

    def process_item(self, item, spider):
        """
        各アイテムを処理し、データベースの記事テーブルに挿入します。
        同じURLを持つアイテムが既に存在する場合、挿入は無視されます。
        """
        try:
            article = Article(
                title=item.get('title'),
                article_number=item.get('article_number'),
                post_date=item.get('post_date'),
                url=item.get('url'),
                article=item.get('article')
            )
            self.session.merge(article)
            self.session.commit()
            logger.info(f"[DB]記事が正常に保存されました。リンク: {item.get('url')}")
        except SQLAlchemyError as e:
            #ユニーク成約の場合はログレベルをwarningで出力し、それ以外のエラーはログレベルをerrorで出力
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"[DB]取得した記事は既に保存済のためスキップします。リンク: {item.get('url')}")
                spider.skip_DB_count += 1
            else:
                logger.error(f"[DB]記事の保存中にエラーが発生しました。リンク: {item.get('url')}\n エラー内容: {e}")
            self.session.rollback()  # 変更をロールバック
        return item