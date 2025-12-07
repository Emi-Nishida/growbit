import os
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone

# .env 読み込み
load_dotenv(dotenv_path=".env")

# =========================
# Secrets/環境変数の取得
# =========================

def _get_supabase_creds():
    """Supabase認証情報を取得"""
    url = None
    key = None
    try:
        url = st.secrets.get("SUPABASE_URL", url)
        key = st.secrets.get("SUPABASE_ANON_KEY", key) or st.secrets.get("SUPABASE_KEY", key)
    except Exception:
        pass
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    return url, key

SUPABASE_URL, SUPABASE_KEY = _get_supabase_creds()

# =========================
# Supabase クライアント
# =========================

def get_supabase_client():
    """Supabaseクライアントを取得"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("⚠️ .env または Secrets に SUPABASE_URL / SUPABASE_KEY が設定されていません。")
        st.stop()
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"❌ Supabase接続に失敗しました: {e}")
        st.stop()

# =========================
# セッション管理
# =========================

def get_or_create_user_id() -> str:
    """ユーザーIDを取得・作成（匿名ユーザー対応）"""
    
    # ===================================================
    # 🚧 テスト用の一時的な修正
    # 📌 本番前に必ずTESTING_MODE = Falseに戻すこと!
    # ===================================================
    TESTING_MODE = True  # ← 本番前にFalseにする
    TEST_USER_ID = "7ff121b7-ea36-4e9a-b642-1cc0b189b156"
    
    if TESTING_MODE:
        if "user_id" not in st.session_state:
            st.session_state.user_id = TEST_USER_ID
            
            # Supabaseのusersテーブルに登録
            supabase = get_supabase_client()
            try:
                # 重複エラーを避けるためupsertを使用
                supabase.table("users").upsert({
                    "id": st.session_state.user_id
                }).execute()
            except Exception:
                pass
        
        return st.session_state.user_id
    # ===================================================
    # 🚧 ここまでテスト用コード
    # ===================================================
    
    # 以下、本番用のコード
    if "user_id" not in st.session_state:
        # 本来は認証機能で取得するが、今回は匿名UUID
        st.session_state.user_id = str(uuid.uuid4())
        
        # Supabaseのusersテーブルに登録
        supabase = get_supabase_client()
        try:
            supabase.table("users").insert({
                "id": st.session_state.user_id
            }).execute()
        except Exception:
            # 既に存在する場合は無視
            pass
    
    return st.session_state.user_id

# =========================
# 日付計算
# =========================

def get_week_start_date(today: Optional[date] = None) -> date:
    """週の開始日（月曜日）を取得"""
    if today is None:
        today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start

def get_month_start_date(today: Optional[date] = None) -> date:
    """月の開始日を取得"""
    if today is None:
        today = datetime.now().date()
    return date(today.year, today.month, 1)

def get_current_season() -> str:
    """現在の季節を取得"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"

# =========================
# マスタデータ取得
# =========================

def get_all_onomatopoeia(supabase) -> List[Dict[str, Any]]:
    """全オノマトペを取得"""
    try:
        response = supabase.table("onomatopoeia_master").select("*").order("id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ オノマトペ取得エラー: {e}")
        return []

def get_all_situations(supabase) -> List[Dict[str, Any]]:
    """全シーンを取得"""
    try:
        response = supabase.table("situation_master").select("*").order("id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ シーン取得エラー: {e}")
        return []

def get_cat_by_onomatopoeia_id(supabase, onomatopoeia_id: int) -> Optional[Dict[str, Any]]:
    """オノマトペIDから対応する猫を取得"""
    try:
        response = (
            supabase.table("cat_master")
            .select("*")
            .eq("onomatopoeia_id", onomatopoeia_id)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"❌ 猫マスタ取得エラー: {e}")
        return None

def get_all_feeds(supabase) -> List[Dict[str, Any]]:
    """
    全餌マスタ（名前とポイント）を取得
    """
    try:
        response = (
            supabase.table("feed_master")
            .select("id, feed_name, feed_point")
            .order("feed_point") # ポイントが低い順に並べ替え
            .execute()
        )
        # feed_masterのid=1(カリカリ=0pt)はイベント対象外と仮定し、ここでは全量取得
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ 餌マスタ取得エラー: {e}")
        return []

