from datetime import datetime
import platform

def format_datetime():
  # 曜日を英語から漢字に変換する辞書
  weekday_dict = {
      'Mon': '月',
      'Tue': '火',
      'Wed': '水',
      'Thu': '木',
      'Fri': '金',
      'Sat': '土',
      'Sun': '日'
  }

  # 現在の日時を取得
  now = datetime.now()

  # 曜日を漢字に変換
  weekday_kanji = weekday_dict[now.strftime("%a")] #%aは曜日の略称。strftime()関数で曜日を取得するためのフォーマット。

  # プラットフォームに応じてフォーマットを変更
  if platform.system() == 'Windows':
      return now.strftime(f"%#m/%#d ({weekday_kanji}) %#H:%#M") # Windowsの場合
  else:
      return now.strftime(f"%-m/%-d ({weekday_kanji}) %-H:%-M") # Windows以外の場合