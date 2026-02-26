import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與時間 (移除微秒與時區顯示) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"

def get_now_str():
    # 取得台灣時間並格式化為: 2026-02-26 16:07:27
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="數位工單系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("選擇人員", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("輸入代碼", type="password")
    if st.button("進入系統", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    # --- 顯示登錄者姓名 (您的新要求) ---
    st.markdown(f"# 👤 當前登錄者：{st.session_state.user}")
    
    # --- 3. 側邊選單 ---
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 4. 工時回報 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.t1 = get_now_str() # 直接存入精簡字串
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 't1' in st.session_state:
                    st.session_state.t2 = get_now_str()
                    # 計算工時 (秒數差)
                    fmt = "%Y-%m-%d %H:%M:%S"
                    d1 = datetime.datetime.strptime(st.session_state.t1, fmt)
                    d2 = datetime.datetime.strptime(st.session_state.t2, fmt)
                    diff = d2 - d1
                    st.session_state.dur = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間", use_container_width=True):
                for k in ['t1', 't2', 'dur']: st.session_state.pop(k, None)
                st.rerun()
            
            # 顯示精簡後的時間 (不再有微秒)
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
                    "姓名": st.session_state.user,
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "累計工時": hours,
                    "開始時間": st.session_state.get('t1', 'N/A'),
                    "提交時間": get_now_str()
                }
                try:
                    requests.post(f"{DB_URL}.json", json=log)
                    st.success("✅ 紀錄已成功提交至 work_logs！")
                except:
                    st.error("❌ 提交失敗，請檢查網路。")

    # --- 5. 紀錄查詢 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                # 將 Firebase 資料轉為表格
                df = pd.DataFrame(list(db_data.values()))
                # 排序：最新提交的在上面
                if "提交時間" in df.columns:
                    df = df.sort_values(by="提交時間", ascending=False)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前資料庫內沒有紀錄。")
        except:
            st.error("讀取資料庫失敗。")
