# app/main.py (案B: 2カラム並び版)
import streamlit as st
import unicodedata
import time

from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_current_week_points,
    get_weekly_balance,
    get_food_type_by_points,
    get_next_goal_message,
    # get_feed_id_by_points, ← 削除済み
    get_feed_point_by_id,
    deduct_weekly_balance,
    execute_weekly_feeding_event,
    get_feeding_history,
    get_week_start_date,
    initialize_weekly_points_if_needed,
    get_all_feeds,  # 新しく追加
)
from utils.constants import FOOD_EMOJIS, CAT_EXPRESSIONS, PAGE_CONFIG
from utils.ui import inject_base_styles
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(**PAGE_CONFIG)
inject_base_styles()

# Supabase接続
supabase = get_supabase_client()
user_id = get_or_create_user_id()

# =========================
# データ取得
# =========================

# 今週分のweekly_pointsレコードを初期化（なければ作成）
initialize_weekly_points_if_needed(supabase, user_id)

# 今週のポイント
week_points = get_current_week_points(supabase, user_id)

# 餌やり可能残高（先週分）
weekly_balance = get_weekly_balance(supabase, user_id)

# 全餌マスタを取得 (新規追加分)
all_feeds = get_all_feeds(supabase) 
# 0ポイントの「カリカリ」を除外し、残高内で買える餌をフィルタ
affordable_feeds = [
    f for f in all_feeds 
    if f['feed_point'] <= weekly_balance and f['feed_point'] > 0
]

# 今週の餌(予定)の変数を再定義 (UIで利用するため復活)
current_food_type = get_food_type_by_points(week_points)
current_food_emoji = FOOD_EMOJIS.get(current_food_type, "🐱")
current_cat_expression = CAT_EXPRESSIONS.get(current_food_type, "🐱")

# 以前使用していたが不要になった変数は削除/コメントアウト:
# available_food_type, available_food_emoji, available_cat_expression は削除済みとして処理を継続
# # 餌やり可能な餌（残高ベース）
# available_food_type = get_food_type_by_points(weekly_balance)
# available_food_emoji = FOOD_EMOJIS.get(available_food_type, "🐱")
# available_cat_expression = CAT_EXPRESSIONS.get(available_food_type, "🐱")

# 先週の日付範囲（表示用）
today = datetime.now().date()
this_week_start = get_week_start_date(today)
last_week_start = this_week_start - timedelta(days=7)
last_week_end = this_week_start - timedelta(days=1)
last_week_range = f"{last_week_start.strftime('%m/%d')}～{last_week_end.strftime('%m/%d')}"

# =========================
# タイトル・キャッチコピー
# =========================

st.title("😸 あなたの気分を、猫様と一緒に前向きに!")
st.markdown("### 日々の​気分や​体調に​寄り​添って​小さな​提案を​してくれる、​癒し系アプリです。")
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =========================
# メインセクション: 気分を記録しよう(2カラム・枠+CTA)
# =========================

st.markdown("### 💭 気分を記録しよう")
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
        <h3 style="margin:5px 0; color:#667eea; font-size:18px;">今の気分を記録する</h3>
        <p style="color:#666; margin:5px 0; font-size:13px; line-height:1.4;">
            猫様があなたに合った<br>アドバイスをくれます
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📝 今の気分を記録する", key="mood_button_main", type="primary", use_container_width=True):
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
        <h3 style="margin:5px 0; color:#5d3f8c; font-size:18px;">過去の記録を見る</h3>
        <p style="color:#666; margin:5px 0; font-size:13px; line-height:1.4;">
            気分の変化を<br>振り返ろう
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 過去の記録を見る", key="feedback_button_main", use_container_width=True):
        st.switch_page("pages/4_feedback.py")

# =========================
# ご褒美セクション: 猫様の餌やり
# =========================

st.markdown("---")
st.markdown("### 🎁 ご褒美:猫様の餌やり")
st.caption("気分改善を続けるとポイントが貯まり、猫様に餌をあげられます")

col_left, col_right = st.columns([1, 1])

