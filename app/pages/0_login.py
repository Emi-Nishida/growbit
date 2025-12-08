import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# ページ設定
st.set_page_config(
    page_title="ログイン - 猫様アプリ",
    page_icon="😸",
    layout="centered"
)

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def sign_up(email, password):
    """新規登録処理"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response and response.user:
            # Supabaseのusersテーブルに Auth UUIDをidとして保存
            supabase.table("users").upsert({
                "id": response.user.id,
                "email": email,
            }).execute()
            st.success("✅ 登録成功!メールを確認してアカウントを有効化してください。")
            return response
    except Exception as e:
        st.error(f"❌ 登録失敗: {e}")
        return None

def sign_in(email, password):
    """ログイン処理"""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response and response.user:
            # セッションに保存
            st.session_state["user_email"] = response.user.email
            st.session_state["auth_user_id"] = response.user.id
            st.success(f"✅ ようこそ、{email}!")
            # ログイン成功後にmainへ遷移
            st.switch_page("main.py")
        return response
    except Exception as e:
        st.error(f"❌ ログイン失敗: {e}")
        return None

def auth_screen():
    """ログイン画面"""
    st.title("😸 猫様アプリへようこそ")
    st.markdown("### 気分を記録して、猫様からアドバイスをもらおう!")
    st.markdown("---")
    
    option = st.selectbox("選択してください", ["ログイン", "新規登録"])
    email = st.text_input("メールアドレス", key="email_input")
    password = st.text_input("パスワード", type="password", key="password_input")

    if option == "新規登録":
        if st.button("🎉 登録する", type="primary", use_container_width=True):
            if email and password:
                sign_up(email, password)
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")

    if option == "ログイン":
        if st.button("🔑 ログイン", type="primary", use_container_width=True):
            if email and password:
                sign_in(email, password)
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")

# =========================
# メイン画面制御
# =========================    
if "auth_user_id" not in st.session_state:
    st.session_state.auth_user_id = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ログイン済みなら自動的にmain.pyへリダイレクト
if st.session_state.auth_user_id:
    st.switch_page("main.py")
else:
    auth_screen()