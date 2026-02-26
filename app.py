import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與台灣時間 (修正 07:12 偏差) ---
# 使用單一資料夾 path，確保資料不會橫向散開
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/production_records"

def get_now():
    # 強制對齊台灣 UTC+8 時間
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 資料庫讀寫 ---
def save_to_db(data):
    try: requests.post(f"{DB_URL}.json", json=data)
    except: pass

def read_from_db():
    try:
        r = requests.get(f"{DB_URL}.json")
        return r.json()
    except: return None

# --- 3. 系統登入 ---
st.set_page_config(page_title="數位報工系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 員工登入")
    u = st.selectbox("請選擇姓名", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("輸入代碼", type="password")
    if st.button("進入系統", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("代碼錯誤")
else:
    # --- 4. 功能選單 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 紀錄查詢"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 5. 工時回報頁面 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器 (解決累計工時 0.00 問題)
        with st.expander("⏱️ 工時計時器", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start_time = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'start_time' in st.session_state:
                    st.session_state.end_time = get_now()
                    diff = st.session_state.end_time - st.session_state.start_time
                    h, m = diff.seconds // 3600, (diff.seconds % 3600) // 60
                    st.session_state.diff_str = f"{h}小時 {m}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間", use_container_width=True):
                for k in ['start_time', 'end_time', 'diff_str']: st.session_state.pop(k, None)
                st.rerun()

            st.write(f"🕒 紀錄開始：{st.session_state.get('start_time','---')} | ⌛ 紀錄結束：{st.session_state.get('end_time','---')}")

        # 回報表單
        with st.form("work_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('diff_str', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log = {
                    "姓名": st.session_state.user,
                    "工號": "1234" if st.session_state.user == "李小龍" else "0000",
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "累計工時": hours,
                    "開始時間": str(st.session_state.get('start_time', 'N/A')),
                    "結束時間": str(get_now()) # 確保提交時間對齊台灣
                }
                save_to_db(log)
                st.success("✅ 紀錄已成功提交！")
                st.rerun()

    # --- 6. 紀錄查詢頁面 ---
    elif menu == "📋 紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        data = read_from_db()
        if data:
            # 將 Firebase 字典轉為表格，不論欄位名稱一律顯示
            df = pd.DataFrame(list(data.values()))
            
            # 排序：最新提交的在上面
            if "結束時間" in df.columns:
                df = df.sort_values(by="結束時間", ascending=False)
            
            st.dataframe(df, use_container_width=True)
            st.info("💡 提示：若紀錄較多，請利用表格右上角的搜尋功能輸入姓名。")
        else:
            st.info("目前尚無資料，請先前往『工時回報』提交一筆紀錄。")
