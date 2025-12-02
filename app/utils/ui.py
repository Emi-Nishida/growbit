# app/utils/ui.py
import streamlit as st
from typing import Optional

# =========================
# 共通スタイル
# =========================

BASE_STYLES = """
<style>
  /* サイドバー */
  section[data-testid="stSidebar"] { 
    width: 180px !important; 
    min-width: 180px !important; 
  }
  
  /* メインコンテンツ */
  .main .block-container { 
    max-width: 1240px; 
    padding: 1.25rem 1rem 2rem 1rem; 
  }

  /* HOMEボタン */
  .home-button { 
    position: fixed; 
    top: 0.7rem; 
    left: 0.7rem; 
    padding: 0.5rem 0.9rem;
    background-color: rgba(240,242,246,0.9); 
    border-radius: 0.3rem; 
    text-decoration: none;
    font-size: 0.9rem; 
    color: #262730; 
    border: 1px solid #ddd; 
    z-index: 99;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
    transition: background-color 0.2s ease; 
  }
  .home-button:hover { 
    background-color: #e0e2e6; 
    text-decoration: none; 
  }

  /* タイトルスペーサー */
  .page-title-spacer { 
    margin-left: 3.5rem; 
    padding-top: 0.5rem; 
    height: 0.5rem; 
  }

  /* ボタン */
  .stButton > button { 
    padding: 0.95rem 1rem !important; 
    font-weight: 800 !important; 
    font-size: 0.98rem !important;
    letter-spacing: 0.01em; 
    border-radius: 8px; 
  }
  
  button[kind="primary"] { 
    text-shadow: 0 1px 1px rgba(0,0,0,0.25); 
    border: 1px solid rgba(0,0,0,0.08); 
  }
  
  button[kind="primary"]:hover { 
    text-shadow: 0 1px 1px rgba(0,0,0,0.35); 
    border-color: rgba(0,0,0,0.15); 
  }

  /* エキスパンダー */
  details > summary { 
    padding: 0.9rem 0.75rem !important; 
    font-weight: 600; 
    font-size: 0.98rem; 
    list-style: none; 
    cursor: pointer; 
  }
  
  details > summary::-webkit-details-marker { 
    display: none; 
  }
</style>
"""

def inject_base_styles() -> None:
    """共通スタイルを注入"""
    st.markdown(BASE_STYLES, unsafe_allow_html=True)

# =========================
# HOMEボタン
# =========================

def home_button(label: str = "🏠 HOME", href: str = "/") -> None:
    """HOMEボタンを表示"""
    st.markdown(
        f'<a href="{href}" class="home-button" target="_self">{label}</a>', 
        unsafe_allow_html=True
    )

# =========================
# タイトル with スペーサー
# =========================

def title_with_spacer(text: str, add_spacer: bool = True) -> None:
    """タイトルを表示（HOMEボタン用のスペーサー付き）"""
    if add_spacer:
        st.markdown('<div class="page-title-spacer"></div>', unsafe_allow_html=True)
    st.title(text)

# =========================
# ページセットアップ（共通初期化）
# =========================

def setup_page(
    page_title: str,
    page_icon: Optional[str] = None,
    layout: str = "wide",
    initial_sidebar_state: str = "collapsed",
    show_home: bool = True,
    home_href: str = "/",
    add_title_spacer: bool = True,
) -> None:
    """ページの共通初期化"""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon or "🐱",
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )
    inject_base_styles()
    if show_home:
        home_button(href=home_href)
    title_with_spacer(page_title, add_spacer=add_title_spacer)