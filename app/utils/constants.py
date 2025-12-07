# app/utils/constants.py
# -*- coding: utf-8 -*-

"""
前向きスイッチアプリで使用する定数を集約するモジュール。
UI/UX、ポイント、絵文字、カテゴリ、ページ設定などを一元管理します。
"""

from typing import Dict, Mapping

# =========================
# 餌の種類と必要ポイント
# =========================
# 修正点:
# - "カリカリ": 10 の後にカンマを追加（構文エラー解消）

FOOD_THRESHOLDS: Dict[str, int] = {
    "カリカリ": 10,
    "ちゅ〜る": 30,
    "サーモン": 60,
    "高級マグロ": 100,
}

# 餌の絵文字
FOOD_EMOJIS: Dict[str, str] = {
    "カリカリ": "🍚",
    "ちゅ〜る": "🍥",
    "サーモン": "🐟",
    "高級マグロ": "🍣",
}

# 猫の表情（餌に応じて変化）
CAT_EXPRESSIONS: Dict[str, str] = {
    "カリカリ": "😺",
    "ちゅ〜る": "😸",
    "サーモン": "😹😹",
    "高級マグロ": "😻😻😻",
}

# =========================
# 気分変化後のマスタ（ポイント対応）
# =========================

AFTER_MOOD_CONFIG: Dict[int, Dict[str, object]] = {
    1: {"label": "😐 変わらない", "points": 5, "description": "試してみたけど、気分は変わらなかった"},
    2: {"label": "🙂 少し楽になった", "points": 10, "description": "ちょっとだけ前向きになれた"},
    3: {"label": "😊 スッキリした!", "points": 20, "description": "気持ちが切り替わって、やる気が出た！"},
}

# =========================
# オノマトペの絵文字マッピング
# =========================

ONOMATOPOEIA_EMOJIS: Dict[str, str] = {
    "しゃきっ": "💪",
    "きびきび": "⚡",
    "のびのび": "🌸",
    "るんるん": "🎵",
    "ぼんやり": "☁️",
    "だらだら": "😪",
    "そわそわ": "😰",
    "まあまあ": "🙂",
    "うとうと": "💤",
    "ぐったり": "🌀",
    "びくびく": "😨",
    "いらいら": "😠",
}

# =========================
# カテゴリ別の色設定（UI用）
# =========================

CATEGORY_COLORS: Dict[str, str] = {
    "憂鬱": "#9B59B6",  # 紫
    "疲労": "#E74C3C",  # 赤
    "不安": "#3498DB",  # 青
    "退屈": "#F39C12",  # オレンジ
}

# カテゴリ別の絵文字
CATEGORY_EMOJIS: Dict[str, str] = {
    "憂鬱": "😔",
    "疲労": "😫",
    "不安": "😰",
    "退屈": "😑",
}

# =========================
# ページ設定
# =========================

PAGE_CONFIG: Dict[str, str] = {
    "page_title": "🐱 前向きスイッチアプリ",
    "page_icon": "🐱",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

# =========================
# メッセージテンプレート
# =========================

ENCOURAGEMENT_MESSAGES: Dict[str, str] = {
    "low": "少しずつでも大丈夫！猫様が見守ってるよ 🐱",
    "medium": "いい調子！この調子で続けよう 😺",
    "high": "すごい！猫様も大喜びだよ！🎉",
}

# =========================
# 週間餌やりの目標
# =========================

WEEKLY_FEEDING_TARGET: int = 7  # 週7回（毎日）


# =========================
# 便利ユーティリティ（定数の健全性チェック）
# =========================

def validate_constants() -> None:
    """
    定数の整合性を軽くチェックする。
    - FOOD_THRESHOLDS と FOOD_EMOJIS/CAT_EXPRESSIONS のキー一致
    - CATEGORY_COLORS と CATEGORY_EMOJIS のキー一致
    - AFTER_MOOD_CONFIG の必須キー存在
    例外を投げず、必要ならログ用途で呼び出す想定。
    """
    food_keys = set(FOOD_THRESHOLDS.keys())
    assert food_keys == set(FOOD_EMOJIS.keys()), "FOOD_EMOJIS のキーが FOOD_THRESHOLDS と一致しません"
    assert food_keys == set(CAT_EXPRESSIONS.keys()), "CAT_EXPRESSIONS のキーが FOOD_THRESHOLDS と一致しません"

    category_keys = set(CATEGORY_COLORS.keys())
    assert category_keys == set(CATEGORY_EMOJIS.keys()), "CATEGORY_EMOJIS のキーが CATEGORY_COLORS と一致しません"

    for level, cfg in AFTER_MOOD_CONFIG.items():
        assert isinstance(level, int), "AFTER_MOOD_CONFIG のキーは int である必要があります"
        for required in ("label", "points", "description"):
            assert required in cfg, f"AFTER_MOOD_CONFIG[{level}] に {required} がありません"
        assert isinstance(cfg["points"], int) and cfg["points"] >= 0, f"AFTER_MOOD_CONFIG[{level}].points は0以上のintが必要です"