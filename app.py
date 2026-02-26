import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (對齊您的 Firebase 網址) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"
LOG_PATH = "work_logs"

def get_now_str():
    # 取得台灣時間並格式化，刪除微秒與時區
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="生產日報管理系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("請選擇您的姓名", ["管理員", "李小龍", "賴智文", "黃沂澈"])
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入", use_container_width=True):
        # 管理員權限與一般員工代碼
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or \
           (u == "賴智文" and p == "098057") or (u == "黃沂澈" and p == "000000"):
            st.session_state.user = u
            st.rerun()
        else:
            st.error("❌ 代碼輸入錯誤")
else:
    # --- 顯示登錄者 (新要求) ---
    st.sidebar.markdown(f"### 👤 當前登錄者\n## {st.session_state.user}")
    
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報頁面 ---
    if menu == "🏗️ 工時回報":
        st.header(f"🏗️ {st.session_state.user} 的生產日報回報")
        
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start_t = get_now_str()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'start_t' in st.session_state:
                    st.session_state.end_t = get_now_str()
                    t1 = datetime.datetime.strptime(st.session_state.start_t, "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.datetime.strptime(st.session_state.end_t, "%Y-%m-%d %H:%M:%S")
                    diff = t2 - t1
                    st.session_state.work_h = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除", use_container_width=True):
                for k in ['start_t', 'end_t', 'work_h']: st.session_state.pop(k, None)
                st.rerun()
            
            # 顯示精簡時間
            st.write(f"🕒 開始：{st.session_state.get('start_t','--')} | ⌛ 結束：{st.session_state.get('end_t','--')}")

        with st.form("work_log_form"):
            col = st.columns(3)
            status = col[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = col[1].text_input("製令")
            pn = col[2].text_input("P/N")
            
            col2 = st.columns(3)
            tp = col2[0].text_input("Type")
            stage = col2[1].text_input("工段名稱")
            hours = col2[2].text_input("累計工時", value=st.session_state.get('work_h', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                payload = {
                    "name": st.session_state.user,
                    "status": status, "order_no": order, "pn": pn, "type": tp, "stage": stage,
                    "hours": hours,
                    "start_time": st.session_state.get('start_t', 'N/A'),
                    "submit_time": get_now_str()
                }
                # 提交至 work_logs
                requests.post(f"{DB_BASE_URL}{LOG_PATH}.json", json=payload)
                st.success("✅ 紀錄已成功提交！請至查詢頁面確認。")

    # --- 4. 歷史紀錄查詢頁面 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        
        # 從 work_logs 抓取資料
        response = requests.get(f"{DB_BASE_URL}{LOG_PATH}.json")
        all_data = response.json()
        
        if all_data:
            # 將 Firebase 資料轉換為表格並顯示
            df = pd.DataFrame(list(all_data.values()))
            
            # 依提交時間倒序排列
            if "submit_time" in df.columns:
                df = df.sort_values(by="submit_time", ascending=False)
            
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ 目前資料庫中沒有任何紀錄。請先完成一筆「工時回報」並提交。")
