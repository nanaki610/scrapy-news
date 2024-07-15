"""
このモジュールは、ニュース記事のデータモデルを定義しています。

`Article` クラスは、ニュース記事の情報を表すモデルで、
記事のID、タイトル、記事番号、投稿日、URL、および記事本文を属性として持ちます。
記事の本文は、特定のリンクのセレクターが特殊であるため、取得に失敗する可能性があることから、NULLを許可しています。

データベース接続とテーブル作成のためのエンジンとセッションの設定は、
実際のデータベース接続情報に基づいて適宜調整する必要があります。
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from const import MYSQL_PATH, SQLITE_PATH, DB_TYPE

Base = declarative_base()

class Article(Base):
	"""
	ニュース記事のデータモデルを表すクラス。

	このクラスは、ニュース記事の各種情報をデータベースに格納するためのモデルです。
	SQLAlchemyのORM機能を利用して、データベーステーブルとして定義されます。

	Attributes:
		id (Integer): 記事の一意なID。主キーとして自動インクリメントされます。
		title (String): 記事のタイトル。NULLを許可しません。
		article_number (String): 記事の番号または識別子。NULLを許可しません。
		post_date (String): 記事の投稿日。DateTime型ではなく、特定のフォーマットの文字列として格納されます。NULLを許可しません。
		url (String): 記事のURL。一意である必要があり、NULLを許可しません。
		article (Text): 記事の本文。特定のリンクのセレクターが特殊である場合、取得に失敗することがあるため、NULLを許可します。
	"""
	__tablename__ = 'articles'
	
	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(String(255), nullable=False)
	article_number = Column(String(255), nullable=False)
	# post_date = Column(DateTime, nullable=False)
	post_date = Column(String(12), nullable=False)
	url = Column(String(255), unique=True, nullable=False)
	article = Column(Text, nullable=True)
# 記事のリンクによってはセレクターが特殊な場合があり、記事の取得に失敗することがあるため、articleはNULLを許可する

# データベース接続とテーブル作成のためのエンジンとセッションを設定する部分は、
# 実際のデータベース接続情報に基づいて適宜調整してください。
if DB_TYPE == "SQLITE":
	engine = create_engine(SQLITE_PATH) #sqlite3を使う場合
elif DB_TYPE == "MYSQL":
	engine = create_engine(MYSQL_PATH) #MySQLを使う場合
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)