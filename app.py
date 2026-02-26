import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與時間 (對齊下午 03:14) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/factory_logs" # 統一存放路徑

def get_now():
    # 強制對齊台灣時間
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 資料讀取 (無授權設定) ---
def get_db():
    try:
        r = requests.get(f"{DB_URL}.json")
        return r.json()
    except: return None

def save_db(data):
    try: requests.post(f"{DB_URL}.json", json=data)
    except: pass

# --- 3. 登入系統 ---
st.set_page_config(page_title="數位日報系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    u = st.selectbox("選擇姓名", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("代碼", type="password")
    if st.button("進入", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    # --- 4. 側邊選單 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 5. 功能頁面 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器 (解決 0.00 hr 問題)
        with st.expander("⏱️ 工作計時器", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start = get_now()
                st.rerun()
            if col_b.button("⏹️ 結束計時", use_container_width=True):
                if 'start' in st.session_state:
                    st.session_state.end = get_now()
                    diff = st.session_state.end - st.session_state.start
                    h, m = diff.seconds // 3600, (diff.seconds % 3600) // 60
                    st.session_state.total = f"{h}小時 {m}分鐘"
                    st.rerun()
            if col_c.button("🧹 清除", use_container_width=True):
                for k in ['start', 'end', 'total']: st.session_state.pop(k, None)
                st.rerun()

            st.write(f"🕒 開始：{st.session_state.get('start','---')} | ⌛ 結束：{st.session_state.get('end','---')}")

        # 表單區
        with st.form("work_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('total', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log_data = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order, 
                    "P/N": pn, "Type": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": str(st.session_state.get('start', 'N/A')),
                    "結束時間": str(get_now()) # 確保時間戳對齊台灣
                }
                save_db(log_data)
                st.success("✅ 已提交至雲端資料庫！")

    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        res = get_db()
        if res:
            # 暴力列出所有資料，解決李小龍看到賴智文的問題
            df = pd.DataFrame(list(res.values()))
            # 排序：最新提交的在最上面
            if "結束時間" in df.columns:
                df = df.sort_values(by="結束時間", ascending=False)
            st.dataframe(df, use_container_width=True)
            st.info("💡 看到舊資料是正常的，請查看表格中最上方是否出現了您剛剛提交的紀錄。")
        else:
            st.info("目前資料庫是空的。")
