import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 資料庫路徑設定 (維持原樣) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "12345"],
        "process_map": {
            "陳德文": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢"],
            "吳政昌": ["S.T作業"],
            "劉志偉": ["收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"]
        },
        "staff_map": {} 
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict): return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式設定 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    
    /* === 加深所有輸入框、下拉選單的邊框顏色 === */
    /* 下拉選單框 */
    div[data-baseweb="select"] > div {
        border: 2px solid #475569 !important; /* 加深為深灰色 */
        border-radius: 8px !important;
    }
    
    /* 數字、文字輸入框 */
    .stTextInput input, .stTextArea textarea, .stDateInput input {
        border: 2px solid #475569 !important;
        border-radius: 8px !important;
    }
    
    /* 針對表單內的框框再次強化 */
    div[data-testid="stForm"] div[data-baseweb="select"] > div {
        border: 2px solid #1e293b !important; /* 表單內用更深色 */
    }

    /* 製令卡片 */
    .order-card { 
        background: white; 
        border-radius: 16px; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 25px; 
        overflow: hidden; 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    /* 卡片標題區 */
    .order-header { 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
        color: white; 
        padding: 15px 20px; 
        font-weight: 900; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-size: 1.2rem;
    }
    
    /* 通電日期標籤 */
    .power-date-tag { 
        background: #fbbf24; 
        color: #1e3a8a; 
        padding: 5px 15px; 
        border-radius: 50px; 
        font-size: 14px; 
        font-weight: 800;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 工序行 */
    .proc-row-container {
        padding: 10px 20px;
        border-bottom: 1px solid #f1f5f9;
        transition: background 0.3s;
    }
    .proc-row-container:hover { background-color: #f8fafc; }
    
    .proc-name { 
        font-weight: 800; 
        color: #334155; 
        font-size: 16px;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
    }
    
    /* 人員標籤 */
    .staff-area { display: flex; flex-wrap: wrap; gap: 6px; }
    .badge-staff { 
        background: #dbeafe; 
        color: #1e40af; 
        padding: 4px 12px; 
        border-radius: 6px; 
        font-size: 13px; 
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    
    /* 狀態顯示 */
    .status-done { 
        color: #059669; 
        font-weight: 800; 
        font-size: 15px; 
        background: #ecfdf5;
        padding: 4px 12px;
        border-radius: 8px;
        display: inline-block;
    }
    .status-empty { color: #94a3b8; font-style: italic; font-size: 14px; }
    
    /* 按鈕容器微調 */
    .stButton>button { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
process_map = settings.get("process_map", {})
staff_map = settings.get("staff_map", {}) 

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

# --- 4. 登入介面 ---
if "user" not in st.session_state:
    st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-size:3rem;">⚓ 超慧科技</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#64748b;">生產管理系統 v2.0</p>', unsafe_allow_html=True)
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇您的組長姓名", sorted(all_leaders))
            if st.button("確認登入系統", use_container_width=True, type="primary"):
                st.session_state.user = u
                st.rerun()
else:
    st.sidebar.markdown(f"### 👤 當前人員：{st.session_state.user}")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900; margin-bottom:30px;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

        # --- 對話框 1：編輯人員 ---
        @st.dialog("👥 編輯施工人員", width="medium")
        def edit_staff_dialog(order_id, proc_name, current_data):
            st.subheader(f"🛠️ {proc_name}")
            current_leader = st.session_state.user
            my_team = staff_map.get(current_leader, [])
            display_options = my_team if my_team else all_staff
            options = ["NA"] + sorted(list(set(display_options)))

            with st.form("staff_edit_form"):
                st.write(f"📦 製令：{order_id}")
                st.write(f"👤 負責組長：**{current_leader}**")
                
                new_wk = []
                for i in range(5):
                    p_val = current_data.get(f"人員{i+1}", "NA")
                    d_idx = options.index(p_val) if p_val in options else 0
                    sel = st.selectbox(f"人員 {i+1}", options, index=d_idx, key=f"dlg_staff_{i}")
                    new_wk.append(sel)
                
                if st.form_submit_button("💾 儲存修改", use_container_width=True):
                    new_payload = current_data.copy()
                    new_payload.update({
                        "最後更新": get_now_str(),
                        "人員1": new_wk[0], "人員2": new_wk[1], "人員3": new_wk[2], "人員4": new_wk[3], "人員5": new_wk[4]
                    })
                    db_id = new_payload.pop("db_id", None)
                    if db_id and db_id != "NA":
                        requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                        st.success("✅ 人員更新成功！")
                        time.sleep(0.5); st.rerun()

        # --- 對話框 2：修改通電日期 ---
        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
            st.subheader(f"📦 製令：{order_id}")
            try:
                default_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d") if current_date_str != "未設定" else datetime.date.today()
            except:
                default_date = datetime.date.today()
            new_
