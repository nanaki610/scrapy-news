"""
文字列操作に関するユーティリティ関数を提供します。

- list2str: リストの要素を連結して文字列に変換し、先頭と末尾の空白を削除します。
- search_word: 文字列から指定した単語があればtrueを返します。
"""

def list2str(list):
    """
      リストを文字列に変換する。リストの各要素を連結し、先頭と末尾の空白を削除する。
    :param list: リスト
    :return: 文字列
    """
    return ''.join(list).strip().replace('\n', '').replace(' ', '')
  
def search_word(text, word):
    """
    文字列から指定した単語があればtrueを返す
    :param text: 検索対象の文字列
    :param word: 検索する単語
    :return: bool
    """
    return word in text 