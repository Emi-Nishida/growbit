# app/pages/3_complete.py
import streamlit as st
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_current_week_points,
    get_food_type_by_points,
)
from utils.ui import setup_page
from utils.constants import FOOD_EMOJIS, FOOD_THRESHOLDS, CAT_EXPRESSIONS

# ページ設定
setup_page(
    page_title="😽🎉 おめでとう！",
    page_icon="😺",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# =========================
# セッション確認
# =========================

if "points_earned" not in st.session_state:
    st.warning("⚠️ 先に気分を登録してください")
    if st.button("気分選択へ", type="primary"):
        st.switch_page("pages/1_select.py")
    st.stop()

# セッションデータ取得
points_earned = st.session_state["points_earned"]
cat_name = st.session_state.get("selected_cat_name", "にゃん")

# 今週の累積ポイント取得
week_points = get_current_week_points(supabase, user_id)
food_type = get_food_type_by_points(week_points)
food_emoji = FOOD_EMOJIS.get(food_type, "🐱")

# 猫の表情（餌に応じて変化）
cat_expression = CAT_EXPRESSIONS.get(food_type, "🐱")

# =========================
# だいじょうぶにゃんのメッセージ（タイトル下に移動）
# =========================

encouragement = ""
if points_earned >= 20:
    encouragement = "すごいっ！気持ちが大きく切り替わったね！この調子で進もう！🌟"
elif points_earned >= 10:
    encouragement = "少しずつでも前進してるよ！その一歩が大事だにゃ 😊"
else:
    encouragement = "焦らず、自分のペースでいいんだよ。続けることが大切だにゃ 💚"

st.markdown(
    f"""
    <h3 style="color:#667eea; font-size:22px; margin:20px 0 30px 0; padding:15px; background-color:#f0f4ff; border-radius:10px; border-left:4px solid #667eea;">
    💬 {cat_name}: 「{encouragement}」
    </h3>
    """,
    unsafe_allow_html=True
)

# =========================
# 2カラムレイアウト
# =========================

col1, col2 = st.columns([1, 1])

# ---------------------
# 左側: 今回獲得ポイント
# ---------------------
with col1:
    st.markdown("### 🎁 今回獲得ポイント")
    
    st.markdown(
        f"""
        <div style="text-align:center; padding:40px 20px; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); border-radius:15px; color:white; margin:10px 0;">
            <h1 style="font-size:60px; margin:0;">+{points_earned}pt</h1>
            <p style="font-size:20px; margin-top:15px; opacity:.9;">🐱 {cat_name} も喜んでいるよ！</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# 間隔を広げる
st.markdown("<div style='margin:40px 0;'></div>", unsafe_allow_html=True)

# ---------------------
# 右側: 今週の累計ポイント
# ---------------------
with col2:
    st.markdown("### 🪙 今週の累計ポイント")
    
    # 進捗バー
    st.progress(min(week_points / 101, 1.0))
    
    col2_1, col2_2 = st.columns([1, 1])
    with col2_1:
        st.metric(
            label="合計",
            value=f"{week_points}pt",
            delta=f"+{points_earned}pt"
        )
    with col2_2:
        st.markdown(
            f'<div style="text-align:center; font-size:60px; margin-top:10px;">{cat_expression}</div>',
            unsafe_allow_html=True
        )
    
    # 次の目標（文字サイズを大きく＋センタリング）
    for threshold, food_name in [(31, "ちゅ〜る"), (71, "サーモン"), (101, "高級マグロ")]:
        if week_points < threshold:
            remaining = threshold - week_points
            st.markdown(
                f"""
                <div style="background-color:#e3f2fd; padding:12px; border-radius:8px; border-left:4px solid #2196f3; text-align:center;">
                    <p style="font-size:18px; margin:0; color:#1976d2; font-weight:bold;">💡 あと{remaining}ptで「{food_name}」！</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            break
    else:
        st.success("🎊 最高達成！")

# =========================
# 今週の餌（今週のスケジュールデザイン）
# =========================

st.markdown("---")
st.markdown("### 🍽️ 今週の餌")

st.markdown(
    """
    <p style="color:#666; font-size:14px; margin-bottom:10px;">
    ポイントを貯めると、時間にどんな餌を貰えるようになるか見えてくる！🔥
    </p>
    """,
    unsafe_allow_html=True
)

# 4列で餌を表示（ロック状態に応じて明度変更）
cols = st.columns(4)

for col, (food_name, threshold) in zip(cols, FOOD_THRESHOLDS.items()):
    with col:
        unlocked = week_points >= threshold
        
        # ロック済み: はっきり、未ロック: ぼやける
        opacity = "1.0" if unlocked else "0.3"
        border_color = "#667eea" if food_name == food_type else "#ddd"
        bg_color = "#f0f4ff" if food_name == food_type else "#f9f9f9"
        
        emoji = FOOD_EMOJIS[food_name]
        status = "✓" if unlocked else "🔒"
        
        st.markdown(
            f"""
            <div style="
                text-align:center; 
                padding:15px; 
                border:2px solid {border_color}; 
                border-radius:10px; 
                background-color:{bg_color}; 
                opacity:{opacity};
                transition: all 0.3s ease;
            ">
                <div style="font-size:40px; margin-bottom:5px;">{emoji}</div>
                <p style="margin:3px 0; font-weight:bold; font-size:14px;">{food_name}</p>
                <p style="margin:0; font-size:11px; color:#666;">{threshold}pt~</p>
                <p style="margin:3px 0; font-size:18px;">{status}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# アクションボタン
# =========================

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 ホームへ戻る", use_container_width=True, type="primary"):
        # セッションクリア（ホームへ戻るため、これまでの記録をクリア）
        keys_to_clear = [
            "selected_onomatopoeia_id",
            "selected_onomatopoeia",
            "selected_cat_id",
            "selected_cat_name",
            "selected_cat_trait",
            "points_earned",
            "after_mood_label",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        st.switch_page("main.py")

with col2:
    # ボタンのラベルを「📊 今月の振り返り」に変更
    # ページのタイトルに合わせて「📊」の絵文字を使用
    if st.button("📊 今月の振り返り", use_container_width=True):
        # 「振り返り」への遷移のため、セッションクリアのロジックは削除
        # 遷移先のページで必要なデータはセッションステートに残しておく

        # 遷移先を pages/4_feedback.py に変更
        st.switch_page("pages/4_feedback.py")