# ---------------------
# 左側: 今週のポイント
# ---------------------
with col_left:
    st.markdown("#### 📊 今週のポイント")
    
    # ポイント表示
    st.progress(min(week_points / 101, 1.0))
    st.metric(label="累計ポイント", value=f"{week_points}pt")
    
    # 猫と餌の絵文字
    st.markdown(
        f"""
        <div style="text-align:center; padding:15px; background:#f9f9f9; border-radius:10px; margin:10px 0;">
            <div style="font-size:40px; margin-bottom:8px;">{current_cat_expression} {current_food_emoji}</div>
            <p style="font-size:16px; margin:0; color:#666;">来週もらえる餌<br><strong>{current_food_type}</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 次の目標
    next_goal = get_next_goal_message(week_points)
    st.info(next_goal)
    
    # 餌の種類プレビュー（小さく表示）
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("**🍽️ 餌の種類**")
    st.caption("ポイントを貯めて猫様に豪華な餌を！")
    
    # 2x2グリッドで4種の餌を表示
    food_col1, food_col2 = st.columns(2)
    
    food_items = [
        ("カリカリ", 0, "🍚"),
        ("ちゅ〜る", 31, "🍥"),
        ("サーモン", 71, "🐟"),
        ("高級マグロ", 101, "🍣"),
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
            status = "✓" if unlocked else "🔒"
            
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
# 右側: 週次餌やりイベント (【修正版】ユーザー選択式)
# ---------------------
with col_right:
    st.markdown("#### 🍽️ 週次餌やりイベント")
    st.caption(f"先週({last_week_range})貯めたポイントで、特別な餌をあげよう!")

    # 買える餌のリストが空かどうかをチェック
    if weekly_balance == 0:
        # 残高がない
        st.info("💡 餌やり可能なポイントがありません")
        st.caption("今週気分を登録してポイントを貯めましょう!")
    
    elif not affordable_feeds:
        # ポイントはあるが、買える餌がない（feed_pointが0pt超の餌が買えない場合）
        st.info(f"💡 残高: {weekly_balance}pt。交換可能な餌がありません。")
        st.caption("もう少しポイントを貯めて、より豪華な餌にチャレンジしましょう！")

    else:
        # 残高表示
        st.metric(
            label="餌やり可能残高", 
            value=f"{weekly_balance}pt"
        )
        
        # 買える餌の選択肢リストを作成 (例: "ちゅ〜る (300pt)")
        food_options = [
            f"{f['feed_name']} ({f['feed_point']}pt)" 
            for f in affordable_feeds
        ]
        
        # ユーザーに選択させるUI
        selected_option = st.selectbox(
            "🎁 あげる餌を選んでください",
            food_options,
            key="feed_select"
        )
        
        # 選択された名前から、元のデータ(辞書)を特定する
        selected_feed_name = selected_option.split(" (")[0]
        # next() を使ってリスト内から該当する餌データを取得
        selected_feed = next(f for f in affordable_feeds if f['feed_name'] == selected_feed_name)
        
        selected_feed_emoji = FOOD_EMOJIS.get(selected_feed_name, "🐱")
        selected_feed_cost = selected_feed['feed_point']
        
        # 選択中の餌の情報をUIで表示
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
                選択中の餌: <strong>{selected_feed_name}</strong><br>
                消費ポイント: <strong>{selected_feed_cost}pt</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 餌やりボタン
        if st.button(
            f"🍽️ {selected_feed_name}をあげる（{selected_feed_cost}pt消費）", 
            key="weekly_feed_button", 
            type="primary", 
            use_container_width=True
        ):
            # 餌IDと消費ポイントを取得
            feed_id = selected_feed['id']
            feed_point = selected_feed['feed_point']
            
            # 残高チェック＆減算
            if deduct_weekly_balance(supabase, user_id, feed_point):
                # 餌やり実行
                success = execute_weekly_feeding_event(supabase, user_id, feed_id)
                
                if success:
                    # 成功メッセージとリロード
                    new_balance = weekly_balance - feed_point
                    
                    st.success(f"🎉 {selected_feed_name}をあげました!")
                    st.balloons()
                    
                    # アニメーション表示
                    selected_cat_expression = CAT_EXPRESSIONS.get(selected_feed_name, "🐱")
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
                            猫様たち大喜び！
                        </h2>
                        <p style="font-size: 16px; color: white; margin: 0;">
                            残高: {new_balance}pt<br>
                            また餌をあげられます！
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 2秒待ってからリロード
                    time.sleep(2)
                    st.rerun()

                else:
                    st.error("餌やりログの登録に失敗しました。")
            else:
                st.error("残高が足りません。選択した餌のポイントを確認してください。")
# ---
# 最近の餌やり履歴(週次イベント内)
# ---

# ★ 以下のブロックは、週次イベントの `else:` のスコープの外に配置してください。
# これが `with col_right:` の最後のコンテンツになります。

with st.expander("📅 最近の餌やり履歴", expanded=False):
    # get_feeding_historyの修正（limit=3を追加）が必要です。
    history = get_feeding_history(supabase, user_id, limit=3)
    
    if not history:
        st.info("まだ餌やり履歴がありません")
    else:
        for record in history:
            # 日付処理には datetime が必要です
            feed_at = datetime.fromisoformat(record["feed_at"].replace("Z", "+00:00"))
            feed_name = record.get("feed_master", {}).get("feed_name", "不明")
            feed_point = record.get("feed_master", {}).get("feed_point", 0)
            feed_emoji = FOOD_EMOJIS.get(feed_name, "🐱")
            
            # 日付フォーマット
            date_str = feed_at.strftime("%m/%d(%a)")
            
            st.markdown(f"""
            <div style="
                padding: 12px;
                margin: 8px 0;
                background: #f9f9f9;
                border-left: 4px solid #667eea;
                border-radius: 5px;
            ">
                <span style="font-size: 14px;">✅ {date_str}</span>
                <span style="font-size: 20px; margin: 0 8px;">{feed_emoji}</span>
                <strong>{feed_name}</strong>
                <span style="color: #999; margin-left: 8px; font-size: 13px;">({feed_point}pt)</span>
            </div>
            """, unsafe_allow_html=True)

# =========================
# 最近の餌やり履歴(週次イベント内)
# =========================

with col_right:
    with st.expander("📅 最近の餌やり履歴", expanded=False):
        history = get_feeding_history(supabase, user_id, limit=3)
        
        if not history:
            st.info("まだ餌やり履歴がありません")
        else:
            for record in history:
                feed_at = datetime.fromisoformat(record["feed_at"].replace("Z", "+00:00"))
                feed_name = record.get("feed_master", {}).get("feed_name", "不明")
                feed_point = record.get("feed_master", {}).get("feed_point", 0)
                feed_emoji = FOOD_EMOJIS.get(feed_name, "🐱")
                
                # 日付フォーマット
                date_str = feed_at.strftime("%m/%d(%a)")
                
                st.markdown(f"""
                <div style="
                    padding: 12px;
                    margin: 8px 0;
                    background: #f9f9f9;
                    border-left: 4px solid #667eea;
                    border-radius: 5px;
                ">
                    <span style="font-size: 14px;">✅ {date_str}</span>
                    <span style="font-size: 20px; margin: 0 8px;">{feed_emoji}</span>
                    <strong>{feed_name}</strong>
                    <span style="color: #999; margin-left: 8px; font-size: 13px;">({feed_point}pt)</span>
                </div>
                """, unsafe_allow_html=True)

# =========================
# アプリの使い方（アコーディオン）
# =========================

st.markdown("---")

with st.expander("📖 このアプリの使い方を見る", expanded=False):
    st.markdown("""
    ### 🐱 前向きスイッチとは？
    **あなたの気分をケアするアプリです。**  
    気分をオノマトペで登録すると、猫様があなたに合ったアドバイスをくれます。
    気分が良くなるとポイントが貯まり、ご褒美に猫様に餌をあげられます！

    ### 📝 使い方
    1. **気分を登録**: 今の気分をオノマトペで記録
    2. **猫様が登場**: 気分に対応した猫様が現れる
    3. **アドバイスを見る**: 猫様からの提案を受け取る
    4. **気分の変化を記録**: 提案後の気分を登録
    5. **ポイント獲得**: 気分が良くなるほど多くのポイント
    6. **週に餌やり**: 貯めたポイントで翌週に餌をあげる

    ### 🍚🍥 餌の種類
    - 🍚 カリカリ（0pt～）
    - 🍥 ちゅ〜る（31pt～）
    - 🐟 サーモン（71pt～）
    - 🍣 高級マグロ（101pt～）

    ### 😾😸 猫様の表情
    - 😾 カリカリ: ちょっと不機嫌
    - 😸 ちゅ〜る: 普通に嬉しい
    - 😹😹 サーモン: とっても嬉しい
    - 😻😻😻 高級マグロ: 最高に幸せ

    ### 📊 ポイントの稼ぎ方
    - **気分が良くなった**: +10~20ポイント
    - **変わらない**: +5ポイント（挑戦が大事）

    毎日登録すると、どんどんポイントが貯まります 🎉
    
    ---
    
    ### 💡 このアプリの特徴
    - **猫様という相棒**: 一緒に頑張る存在がいる安心感
    - **すぐできる提案**: 具体的で実践しやすいアドバイス
    - **気分の可視化**: ポイントで変化を実感できる
    - **継続の楽しさ**: 猫様への餌やりがモチベーション
    """)

# =========================
# デバッグ情報(本番前に削除)
# =========================
with st.expander("🔍 デバッグ情報（開発用）"):
    st.write("user_id:", user_id)
    st.write("week_points (今週):", week_points)
    st.write("weekly_balance (残高):", weekly_balance)
    st.write("今日:", today)
    st.write("今週の開始:", this_week_start)
    st.write("先週の開始:", last_week_start)
    st.write("先週の終了:", last_week_end)

    st.write("🔍 餌の情報")
    st.write("全餌マスタ (all_feeds):", all_feeds)
    st.write("残高内で購入可能な餌 (affordable_feeds):", affordable_feeds)
    
    # 以前の自動判定ロジックは削除し、新しい変数を確認する
    
    # 今週のポイントから決定される予定の餌
    st.write("今週のポイントから決定される餌(current_food_type):", current_food_type)
    
    if weekly_balance > 0 and 'selected_feed' in locals() and selected_feed:
        # 週次イベントが実行可能な状態かつ、選択肢の処理が通った後の情報を表示
        st.write("ユーザー選択中の餌:", selected_feed)
    elif weekly_balance > 0:
         st.write("⚠️ ユーザーはまだ餌を選択していません")
    else:
         st.write("⚠️ 残高がありません (週次イベント実行不可)")