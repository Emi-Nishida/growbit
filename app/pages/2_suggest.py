# app/pages/2_suggest.py
import streamlit as st
import time
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    register_mood,
)
from utils.ui import setup_page
from utils.constants import AFTER_MOOD_CONFIG
from utils.rhythm_reset import get_rhythm_reset
from utils.meal_suggest import generate_meal_suggestion, get_fallback_meal
from utils.character_profiles import select_character

# ページ設定
setup_page(
    page_title="🐾猫様からの提案",
    page_icon="🐱",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)

# カスタムCSS（間隔調整）
st.markdown("""
<style>
    .stMarkdown p { margin-bottom: 0.3em; line-height: 1.4; }
    .stMarkdown h3 { margin-top: 0.5em; margin-bottom: 0.3em; }
    .stMarkdown ul { margin-top: 0.2em; margin-bottom: 0.2em; }
    div[data-testid="stExpander"] { margin-top: 0; }
</style>
""", unsafe_allow_html=True)

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# =========================
# セッション確認
# =========================

required_keys = ["selected_onomatopoeia_id", "selected_cat_id", "selected_cat_name", "selected_onomatopoeia"]
missing_keys = [k for k in required_keys if k not in st.session_state]

if missing_keys:
    st.warning("⚠️ まず、気分を選択してください")
    if st.button("気分選択へ戻る", type="primary"):
        st.switch_page("pages/1_select.py")
    st.stop()

# セッションデータ取得
onomatopoeia = st.session_state["selected_onomatopoeia"]
cat_name = st.session_state["selected_cat_name"]

# キャラクター選択（オノマトペに応じて自動選択）
character_name, character_profile = select_character(onomatopoeia)

# =========================
# 上半分: 猫からの提案
# =========================

st.markdown(f"### 🐱 「{onomatopoeia}」な気持ち、わかるよ！")
# 案3: 絵文字 + カタカナ + 日本語（括弧）
st.markdown(f"**{cat_name}が【{character_profile['emoji']} {character_name}（{character_profile['role']}）】を呼んできたにゃ！一緒に、少しずつ前に進もう 🐾**")

st.markdown("---")

# 2カラムレイアウト
col1, col2 = st.columns(2)

# =========================
# 左カラム: リズムリセット
# =========================

