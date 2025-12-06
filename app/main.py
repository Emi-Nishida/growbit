# app/main.py (案B: 2カラム並び版)
import streamlit as st
import unicodedata
import time
from utils.services import (
    get_supabase_client,
    get_or_create_user_id,
    get_current_week_points,
    get_food_type_by_points,
    get_next_goal_message,
    get_last_week_total_points,
    has_fed_this_week,
    get_feed_id_by_points,
    execute_weekly_feeding_event,
    get_feeding_history,
    get_week_start_date,
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

# データ取得
week_points = get_current_week_points(supabase, user_id)

# 先週の開始日を明示的に指定してポイントを取得
today = datetime.now().date()
this_week_start = get_week_start_date(today)
last_week_start = this_week_start - timedelta(days=7)

last_week_points = get_last_week_total_points(supabase, user_id)
already_fed = has_fed_this_week(supabase, user_id)

response = (
    supabase.table("weekly_points")
    .select("total_points")
    .eq("user_id", user_id)
    .eq("week_start_date", last_week_start.isoformat())
    .execute()
)

if response.data:
    last_week_points = response.data[0]["total_points"]
else:
    last_week_points = 0

already_fed = has_fed_this_week(supabase, user_id)

# 今週の餌(予定)
current_food_type = get_food_type_by_points(week_points)
current_food_emoji = FOOD_EMOJIS.get(current_food_type, "🐱")
current_cat_expression = CAT_EXPRESSIONS.get(current_food_type, "🐱")

# 先週の餌
last_week_food_type = get_food_type_by_points(last_week_points)
last_week_food_emoji = FOOD_EMOJIS.get(last_week_food_type, "🐱")
last_week_cat_expression = CAT_EXPRESSIONS.get(last_week_food_type, "🐱")

# 先週の日付範囲
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
        <div style="text-align:center; padding:20px; background:#f9f9f9; border-radius:10px; margin:10px 0;">
            <div style="font-size:40px; margin-bottom:10px;">{current_cat_expression} {current_food_emoji}</div>
            <p style="font-size:16px; margin:0; color:#666;">来週もらえる餌<br><strong>{current_food_type}</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 次の目標
    next_goal = get_next_goal_message(week_points)
    st.info(next_goal)

# ---------------------
# 右側: 週次餌やりイベント
# ---------------------
with col_right:
    st.markdown("#### 🍽️ 週次餌やりイベント")
    st.caption(f"先週({last_week_range})貯めたポイントで、特別な餌をあげよう!")
    
    if last_week_points == 0:
        # 先週ポイントがない
        st.info("💡 先週のポイントがありません")
        st.caption("今週気分を登録してポイントを貯めましょう!")
    
    elif already_fed:
        # すでに餌やり済み
        st.success("✅ 今週はすでに餌をあげました!")
        
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 25px;
            background: linear-gradient(135deg, #fff9e6 0%, #ffe6f0 100%);
            border-radius: 12px;
            margin: 15px 0;
        ">
            <div style="font-size: 60px; margin-bottom: 10px;">😻😻😻</div>
            <p style="font-size: 16px; color: #666; margin: 0;">
                猫様たちは大満足！<br>
                また来週も頑張りましょう！
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # 餌やり可能
        st.metric(
            label="先週の獲得ポイント", 
            value=f"{last_week_points}pt"
        )
        
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 10px;
            border: 2px solid #667eea;
            margin: 10px 0;
        ">
            <div style="font-size: 40px; margin-bottom: 5px;">{last_week_cat_expression} {last_week_food_emoji}</div>
            <p style="font-size: 16px; margin: 0; color: #666;">
                今週の特別な餌<br>
                <strong>{last_week_food_type}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 餌やりボタン
        if st.button(
            f"🍽️ {last_week_food_type}をあげる", 
            key="weekly_feed_button", 
            type="primary", 
            use_container_width=True
        ):
            # 餌IDを取得
            feed_id = get_feed_id_by_points(supabase, last_week_points)
            
            # 餌やり実行
            success = execute_weekly_feeding_event(supabase, user_id, feed_id)
            
            if success:
                st.success(f"🎉 {last_week_food_type}を全員にあげました!")
                st.balloons()
                
                # アニメーション表示
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 35px;
                    background: linear-gradient(135deg, #ffeb3b 0%, #ff9800 100%);
                    border-radius: 20px;
                    margin: 20px 0;
                    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
                ">
                    <div style="font-size: 80px; margin-bottom: 15px;">{last_week_cat_expression}{last_week_cat_expression}{last_week_cat_expression}</div>
                    <h2 style="color: white; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                        猫様たち大喜び！
                    </h2>
                    <p style="font-size: 16px; color: white; margin: 0;">
                        今週も頑張りましょう！
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 3秒待ってからリロード
                time.sleep(3)
                st.rerun()

            else:
                st.error("❌ 餌やりに失敗しました。もう一度お試しください。")

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
    st.write("last_week_points:", last_week_points)
    st.write("今日:", today)
    st.write("今週の開始:", this_week_start)
    st.write("先週の開始:", last_week_start)
    st.write("先週の終了:", last_week_end)

    st.write("🔍 餌の情報")
    st.write("ポイントから判定した餌:", repr(last_week_food_type))
    st.write("餌のバイト列:", last_week_food_type.encode('utf-8').hex())
    st.write("餌の長さ:", len(last_week_food_type))

    # 波ダッシュ(U+301C)を全角チルダ(U+FF5E)に置換
    normalized_food = last_week_food_type.replace("\u301C", "\uFF5E").strip()
    st.write("正規化後の餌名:", repr(normalized_food))
    st.write("正規化後のバイト列:", normalized_food.encode('utf-8').hex())
    st.write("正規化後の長さ:", len(normalized_food))

    # NFKC正規化
    normalized_food = unicodedata.normalize("NFKC", last_week_food_type).strip()

    # --- ① feed_name検索（文字列一致チェック用）
    response = supabase.table("feed_master").select("*").eq("feed_name", normalized_food).execute()
    st.write("🔍 feed_name 検索結果:", response)

    if response.data:
        db_name = response.data[0]['feed_name']
        st.write("DBの餌名:", repr(db_name))
        st.write("DBのバイト列:", db_name.encode('utf-8').hex())
        st.write("Pythonとの一致?:", last_week_food_type == db_name)
        st.write("正規化後との一致?:", normalized_food == db_name)
    else:
        st.write("⚠️ DBデータ取得失敗")

    st.write("---")

    # --- ② feed_point検索（ポイントから餌を判定する本流）
    points = int(last_week_points)  # DBから取得した値を利用
    response = (
        supabase.table("feed_master")
        .select("*")
        .lte("feed_point", points)
        .order("feed_point", desc=True)
        .limit(1)
        .execute()
    )
    st.write(f"🔍 feed_point<={points} の最大行:", response)

    if response.data:
        feed = response.data[0]
        feed_id = feed["id"]
        feed_name = feed["feed_name"]
        st.write("取得したfeed_id:", feed_id)
        st.write(f"✅ {points}ポイントに対応する餌は: {feed_name}")
    else:
        st.write("⚠️ ポイントから餌が判定できません")

    st.markdown("---")
