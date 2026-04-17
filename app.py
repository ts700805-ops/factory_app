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
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                staff = data.get("all_staff", default_settings["all_staff"])
                procs = data.get("processes", default_settings["processes"])
                return {"all_staff": staff, "processes": procs}
        return default_settings
    except Exception:
        return default_settings

# --- 2. 頁面配置與強化的 CSS 介面 ---
st.set_page_config(page_title="大量科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 整體背景 */
    .stApp { background-color: #f8fafc; }
    
    /* 標題樣式 */
    .main-title { 
        font-size: 32px !important; 
        font-weight: 800; 
        color: #1e293b; 
        padding: 15px 0;
        border-bottom: 4px solid #2563eb;
        margin-bottom: 25px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    /* 強化所有輸入框與選單的邊框 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        border: 2px solid #cbd5e1 !important; /* 加深邊框顏色 */
        border-radius: 8px !important;
        background-color: #ffffff !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.1) !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    /* 聚焦時的顏色 */
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within, .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }

    /* 卡片樣式強化 */
    .order-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* 加深陰影 */
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

    /* 工序格子強化 */
    .compact-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
        gap: 10px;
    }
    .compact-box {
        background: #f1f5f9;
        padding: 10px 6px;
        border-radius: 8px;
        border: 1.5px solid #cbd5e1; /* 邊框明顯化 */
        text-align: center;
        min-height: 65px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .p-name { font-size: 12px; font-weight: 700; color: #64748b; margin-bottom: 4px; }
    .p-worker { font-size: 14px; font-weight: 800; color: #0f172a; }
    
    /* 設定頁面的輸入區塊外框 */
    .config-section {
        background: #ffffff;
        padding: 20px;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]

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

    # --- 取得所有現有製令 ---
    existing_orders = []
    try:
        r_orders = requests.get(f"{DB_URL}.json", timeout=5)
        data_orders = r_orders.json()
        if data_orders:
            existing_orders = sorted(list(set([v.get("製令") for k, v in data_orders.items() if v and v.get("製令")])))
    except:
        pass

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

    # --- 4. 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<p class="main-title">📝 新增派工任務</p>', unsafe_allow_html=True)
        order_mode = st.radio("🛠️ 製令輸入模式", ["從現有挑選", "手動輸入新製令"], horizontal=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            if order_mode == "從現有挑選":
                order_no = c1.selectbox("📦 選擇製令", existing_orders if existing_orders else ["(無資料)"])
            else:
                order_no = c1.text_input("📦 輸入新製令編號", placeholder="請輸入編號...")
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.write("---")
            st.write("👥 **人員配置 (最多5位)**")
            pc = st.columns(5)
            ws = [pc[i].selectbox(f"人員{i+1}", all_staff, key=f"nw{i}") for i in range(5)]
            
            user_idx = all_staff.index(st.session_state.user) if st.session_state.user in all_staff else 0
            assigner = st.selectbox("🚩 派工負責人", all_staff, index=user_idx)
            
            if st.form_submit_button("🚀 確認發布至看板"):
                if not order_no or order_no == "(無資料)":
                    st.error("請確認製令編號！")
                else:
                    log = {"製令": order_no, "製造工序": proc_name, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "派工人員": assigner, "提交時間": get_now_str()}
                    requests.post(f"{DB_URL}.json", data=json.dumps(log))
                    st.success("派發成功！")
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

    # --- 6. ⚙️ 系統設定 ---
    elif menu == "⚙️ 系統設定":
        st.markdown('<p class="main-title">⚙️ 基礎資料管理</p>', unsafe_allow_html=True)
        st.info("💡 請在下方框中輸入內容，多個項目請用 **半形逗號 ( , )** 隔開。")
        
        with st.form("sys_config"):
            st.markdown("### 👥 人員名單設定")
            all_staff_str = st.text_area("目前的清單：", value=",".join(all_staff), height=150, help="例如：管理員,張三,李四")
            
            st.markdown("---")
            
            st.markdown("### ⚙️ 工序流程設定")
            new_processes = st.text_area("目前的清單：", value=",".join(process_list), height=150, help="例如：骨架作業,前置作業,包裝")
            
            st.write("")
            if st.form_submit_button("💾 儲存所有設定"):
                new_data = {
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定已成功存入資料庫！")
                st.rerun()
