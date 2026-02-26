import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與精簡時間函數 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"

def get_now_str():
    # 取得台灣時間，格式化為 2026-02-26 16:07:27
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="生產日報管理系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("選擇姓名", ["管理員", "李小龍", "賴智文", "黃沂澈"])
    p = st.text_input("輸入代碼", type="password")
    if st.button("登入", use_container_width=True):
        codes = {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澈": "000000"}
        if u in codes and p == codes[u]:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    # --- 顯示當前登錄者 (左側大字顯示) ---
    st.sidebar.markdown(f"## 👤 {st.session_state.user}")
    
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報頁面 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        with st.expander("⏱️ 計時器工具 (移除微秒顯示)", expanded=True):
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
                    st.session_state.dur = f"{diff.seconds//3600}時 {(diff.seconds%3600)//60}分"
                    st.rerun()
            if c3.button("🧹 清除"):
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
                # 提交時直接使用中文 Key，確保資料庫與表格顯示一致
                log = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order,
                    "PN": pn, "類型": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": st.session_state.get('t1', 'N/A'),
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=log)
                st.success("✅ 提交成功！")

    # --- 4. 歷史紀錄查詢頁面 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                # 建立表格並進行欄位翻譯
                df = pd.DataFrame(list(data.values()))
                
                # 建立翻譯對照表，對應您圈選的英文欄位
                cmap = {
                    "name": "姓名", "hours": "累計工時", "order_no": "製令",
                    "pn": "PN", "stage": "工段名稱", "status": "狀態",
                    "submit_time": "提交時間", "time": "提交時間", "type": "類型",
                    "start_time": "開始時間", "startTime": "開始時間"
                }
                df = df.rename(columns=cmap)
                
                # 安全排序：優先找「提交時間」，找不到則不排序
                if "提交時間" in df.columns:
                    df = df.sort_values(by="提交時間", ascending=False)
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前尚無資料。")
        except Exception as e:
            st.error(f"讀取失敗：{e}")
