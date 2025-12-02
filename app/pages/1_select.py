# app/pages/1_select.py
import streamlit as st
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_all_onomatopoeia,
    get_cat_by_onomatopoeia_id,
)
from utils.ui import setup_page
from utils.constants import ONOMATOPOEIA_EMOJIS

# ページ設定
setup_page(
    page_title="😊 今の気分は？",
    page_icon="😺",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# オノマトペデータ取得
onomatopoeia_list = get_all_onomatopoeia(supabase)

if not onomatopoeia_list:
    st.error("❌ オノマトペデータが取得できません")
    st.stop()

# =========================
# ポジティブ優先の並べ替え
# =========================

# polarityで並び替え: ポジティブ → ニュートラル → ネガティブ
polarity_order = {"ポジティブ": 1, "ニュートラル": 2, "ネガティブ": 3}
onomatopoeia_list_sorted = sorted(
    onomatopoeia_list, 
    key=lambda x: (polarity_order.get(x["polarity"], 4), x["id"])
)

# =========================
# オノマトペボタン表示（カテゴリなし・3列グリッド）
# =========================

st.markdown("### 今の気分に近いものを選んでください 🐾")
st.markdown("<br>", unsafe_allow_html=True)

# 3列×5行のグリッド表示（15個のオノマトペを想定）
cols_per_row = 3
rows = [onomatopoeia_list_sorted[i:i + cols_per_row] for i in range(0, len(onomatopoeia_list_sorted), cols_per_row)]

for row_idx, row in enumerate(rows):
    cols = st.columns(cols_per_row)
    for col_idx, item in enumerate(row):
        with cols[col_idx]:
            # 選択中かどうか
            is_selected = st.session_state.get("selected_onomatopoeia_id") == item["id"]
            
            # オノマトペに対応する絵文字を取得
            ono_text = item['onomatopoeia']
            emoji = ONOMATOPOEIA_EMOJIS.get(ono_text, "")
            
            # ボタンラベル（絵文字 + オノマトペ）
            label = f"{emoji} {ono_text}" if emoji else ono_text
            if is_selected:
                label = f"✓ {label}"
            
            button_type = "primary" if is_selected else "secondary"
            
            # ボタン
            if st.button(label, key=f"ono_{item['id']}", use_container_width=True, type=button_type):
                # 対応する猫を取得
                cat = get_cat_by_onomatopoeia_id(supabase, item["id"])
                
                if cat:
                    # セッションに保存
                    st.session_state["selected_onomatopoeia_id"] = item["id"]
                    st.session_state["selected_onomatopoeia"] = item["onomatopoeia"]
                    st.session_state["selected_cat_id"] = cat["id"]
                    st.session_state["selected_cat_name"] = cat["cat_name"]
                    st.session_state["selected_cat_trait"] = cat["personality_trait"]
                    
                    # 画面を再描画して選択状態を表示
                    st.rerun()
                else:
                    st.error("❌ 対応する猫が見つかりません")

# =========================
# 選択状態の表示 + CTAボタン
# =========================

if st.session_state.get("selected_onomatopoeia"):
    st.markdown("---")
    
    # 選択中のオノマトペの絵文字を取得
    selected_ono = st.session_state['selected_onomatopoeia']
    selected_emoji = ONOMATOPOEIA_EMOJIS.get(selected_ono, "")
    
    st.success(f"✅ 選択中: {selected_emoji} {selected_ono}")
    st.info(f"🐱 対応する猫: {st.session_state.get('selected_cat_name', '不明')}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CTAボタン（大きく目立つ）
    _, center, _ = st.columns([1, 2, 1])
    with center:
        if st.button("😺 気分を登録して猫様に会う", type="primary", use_container_width=True, key="confirm_selection"):
            st.switch_page("pages/2_suggest.py")