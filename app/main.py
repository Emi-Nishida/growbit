# app/main.py (ログイン対応版)
import streamlit as st
import unicodedata
import time

from utils.services import (
    get_supabase_client,
    check_authentication,  # 🆕 追加
    get_authenticated_user_id,  # 🆕 追加
    logout,  # 🆕 追加
    get_current_week_points,
    get_weekly_balance,
    get_food_type_by_points,
    get_next_goal_message,
    get_feed_point_by_id,
    deduct_weekly_balance,
    execute_weekly_feeding_event,
    get_feeding_history,
    get_week_start_date,
    initialize_weekly_points_if_needed,
    get_all_feeds,
)
from utils.constants import FOOD_EMOJIS, CAT_EXPRESSIONS, PAGE_CONFIG
from utils.ui import inject_base_styles
from datetime import datetime, timedelta

# =========================
# 🔐 認証チェック（最優先）
# =========================
check_authentication()

# ページ設定
st.set_page_config(**PAGE_CONFIG)
inject_base_styles()

# Supabase接続
supabase = get_supabase_client()
user_id = get_authenticated_user_id()  # 🆕 認証済みユーザーIDを取得

# =========================
# 🆕 ヘッダー：ログアウトボタン
# =========================
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.title("😸 あなたの気分を、猫様と一緒に前向きに!")
with col_logout:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ログアウト", key="logout_btn"):
        logout()

# =========================
# データ取得
# =========================

# 今週分のweekly_pointsレコードを初期化(なければ作成)
initialize_weekly_points_if_needed(supabase, user_id)

# 今週のポイント
week_points = get_current_week_points(supabase, user_id)

# 餌やり可能残高(先週分)
weekly_balance = get_weekly_balance(supabase, user_id)

# 全餌マスタを取得
all_feeds = get_all_feeds(supabase) 
# 0ポイントの「カリカリ」を除外し、残高で買える餌をフィルタ
affordable_feeds = [
    f for f in all_feeds 
    if f['feed_point'] <= weekly_balance and f['feed_point'] > 0
]

# 今週の餌(予定)の変数を再定義 (UIで利用するため)
current_food_type = get_food_type_by_points(week_points)
current_food_emoji = FOOD_EMOJIS.get(current_food_type, "❓")
current_cat_expression = CAT_EXPRESSIONS.get(current_food_type, "😸")

# 先週の日付範囲(表示用)
today = datetime.now().date()
this_week_start = get_week_start_date(today)
last_week_start = this_week_start - timedelta(days=7)
last_week_end = this_week_start - timedelta(days=1)
last_week_range = f"{last_week_start.strftime('%m/%d')}~{last_week_end.strftime('%m/%d')}"

# =========================
# キャッチコピー（タイトル削除済み、ヘッダーに移動）
# =========================

st.markdown("### 日々の😊気分や🌈虹の後に🌻ひまわりって😆笑顔になれる🍀小さな🌱ツールを🎁贈ってくれる、🐱優しいアプリです。")
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =========================
# アプリの使い方(アコーディオン)
# =========================

with st.expander("📖 このアプリの使い方を見る", expanded=False):
    st.markdown("""
### 😸 前向きスイッチとは?
気分を**オノマトペ**で登録すると、猫様(AI)が あなたにぴったりの**季節のお手軽食事・運動レシピアドバイス**を書いてくれます。
このアプリは、 あなたの**気分向上を楽しく後押し**させるための工夫が込められています!

* **😸 猫様という寄り添い**: いつもそばで一緒に寄り添ってくれる存在がいるから、安心して過ごせます。
* **💖 気分の見える化とご褒美**: 気分が向上すると**ポイント**が貯まり、自分の変化を実感できます。
* **🍖 後押しの仕組み**: 貯めたポイントで猫様に**ご飯(餌やり)**を あげられる仕組みが、後押しを楽しくサポートします。

---
### 📝 使い方

1. **気分を登録**: 今の気分をオノマトペで記録
2. **猫様が登場**: 気分に対した猫様が現れる
3. **アドバイスを見る**: 猫様からのご褒美を受け取る
4. **気分の変化を記録**: ご褒美後の気分を登録
5. **ポイント貯蓄**: 気分が良くなるほど多くのポイント
6. **週に餌やり**: 貯めたポイントで週に餌を あげる

---
### 🍖🐟 餌の種類

* 😿 **カリカリ**(10pt)
* 😺 **ちゅ~る**(30pt)
* 😸😸 **サーモン**(60pt)
* 😻😻😻 **マグロ**(100pt)

---
### 😸😺😻 猫様の表情

* 😿 **カリカリ**: ちょっと不機嫌
* 😺 **ちゅ~る**: 普通に嬉しい
* 😸😸 **サーモン**: とっても嬉しい
* 😻😻😻 **マグロ**: 最高に幸せ

---
### 💯 ポイントの貯まり方

* **気分が良くなった**: +10~20ポイント
* **変わらない**: +5ポイント(過ごしが大事)

日々登録すると、どんどんポイントが貯まります 😊

---
### 📊 振り返り機能とは?

**❤️ あなたが記録した気分をまとめて振り返ることができる機能です。**
過去31日間の気分を一覧で確認し、今週と先週の記録数やポイントの変化も見える仕様です。

* **😸 猫様からのフィードバック**: AIが あなたの気分データを分析し、猫様らしい優しい・厳しいアドバイスを投げかけてくれます。日々の変化を振り返りながら、次のステップも楽しく見つけられます。
* **📈 傾向の確認**: 過去の状況やオノマトペを一覧で見返せるので、自分の気分のパターンを掴むことができます。

振り返りを通じて、 あなたの気分の変化をより深く知ることができます!😊
    """)