with col1:
    # ヘッダー（薄い黄色）
    st.markdown("""
        <div style="background: linear-gradient(135deg, #fffbea 0%, #fff9c4 100%); 
                    border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #fff59d;">
            <h2 style="color: #5d4037; margin: 0; font-size: 1.5em;">🔄 リズムリセット</h2>
            <p style="color: #6d4c41; margin: 3px 0 0 0; font-size: 0.85em;">
                短時間でできる小さな仕掛け
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # OpenAI生成（キャッシュ対応）
    cache_key = f"rhythm_{onomatopoeia}_{character_name}"
    
    if cache_key not in st.session_state:
        with st.spinner("🐱 猫様が考え中..."):
            reset = get_rhythm_reset(onomatopoeia, character_name, character_profile, use_ai=True)
            st.session_state[cache_key] = reset
    else:
        reset = st.session_state[cache_key]
    
    # メッセージ（AI生成の内容をそのまま表示）
    st.markdown(f"""
        <div style="background: #fff9e6; border-left: 4px solid #ffb74d; padding: 10px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0; color: #e65100; font-size: 0.9em; line-height: 1.5;">
                💬 {reset.get("one_liner", "")}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # タイトル
    st.markdown(f"### {reset.get('title', '')}")
    
    # やり方
    st.markdown("**📝 やり方：**")
    for i, step in enumerate(reset.get("steps", []), 1):
        st.markdown(f"**{i}.** {step}")
    
    st.markdown("")
    
    # タイマーボタン（10秒/20秒/30秒、20秒がデフォルト）
    st.markdown("**⏱️ タイマー：**")
    col_t1, col_t2, col_t3 = st.columns(3)
    
    timer_clicked = None
    with col_t1:
        if st.button("10秒", key="timer_10", use_container_width=True):
            timer_clicked = 10
    with col_t2:
        if st.button("20秒", key="timer_20", use_container_width=True, type="primary"):
            timer_clicked = 20
    with col_t3:
        if st.button("30秒", key="timer_30", use_container_width=True):
            timer_clicked = 30
    
    # タイマー実行
    if timer_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for t in range(timer_clicked, 0, -1):
            progress = (timer_clicked - t) / timer_clicked
            progress_bar.progress(progress)
            status_text.info(f"⏱️ 残り {t} 秒")
            time.sleep(1)
        
        progress_bar.progress(1.0)
        status_text.success(f"✅ {reset.get('one_liner_after', 'お疲れ様！')}")
    
    # 猫のミニ儀式（薄い青、ここで改行OK）
    st.markdown(f"""
        <div style="background: #e8f4f8; border-left: 4px solid #4fc3f7; padding: 10px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0; color: #01579b; font-size: 1em; line-height: 1.6;">
                🐱 {reset.get("cat_ritual", "")}
            </p>
        </div>
    """, unsafe_allow_html=True)

# =========================
# 右カラム: 食事提案
# =========================

with col2:
    # ヘッダー（薄いピンク）
    st.markdown("""
        <div style="background: linear-gradient(135deg, #fff0f5 0%, #ffe4e1 100%); 
                    border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #ffcdd2;">
            <h2 style="color: #5d4037; margin: 0; font-size: 1.5em;">🍳🍲 気持ちを整える食</h2>
            <p style="color: #6d4c41; margin: 3px 0 0 0; font-size: 0.85em;">
                3分で作れる簡単レシピ
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # OpenAI生成（キャッシュ対応）
    cache_key = f"meal_{onomatopoeia}_{character_name}"
    
    if cache_key not in st.session_state:
        with st.spinner("🐱 猫様が考え中..."):
            meal = generate_meal_suggestion(onomatopoeia, character_name, character_profile)
            
            if meal is None:
                meal = get_fallback_meal(onomatopoeia)
            
            st.session_state[cache_key] = meal
    else:
        meal = st.session_state[cache_key]
    
    # メッセージ（AI生成の内容をそのまま表示）
    st.markdown(f"""
        <div style="background: #fff9e6; border-left: 4px solid #ffb74d; padding: 10px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0; color: #e65100; font-size: 0.9em; line-height: 1.5;">
                💬 {meal.get("empathy", "")}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # メニュー名
    human = meal.get("human", {})
    st.markdown(f"### 🍽️ {human.get('menu', '')}")
    
    # 材料
    st.markdown("**🛒 材料：**")
    for ingredient in human.get("ingredients", []):
        st.markdown(f"• {ingredient}")
    
    st.markdown("")
    
    # 作り方
    st.markdown("**👨‍🍳👩‍🍳 作り方：**")
    for i, step in enumerate(human.get("steps", []), 1):
        st.markdown(f"**{i}.** {step}")
    
    st.markdown("")
    
    # 猫のミニ儀式（薄い青、ここで改行OK）
    st.markdown(f"""
        <div style="background: #e8f4f8; border-left: 4px solid #4fc3f7; padding: 10px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0; color: #01579b; font-size: 1em; line-height: 1.6;">
                🐱 {meal.get("cat_ritual", "")}
            </p>
        </div>
    """, unsafe_allow_html=True)

# =========================
# 下半分: 気分の変化を登録
# =========================

st.markdown("---")
st.markdown("### 🐾 提案を見て、今の気持ちは？")

# 3つの選択肢（横並び）
cols = st.columns(3)

selected_after_mood_id = None

for after_mood_id, config in AFTER_MOOD_CONFIG.items():
    col_idx = after_mood_id - 1
    with cols[col_idx]:
        st.markdown(
            f"""
            <div style="border:2px solid #ddd; border-radius:10px; padding:15px; margin:10px 0; background:#f9f9f9; text-align:center; height:180px; display:flex; flex-direction:column; justify-content:center;">
                <h2 style="margin:10px 0; font-size:1.5em;">{config['label']}</h2>
                <p style="color:#666; font-size:14px;">{config['description']}</p>
                <p style="color:#999; font-size:12px;">+{config['points']}pt</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button(
            "これ選ぶ", 
            key=f"after_mood_{after_mood_id}", 
            use_container_width=True,
            type="primary" if after_mood_id == 2 else "secondary"
        ):
            selected_after_mood_id = after_mood_id

# =========================
# 気分登録
# =========================

if selected_after_mood_id:
    points_earned = AFTER_MOOD_CONFIG[selected_after_mood_id]["points"]
    
    # データベースに登録（キャラクター情報も含める）
    success = register_mood(
        supabase,
        user_id,
        st.session_state["selected_onomatopoeia_id"],
        st.session_state["selected_cat_id"],
        selected_after_mood_id,
        points_earned,
        character_name=character_name,
        rhythm_content=st.session_state.get(f"rhythm_{onomatopoeia}_{character_name}"),
        meal_content=st.session_state.get(f"meal_{onomatopoeia}_{character_name}")
    )
    
    if success:
        # セッションに保存（3_complete.pyで使用）
        st.session_state["points_earned"] = points_earned
        st.session_state["after_mood_label"] = AFTER_MOOD_CONFIG[selected_after_mood_id]["label"]
        
        # 完了画面へ
        st.switch_page("pages/3_complete.py")
    else:
        st.error("❌ 登録に失敗しました。もう一度お試しください。")