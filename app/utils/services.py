# app/utils/services.py
import os
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

import streamlit as st
from dotenv import load_dotenv

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

def get_last_week_points(supabase, user_id: str) -> Optional[Dict[str, Any]]:
    """先週のポイント（交換可能）を取得"""
    last_week_start = get_week_start_date() - timedelta(days=7)
    try:
        response = (
            supabase.table("weekly_points")
            .select("*")
            .eq("user_id", user_id)
            .eq("week_start_date", str(last_week_start))
            .eq("exchangeable_next_week", True)
            .eq("exchanged", False)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"❌ 先週ポイント取得エラー: {e}")
        return None

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
    
    Args:
        supabase: Supabaseクライアント
        user_id: ユーザーID
        onomatopoeia_id: オノマトペID
        cat_id: 猫ID
        after_mood_id: 提案後の気分ID
        points_earned: 獲得ポイント
        situation_id: シーンID（オプション）
        comment: コメント（オプション）
        character_name: 選ばれたキャラクター名（オプション）
        rhythm_content: リズム・リセット生成内容（オプション）
        meal_content: 料理提案生成内容（オプション）
    
    Returns:
        bool: 成功時True、失敗時False
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
        return True
    except Exception as e:
        st.error(f"❌ 気分登録エラー: {e}")
        return False

# =========================
# 餌やりイベント（日次カウント）
# =========================

def get_week_feeding_count(supabase, user_id: str) -> int:
    """今週の餌やり回数を取得"""
    week_start = get_week_start_date()
    try:
        response = (
            supabase.table("weekly_feeding_count")
            .select("feed_count")
            .eq("user_id", user_id)
            .eq("week_start_date", str(week_start))
            .execute()
        )
        return response.data[0]["feed_count"] if response.data else 0
    except Exception as e:
        st.error(f"❌ 餌やり回数取得エラー: {e}")
        return 0

def increment_feeding_count(supabase, user_id: str) -> int:
    """餌やり回数をインクリメント"""
    week_start = get_week_start_date()
    now = datetime.now()
    
    try:
        # 既存レコード確認
        existing = (
            supabase.table("weekly_feeding_count")
            .select("*")
            .eq("user_id", user_id)
            .eq("week_start_date", str(week_start))
            .execute()
        )
        
        if existing.data:
            # 更新
            new_count = existing.data[0]["feed_count"] + 1
            supabase.table("weekly_feeding_count").update({
                "feed_count": new_count,
                "last_fed_at": now.isoformat()
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            # 新規作成
            supabase.table("weekly_feeding_count").insert({
                "user_id": user_id,
                "week_start_date": str(week_start),
                "feed_count": 1,
                "last_fed_at": now.isoformat()
            }).execute()
            new_count = 1
        
        # 履歴記録
        supabase.table("feeding_event_log").insert({
            "user_id": user_id,
            "week_start_date": str(week_start),
            "feed_at": now.isoformat(),
            "is_daily_feed": True
        }).execute()
        
        return new_count
    except Exception as e:
        st.error(f"❌ 餌やりカウント更新エラー: {e}")
        return 0

# =========================
# ポイント交換
# =========================

def get_food_type_by_points(points: int) -> str:
    """ポイントに応じた餌の種類を取得"""
    if points >= 101:
        return "高級マグロ"
    elif points >= 71:
        return "サーモン"
    elif points >= 31:
        return "ちゅ~る"
    else:
        return "カリカリ"

def get_next_goal_message(points: int) -> str:
    """次の目標メッセージを取得"""
    thresholds = [(31, "ちゅ~る"), (71, "サーモン"), (101, "高級マグロ")]
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