st.markdown("---")

# =========================
# アイコン: 気分を記録しよう(2カラム+CTA)
# =========================

st.markdown("### 📝記録と振り返り:")
st.caption("日々登録するとどんどんポイントが貯まり、猫様にナイスな餌を あげられます!")
st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

# ---------------------
# 左側: 気分を記録
# ---------------------
with col_left:
    st.markdown("""
    <div style="
        border:3px solid #667eea; 
        border-radius:15px; 
        padding:25px 15px; 
        text-align:center; 
        background:linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
        margin:0 5px 15px 0;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size:42px; margin-bottom:8px;">📝</div>
        <h3 style="margin:5px 0; color:#667eea; font-size:22px;">今の気分を記録する</h3>
        <p style="color:#666; margin:5px 0; font-size:14px; line-height:1.4;">
            猫様が あなたにぴったりの<br>アドバイスを書いてくれます
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📝 さっそく記録する", key="mood_button_main", type="primary", use_container_width=True):
        st.switch_page("pages/1_select.py")

# ---------------------
# 右側: 過去の記録
# ---------------------
with col_right:
    st.markdown("""
    <div style="
        border:3px solid #9b7eb8; 
        border-radius:15px; 
        padding:25px 15px; 
        text-align:center; 
        background:linear-gradient(135deg, #fbf7ff 0%, #f5edff 100%);
        margin:0 0 15px 5px;
        box-shadow: 0 4px 6px rgba(155, 126, 184, 0.2);
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size:42px; margin-bottom:8px;">📊</div>
        <h3 style="margin:5px 0; color:#5d3f8c; font-size:22px;">過去31日を振り返る</h3>
        <p style="color:#666; margin:5px 0; font-size:14px; line-height:1.4;">
            気分の変化を<br>振り返ろう
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 さっそく振り返る", key="feedback_button_main", use_container_width=True):
        st.switch_page("pages/4_feedback.py")

# =========================
# ご飯セクション: 猫様の餌やり
# =========================

st.markdown("---")
st.markdown("### 🍖 ご飯:猫様の餌やり")

col_left, col_right = st.columns([1, 1])

# ---------------------
# 左側: 今週のポイント
# ---------------------
with col_left:
    st.markdown("#### 💯 今週の貯蓄ポイント")
    
    # ポイント表示
    st.caption("ポイントを貯めて猫様を喜ばせよう!")
    st.progress(min(week_points / 101, 1.0))
    st.metric(label="累計ポイント", value=f"{week_points}pt")
    
    # 猫と餌の絵文字
    st.markdown(
        f"""
        <div style="text-align:center; padding:15px; background:#f9f9f9; border-radius:10px; margin:10px 0;">
            <div style="font-size:40px; margin-bottom:8px;">{current_cat_expression} {current_food_emoji}</div>
            <p style="font-size:16px; margin:0; color:#666;">週末あげる餌<br><strong>{current_food_type}</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 次の目標
    next_goal = get_next_goal_message(week_points)
    st.info(next_goal)
    
    # 餌の種類プレビュー(小さく表示)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("**🍖🐟 餌の種類**")
    
    # 2x2グリッドで4種の餌を表示
    food_col1, food_col2 = st.columns(2)
    
    food_items = [
        ("カリカリ", 10, "😿"),
        ("ちゅ~る", 30, "😺"),
        ("サーモン", 60, "😸"),
        ("マグロ", 100, "😻"),
    ]
    
    for idx, (food_name, threshold, emoji) in enumerate(food_items):
        target_col = food_col1 if idx % 2 == 0 else food_col2
        
        with target_col:
            unlocked = week_points >= threshold
            is_current = food_name == current_food_type
            
            # スタイル設定
            opacity = "1.0" if unlocked else "0.4"
            border_color = "#667eea" if is_current else "#ddd"
            bg_color = "#f0f4ff" if is_current else "#f9f9f9"
            status = "✅" if unlocked else "🔒"
            
            st.markdown(
                f"""
                <div style="
                    text-align:center; 
                    padding:8px; 
                    margin:3px 0;
                    border:2px solid {border_color}; 
                    border-radius:8px; 
                    background-color:{bg_color}; 
                    opacity:{opacity};
                ">
                    <div style="font-size:24px; margin-bottom:2px;">{emoji}</div>
                    <p style="margin:2px 0; font-weight:bold; font-size:11px;">{food_name}</p>
                    <p style="margin:0; font-size:9px; color:#666;">{threshold}pt~</p>
                    <p style="margin:2px 0; font-size:14px;">{status}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------------
# 右側: 週末餌やりイベント
# ---------------------
with col_right:
    st.markdown("#### 🎉🍖 餌やりイベント開催中!")
    st.caption(f"先週({last_week_range})貯めたポイントで、猫様にさっそく餌を あげよう!")

    # 追加するスペーサー(左側のプログレスバーと高さを揃えるため)
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    if weekly_balance == 0:
        st.info("😿 餌やり可能なポイントが ありません")
        st.caption("今週気分を登録してポイントを貯めましょう!")

    elif not affordable_feeds:
        st.info(f"😺 残: {weekly_balance}pt。買える可能な餌が ありません。")
        st.caption("もう少しポイントを貯めて、より良い餌にチャレンジしましょう!")

    else:
        st.metric(label="餌やり可能残高", value=f"{weekly_balance}pt")

        food_options = [
            f"{f['feed_name']} ({f['feed_point']}pt)"
            for f in affordable_feeds
        ]

        selected_option = st.selectbox(
            "🍖 あげる餌を選んでください",
            food_options,
            key="feed_select"
        )

        selected_feed_name = selected_option.split(" (")[0]
        selected_feed = next(f for f in affordable_feeds if f['feed_name'] == selected_feed_name)

        selected_feed_emoji = FOOD_EMOJIS.get(selected_feed_name, "❓")
        selected_feed_cost = selected_feed['feed_point']

        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px;
            background: #f0f4ff;
            border-radius: 10px;
            border: 2px solid #667eea;
            margin: 10px 0;
        ">
            <div style="font-size: 40px; margin-bottom: 5px;">{selected_feed_emoji}</div>
            <p style="font-size: 16px; margin: 0; color: #666;">
                選択の餌: <strong>{selected_feed_name}</strong><br>
                必要ポイント: <strong>{selected_feed_cost}pt</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            f"🎁🍖 {selected_feed_name}を あげる({selected_feed_cost}pt消費)",
            key="weekly_feed_button",
            type="primary",
            use_container_width=True
        ):
            feed_id = selected_feed['id']

            if deduct_weekly_balance(supabase, user_id, selected_feed_cost):
                success = execute_weekly_feeding_event(supabase, user_id, feed_id)

                if success:
                    new_balance = weekly_balance - selected_feed_cost

                    st.success(f"🎉 {selected_feed_name}を あげました!")
                    st.balloons()

                    selected_cat_expression = CAT_EXPRESSIONS.get(selected_feed_name, "😸")
                    st.markdown(f"""
                    <div style="
                        text-align: center;
                        padding: 35px;
                        background: linear-gradient(135deg, #ffeb3b 0%, #ff9800 100%);
                        border-radius: 20px;
                        margin: 20px 0;
                        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
                    ">
                        <div style="font-size: 80px; margin-bottom: 15px;">{selected_cat_expression}{selected_cat_expression}{selected_cat_expression}</div>
                        <h2 style="color: white; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                            猫様たち大喜び!
                        </h2>
                        <p style="font-size: 16px; color: white; margin: 0;">
                            残高: {new_balance}pt<br>
                            また餌を あげられます!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("餌やり履歴の登録に失敗しました。")
            else:
                st.error("残高が足りません。選択した餌のポイントを確認してください。")

        # 📜💬 最近の餌やり履歴(右側ボックス内に表示)
        with st.expander("📜 最近の餌やり履歴", expanded=False):
            history = get_feeding_history(supabase, user_id, limit=3)

            if not history:
                st.info("まだ餌やり履歴が ありません")
            else:
                for record in history:
                    feed_at = datetime.fromisoformat(record["feed_at"].replace("Z", "+00:00"))
                    feed_name = record.get("feed_master", {}).get("feed_name", "不明")
                    feed_point = record.get("feed_master", {}).get("feed_point", 0)
                    feed_emoji = FOOD_EMOJIS.get(feed_name, "❓")
                    date_str = feed_at.strftime("%m/%d(%a)")

                    st.markdown(f"""
                    <div style="
                        padding: 12px;
                        margin: 8px 0;
                        background: #f9f9f9;
                        border-left: 4px solid #667eea;
                        border-radius: 5px;
                    ">
                        <span style="font-size: 14px;">📅 {date_str}</span>
                        <span style="font-size: 20px; margin: 0 8px;">{feed_emoji}</span>
                        <strong>{feed_name}</strong>
                        <span style="color: #999; margin-left: 8px; font-size: 13px;">({feed_point}pt)</span>
                    </div>
                    """, unsafe_allow_html=True)