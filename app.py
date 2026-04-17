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

# --- 2. 頁面配置與「絕對固定」CSS ---
st.set_page_config(page_title="超慧科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* 🟢 核心：強效固定卡片結構 */
    .order-card {
        background: white;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        border: 2px solid #e2e8f0;
        height: 600px;         /* 每個製令卡片固定總高度 */
        display: flex;         /* 啟用垂直佈局 */
        flex-direction: column;
        overflow: hidden;      /* 確保內容不溢出 */
    }

    /* 🟢 核心：絕對固定標題欄 */
    .order-header {
        background: #1e40af;
        color: #ffffff;
        padding: 15px 20px;
        font-size: 20px;
        font-weight: 800;
        flex-shrink: 0;        /* 強制標題不縮小、不參與捲動 */
        border-bottom: 2px solid #1e3a8a;
        z-index: 10;
    }

    /* 🟢 核心：獨立捲動內容區 */
    .order-content-scroll {
        flex-grow: 1;          /* 佔滿剩餘空間 */
        overflow-y: auto !important; /* 強制開啟垂直捲動 */
        padding: 15px;
        background: #ffffff;
    }

    /* 格位排版微調 */
    .compact-grid {
        display: grid;
        grid-template-columns: 1fr; /* 三欄模式下改為單列或雙列最清楚 */
        gap: 12px;
    }
    
    .compact-box {
        background: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 1.5px solid #cbd5e1;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        transition: 0.2s;
    }
    .compact-box:hover { border-color: #1e40af; background: #f8fafc; }

    .p-name { 
        font-size: 14px; 
        font-weight: 800; 
        color: #1e40af; 
        margin-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
        width: 100%;
        text-align: center;
    }
    
    .leader-tag {
        background: #dbeafe;
        color: #1e40af;
        font-size: 11px;
        padding: 1px 4px;
        border-radius: 3px;
        margin-right: 5px;
        border: 1px solid #1e40af;
        font-weight: bold;
    }

    .main-worker-name {
        font-size: 18px !important;
        font-weight: 900 !important;
        color: #000000 !important;
        margin-bottom: 6px;
    }
    
    .sub-workers-wrap {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 5px;
    }

    .sub-worker-name {
        font-size: 13px !important;
        color: #475569 !important;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
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

    # --- 3. 📊 生產看板 (強效固定版) ---
    if menu == "📊 生產看板":
        st.markdown(f'<div style="text-align:center; padding:10px;"><h1 style="color:#1e40af; font-weight:900;">📊 超慧科技●生產進度看板</h1></div>', unsafe_allow_html=True)
        
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

                    # 3 欄顯示
                    cols = st.columns(3)
                    for idx, order in enumerate(filtered_orders):
                        order_df = df[df["製令"] == order]
                        with cols[idx % 3]:
                            # 🟢 結構修改：Header 與 Content 完全分離
                            st.markdown(f'''
                                <div class="order-card">
                                    <div class="order-header">📦 製令：{order}</div>
                                    <div class="order-content-scroll">
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
                                    box_content = main_html + sub_html
                                else:
                                    box_content = '<div style="color:#cbd5e1; font-size:14px; margin-top:15px; font-weight:bold;">尚未派工</div>'
                                
                                st.markdown(f'<div class="compact-box"><div class="p-name">{proc}</div>{box_content}</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div></div></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"連線資料庫失敗: {e}")

    # --- 後續派工、編輯功能不變 ---
    elif menu == "📝 派工錄入":
        st.markdown('<h2 style="color:#1e40af;">📝 派發新任務</h2>', unsafe_allow_html=True)
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.selectbox("📦 選擇製令", order_list)
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            st.write("---")
            pc = st.columns(5)
            ws = [pc[0].selectbox("主要人員 (人員1)", all_staff, key="nw0")]
            for i in range(1, 5):
                ws.append(pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"nw{i}"))
            st.write("---")
            assigner = st.selectbox("🚩 派工負責人", assigner_list)
            if st.form_submit_button("🚀 確認發布"):
                log = {"製令": order_no, "製造工序": proc_name, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "派工人員": assigner, "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success(f"✅ 製令 {order_no} 任務已發布")
                st.rerun()

    elif menu == "📝 紀錄編輯":
        st.markdown('<h2 style="color:#1e40af;">📝 修改現有派工</h2>', unsafe_allow_html=True)
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            log_opts = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')}" for log in all_logs}
            tid = st.selectbox("🔍 搜尋紀錄", options=list(log_opts.keys()), format_func=lambda x: log_opts[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                ec = st.columns(5)
                nw = [ec[0].selectbox("主要人員", all_staff, index=all_staff.index(curr.get('人員1')) if curr.get('人員1') in all_staff else 0, key="e0")]
                for i in range(1, 5):
                    nw.append(ec[i].selectbox(f"人員 {i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}"))
                if st.button("💾 儲存修改"):
                    upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                    requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                    st.rerun()
                if st.button("🗑️ 刪除紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{tid}.json")
                    st.rerun()

    elif menu == "⚙️ 系統設定":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統設定</h2>', unsafe_allow_html=True)
        with st.form("sys_config"):
            new_order_str = st.text_area("製令名單：", value=",".join(order_list))
            new_assigner_str = st.text_area("派工負責人：", value=",".join(assigner_list))
            all_staff_str = st.text_area("人員總名單：", value=",".join(all_staff))
            new_processes = st.text_area("工序名單：", value=",".join(process_list))
            if st.form_submit_button("💾 儲存設定"):
                new_data = {
                    "order_list": [x.strip() for x in new_order_str.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigner_str.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定已同步")
                st.rerun()
