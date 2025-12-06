# app/pages/1_select.py
import streamlit as st
from datetime import datetime
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_all_onomatopoeia,
    get_cat_by_onomatopoeia_id,
    get_all_situations,
)
from utils.ui import setup_page
from utils.constants import ONOMATOPOEIA_EMOJIS

# ページ設定
setup_page(
    page_title="😊 あなたの今の気分は？",
    page_icon="😺",
    show_home=True,
    home_href="/",
    add_title_spacer=True,
)

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# =========================
# 時間帯に応じたデフォルトシーン取得
# =========================
def get_default_situation_id():
    """現在時刻に基づいてデフォルトのsituation_idを返す"""
    now = datetime.now()
    hour = now.hour
    
    # 時間帯別のデフォルトシーン
    if 5 <= hour < 11:
        return 3  # 朝イチ
    elif 11 <= hour < 14:
        return 4  # 昼食後
    elif 14 <= hour < 18:
        return 5  # 午後
    elif 18 <= hour < 22:
        return 7  # 夜
    elif 22 <= hour or hour < 5:
        return 8  # 寝る前
    else:
        return 6  # その他

# =========================
# シーン選択（コンパクト）
# =========================

# シーンデータ取得
situations = get_all_situations(supabase)

if not situations:
    st.error("❌ シーンデータが取得できません")
    st.stop()

# セッションステートの初期化
if "selected_situation_id" not in st.session_state:
    st.session_state["selected_situation_id"] = get_default_situation_id()

# シーンの並び順を指定
situation_order = {3: 1, 1: 2, 2: 3, 4: 4, 5: 5, 7: 6, 8: 7, 6: 8}  # 朝イチ→会議前→締め切り直前→昼食後→午後→夜→寝る前→その他
situations_sorted = sorted(situations, key=lambda x: situation_order.get(x["id"], 99))

# シーン選択用の選択肢を作成
situation_options = {sit["situation"]: sit["id"] for sit in situations_sorted}
situation_labels = list(situation_options.keys())

# デフォルト値のインデックスを取得
default_situation = next(
    (sit["situation"] for sit in situations_sorted if sit["id"] == st.session_state["selected_situation_id"]),
    "その他"
)
default_index = situation_labels.index(default_situation) if default_situation in situation_labels else 0

# 1行レイアウト: ラベル + セレクトボックス
col_label, col_select, col_spacer = st.columns([1, 2, 3])
with col_label:
    st.markdown("<p style='text-align: right; margin-top: 8px;'><strong>🕐 シーン：</strong></p>", unsafe_allow_html=True)
with col_select:
    selected_situation_label = st.selectbox(
        "シーンを選択",
        options=situation_labels,
        index=default_index,
        key="situation_selector",
        label_visibility="collapsed"
    )

# 選択されたsituation_idを保存
st.session_state["selected_situation_id"] = situation_options[selected_situation_label]

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# オノマトペデータ取得と整理
# =========================
st.markdown("### 今の気分に近いものを選んでください 🐾")

onomatopoeia_list = get_all_onomatopoeia(supabase)

if not onomatopoeia_list:
    st.error("❌ オノマトペデータが取得できません")
    st.stop()

# polarityごとに分類
negative_list = [item for item in onomatopoeia_list if item["polarity"] == "ネガティブ"]
neutral_list = [item for item in onomatopoeia_list if item["polarity"] == "ニュートラル"]
positive_list = [item for item in onomatopoeia_list if item["polarity"] == "ポジティブ"]

# 各polarityでid順にソート
negative_list.sort(key=lambda x: x["id"])
neutral_list.sort(key=lambda x: x["id"])
positive_list.sort(key=lambda x: x["id"])

# =========================
# 3カラムレイアウトで表示
# =========================

col_neg, col_neu, col_pos = st.columns(3)

