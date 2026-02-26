import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"

def get_now_str():
    # 格式化時間：刪除微秒與時區，只留秒
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技工時登錄系統", layout="wide")

if "user" not in st.session_state:
    # 修改標題為您要求的名稱
    st.title("🔐 超慧科技工時登錄系統")
    u = st.selectbox("選擇姓名", ["管理員", "李小龍", "賴智文", "黃沂澈"])
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入", use_container_width=True):
        codes = {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澈": "000000"}
        if u in codes and p == codes[u]:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    # 側邊欄：顯示當前登錄者
    st.sidebar.markdown(f"## 👤 當前登錄者\n# {st.session_state.user}")
    
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報 (維持成功邏輯) ---
    if menu == "🏗️ 工時回報":
        st.header(f"🏗️ {st.session_state.user} 的工時回報")
        
        with st.expander("⏱️ 計時器工具 (已精簡時間)", expanded=True):
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
                st.rerun()
            st.write(f"🕒 開始：{st.session_state.get('t1','--')} | ⌛ 結束：{st.session_state.get('t2','--')}")

        with st.form("work_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('dur', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order,
                    "PN": pn, "類型": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": st.session_state.get('t1', 'N/A'),
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=log)
                st.success("✅ 紀錄已成功提交！")

    # --- 4. 歷史紀錄查詢 (解決資料不顯示與 None 問題) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                # 建立原始表格
                df = pd.DataFrame(list(data.values()))
                
                # 強大翻譯對照表：解決帶冒號或英文標籤的問題
                rename_map = {
                    "name": "姓名", "hours": "累計工時", "order_no": "製令", "製令:": "製令",
                    "pn": "PN", "PN:": "PN", "stage": "工段名稱", "工段名稱:": "工段名稱",
                    "status": "狀態", "狀態:": "狀態", "type": "類型", "類型:": "類型",
                    "submit_time": "提交時間", "time": "提交時間", "提交時間:": "提交時間",
                    "start_time": "開始時間", "startTime": "開始時間",