# =========================
# ポイント管理
# =========================

def get_current_week_points(supabase, user_id: str) -> int:
    """今週の累積ポイントを取得"""
    week_start = get_week_start_date()
    try:
        response = (
            supabase.table("mood_register_log")
            .select("points_earned")
            .eq("user_id", user_id)
            .gte("created_at", f"{week_start}T00:00:00")
            .execute()
        )
        if response.data:
            return sum(item["points_earned"] for item in response.data)
        return 0
    except Exception as e:
        st.error(f"❌ ポイント取得エラー: {e}")
        return 0

# =========================
# 気分登録
# =========================

def register_mood(
    supabase,
    user_id: str,
    onomatopoeia_id: int,
    cat_id: str,
    after_mood_id: int,
    points_earned: int,
    situation_id: Optional[int] = None,
    comment: Optional[str] = None,
    character_name: Optional[str] = None,
    rhythm_content: Optional[Dict[str, Any]] = None,
    meal_content: Optional[Dict[str, Any]] = None
) -> bool:
    """
    気分を登録
    """
    try:
        data = {
            "user_id": user_id,
            "onomatopoeia_id": onomatopoeia_id,
            "cat_id": cat_id,
            "after_mood_id": after_mood_id,
            "points_earned": points_earned,
            "situation_id": situation_id,
            "comment": comment
        }
        
        # 追加データがあれば含める
        if character_name:
            data["character_name"] = character_name
        if rhythm_content:
            data["rhythm_content"] = rhythm_content
        if meal_content:
            data["meal_content"] = meal_content
        
        supabase.table("mood_register_log").insert(data).execute()

        # === weekly_points 更新処理 20251206石原追加===
        now = datetime.now(timezone.utc)
        week_start_date = get_week_start_date(now)

        existing_weekly = (
            supabase.table("weekly_points")
            .select("*")
            .eq("user_id", user_id)
            .eq("week_start_date", str(week_start_date))
            .execute()
        )

        if existing_weekly.data:
            # レコードが存在する場合 → 更新
            current_points = existing_weekly.data[0]["total_points"]
            new_points = current_points + points_earned
            supabase.table("weekly_points").update({
                "total_points": new_points,
                "updated_at": now.isoformat()
            }).eq("id", existing_weekly.data[0]["id"]).execute()
        else:
            # レコードが存在しない場合 → 新規作成
            supabase.table("weekly_points").insert({
                "user_id": user_id,
                "week_start_date": str(week_start_date),
                "total_points": points_earned,
                "exchangeable_next_week": True,
                "exchangeable": False,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }).execute()

        return True
    except Exception as e:
        st.error(f"❌ 気分登録エラー: {e}")
        return False

# =========================
# ポイント交換
# =========================

def get_food_type_by_points(points: int) -> str:
    """
    ポイントに応じた餌の種類を取得（最高達成ランク）
    
    【修正点】: 新しいポイント設計 (10, 30, 60, 100) に対応
    """
    # 100pt以上で「高級マグロ」がアンロック
    if points >= 100:
        return "高級マグロ"
        
    # 60pt以上で「サーモン」がアンロック
    elif points >= 60:
        return "サーモン"
        
    # 30pt以上で「ちゅ〜る」がアンロック
    elif points >= 30:
        return "ちゅ〜る"
        
    # 10pt以上で「カリカリ」がアンロック
    elif points >= 10:
        return "カリカリ"
        
    # 10pt未満の場合
    else:
        return "カリカリ"

def get_next_goal_message(points: int) -> str:
    """
    次の目標メッセージを取得
    
    【修正点】: 新しいポイント設計 (10, 30, 60, 100) に対応
    """
    # 目標達成に必要なポイントとその名前
    # (目標ポイント, 餌の名前)
    thresholds = [(10, "カリカリ"), (30, "ちゅ〜る"), (60, "サーモン"), (100, "高級マグロ")]
    
    for threshold, food_name in thresholds:
        if points < threshold:
            remaining = threshold - points
            return f"💡 あと{remaining}ptで「{food_name}」！"
            
    return "🎉 最高ランク達成！猫様大喜び！"

