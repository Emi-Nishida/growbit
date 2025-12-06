# app/pages/4_feedback.py
import streamlit as st
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_month_summary,
)
from utils.ui import setup_page
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client

# ページ設定
setup_page(
    page_title="📊 今月の振り返り",
    page_icon="😺",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)

# Supabase接続
supabase = get_supabase_client()

# ===================================
# 今週と先週の餌ポイントを取得
# ===================================
try:
    # 関数呼び出し
    result = supabase.rpc("weekly_points_users").execute()

    # DataFrameに変換
    df = pd.DataFrame(result.data)

    # 今日の日付
    today = date.today()

    # 今週の月曜と先週の月曜を計算
    monday_this_week = today - timedelta(days=today.weekday())
    monday_last_week = monday_this_week - timedelta(weeks=1)

    # 対象ユーザーのUUID★★★後で変更
    target_user_id = get_or_create_user_id()

    # 特定ユーザーだけ抽出
    user_df = df[df["user_id"] == target_user_id]

    # 今週と先週のポイント抽出（特定ユーザーのみ）
    points_this_week = user_df.loc[user_df["week_start"] == monday_this_week.isoformat(), "total_points"].sum()
    points_last_week = user_df.loc[user_df["week_start"] == monday_last_week.isoformat(), "total_points"].sum()

    # 表示
    print("=== 今週のポイント ===")
    print(points_this_week)

    print("=== 先週のポイント ===")
    print(points_last_week)
        
except Exception as e:
        st.error(f"❌ 週次ポイント計算エラーが発生しました: {e}")

# =========================
# 生成AI分析用ロジック
# =========================    
## ---------------------------------------------
## A. ログ取得と整形のためのユーティリティ関数
## ---------------------------------------------

def fetch_user_logs_for_analysis(user_id: str, week_start_iso: str) -> List[Dict[str, Any]]:
    """
    Supabaseからユーザーの週間ログと関連する感情名を取得する
    """
    try:
        # mood_register_log からメモと作成日時を取得し、
        # after_mood_master から感情名（mood_name）を取得（外部キー結合）
        logs_response = (
            supabase.table("mood_register_log")
            .select("created_at, note, after_mood_master(mood_name)") 
            .eq("user_id", user_id)
            .gte("created_at", week_start_iso) # 今週の月曜日以降のデータをフィルタ
            .order("created_at", desc=True)
            .execute()
        )
        return logs_response.data
    
    except Exception as e:
        st.error(f"分析用ログの取得に失敗: {e}")
        return []

def format_logs_for_ai(data: List[Dict[str, Any]]) -> str:
    """取得したログデータをAI向けの一つのテキストに整形する"""
    formatted_logs = []
    for item in data:
        # タイムスタンプをYYYY-MM-DD形式に整形
        time = item['created_at'][:10] 
        # 感情名を取得（外部結合で取得できなかった場合はデフォルト値を設定）
        mood = item.get('after_mood_master', {}).get('mood_name', '不明')
        note = item.get('note', '（記述なし）')
        
        formatted_logs.append(f"日時: {time}, 感情: {mood}, 出来事/メモ: {note}")
        
    log_text = "\n".join(formatted_logs)
    return log_text


## ---------------------------------------------
## B. 生成AI API 呼び出し関数
## ---------------------------------------------

def analyze_mood_logs(logs_text: str) -> str:
    """Gemini APIを呼び出し、分析結果を返す"""
    
    # 認証情報を secrets.toml から取得
    if "OPENAI_API_KEY" not in st.secrets:
        return "🚨 OPENAI_API_KEY が secrets.toml に設定されていません。"

    try:
        client = OpenAI()

        # AIへの指示文
        system_instruction = (
            "あなたはユーザーの気分ログを分析する優秀なAIアシスタントです。 "
            "以下のオノマトペログから、ユーザーの31日間の入力した状況にともなう身体状態、感情の傾向を日本語で簡潔に分析してください。"
            "また、その状態から改善するのに最適な行動案を提案してください"
            "分析結果はMarkdown形式で、3行で出力してください。"
        )
        
        prompt = (
            f"{system_instruction}\n\n"
            f"--- [ユーザーの気分ログ（全{len(logs_text.splitlines())}件）] ---\n"
            f"{logs_text}\n"
        )

        output_analysis_result = client.models.generate_content(
            model='gpt-5 nano',
            contents=prompt
        )
        
        return output_analysis_result.text

    except Exception as e:
        return f"AI分析エラーが発生しました: {type(e).__name__}: {e}"

# =========================
# 月次サマリ取得
# =========================

summary = get_month_summary(supabase, user_id)
total_records = summary["total_records"]
total_points = summary["total_points"]

## ---------------------------------------------
## C. Streamlit アプリのメインロジック
## ---------------------------------------------

# =========================
# サマリ表示
# =========================

st.markdown("### 📈 今週の記録")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="記録回数",
        value=f"{total_records}回"
    )

with col2:
    st.metric(
        label="獲得ポイント",
        value=f"{total_weekly_points}pt"
    )

# =========================
# メッセージ
# =========================

st.markdown("---")

if total_records == 0:
    st.info("📝 まだ記録がありません。気分を記録して猫様と一緒に前向きになろう！")
elif total_records < 5:
    st.success("🌱 記録を始めましたね！この調子で続けましょう！")
elif total_records < 10:
    st.success("🌿 順調に記録が続いています！素晴らしい！")
else:
    st.success("🌟 たくさん記録していますね！継続は力なり！")

# 2. 分析期間（今週）の決定
week_start_iso = get_start_of_week()

# 3. ログの取得
st.subheader(f"📅 分析対象期間: {week_start_iso} 以降のログ")
raw_logs_data = fetch_user_logs_for_analysis(current_user_id, week_start_iso)

if not raw_logs_data:
    st.info("分析するためのログデータが取得できませんでした。")
    st.stop()

# 4. ログデータの整形
user_log_text = format_logs_for_ai(raw_logs_data)

# 5. AI分析の実行と表示
st.markdown("---")
st.header("レポート生成")

if st.button("AI分析を実行する", type="primary"):
    
    # API呼び出しには時間がかかるため、st.status でラップしてユーザーに待機を促す
    with st.status("AIが取得したログを分析中です...", expanded=True) as status:
        
        # ログの確認（デバッグ用）
        status.update(label="ログデータをAIに渡す形式に整形中...", state="running")
        st.code(user_log_text) # 渡すログをデバッグ表示
        
        # API呼び出し
        status.update(label="Gemini APIを呼び出し中...", state="running")
        analysis_report = analyze_mood_logs(user_log_text)
        
        # 完了
        status.update(label="分析が完了しました！", state="complete", expanded=False)
        
    st.markdown("## 🤖 AI分析結果")
    st.markdown(analysis_report)
    
else:
    st.info("上のボタンを押して分析を開始してください。")

# =========================
# 余力対応: 詳細情報
# =========================

with st.expander("📋 詳細情報を見る（開発中）", expanded=False):
    st.markdown("""
    **将来実装予定の機能:**
    - よく選んだオノマトペTOP3
    - よく会った猫TOP3
    - 週ごとの記録推移グラフ
    - 気分の変化トレンド
    
    ※ 別メンバーが実装予定です
    """)

# =========================
# アクションボタン
# =========================

st.markdown("---")

if st.button("🏠 ホームへ戻る", use_container_width=True, type="primary"):
    st.switch_page("main.py")