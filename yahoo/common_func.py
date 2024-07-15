"""
common_func.py
共通の関数をまとめたモジュール。
このモジュールは以下の関数を含みます:
- list2str(list): リストを文字列に変換します。
- str2int(text): 文字列を整数に変換します。
- search_word(text, word): 文字列から指定した単語があればtrueを返します。
- convert_date(refDate): 指定された日時文字列をMMDDhhmm形式に変換します。
- get_today(): 現在の日付をMMDD形式で取得します。
- post_slack(text): Slackにメッセージを投稿します。
- setup_logger(logger_name='python', log_file='execute.log', level=logging.INFO): ロガーを設定し、ログファイルを準備します。
"""
import requests
import json
from datetime import datetime
import pytz
import logging
import logging.handlers
from const import SLACK_WEBHOOK_URL

def list2str(list):
    """
      リストを文字列に変換する。リストの各要素を連結し、先頭と末尾の空白を削除する。
    :param list: リスト
    :return: 文字列
    """
    return ''.join(list).strip().replace('\n', '').replace(' ', '')

def str2int(text):
    """
    文字列を整数に変換する。変換できない場合はNoneを返す。
    :param text: 変換する文字列
    :return: 整数|None
    """
    try:
        return int(text)
    except ValueError:
        return None
  
def search_word(text, word):
    """
    文字列から指定した単語があればtrueを返す
    :param text: 検索対象の文字列
    :param word: 検索する単語
    :return: bool
    """
    return word in text 
  

def convert_date(refDate):
    """
    "月/日(曜日) hh:mm"形式の引数の日時をMMDDhhmm形式に変換する関数

    :param refDate (str): 変換対象の日時文字列
    :return: dict: 変換後の日付と時刻を含む辞書、または不正な形式の場合はNone
    """
    try:
        date, time = refDate.split('(')[0], refDate.split(')')[1].split()[0]
        month, day = date.split('/')[0].zfill(2), date.split('/')[1].zfill(2)
        hour, minute = time.split(':')[0].zfill(2), time.split(':')[1].zfill(2)
        return {'date': f'{month}{day}', 'time': f'{hour}{minute}'}
    except ValueError as e:
        # 不正な日付形式の場合のエラーハンドリング
        print(f"Error 不正な日付形式: {e}")
        return None

def get_today():
    """
    現在の日付をMMDD形式で取得する関数

    :return str: 現在の日付をMMDD形式で表した文字列
    """
    today = datetime.now(pytz.timezone('Asia/Tokyo'))
    return today.strftime('%m%d')
  
def post_slack(text="test投稿"):
    """
    SLACK_WEBHOOK_URLに指定されたURLにPOSTリクエストを送信し、メッセージを投稿する関数

    :param text (str): 投稿するメッセージ
    :return: None
    """
    # SlackのWebhook URL
    web_hook_url = SLACK_WEBHOOK_URL

    # Slackに投稿するメッセージ
    message = {
        "text": text
    }

    # SlackにPOSTリクエストを送信
    try:
        requests.post(web_hook_url, data=json.dumps(message))
    except requests.exceptions.RequestException as e:
        print(f"Slackへの投稿に失敗しました: {e}")
        
def setup_logger(logger_name='python', log_file='execute.log', level='INFO'):
    """
    特定のロガーのログレベルを設定し、ログファイルを準備する関数。

    :param logger_name: 設定するロガーの名前。
    :param log_file: ログを保存するファイルのパス。
    :param level: 設定するログレベル。
    :return: logger: 設定されたロガー
    """
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_levels[level])
    
    if not logger.hasHandlers(): # ハンドラが未設定の場合のみ設定
        handler = logging.FileHandler(filename=log_file, encoding='utf-8')
        # handler = logging.handlers.RotatingFileHandler(filename=log_file, maxBytes=100000, backupCount=5, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

#単体で実行された場合はslackにテスト投稿を行う
if __name__ == "__main__":
    post_slack("common_func.pyのテスト投稿です。")