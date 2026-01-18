import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
import requests
import base64
import time

# 1. 頁面設定 (必須放在第一行)
st.set_page_config(page_title="SEO 自動化流量引擎", layout="wide", page_icon="🚀")

# ==========================================
# 🔐 安全閘門 (Security Gate)
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "請輸入系統通行碼 (Access Code)", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again.
        st.text_input(
            "密碼錯誤，請重試", type="password", on_change=password_entered, key="password"
        )
        st.error("❌ 存取被拒絕")
        return False
    else:
        # Password correct.
        return True

# 如果密碼檢查沒通過，就直接停止執行後面的程式
if not check_password():
    st.stop()

# ==========================================
# 🚀 以下是原本的 SEO 工具程式碼 (通過閘門才看得到)
# ==========================================

# 讀取雲端環境變數 (Secrets)
# 注意：上線後，變數會從 Streamlit Cloud 的 Secrets 讀取，而不是 .env
if "GOOGLE_API_KEY" in st.secrets:
    env_api_key = st.secrets["GOOGLE_API_KEY"]
else:
    env_api_key = None

# 初始化 session state
if "generated_article" not in st.session_state: st.session_state.generated_article = None
if "generated_title" not in st.session_state: st.session_state.generated_title = None
if "wp_categories" not in st.session_state: st.session_state.wp_categories = {} 

# 2. 側邊欄：設定中心
with st.sidebar:
    st.title("⚙️ 控制台")
    st.success("🔓 已登入系統")
    
    if env_api_key:
        st.caption("✅ Google API Key 已載入")
        google_api_key = env_api_key
    else:
        google_api_key = st.text_input("輸入 Google API Key", type="password")
    
    st.markdown("---")
    st.header("🌍 WordPress 連線")
    
    # 從 Secrets 讀取預設值 (若有設定)
    default_url = st.secrets.get("WP_URL", "")
    default_user = st.secrets.get("WP_USER", "")
    default_pass = st.secrets.get("WP_PASSWORD", "")
    
    wp_url = st.text_input("網站網址", value=default_url)
    wp_user = st.text_input("帳號", value=default_user)
    wp_password = st.text_input("應用程式密碼", value=default_pass, type="password")
    
    if st.button("🔄 測試連線並抓取分類"):
        if not wp_url or not wp_user or not wp_password:
            st.error("請填寫完整資訊")
        else:
            try:
                base_url = wp_url.rstrip("/")
                cat_url = f"{base_url}/wp-json/wp/v2/categories?per_page=100"
                clean_password = wp_password.replace(" ", "")
                credentials = f"{wp_user}:{clean_password}"
                token = base64.b64encode(credentials.encode()).decode()
                headers = {"Authorization": f"Basic {token}"}
                
                with st.spinner("連線中..."):
                    res = requests.get(cat_url, headers=headers)
                
                if res.status_code == 200:
                    categories = res.json()
                    cat_dict = {c['name']: c['id'] for c in categories}
                    st.session_state.wp_categories = cat_dict
                    st.success(f"✅ 抓到 {len(categories)} 個分類")
                else:
                    st.error(f"失敗代碼: {res.status_code}")
            except Exception as e:
                st.error(f"錯誤：{str(e)}")
                
    if st.session_state.wp_categories:
         st.caption(f"已同步分類：{len(st.session_state.wp_categories)} 個")

# 3. 主畫面
st.title("🚀 SEO 自動化流量引擎 - Cloud Ver.")
tab1, tab2, tab3 = st.tabs(["📊 1. 關鍵字分析", "✍️ 2. AI 文章寫作", "🚀 3. 自動發佈"])

# (以下邏輯保持不變，直接複製原本的功能)
with tab1:
    st.subheader("關鍵字挖掘")
    c1, c2 = st.columns([3, 1])
    with c1: kw_input = st.text_input("核心關鍵字", key="kw")
    with c2: kw_count = st.selectbox("數量", [10, 20], key="count")
    if st.button("開始挖掘", key="btn1"):
        if not google_api_key: st.error("缺 API Key")
        else:
            try:
                genai.configure(api_key=google_api_key)
                model = genai.GenerativeModel('gemini-3-flash-preview')
                with st.spinner("分析中..."):
                    prompt = f"針對「{kw_input}」產出 {kw_count} 組長尾關鍵字 (JSON格式: 關鍵字, 搜尋量, 難易度)。嚴格 JSON List 格式。"
                    res = model.generate_content(prompt)
                    text = res.text.replace("```json", "").replace("```", "").strip()
                    if "[" in text: text = text[text.find("["):text.rfind("]")+1]
                    st.dataframe(pd.DataFrame(json.loads(text)), use_container_width=True)
            except Exception as e: st.error(str(e))

with tab2:
    st.subheader("SEO 文章生成")
    col_a, col_b = st.columns([2, 1])
    with col_a: topic = st.text_input("文章主題", key="topic")
    with col_b: tone = st.selectbox("語氣", ["專業信任", "親切口語"])
    if st.button("生成文章", key="btn2"):
        if not google_api_key or not topic: st.warning("請輸入主題")
        else:
            try:
                genai.configure(api_key=google_api_key)
                model = genai.GenerativeModel('gemini-3-flash-preview')
                with st.spinner("AI 撰寫中..."):
                    prompt = f"""
                    請撰寫一篇關於「{topic}」的 SEO 文章 (HTML 格式)。語氣：{tone}。
                    1. 使用 <h2>, <h3>。 2. 2000字以上。 3. 含表格。 
                    4. FAQ 用 <details>。 5. 文末 CTA 優化。
                    直接輸出 HTML Body。
                    """
                    res = model.generate_content(prompt)
                    article_html = res.text.replace("```html", "").replace("```", "")
                    st.session_state.generated_title = topic
                    st.session_state.generated_article = article_html
                    st.success("✅ 生成完畢")
                    with st.expander("預覽"): st.markdown(article_html, unsafe_allow_html=True)
            except Exception as e: st.error(str(e))

with tab3:
    st.subheader("🚀 發佈到 WordPress")
    if not st.session_state.generated_article: st.info("請先生成文章")
    else:
        st.write(f"準備發佈：**{st.session_state.generated_title}**")
        if st.session_state.wp_categories:
            cat_name = st.selectbox("選擇文章分類", list(st.session_state.wp_categories.keys()))
            cat_id = st.session_state.wp_categories[cat_name]
        else:
            cat_id = st.number_input("或手動輸入分類 ID", value=1)
        status = st.selectbox("狀態", ["draft (草稿)", "publish (公開)"], index=0)
        if st.button("🚀 確認上傳"):
            if not wp_url: st.error("請設定網站資訊")
            else:
                try:
                    base_url = wp_url.rstrip("/")
                    api_url = f"{base_url}/wp-json/wp/v2/posts"
                    clean_password = wp_password.replace(" ", "")
                    credentials = f"{wp_user}:{clean_password}"
                    token = base64.b64encode(credentials.encode()).decode()
                    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
                    post_data = {"title": st.session_state.generated_title, "content": st.session_state.generated_article, "status": status.split(" ")[0], "categories": [cat_id]}
                    with st.spinner("上傳中..."):
                        res = requests.post(api_url, headers=headers, json=post_data)
                    if res.status_code == 201:
                        st.balloons()
                        st.success("🎉 發佈成功！")
                        st.markdown(f"[查看文章]({res.json()['link']})")
                    else: st.error(f"失敗：{res.text}")
                except Exception as e: st.error(str(e))