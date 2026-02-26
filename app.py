import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 (請確認網址結尾沒有多餘空格) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/.json"

def get_tw_time():
    # 強制對齊您電腦右下角的台灣時間
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 頁面配置 ---
st.set_page_config(page_title="生產日報-終極穩定版", layout="wide")

# --- 3. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("姓名", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("代碼", type="password")
    if st.button("進入系統", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼不正確")
else:
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 紀錄查詢"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 4. 功能：工時回報 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器區塊
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start_raw = get_tw_time()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'start_raw' in st.session_state:
                    now = get_tw_time()
                    diff = now - st.session_state.start_raw
                    st.session_state.duration = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除", use_container_width=True):
                for k in ['start_raw', 'duration']: st.session_state.pop(k, None)
                st.rerun()
            
            st.info(f"🕒 本次開始時間：{st.session_state.get('start_raw', '尚未開始')}")

        # 表單區塊
        with st.form("main_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('duration', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                new_data = {
                    "姓名": st.session_state.user,
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "累計工時": hours,
                    "開始時間": str(st.session_state.get('start_raw', 'N/A')),
                    "提交時間": str(get_tw_time())
                }
                # 使用 requests 直接推送到最頂層路徑
                try:
                    res = requests.post(DB_BASE_URL, json=new_data)
                    if res.status_code == 200:
                        st.success("✅ 存檔成功！請切換至紀錄查詢查看。")
                    else:
                        st.error(f"❌ 存檔失敗，錯誤碼：{res.status_code}")
                except Exception as e:
                    st.error(f"❌ 連線異常：{e}")

    # --- 5. 功能：紀錄查詢 ---
    elif menu == "📋 紀錄查詢":
        st.header("📋 歷史紀錄清單")
        try:
            r = requests.get(DB_BASE_URL)
            raw_json = r.json()
            
            if raw_json:
                # 處理 Firebase 回傳的雜亂格式
                all_logs = []
                for key, val in raw_json.items():
                    if isinstance(val, dict): # 確保是我們存入的物件格式
                        all_logs.append(val)
                
                if all_logs:
                    df = pd.DataFrame(all_logs)
                    # 依時間排序
                    if "提交時間" in df.columns:
                        df = df.sort_values(by="提交時間", ascending=False)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("資料庫內有東西，但格式無法解析。")
                    st.json(raw_json) # 暴力顯示原始資料供偵錯
            else:
                st.info("目前資料庫完全沒有任何內容")
        except Exception as e:
            st.error(f"讀取失敗：{e}")
