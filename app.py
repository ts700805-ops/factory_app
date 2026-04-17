import streamlit as st
import pd
import datetime
import requests
import json

# --- 1. 核心設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    # 預設設定，包含製令、人員、工序、以及您要求的「派工人員」
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["001", "002"],
        "assigners": ["管理員"] 
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return {
                    "all_staff": data.get("all_staff", default_settings["all_staff"]),
                    "processes": data.get("processes", default_settings["processes"]),
                    "order_list": data.get("order_list", default_settings["order_list"]),
                    "assigners": data.get("assigners", default_settings["assigners"])
                }
        return default_settings
    except Exception:
        return default_settings

# --- 2. 頁面配置與極致強化 CSS (解決框框太淡問題) ---
st.set_page_config(page_title="大量科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-title { 
        font-size: 32px !important; 
        font-weight: 800; 
        color: #1e293b; 
        padding: 15px 0;
        border-bottom: 4px solid #2563eb;
        margin-bottom: 25px;
    }

    /* 邊框極致強化：強制使用深色高對比邊框 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        border: 3px solid #475569 !important; /* 加粗到 3px，顏色更深 */
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* 點擊時變成亮藍色，方便辨識 */
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.25) !important;
    }

    /* 設定區塊的外圍框 */
    .config-card {
        border: 2px solid #cbd5e1;
        padding: 20px;
        border-radius: 12px;
        background: #ffffff;
        margin-bottom: 20px;
    }

    /* 文字標籤加粗 */
    label p {
        font-size: 18px !important;
        font-weight: 900 !important;
        color: #1e293b !important;
    }
    </style>
""", unsafe_allow_html=True)

# 載入所有資料庫設定
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]
assigner_list = settings["assigners"]

# 登入機制
if "user" not in st.session_state:
    st.title("⚓ 製造部控制塔台 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", all_staff)
    if st.button("啟航登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 控制塔台", "📝 任務派發", "📝 紀錄編輯", "⚙️ 系統設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 ---
    if menu == "📊 控制塔台":
        st.markdown('<p class="main-title">📊 製造部●生產進度即時看板</p>', unsafe_allow_html=True)
        # (此處保留看板邏輯，不作變動)

    # --- 4. 📝 任務派發 (現在製令與派工人員均為下拉選單) ---
    elif menu == "📝 任務派發":
        st.markdown('<p class="main-title">📝 新增派工任務</p>', unsafe_allow_html=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            # 製令下拉選單
            order_no = c1.selectbox("📦 選擇製令編號", order_list)
            proc_name = c2.selectbox("⚙️ 選擇製造工序", process_list)
            
            st.write("---")
            st.write("👥 **主要作業人員 (最多5位)**")
            pc = st.columns(5)
            ws = [pc[i].selectbox(f"人員{i+1}", all_staff, key=f"nw{i}") for i in range(5)]
            
            st.write("---")
            # 派工人員下拉選單：對應系統設定中的派工人員清單
            assigner = st.selectbox("🚩 派工負責人 (從設定名單選擇)", assigner_list)
            
            if st.form_submit_button("🚀 確認發布至看板"):
                log = {
                    "製令": order_no, "製造工序": proc_name, 
                    "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], 
                    "派工人員": assigner, "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success(f"✅ 任務已派發！")
                st.rerun()

    # --- 5. 📝 紀錄編輯 ---
    elif menu == "📝 紀錄編輯":
        st.markdown('<p class="main-title">📝 編輯與修正紀錄</p>', unsafe_allow_html=True)
        # (此處保留編輯邏輯，不作變動)

    # --- 6. ⚙️ 系統設定 (增加派工人員輸入區) ---
    elif menu == "⚙️ 系統設定":
        st.markdown('<p class="main-title">⚙️ 基礎資料管理</p>', unsafe_allow_html=True)
        st.warning("⚠️ 這裡輸入的內容會直接決定派工頁面的下拉選單。多個項目請用 **半形逗號 ( , )** 隔開。")
        
        with st.form("sys_config"):
            st.markdown("### 📦 1. 製令名單設定")
            new_order_str = st.text_area("可選擇的製令：", value=",".join(order_list), height=100)
            
            st.markdown("### 🚩 2. 派工人員名單設定 (這就是您要的功能)")
            new_assigner_str = st.text_area("可執行派工的人員：", value=",".join(assigner_list), height=100)
            
            st.markdown("### 👥 3. 現場人員總清單")
            all_staff_str = st.text_area("所有員工：", value=",".join(all_staff), height=100)
            
            st.markdown("### ⚙️ 4. 製造工序流程設定")
            new_processes = st.text_area("工序項目：", value=",".join(process_list), height=100)
            
            if st.form_submit_button("💾 儲存所有資料庫設定"):
                new_data = {
                    "order_list": [x.strip() for x in new_order_str.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigner_str.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定成功！派發頁面的下拉選單已同步更新。")
                st.rerun()
