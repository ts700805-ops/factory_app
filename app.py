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

# --- 2. 頁面配置與專業 CSS ---
st.set_page_config(page_title="大量科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-title { 
        font-size: 28px !important; 
        font-weight: 800; 
        color: #0f172a; 
        padding: 10px 0;
        border-bottom: 3px solid #3b82f6;
        margin-bottom: 20px;
    }
    .order-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .order-header {
        font-size: 18px;
        font-weight: bold;
        color: #1e40af;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        border-left: 5px solid #3b82f6;
        padding-left: 10px;
    }
    .compact-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 8px;
    }
    .compact-box {
        background: #f8fafc;
        padding: 8px 4px;
        border-radius: 6px;
        border: 1px solid #f1f5f9;
        text-align: center;
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .p-name { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
    .p-worker { font-size: 13px; font-weight: 600; color: #334155; }
    .status-empty { color: #cbd5e1; font-weight: normal; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]

# 登入機制
if "user" not in st.session_state:
    st.title("⚓ 製造部控制塔台 - 登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("啟航登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 控制塔台", "📝 任務派發", "📝 紀錄編輯", "⚙️ 系統設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 取得所有現有製令 (供下拉選單使用) ---
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
                                    worker_html = '<div class="p-worker status-empty">-</div>'
                                st.markdown(f'<div class="compact-box"><div class="p-name">{proc}</div>{worker_html}</div>', unsafe_allow_html=True)
                            st.markdown('</div></div>', unsafe_allow_html=True)
                else:
                    st.info("尚無派工紀錄。")
            else:
                st.info("目前無資料。")
        except:
            st.error("看板讀取失敗")

    # --- 4. 📝 任務派發 (新增製令下拉選單) ---
    elif menu == "📝 任務派發":
        st.markdown('<p class="main-title">📝 新增派工任務</p>', unsafe_allow_html=True)
        
        # 讓使用者選擇是要「輸入新製令」還是「從現有挑選」
        order_mode = st.radio("製令輸入模式", ["從現有製令選擇", "手動輸入新製令"], horizontal=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            
            if order_mode == "從現有製令選擇":
                order_no = c1.selectbox("📦 選擇現有製令", existing_orders if existing_orders else ["(尚無資料)"])
            else:
                order_no = c1.text_input("📦 輸入新製令編號", placeholder="例如: 1111")
                
            proc_name = c2.selectbox("⚙️ 選擇製造工序", process_list)
            
            st.write("👥 人員配置")
            pc = st.columns(5)
            w1 = pc[0].selectbox("人員1", all_staff, key="nw1")
            w2 = pc[1].selectbox("人員2", all_staff, key="nw2")
            w3 = pc[2].selectbox("人員3", all_staff, key="nw3")
            w4 = pc[3].selectbox("人員4", all_staff, key="nw4")
            w5 = pc[4].selectbox("人員5", all_staff, key="nw5")
            
            user_idx = all_staff.index(st.session_state.user) if st.session_state.user in all_staff else 0
            assigner = st.selectbox("🚩 派工負責人", all_staff, index=user_idx)
            
            if st.form_submit_button("🚀 發布至看板"):
                if not order_no or order_no == "(尚無資料)":
                    st.error("請確認製令編號！")
                else:
                    log = {"製令": order_no, "製造工序": proc_name, "人員1": w1, "人員2": w2, "人員3": w3, "人員4": w4, "人員5": w5, "派工人員": assigner, "提交時間": get_now_str()}
                    requests.post(f"{DB_URL}.json", data=json.dumps(log))
                    st.success(f"製令 {order_no} 派發成功！")
                    st.rerun()

    # --- 5. 📝 紀錄編輯 ---
    elif menu == "📝 紀錄編輯":
        st.header("📝 編輯現有紀錄")
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            log_options = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')}" for log in all_logs}
            tid = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                with st.expander("修改內容"):
                    new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                    ec = st.columns(5)
                    nw = [ec[i].selectbox(f"人員{i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}") for i in range(5)]
                    if st.button("💾 儲存修改"):
                        upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                        requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                        st.rerun()
                if st.button("🗑️ 刪除紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{tid}.json")
                    st.rerun()

    # --- 6. ⚙️ 系統設定 ---
    elif menu == "⚙️ 系統設定":
        st.header("⚙️ 基礎資料管理")
        with st.form("sys_config"):
            all_staff_str = st.text_area("👥 人員清單 (逗號隔開)", value=",".join(all_staff))
            new_processes = st.text_area("⚙️ 工序清單 (逗號隔開)", value=",".join(process_list))
            if st.form_submit_button("💾 儲存設定"):
                new_data = {
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("設定已更新")
                st.rerun()