# =========================
# 月次サマリ（振り返り用）
# =========================

def get_month_summary(supabase, user_id: str) -> Dict[str, Any]:
    """今月のサマリを取得"""
    month_start = get_month_start_date()
    
    try:
        # 今月の記録件数とポイント
        response = (
            supabase.table("mood_register_log")
            .select("points_earned")
            .eq("user_id", user_id)
            .gte("created_at", f"{month_start}T00:00:00")
            .execute()
        )
        
        total_records = len(response.data) if response.data else 0
        total_points = sum(item["points_earned"] for item in response.data) if response.data else 0
        
        return {
            "total_records": total_records,
            "total_points": total_points
        }
    except Exception as e:
        st.error(f"❌ 月次サマリ取得エラー: {e}")
        return {"total_records": 0, "total_points": 0}

# =========================
# 週次餌やりイベント関連
# =========================

def get_last_week_points(supabase, user_id: str) -> int:
    """
    先週の合計ポイントを取得
    """
    today = datetime.now().date()
    this_week_start = get_week_start_date(today)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)
    
    try:
        response = (
            supabase.table("mood_register_log")
            .select("points_earned")
            .eq("user_id", user_id)
            .gte("created_at", f"{last_week_start}T00:00:00")
            .lte("created_at", f"{last_week_end}T23:59:59")
            .execute()
        )
        
        if response.data:
            return sum(item["points_earned"] for item in response.data)
        return 0
    except Exception as e:
        st.error(f"❌ 先週ポイント取得エラー: {e}")
        return 0


def has_fed_this_week(supabase, user_id: str) -> bool:
    """
    今週すでに週次餌やりをしたかチェック
    """
    week_start = get_week_start_date()
    
    try:
        response = (
            supabase.table("feeding_event_log")
            .select("feed_id")
            .eq("user_id", user_id)
            .gte("feed_at", f"{week_start}T00:00:00")
            .execute()
        )
        
        if not response.data:
            return False
        
        # feed_id >= 2 (ちゅ〜る以上)が週次イベントの餌と仮定
        weekly_feeds = [log for log in response.data if log.get("feed_id", 1) >= 2]
        return len(weekly_feeds) > 0
        
    except Exception as e:
        st.error(f"❌ 餌やり済みチェックエラー: {e}")
        return False


def get_feed_point_by_id(supabase, feed_id: int) -> int:
    """
    餌IDから必要ポイントを取得
    """
    try:
        response = (
            supabase.table("feed_master")
            .select("feed_point")
            .eq("id", feed_id)
            .execute()
        )
        
        if response.data:
            return response.data[0]["feed_point"]
        return 0
        
    except Exception as e:
        st.error(f"❌ 餌ポイント取得エラー: {e}")
        return 0

