# app/pages/4_feedback.py
import streamlit as st
from utils.services import (
    check_authentication,       # 追加
    get_authenticated_user_id,  # 追加
    get_supabase_client,
    get_month_summary,
)
from utils.ui import setup_page
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from openai import OpenAI
import pandas as pd

# ページ設定
setup_page(
    page_title="📊 31日間の振り返り",
    page_icon="😺",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)
# 🔐 認証チェック（最優先）
check_authentication()

# Supabase接続
supabase = get_supabase_client()
user_id = get_authenticated_user_id()  # 変更

# 今日の日付
today = date.today()
monday_this_week = today - timedelta(days=today.weekday())  # 月曜始まり
monday_last_week = monday_this_week - timedelta(weeks=1)

# 対象ユーザーのUUID（認証済みユーザー）
target_user_id = user_id  # 🆕 変更: 既に取得済みのuser_idを使用

# ===================================
# ログをまとめて取得（Supabaseクエリを1回に統合）★変更点
# ===================================
start_date_31days = (date.today() - timedelta(days=31)).isoformat()
logs_response = (
    supabase.table("mood_register_log")
    .select("id, created_at, situation_master(situation), onomatopoeia_master(onomatopoeia), cat_master(cat_name), points_earned")
    .eq("user_id", target_user_id)
    .gte("created_at", start_date_31days)
    .execute()
)
df_logs = pd.DataFrame(logs_response.data)

# 今週・先週・31日間の件数を pandas 側で計算
# 日時のパース：Timestamp型として保持
df_logs["created_at"] = pd.to_datetime(df_logs["created_at"], format='ISO8601', utc=True)
df_logs["created_at_jst"] = df_logs["created_at"].dt.tz_convert('Asia/Tokyo')

# 日付カラムを追加(比較用)
df_logs["date"] = df_logs["created_at_jst"].dt.date

# 今週・先週・31日間の件数を計算
this_week_log_count = (df_logs["date"] >= monday_this_week).sum()
last_week_log_count = ((df_logs["date"] >= monday_last_week) & (df_logs["date"] < monday_this_week)).sum()
last_31days_log_count = df_logs.shape[0]

# ===================================
# 今週と先週の餌ポイントを取得
# ===================================
try:
    # 今週のポイント合計
    points_this_week = df_logs[df_logs["date"] >= monday_this_week]["points_earned"].sum()
    
    # 先週のポイント合計
    points_last_week = df_logs[
        (df_logs["date"] >= monday_last_week) & 
        (df_logs["date"] < monday_this_week)
    ]["points_earned"].sum()
        
except Exception as e:
    st.error(f"❌ ポイント計算エラーが発生しました: {e}")
    points_this_week = 0
    points_last_week = 0


# ===================================
# ログ整形（json_normalizeで高速化）★変更点
# ===================================
df_logs["日付"] = pd.to_datetime(df_logs["created_at_jst"]).dt.strftime("%Y-%m-%d")

# ネスト展開を apply ではなく json_normalize に変更
situations = pd.json_normalize(df_logs["situation_master"])
onomatopoeias = pd.json_normalize(df_logs["onomatopoeia_master"])
cats = pd.json_normalize(df_logs["cat_master"])
df_logs["シーン"] = situations["situation"]
df_logs["オノマトペ"] = onomatopoeias["onomatopoeia"]
df_logs["猫"] = cats["cat_name"]

# 必要な列だけ残す
log_display_df = df_logs[["日付", "シーン", "オノマトペ"]]

#新しい日付が上に来るように並び替え
log_display_df = log_display_df.sort_values(by="日付", ascending=False).reset_index(drop=True)

# インデックスを 1 からにする
log_display_df.index = log_display_df.index + 1

# ===================================
# 今週一番登場した猫
# ===================================
df_week_cats = df_logs[df_logs["date"] >= monday_this_week]
if not df_week_cats.empty:
    cat_counts = df_week_cats.groupby("猫").size().reset_index(name="count")
    top_cat_row = cat_counts.loc[cat_counts["count"].idxmax()]
    top_cat_name = top_cat_row["猫"]
    top_cat_count = top_cat_row["count"]
