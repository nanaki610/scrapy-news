# scrapy-news

このプロジェクトは、scrapy-playwrightを使用してヤフーニュースの「主要トピックス一覧」ページの記事を収集し、csvとDBに保存するためのものです。取得した情報は **タイトル、投稿日時、記事番号、URL、本文**が含まれます。ただし、本文ページが複数ページある場合でも1ページのみ保存する仕様になります。

## プロジェクト構成

- [`run_scrapy.py`](#file:run_scrapy.py-context): スクレイピングを実行するためのスクリプトです。このスクリプトを実行することで、スクレイピングが開始されます。
- [`news.py`](#file:news.py-context): スクレイピングの対象となるウェブサイトやページを定義し、スクレイピングのロジックを実装しています。
- [`items.py`](#file:items.py-context): スクレイピングで収集するデータの構造を定義しています。Yahooニュースの記事に関する情報を格納するためのクラスが含まれます。
- [`pipelines.py`](#file:pipelines.py-context): 収集したデータの後処理や保存を行うためのパイプラインを定義しています。
- [`models.py`](#file:models.py-context): データベースのモデルを定義しています。収集したデータを保存する際に使用します。
- [`settings.py`](#file:settings.py-context): Scrapyプロジェクトの設定ファイルです。ボットの名前やパイプラインの設定などが含まれます。
- [`const.py`](#file:const.py-context): プロジェクト全体で使用する定数を定義しています。セレクターの設定値やDBの接続情報等の設定値を定義しています。
- [`middlewares.py`](#file:middlewares.py-context):Scrapyプロジェクトのミドルウェアが定義されています。ここでは、スクレイピング中に発生したエラーをSlackに通知するミドルウェアSlackNotificationMiddlewareを定義しています。
- [`common_func.py`](#file:common_func.py-context): プロジェクト全体で使用する共通の関数を定義しています。文字列の変換や日付の処理、Slackへの通知などの機能が含まれます。

## 開発環境

このプロジェクトは以下の環境で開発されています。

- Python: 3.8以上
- Scrapy: 2.11.1
- scrapy-playwright: 0.0.26

## 使い方

1. 必要なライブラリをインストールします。プロジェクトのルートディレクトリで以下のコマンドを実行してください。

    ```sh
    poetry install
    ```

2. playwrightをインストールします。

    ```sh
    poetry run playwright install
    ```

3. `run_scrapy.py`を実行してスクレイピングを開始します。

    ```sh
    poetry run python yahoo/run_scrapy.py
    ```

4. スクレイピングが完了すると、定義されたパイプラインに従ってデータが処理され、保存されます。

5. 保存データは`yahoo_news.csv`と`yahoo.db`(SQLite3選択の場合)です。また、各ページのスクリーンショットが`SS`フォルダ内に画像保存されます。


## 出力形式の選択

デフォルトではcsvファイルとDBファイルが出力されます。どちらか片方の出力を望む場合は、`settings.py`のITEM?PIPELINESの内容をコメントアウトしてください。

```
#どちらかをコメントアウトする
ITEM_PIPELINES = {
   'yahoo.pipelines.CsvPipeline': 400,
   'yahoo.pipelines.SQLAlchemyPipeline': 500,
}
```

また、DBはSQLite3かMYSQLの選択が可能です。デフォルトではSQLite3が選択されています。MYSQLの出力を希望する場合は`const.py`の以下の変数を修正してください。

```
#SQLiteかMYSQLかを選択
# DB_TYPE="MYSQL"
DB_TYPE="SQLITE"
```

取得記事は全件取得か当日の記事のみ取得か選択可能です。`const.py`の以下の変数にTrue/Falseの切り替えで設定可能です。

```
#TARGET_TODAYがTrueの場合、当日の記事のみを対象とする。Falseの場合は全件取得する。
TARGET_TODAY = False
```

## GitHub Actions

このプロジェクトでは、`scrapy.yaml` GitHub Actionsワークフローを使用して、Yahooニュースのスクレイピングとその結果をSlackに送信する自動化を実装しています。このワークフローは、以下のトリガーで実行されます：

- `main` または `dev` ブランチへのpush。
- ワークフローの手動ディスパッチ。
- 毎日日本時間の23時にスケジュールされた実行。

ワークフローのステップは以下の通りです：

1. リポジトリのコードをチェックアウト。
2. Python 3.8 環境のセットアップ。
3. Poetryのインストールと依存関係のインストール。
4. Playwrightのインストール。
5. `.env` ファイルの作成とSlack Webhook URLの設定。
6. NODE_OPTIONS環境変数を設定してメモリ不足エラーを回避しながらScrapyスクリプトを実行。
7. 成果物（`yahoo_news.csv`、`yahoo.db`、`scrapy.log`）のアップロード。
8. 成果物のダウンロードリンクを含むメッセージをSlackに送信。

このワークフローにより、ユーザーはYahooニュースのスクレイピング結果をSlack経由で受け取ることができます。

## 注意事項

データベース接続情報やSlackのWebhook URLは環境変数から読み込まれます。プロジェクトのルートディレクトリに`.env`ファイルを作成し、以下の形式で必要な情報を設定してください。
```
    SLACK_WEBHOOK_URL=SlackのWebhook URL
    SQLITE_PATH=SQLiteデータベースファイルのパス
    MYSQL_DB_USER=MySQLユーザー名
    MYSQL_PASSWORD=MySQLパスワード
    MYSQL_HOST=MySQLホスト
    MYSQL_DATABASE=MySQLデータベース名
```

また、GitHub Actionsのseacretsの設定も必要です。settings -> Seacrets andvariables -> Actionsから次の設定値を追加してください。
```
SLACK_WEBHOOK_URL=SlackのWebhook URL
```

## (補足)メモリ不足エラー対処法

scrapy実行中に**`FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory`**が発生してハングアップする場合があります。playwrightライブラリを動かすのに必要なメモリ容量がヒープ領域よりも小さいことで発生している可能性が高い為、発生時は次のように Node.js の起動オプション ---max-old-space-sizeの設定値を変更した上でscrapyを実行してください。

```
export NODE_OPTIONS=--max_old_space_size=8192 #コンピュータの利用可能なメモリサイズ以内で設定
poetry run python yahoo/run_scrapy.py
```
