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

# --- 2. 頁面配置與 CSS 強化 (新增標題凍結邏輯) ---
st.set_page_config(page_title="超慧科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-title { 
        font-size: 32px !important; 
        font-weight: 900; 
        color: #1e293b; 
        padding: 10px 0;
        border-bottom: 5px solid #1e40af;
        margin-bottom: 20px;
        text-align: center;
    }

    /* 邊框強化 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border: 2px solid #334155 !important; 
        border-radius: 8px !important;
    }

    /* 製令卡片容器：新增內部滾動 */
    .order-card {
        background: white;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 2px solid #e2e8f0;
        height: 550px; /* 固定卡片高度 */
        overflow-y: auto; /* 內部可滾動 */
        position: relative;
    }

    /* 🟢 核心修改：凍結標題 */
    .order-header {
        position: sticky; /* 黏性定位 */
        top: 0;           /* 固定在卡片最上方 */
        z-index: 100;     /* 確保在最上層 */
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        background: #1e40af;
        padding: 12px 15px;
        border-radius: 10px 10px 0 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* 內部工序區域內距 */
    .order-content {
        padding: 15px;
    }

    .compact-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 10px;
    }
    
    .compact-box {
        background: #ffffff;
        padding: 10px 5px;
        border-radius: 8px;
        border: 1.5px solid #cbd5e1;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        align-items: center;
        transition: border-color 0.2s;
    }
    .compact-box:hover { border-color: #1e40af; }

    .p-name { 
        font-size: 13px; 
        font-weight: 800; 
        color: #1e40af; 
        margin-bottom: 6px;
        border-bottom: 1px solid #f1f5f9;
        width: 100%;
        text-align: center;
    }
    
    .leader-tag {
        background: #dbeafe;
        color: #1e40af;
        font-size: 10px;
        padding: 0px 3px;
        border-radius: 3px;
        margin-right: 3px;
        border: 1px solid #1e40af;
    }
    .main-worker-name {
        font-size: 16px !important;
        font-weight: 900 !important;
        color: #000000 !important;
        margin-bottom: 4px;
    }
    
    .sub-workers-wrap {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 3px;
    }
    .sub-worker-name {
        font-size: 12px !important;
        color: #64748b !important;
        background: #f1f5f9;
        padding: 0px 4px;
        border-radius: 3px;
        font-weight: 600;
    }

    .search-box {
        background-color: #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 2px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]
assigner_list = settings["assigners"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技 - 系統登入")
    u = st.selectbox("👤 請選擇您的姓名", all_staff)
    if st.button("確認登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 生產看板", "📝 派工錄入", "📝 紀錄編輯", "⚙️ 系統設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 生產看板 (凍結標題版) ---
    if menu == "📊 生產看板":
        st.markdown('<p class="main-title">📊 超慧科技●生產進度看板</p>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-box">', unsafe_allow_html=True)
            col_s1, col_s2 = st.columns(2)
            search_order = col_s1.selectbox("🔍 搜尋製令", ["全部"] + sorted(order_list))
            search_staff = col_s2.selectbox("👤 搜尋參與人員", ["全部"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v and isinstance(v, dict)]
                if all_logs:
                    df = pd.DataFrame(all_logs)
                    unique_orders = df["製令"].unique()
                    
                    filtered_orders = []
                    for order in unique_orders:
                        if search_order != "全部" and search_order != order: continue
                        order_df = df[df["製令"] == order]
                        if search_staff != "全部":
                            staff_cols = [f"人員{i}" for i in range(1, 6)]
                            if not order_df[staff_cols].apply(lambda row: search_staff in row.values, axis=1).any(): continue
                        filtered_orders.append(order)

                    cols = st.columns(3)
                    for idx, order in enumerate(filtered_orders):
                        order_df = df[df["製令"] == order]
                        with cols[idx % 3]:
                            # 卡片結構：外部固定高度 + 內部凍結標題
                            st.markdown(f'''
                                <div class="order-card">
                                    <div class="order-header">📦 {order}</div>
                                    <div class="order-content">
                                        <div class="compact-grid">
                            ''', unsafe_allow_html=True)
                            
                            for proc in process_list:
                                matched = order_df[order_df["製造工序"] == proc]
                                if not matched.empty:
                                    row = matched.iloc[0]
                                    main_w = row.get("人員1", "-")
                                    subs = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", "管理員", None, ""]]
                                    
                                    main_html = f'<div class="main-worker-name"><span class="leader-tag">主</span>{main_w}</div>'
                                    sub_html = '<div class="sub-workers-wrap">' + "".join([f'<span class="sub-worker-name">{s}</span>' for s in subs]) + '</div>'
                                    worker_box_content = main_html + sub_html
                                else:
                                    worker_box_content = '<div style="color:#cbd5e1; font-size:12px; margin-top:10px;">尚未派工</div>'
                                
                                st.markdown(f'<div class="compact-box"><div class="p-name">{proc}</div>{worker_box_content}</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div></div></div>', unsafe_allow_html=True)
        except:
            st.error("看板資料讀取異常")

    # --- 4. 📝 任務派發 ---
    elif menu == "📝 派工錄入":
        st.markdown('<p class="main-title">📝 派發新任務</p>', unsafe_allow_html=True)
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.selectbox("📦 選擇製令", order_list)
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.write("---")
            st.markdown("### 👥 作業人員配置")
            pc = st.columns(5)
            ws = []
            ws.append(pc[0].selectbox("主要人員 (人員1)", all_staff, key="nw0"))
            for i in range(1, 5):
                ws.append(pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"nw{i}"))
            
            st.write("---")
            assigner = st.selectbox("🚩 派工負責人", assigner_list)
            
            if st.form_submit_button("🚀 確認發布此任務"):
                log = {
                    "製令": order_no, "製造工序": proc_name, 
                    "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], 
                    "派工人員": assigner, "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success(f"✅ 任務已同步")
                st.rerun()

    # --- 其餘編輯與設定維持原樣 ---
    elif menu == "📝 紀錄編輯":
        st.markdown('<p class="main-title">📝 修改現有派工</p>', unsafe_allow_html=True)
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            log_options = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')}" for log in all_logs}
            tid = st.selectbox("🔍 搜尋紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                with st.container():
                    st.markdown('<div class="order-card" style="height:auto; overflow:visible;">', unsafe_allow_html=True)
                    new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                    ec = st.columns(5)
                    nw = []
                    nw.append(ec[0].selectbox("主要人員", all_staff, index=all_staff.index(curr.get('人員1')) if curr.get('人員1') in all_staff else 0, key="e0"))
                    for i in range(1, 5):
                        nw.append(ec[i].selectbox(f"人員 {i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}"))
                    
                    c1, c2 = st.columns([1, 4])
                    if c1.button("💾 儲存修改"):
                        upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                        requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                        st.rerun()
                    if c2.button("🗑️ 刪除紀錄", type="primary"):
                        requests.delete(f"{DB_URL}/{tid}.json")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "⚙️ 系統設定":
        st.markdown('<p class="main-title">⚙️ 系統後台管理</p>', unsafe_allow_html=True)
        with st.form("sys_config"):
            st.markdown("### 📦 製令名單管理")
            new_order_str = st.text_area("製令清單 (逗號隔開)：", value=",".join(order_list), height=80)
            st.markdown("### 🚩 派工權限名單")
            new_assigner_str = st.text_area("派工負責人清單：", value=",".join(assigner_list), height=80)
            st.markdown("### 👥 員工總名單")
            all_staff_str = st.text_area("所有人員：", value=",".join(all_staff), height=80)
            st.markdown("### ⚙️ 工序流程管理")
            new_processes = st.text_area("工序清單：", value=",".join(process_list), height=80)
            
            if st.form_submit_button("💾 同步資料庫設定"):
                new_data = {
                    "order_list": [x.strip() for x in new_order_str.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigner_str.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定已更新")
                st.rerun()
