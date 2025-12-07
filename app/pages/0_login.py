import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
superbase_url = os.getenv("SUPABASE_URL")
superbase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(superbase_url, superbase_key)

def sign_up(email, password):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        if user and user.user:
            # 新規登録時にusersテーブルにAuth UUIDをidとして保存
            supabase.table("users").upsert({
                "id": user.user.id, # Supabase AuthのUUID
                "email": email,
            }).execute()
    except Exception as e:
        st.error(f"Sign-up failed: {e}")

def sign_in(email, password):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user and user.user:
            auth_user_id = user.user.id
            #セッションに保存(DB更新なし)
            st.session_state["user_email"] = user.user.email
            st.session_state["auth_user_id"] = auth_user_id
            st.success(f"Welcome back, {email}!")
            #ログイン成功後にmainへ遷移
            st.switch_page("main.py")
        return user
    except Exception as e:
        st.error(f"Login failed: {e}")

def sign_out():
    try:
        supabase.auth.sign_out()
        st.session_state.user_email = None
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")

def main_app(user_email):
    st.title("🎉Welcome Page")
    st.success(f"Welcome, {user_email}!👋")
    if st.button("Logout"):
        sign_out()

def auth_screen():
    st.title("🔐 Login Page")
    option = st.selectbox("Choose an option", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Sign Up" and st.button("Register"):
        user = sign_up(email, password)
        if user and user.user:
            st.success("Registration successful! Please log in.")

    if option == "Login" and st.button("Login"):
        user = sign_in(email, password)
        if user and user.user:
            st.session_state.user_email = user.user.email
            st.success(f"Welcome back, {email}!")
            st.rerun()
# =========================
# 画面設定
# =========================    
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if st.session_state.user_email:
    main_app(st.session_state.user_email)
else:
    auth_screen()