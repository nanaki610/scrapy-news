"""
date_util.py
"月/日(曜日) hh:mm"形式の日時文字列をMMDDhhmm形式に変換するモジュール。
また、現在の日付をMMDD形式で取得する機能も提供します。

このモジュールは以下の関数を含みます:
- convert_date(refDate): 指定された日時文字列をMMDDhhmm形式に変換します。
- get_today(): 現在の日付をMMDD形式で取得します。
"""

from datetime import datetime
import pytz

def convert_date(refDate):
    """
    "月/日(曜日) hh:mm"形式の引数の日時をMMDDhhmm形式に変換する関数

    Parameters:
    refDate (str): 変換対象の日時文字列

    Returns:
    dict: 変換後の日付と時刻を含む辞書、または不正な形式の場合はNone
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

    Returns:
    str: 現在の日付をMMDD形式で表した文字列
    """
    today = datetime.now(pytz.timezone('Asia/Tokyo'))
    return today.strftime('%m%d')

if __name__ == "__main__":
    print("このモジュールはimport専用です。")