def get_feeding_history(supabase, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    餌やり履歴を取得
    """
    try:
        response = (
            supabase.table("feeding_event_log")
            .select("feed_at, feed_id, feed_master(feed_name, feed_point)")
            .eq("user_id", user_id)
            .gte("feed_id", 2)  # 週次イベントのみ(カリカリ除外)
            .order("feed_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"❌ 履歴取得エラー: {e}")
        return []

def execute_weekly_feeding_event(supabase, user_id: str, feed_id: int) -> bool:
    """
    週次餌やりイベントを実行
    """
    try:
        supabase.table("feeding_event_log").insert({
            "user_id": user_id,
            "feed_id": feed_id,
            "feed_at": datetime.now().isoformat()
        }).execute()
        
        return True
        
    except Exception as e:
        st.error(f"❌ 餌やりエラー: {e}")
        return False


def initialize_weekly_points_if_needed(supabase, user_id: str) -> bool:
    """
    今週のweekly_pointsレコードを作成（存在しない場合のみ）
    """
    today = datetime.now().date()
    week_start = get_week_start_date(today)
    
    try:
        # 既存レコードをチェック
        response = (
            supabase.table("weekly_points")
            .select("id")
            .eq("user_id", user_id)
            .eq("week_start_date", week_start.isoformat())
            .execute()
        )
        
        if response.data:
            return True  # 既に存在
        
        # 今週分を作成（初期値0）
        supabase.table("weekly_points").insert({
            "user_id": user_id,
            "week_start_date": week_start.isoformat(),
            "total_points": 0
        }).execute()
        
        return True
        
    except Exception as e:
        st.error(f"❌ weekly_points初期化エラー: {e}")
        return False

def get_weekly_balance(supabase, user_id: str) -> int:
    """
    今週の餌やり可能残高を取得（先週分のポイント）
    """
    today = datetime.now().date()
    this_week_start = get_week_start_date(today)
    last_week_start = this_week_start - timedelta(days=7)
    
    try:
        # 先週のweekly_pointsを取得
        response = (
            supabase.table("weekly_points")
            .select("total_points")
            .eq("user_id", user_id)
            .eq("week_start_date", last_week_start.isoformat())
            .execute()
        )
        
        if response.data:
            return response.data[0]["total_points"]
        
        # なければ先週分を集計して作成
        last_week_points = get_last_week_points(supabase, user_id)
        
        if last_week_points > 0:
            supabase.table("weekly_points").insert({
                "user_id": user_id,
                "week_start_date": last_week_start.isoformat(),
                "total_points": last_week_points
            }).execute()
        
        return last_week_points
        
    except Exception as e:
        st.error(f"❌ 残高取得エラー: {e}")
        return 0


def deduct_weekly_balance(supabase, user_id: str, points: int) -> bool:
    """
    残高からポイントを差し引く
    """
    today = datetime.now().date()
    this_week_start = get_week_start_date(today)
    last_week_start = this_week_start - timedelta(days=7)
    
    try:
        # 現在の残高を取得
        response = (
            supabase.table("weekly_points")
            .select("id, total_points")
            .eq("user_id", user_id)
            .eq("week_start_date", last_week_start.isoformat())
            .execute()
        )
        
        if not response.data:
            st.error("❌ 残高データが見つかりません")
            return False
        
        record = response.data[0]
        current_balance = record["total_points"]
        
        if current_balance < points:
            st.error(f"❌ 残高不足です（残高: {current_balance}pt、必要: {points}pt）")
            return False
        
        # 残高を更新
        new_balance = current_balance - points
        supabase.table("weekly_points").update({
            "total_points": new_balance
        }).eq("id", record["id"]).execute()
        
        return True
        
    except Exception as e:
        st.error(f"❌ 残高更新エラー: {e}")
        return False

# app/utils/services.py (追記・新規追加)

import urllib.parse

def generate_meal_suggestion_link(keyword: str, service: str) -> str:
    """
    提案された軽食キーワードに基づいて、外部サービスの検索URLを生成する。
    
    :param keyword: 検索に使用するキーワード（例: "レンジでホットヨーグルト"）
    :param service: 遷移先サービス ('amazon' または 'uber_eats')
    :return: 検索URL
    """
    
    # キーワードのURLエンコード処理
    # キーワードが None の場合や空文字の場合に備えてフォールバックを設定
    safe_keyword = keyword if keyword else "軽食"
    encoded_keyword = urllib.parse.quote_plus(safe_keyword)
    
    if service == "amazon":
        # Amazon検索のURL（主に材料購入を想定）
        # 注: アフィリエイトタグなどは除外
        return f"https://www.amazon.co.jp/s?k={encoded_keyword}"
    
    elif service == "uber_eats":
        # Uber EatsのWeb検索URL（完成品の注文を想定）
        # ユーザーの現在地は不明だが、Webページに誘導することで現在地に基づく店舗検索を促す
        return f"https://www.ubereats.com/search?q={encoded_keyword}"
        
    else:
        # 想定外のサービスの場合はGoogle検索にフォールバック
        return f"https://www.google.com/search?q={encoded_keyword}"