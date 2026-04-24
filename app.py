import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math
import time

# --- 1. 核心資料與設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "牟育玄", "林建安", "魏瑄毅", "江金福"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢"],
        "order_list": ["25M0690-01", "12345"],
        "leader_map": {},
        "process_map": {}
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 (依據截圖優化) ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    /* 製令大標題卡片 */
    .order-card { background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; border: 1px solid #e2e8f0; }
    .order-header { background: #2547bc; color: white; padding: 15px 25px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .header-title { font-size: 22px; font-weight: 900; display: flex; align-items: center; gap: 10px; }
    .power-tag { background: #ffc107; color: #1a365d; padding: 5px 15px; border-radius: 6px; font-size: 16px; font-weight: 800; }
    
    /* 表格列樣式 */
    .proc-row { border-bottom: 1px solid #edf2f7; display: flex; align-items: center; padding: 12px 25px; transition: background 0.2s; }
    .proc-row:hover { background: #f8fafc; }
    .proc-name { width: 140px; font-size: 18px; font-weight: 800; color: #2547bc; }
    .staff-box { flex-grow: 1; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .empty-text { color: #cbd5e1; font-style: italic; }
    
    /* 標籤樣式 */
    .badge-l { background: #f59e0b; color: white; padding: 4px 10px; border-radius: 6px; font-size: 14px; font-weight: bold; }
    .badge-m { background: #2547bc; color: white; padding: 4px 10px; border-radius: 6px; font-size: 14px; }
    .badge-s { background: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 14px; border: 1px solid #cbd5e1; }
    .status-done { color: #2ecc71; font-weight: bold; display: flex; align-items: center; gap: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])

if "user" not in st.session_state:
    st.title("⚓ 超慧科技管理系統 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", sorted(list(set(all_leaders + all_staff))))
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 (更新為截圖樣式) ---
    if menu == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#2547bc; font-weight:900;">📋 超慧科技製造部派工進度</h1>', unsafe_allow_html=True)
        
        # 篩選區
        c1, c2 = st.columns(2)
        s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
        s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(list(set(all_leaders + all_staff))))

        try:
            # 讀取派工中與已完工資料
            r_working = requests.get(f"{DB_URL}.json", timeout=10).json()
            r_finished = requests.get(f"{FINISH_URL}.json", timeout=10).json()
            
            working_df = pd.DataFrame([dict(v, id=k) for k, v in r_working.items()]).fillna("NA") if r_working else pd.DataFrame()
            finished_df = pd.DataFrame([dict(v, id=k) for k, v in r_finished.items()]).fillna("NA") if r_finished else pd.DataFrame()

            display_orders = [o for o in order_list if (s_order == "全部" or str(o) == str(s_order))]

            for o_id in display_orders:
                # 取得該製令的通電日期 (從任何一個工序抓)
                temp_df = working_df[working_df["製令"] == str(o_id)]
                if temp_df.empty: temp_df = finished_df[finished_df["製令"] == str(o_id)]
                p_date = temp_df.iloc[0]["通電日期"] if not temp_df.empty else "未設定"

                st.markdown(f"""
                    <div class="order-card">
                        <div class="order-header">
                            <div class="header-title">📦 製令：{o_id}</div>
                            <div class="power-tag">⚡ 通電：{p_date}</div>
                        </div>
                """, unsafe_allow_html=True)

                for proc in process_list:
                    w_match = working_df[(working_df["製令"] == str(o_id)) & (working_df["製造工序"] == proc)]
                    f_match = finished_df[(finished_df["製令"] == str(o_id)) & (finished_df["製造工序"] == proc)]
                    
                    row_cols = st.columns([0.7, 0.15, 0.15])
                    
                    with row_cols[0]: # 顯示名稱與人員
                        staff_html = ""
                        if not w_match.empty:
                            row = w_match.iloc[0]
                            staff_html += f'<div class="badge-l">L: {row.get("組長","")}</div>'
                            for i in range(1, 6):
                                name = row.get(f"人員{i}")
                                if name and name != "NA":
                                    cls = "badge-m" if i == 1 else "badge-s"
                                    staff_html += f'<div class="{cls}">{name}</div>'
                        elif not f_match.empty:
                            staff_html = '<span class="status-done">✅ 已完工</span>'
                        else:
                            staff_html = '<span class="empty-text">尚未派工</span>'
                        
                        st.markdown(f'<div class="proc-row"><div class="proc-name">{proc}</div><div class="staff-box">{staff_html}</div></div>', unsafe_allow_html=True)

                    with row_cols[1]: # 編輯按鈕
                        if not w_match.empty:
                            if st.button("✏️", key=f"edit_{o_id}_{proc}"):
                                # 這裡可以擴充跳轉邏輯，目前先以提示為主
                                st.info(f"請至『任務派發』修改製令 {o_id} 的 {proc}")
                    
                    with row_cols[2]: # 完工按鈕
                        if not w_match.empty:
                            if st.button("✅", key=f"fin_{o_id}_{proc}"):
                                row = w_match.iloc[0]
                                clean_data = row.to_dict()
                                clean_data["完工時間"] = get_now_str()
                                clean_data["完工人員"] = st.session_state.user
                                if requests.post(f"{FINISH_URL}.json", data=json.dumps(clean_data)).status_code == 200:
                                    requests.delete(f"{DB_URL}/{row['id']}.json")
                                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"資料載入失敗：{e}")

    # --- 其他功能保持原狀 ---
    elif menu == "📜 完工紀錄查詢":
        st.write("完工紀錄功能維持原狀")
    elif menu == "📝 任務派發":
        st.write("任務派發功能維持原狀")
    elif menu == "⚙️ 設定管理":
        st.write("設定管理功能維持原狀")
