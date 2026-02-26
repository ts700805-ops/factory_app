import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (完全沒動) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"

def get_now_str():
    # 格式化時間：移除微秒與時區
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技工時登錄系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 超慧科技工時登錄系統")
    # ✅ 僅修正名字：黃沂澂
    u = st.selectbox("選擇姓名", ["管理員", "李小龍", "賴智文", "黃沂澂"])
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入", use_container_width=True):
        # ✅ 僅修正字典姓名：黃沂澂
        codes = {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澂": "000000"}
        if u in codes and p == codes[u]:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    # 側邊欄 (完全沒動)
    st.sidebar.markdown(f"## 👤 當前登錄者\n# {st.session_state.user}")
    
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報 (完全沒動) ---
    if menu == "🏗️ 工時回報":
        st.header(f"🏗️ {st.session_state.user} 的工時回報")
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時"):
                st.session_state.t1 = get_now_str()
                st.rerun()
            if c2.button("⏹️ 結束計時"):
                if 't1' in st.session_state:
                    st.session_state.t2 = get_now_str()
                    d1 = datetime.datetime.strptime(st.session_state.t1, "%Y-%m-%d %H:%M:%S")
                    d2 = datetime.datetime.strptime(st.session_state.t2, "%Y-%m-%d %H:%M:%S")
                    diff = d2 - d1
                    st.session_state.dur = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間"):
                for k in ['t1','t2','dur']: st.session_state.pop(k, None)