else:
    top_cat_name, top_cat_count = "記録なし", 0

# =========================
# 生成AI分析用ロジック
# =========================    

## ---------------------------------------------
## A. 生成AI API 呼び出し関数
## ---------------------------------------------
client = OpenAI()
#GPT呼び出しをキャッシュ化
@st.cache_data(ttl=3600) # キャッシュの有効期限を1時間に設定
def run_gpt_cached(logs_text):
    request_to_gpt = f"""
    あなたはユーザーの感情データを分析する優秀なアシスタントです。以下は、あるユーザーが過去31日間に記録した感情データです。
    各行には、記録日時、状況の説明、感情を表すオノマトペが含まれています。
    これらのデータをもとに、ユーザーの身体状態、感情傾向を分析し、今の状況を改善して日々のパフォーマンスを向上させる具体的で役立つ食事以外のフィードバックを猫風にMarkdown形式で提供してください。
    **Markdownの構造ルール：**
    - 最初に大きなタイトルは不要です（`#`や`##`は使わない）
    - 最初に一文で総括を述べてください
    - 各セクションのタイトルは `####` を必ず以下の絵文字付きタイトルを使ってください：
        - `#### 🏃‍♀️ 身体状態の傾向`
        - `#### 💖 感情傾向の分析`
        - `#### 🌈 改善のためのアドバイス`
    - 本文はやさしく明るくですます調でお願いします。最初の総括と最後のフィードバックだけ猫っぽい語尾（「ニャ」など）を使ってください
    - 箇条書きは `-` または `1.` を使ってください
    - 出力はMarkdown形式で整えてください
    - ユーザのこと呼ぶときは「ユーザー」ではなく「あなた」と呼んでください
    データ:
    {logs_text}
    """
    response =  client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": request_to_gpt },
            ],
        )
    # 返って来たレスポンスの内容はresponse.choices[0].message.content.strip()に格納されているので、これをoutput_contentに代入
    output_content = response.choices[0].message.content.strip()
    return output_content # 返って来たレスポンスの内容を返す

## ---------------------------------------------
## A. ログ取得と整形
## ---------------------------------------------
try:
    #created_at と situation と onomatopoeia をプロンプト用に文章に変換
    logs_text = "\n".join(
        f"{row['created_at']}: "
        f"{row['situation_master']['situation'] if row.get('situation_master') else ''}: "
        f"{row['onomatopoeia_master']['onomatopoeia'] if row.get('onomatopoeia_master') else ''}"
        for _, row in df_logs.iterrows()
    )
    #生成AI分析実行
    with st.spinner("振り返りを作成中です。少々お待ちくださいニャ…🐾"):
        output_content_text = run_gpt_cached(logs_text)
except Exception as e:
    st.error(f"AI分析エラーが発生しました: {type(e).__name__}: {e}")

# =========================
# サマリ表示(タイトル以降のここから画面表示)
# =========================

st.markdown("### 📈 今週の記録")

col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    st.metric(
        label="記録回数",
        value=f"{this_week_log_count}回"
    )

with col2:
    st.metric(
        label="獲得ポイント",
        value=f"{points_this_week}pt"
    )

with col3:
    st.metric(
        label="今週よく登場した猫🐱",
        value=f"{top_cat_name}"
    )

# =========================
# フィードバック表示
# =========================

st.markdown("---")

st.markdown("### 🐱 猫様からのフィードバック")
if last_31days_log_count == 0:
    st.warning("記録が31日間ありません。まずは気分を記録してほしいニャ！")
else:
    st.info(output_content_text)

with st.expander("📂 直近31日のログを表示"):
    st.dataframe(log_display_df)

# =========================
# アクションボタン
# =========================

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 ホームへ戻る", use_container_width=True, type="secondary"):
        st.switch_page("main.py")

with col2:
    if st.button("📝 今の気分を記録する", use_container_width=True, type="primary"):
        st.switch_page("pages/1_select.py") 