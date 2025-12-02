# app/main.py
import streamlit as st
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_current_week_points,
    get_week_feeding_count,
    increment_feeding_count,
    get_food_type_by_points,
    get_next_goal_message,
)
from utils.constants import FOOD_EMOJIS, CAT_EXPRESSIONS, PAGE_CONFIG, WEEKLY_FEEDING_TARGET
from utils.ui import inject_base_styles

# ページ設定
st.set_page_config(**PAGE_CONFIG)
inject_base_styles()

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# データ取得
week_points = get_current_week_points(supabase, user_id)
feed_count = get_week_feeding_count(supabase, user_id)
food_type = get_food_type_by_points(week_points)
food_emoji = FOOD_EMOJIS.get(food_type, "🐱")
cat_expression = CAT_EXPRESSIONS.get(food_type, "🐱")

# =========================
# タイトル・宣言
# =========================

st.title("😸 前向きスイッチアプリ")
st.markdown(
    "### 猫様と一緒に気分をスイッチ！貯まったポイントで、週に餌をあげられます！"
)


st.markdown("---")

# =========================
# メインコンテンツ（2カラム）
# =========================

left_col, right_col = st.columns([3, 2])

# ---------------------
# 左側: 今週の餌事情
# ---------------------
with left_col:
    st.markdown("### 🍚 今週の餌事情")
    
    # ポイント表示
    st.progress(min(week_points / 101, 1.0))
    st.metric(label="週ポイント累計", value=f"{week_points}pt")
    
    # 猫と餌の絵文字
    st.markdown(
        f"""
        <div style="text-align:center; padding:20px; background:#f9f9f9; border-radius:10px; margin:10px 0;">
            <div style="font-size:48px; margin-bottom:10px;">{cat_expression} {food_emoji}</div>
            <p style="font-size:18px; margin:0; color:#666;">今週の餌: <strong>{food_type}</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 次の目標
    next_goal = get_next_goal_message(week_points)
    st.info(next_goal)

# ---------------------
# 右側: 今日の気分を登録しよう
# ---------------------
with right_col:
    st.markdown("### 🐾 今日の気分を登録しよう")
    
    # 気分を登録（大きなCTA）
    st.markdown(
        """
        <div style="border:2px solid #667eea; border-radius:10px; padding:20px; text-align:center; background:#f0f4ff; margin:10px 0;">
            <h2 style="margin:0; color:#667eea;">📝 気分を登録</h2>
            <p style="color:#666; margin:10px 0 0 0;">今の気分を登録して、<br>猫様からアドバイスをもらおう！</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("📝 気分を登録する", key="mood_button", type="primary", use_container_width=True):
        st.switch_page("pages/1_select.py")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 振り返り（控えめ）
    st.markdown(
        """
        <div style="border:1px solid #cdbfe3; border-radius:10px; padding:15px; text-align:center; background:#fbf7ff; margin:10px 0;">
            <h3 style="margin:0; color:#5d3f8c;">📊 振り返り</h3>
            <p style="color:#666; margin:8px 0 0 0; font-size:14px;">過去の記録を振り返ろう</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("📊 過去の記録を見る", key="feedback_button", use_container_width=True):
        st.switch_page("pages/4_feedback.py")

# =========================
# 今週の餌やり進捗
# =========================

st.markdown("---")
st.markdown("### 🍽️ 今週の餌やり進捗")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        f"""
        <div style="text-align:center; padding:30px; background:linear-gradient(135deg,#ffb347 0%,#ffcc33 100%); border-radius:15px; color:white;">
            <h2 style="margin:0;">今週の餌やり</h2>
            <h1 style="font-size:48px; margin:10px 0;">{feed_count}/{WEEKLY_FEEDING_TARGET} 🍚</h1>
            <p style="color:#666;">毎日続けて猫様を喜ばせよう！</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 進捗バー
    st.progress(min(feed_count / WEEKLY_FEEDING_TARGET, 1.0))

with col2:
    # 餌やりボタン
    if st.button("🍚🍚 今日の餌やり", type="primary", use_container_width=True, key="feed_button"):
        new_count = increment_feeding_count(supabase, user_id)
        st.success(f"✅ 餌やり完了！今週 {new_count}回目 🎉")
        st.balloons()
        st.rerun()

# =========================
# アプリの使い方（アコーディオン）
# =========================

st.markdown("---")

with st.expander("📖 このアプリの使い方を見る", expanded=False):
    st.markdown("""
    ### 🐱 前向きスイッチアプリとは？
    気分をオノマトペで登録して、猫様からのアドバイスをもらえるアプリです。
    気分が良くなるとポイントが貯まり、週に猫様に餌をあげられます！

    ### 📝 使い方
    1. **気分を登録**: 今の気分をオノマトペで登録
    2. **猫様を確認**: 気分に対応した猫様が登場
    3. **試してを見る**: 猫様からのアドバイスを見る
    4. **気分の変化を登録**: 試してを見て気分がどう変わったか登録
    5. **ポイント獲得**: 気分が良くなるほど多くのポイント
    6. **週に餌やり**: 貯めたポイントで餌をゲット

    ### 🍚🍥 餌の種類
    - 🍚 カリカリ（0pt～）
    - 🍥 ちゅ~る（31pt～）
    - 🐟 サーモン（71pt～）
    - 🍣 高級マグロ（101pt～）

    ### 😾😸 猫様の表情
    - 😾 カリカリ: ちょっと不機嫌
    - 😸 ちゅ~る: 普通に嬉しい
    - 😹😹 サーモン: とっても嬉しい
    - 😻😻😻 高級マグロ: 最高に幸せ

    ### 📊 ポイントの稼ぎ方
    - 気分が良くなった: +10~20ポイント
    - 変わらない: +5ポイント（挑戦が大事）

    毎日登録すると、どんどんポイントが貯まります 🎉
    """)