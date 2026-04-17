import streamlit as st
import pandas as pd
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
        "assigners": ["管理員"] # 新增派工人員預設值
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
                    "assigners": data.get("assigners", default_settings["assigners"]) # 讀取資料庫中的派工名單
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

    /* 邊框極致強化：強制使用 3px 深色高對比邊框 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        border: 3px solid #334155 !important; 
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.25) !important;
    }

    .order-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .order-header {
        font-size: 20px;
        font-weight: bold;
        color: #1e40af;
        margin-bottom: 15px;
        border-left: 6px solid #2563eb;
        padding-left: 12px;
    }

    .compact-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
        gap: 10px;
    }
    .compact-box {
        background: #f1f5f9;
        padding: 10px 6px;
        border-radius: 8px;
        border: 2px solid #cbd5e1;
        text-align: center;
        min-height: 65px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .p-name { font-size: 12px; font-weight: 700; color: #64748b; margin-bottom: 4px; }
    .p-worker { font-size: 14px; font-weight: 800; color: #0f172a; }

    /* 文字標籤強化 */
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
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v and isinstance(v, dict)]
                if all_logs:
                    df = pd.DataFrame(all_logs)
                    unique_orders = df["製令"].unique()
                    cols = st.columns(2)
                    for idx, order in enumerate(unique_orders):
                        order_df = df[df["製令"] == order]
                        with cols[idx % 2]:
                            st.markdown(f'<div class="order-card"><div class="order-header">📦 製令：{order}</div><div class="compact-grid">', unsafe_allow_html=True)
                            for proc in process_list:
                                matched = order_df[order_df["製造工序"] == proc]
                                if not matched.empty:
                                    row = matched.iloc[0]
                                    active_workers = [row.get(f"人員{i}") for i in range(1, 6) if row.get(f"人員{i}") not in ["NA", "管理員", None]]
                                    w_display = "、".join(active_workers) if active_workers else "-"
                                    worker_html = f'<div class="p-worker">{w_display}</div>'
                                else:
                                    worker_html = '<div class="p-worker" style="color:#cbd5e1;">-</div>'
                                st.markdown(f'<div class="compact-box"><div class="p-name">{proc}</div>{worker_html}</div>', unsafe_allow_html=True)
                            st.markdown('</div></div>', unsafe_allow_html=True)
        except:
            st.error("看板讀取失敗")

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
            # 派工人員改為從「派工名單」抓取下拉選單
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
        st.markdown('<p class="main-title">📝 編輯現有紀錄</p>', unsafe_allow_html=True)
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            log_options = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')}" for log in all_logs}
            tid = st.selectbox("🔍 選擇要修改的項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                with st.container():
                    st.markdown('<div class="order-card">', unsafe_allow_html=True)
                    new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                    ec = st.columns(5)
                    nw = [ec[i].selectbox(f"人員{i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}") for i in range(5)]
                    c1, c2 = st.columns([1, 4])
                    if c1.button("💾 儲存修改"):
                        upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                        requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                        st.rerun()
                    if c2.button("🗑️ 刪除這筆紀錄", type="primary"):
                        requests.delete(f"{DB_URL}/{tid}.json")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. ⚙️ 系統設定 (增加派工人員輸入區) ---
    elif menu == "⚙️ 系統設定":
        st.markdown('<p class="main-title">⚙️ 基礎資料管理</p>', unsafe_allow_html=True)
        st.warning("⚠️ 多個項目請用 **半形逗號 ( , )** 隔開。")
        
        with st.form("sys_config"):
            st.markdown("### 📦 1. 製令名單管理")
            new_order_str = st.text_area("可選擇的製令：", value=",".join(order_list), height=100)
            
            st.markdown("### 🚩 2. 派工權限名單 (下拉選單內容)")
            new_assigner_str = st.text_area("可執行派工的人員：", value=",".join(assigner_list), height=100)
            
            st.markdown("### 👥 3. 現場人員總名單")
            all_staff_str = st.text_area("所有員工：", value=",".join(all_staff), height=100)
            
            st.markdown("### ⚙️ 4. 製造工序管理")
            new_processes = st.text_area("工序項目：", value=",".join(process_list), height=100)
            
            if st.form_submit_button("💾 儲存所有資料庫設定"):
                new_data = {
                    "order_list": [x.strip() for x in new_order_str.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigner_str.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定成功！派發頁面的下拉選單已同步。")
                st.rerun()
