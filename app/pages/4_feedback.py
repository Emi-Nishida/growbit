# app/pages/4_feedback.py
import streamlit as st
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_month_summary,
)
from utils.ui import setup_page

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
user_id = get_or_create_user_id()

# =========================
# 月次サマリ取得
# =========================

summary = get_month_summary(supabase, user_id)
total_records = summary["total_records"]
total_points = summary["total_points"]

# =========================
# サマリ表示
# =========================

st.markdown("### 📈 今月の記録")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="記録回数",
        value=f"{total_records}回"
    )

with col2:
    st.metric(
        label="獲得ポイント",
        value=f"{total_points}pt"
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