# ネガティブカラム
with col_neg:
    st.markdown("##### 😢 ネガティブ")
    for item in negative_list:
        is_selected = st.session_state.get("selected_onomatopoeia_id") == item["id"]
        
        ono_text = item['onomatopoeia']
        emoji = ONOMATOPOEIA_EMOJIS.get(ono_text, "")
        label = f"{emoji} {ono_text}" if emoji else ono_text
        if is_selected:
            label = f"✓ {label}"
        
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(label, key=f"ono_neg_{item['id']}", use_container_width=True, type=button_type):
            cat = get_cat_by_onomatopoeia_id(supabase, item["id"])
            
            if cat:
                st.session_state["selected_onomatopoeia_id"] = item["id"]
                st.session_state["selected_onomatopoeia"] = item["onomatopoeia"]
                st.session_state["selected_cat_id"] = cat["id"]
                st.session_state["selected_cat_name"] = cat["cat_name"]
                st.session_state["selected_cat_trait"] = cat["personality_trait"]
                st.rerun()
            else:
                st.error("❌ 対応する猫が見つかりません")

# ニュートラルカラム
with col_neu:
    st.markdown("##### 😐 ニュートラル")
    for item in neutral_list:
        is_selected = st.session_state.get("selected_onomatopoeia_id") == item["id"]
        
        ono_text = item['onomatopoeia']
        emoji = ONOMATOPOEIA_EMOJIS.get(ono_text, "")
        label = f"{emoji} {ono_text}" if emoji else ono_text
        if is_selected:
            label = f"✓ {label}"
        
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(label, key=f"ono_neu_{item['id']}", use_container_width=True, type=button_type):
            cat = get_cat_by_onomatopoeia_id(supabase, item["id"])
            
            if cat:
                st.session_state["selected_onomatopoeia_id"] = item["id"]
                st.session_state["selected_onomatopoeia"] = item["onomatopoeia"]
                st.session_state["selected_cat_id"] = cat["id"]
                st.session_state["selected_cat_name"] = cat["cat_name"]
                st.session_state["selected_cat_trait"] = cat["personality_trait"]
                st.rerun()
            else:
                st.error("❌ 対応する猫が見つかりません")

# ポジティブカラム
with col_pos:
    st.markdown("##### ✨ ポジティブ")
    for item in positive_list:
        is_selected = st.session_state.get("selected_onomatopoeia_id") == item["id"]
        
        ono_text = item['onomatopoeia']
        emoji = ONOMATOPOEIA_EMOJIS.get(ono_text, "")
        label = f"{emoji} {ono_text}" if emoji else ono_text
        if is_selected:
            label = f"✓ {label}"
        
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(label, key=f"ono_pos_{item['id']}", use_container_width=True, type=button_type):
            cat = get_cat_by_onomatopoeia_id(supabase, item["id"])
            
            if cat:
                st.session_state["selected_onomatopoeia_id"] = item["id"]
                st.session_state["selected_onomatopoeia"] = item["onomatopoeia"]
                st.session_state["selected_cat_id"] = cat["id"]
                st.session_state["selected_cat_name"] = cat["cat_name"]
                st.session_state["selected_cat_trait"] = cat["personality_trait"]
                st.rerun()
            else:
                st.error("❌ 対応する猫が見つかりません")

# =========================
# 選択状態の表示 + CTAボタン
# =========================

st.markdown("<br>", unsafe_allow_html=True) # スペースを調整

# CTAボタン
_, center, _ = st.columns([1, 2, 1])
with center:
    # 常にボタンを表示
    if st.button("😺 気分を登録して猫様に会う", type="primary", use_container_width=True, key="confirm_selection"):
        # 画面遷移の前に、オノマトペが選択されているか確認
        if st.session_state.get("selected_onomatopoeia_id"):
            st.switch_page("pages/2_suggest.py")
        else:
            # 選択されていない場合はエラーメッセージを表示して処理を中断
            st.error("🐾 まず、今の気分に近いオノマトペを選択してください。")
            st.stop()