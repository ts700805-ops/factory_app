import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (絕對不動) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        data = r.json()
        if not data: 
            return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}
        if "worker_map" not in data: data["worker_map"] = {}
        if "processes" not in data: data["processes"] = ["預設工序"]
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}

# --- 2. 頁面配置 (增強樣式) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 基礎字體與樣式 */
    .stApp { background-color: #f8fafc; }
    .main-title { font-size: 36px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    
    /* 歷史紀錄卡片樣式 */
    .history-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #059669;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .history-time { color: #64748b; font-size: 14px; font-weight: bold; }
    .history-order { color: #1e293b; font-size: 22px; font-weight: 800; margin: 5px 0; }
    .history-detail { font-size: 18px; color: #334155; }
    .status-badge {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    /* 原有看板樣式保留 */
    .stat-card { 
        background-color: #ffffff; 
        padding: 10px; 
        border-radius: 10px; 
        border-top: 4px solid #1E3A8A; 
        text-align: center; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stat-value { font-size: 28px !important; font-weight: bold; color: #1E3A8A; }
    
    .stButton>button { border-radius: 8px; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "✅ 已完工歷史紀錄查詢", "📝 現場派工作業", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (保持原樣) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 超慧科技現場派工看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    if v: v['db_key'] = k; all_logs.append(v)
                df = pd.DataFrame(all_logs).fillna("無")
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'''<div class="stat-card"><div style="color:#666">總派件數</div><div class="stat-value">{len(df)} 件</div></div>''', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'''<div class="stat-card"><div style="color:#666">動員人力</div><div class="stat-value">{worker_count} 人</div></div>''', unsafe_allow_html=True)
                
                st.write("")
                st.subheader("📑 待辦任務清單")
                st.dataframe(df[["製令", "製造工序", "作業人員", "作業期限"]], use_container_width=True, hide_index=True)
                
                for index, row in df.iterrows():
                    with st.expander(f"📦 {row['製令']} - {row['製造工序']}"):
                        col_i, col_b = st.columns([4, 1])
                        col_i.write(f"**主要人員：** {row['作業人員']} | **協助人員：** {row.get('協助人員', '無')}")
                        if col_b.button("✅ 標記完工", key=f"done_{row['db_key']}"):
                            done_data = row.to_dict()
                            db_key = done_data.pop('db_key')
                            done_data['實際完工時間'] = get_now_str()
                            requests.post(f"{DONE_URL}.json", json=done_data)
                            requests.delete(f"{DB_URL}/{db_key}.json")
                            st.rerun()
            else: st.info("目前尚無待辦任務。")
        except Exception as e: st.error(f"錯誤：{e}")

    # --- 4. ✅ 已完工歷史紀錄查詢 (精修美化版) ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title" style="color: #059669; border-bottom-4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = []
                for k, v in done_data.items():
                    if v: v['done_key'] = k; done_list.append(v)
                
                df_done = pd.DataFrame(done_list).fillna("無")
                if '實際完工時間' in df_done.columns:
                    df_done = df_done.sort_values(by='實際完工時間', ascending=False)
                
                # 篩選區
                with st.container():
                    s1, s2 = st.columns(2)
                    q_order = s1.text_input("🔍 搜尋製令單號")
                    q_worker = s2.selectbox("👤 按人員篩選", ["全部"] + sorted(df_done["作業人員"].unique().tolist()))
                
                filtered_done = df_done.copy()
                if q_order: filtered_done = filtered_done[filtered_done["製令"].str.contains(q_order)]
                if q_worker != "全部": filtered_done = filtered_done[filtered_done["作業人員"] == q_worker]

                st.markdown("---")
                
                # 顯示歷史紀錄卡片
                for _, row in filtered_done.iterrows():
                    st.markdown(f"""
                    <div class="history-card">
                        <div class="status-badge">COMPLETED 已完工</div>
                        <div class="history-time">📅 完工時間：{row.get('實際完工時間', '無')}</div>
                        <div class="history-order">製令：{row['製令']}</div>
                        <div class="history-detail">
                            ⚙️ 工序：<b>{row['製造工序']}</b> | 👷 主手：<b>{row['作業人員']}</b> | 🤝 助手：{row.get('協助人員', '無')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 編輯與刪除放在摺疊區以保持整潔
                    with st.expander(f"🛠️ 管理此筆紀錄 ({row['製令']})"):
                        ec1, ec2 = st.columns(2)
                        p_assigner = row.get('派工人員', '管理員')
                        p_worker_list = settings.get("worker_map", {}).get(p_assigner, [])
                        
                        new_h_worker = ec1.selectbox("修改主手", p_worker_list, index=p_worker_list.index(row['作業人員']) if row['作業人員'] in p_worker_list else 0, key=f"edit_w_{row['done_key']}")
                        new_h_assist = ec2.selectbox("修改助手", ["無"] + p_worker_list, index=(["無"] + p_worker_list).index(row['協助人員']) if row['協助人員'] in (["無"] + p_worker_list) else 0, key=f"edit_a_{row['done_key']}")
                        
                        bc1, bc2 = st.columns([1, 1])
                        if bc1.button("💾 儲存修改", key=f"save_h_{row['done_key']}", use_container_width=True):
                            requests.patch(f"{DONE_URL}/{row['done_key']}.json", json={"作業人員": new_h_worker, "協助人員": new_h_assist})
                            st.success("紀錄已更新！")
                            st.rerun()
                        
                        if bc2.button("🗑️ 刪除紀錄", key=f"del_h_{row['done_key']}", type="primary", use_container_width=True):
                            requests.delete(f"{DONE_URL}/{row['done_key']}.json")
                            st.rerun()
            else: st.info("目前尚無完工紀錄。")
        except Exception as e: st.error(f"連線失敗：{e}")

    # --- 5. 📝 現場派工作業 (絕對不動) ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
        process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
        c1, c2, c3 = st.columns(3)
        assign_list = settings.get("assigners", [])
        assigner = c1.selectbox("🚩 派工人員", assign_list, index=assign_list.index(st.session_state.user) if st.session_state.user in assign_list else 0)
        my_workers = settings.get("worker_map", {}).get(assigner, [])
        worker = c2.selectbox("👷 主要人員", my_workers)
        assistant = c3.selectbox("🤝 協助人員", ["無"] + my_workers)
        deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
        
        if st.button("🚀 發布任務", use_container_width=True):
            if not worker: st.error("請先配置作業人員。")
            else:
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("發布成功！")

    # --- 6. 📝 編輯派工紀錄 (絕對不動) ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 待辦派工紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"{log.get('製令')} - {log.get('作業人員')}" for log in all_logs}
                target_id = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                if curr:
                    with st.form("edit_form"):
                        e_order = st.selectbox("製令", settings.get("orders", []), index=settings.get("orders", []).index(curr['製令']) if curr['製令'] in settings.get("orders", []) else 0)
                        e_proc = st.selectbox("工序", settings.get("processes", []), index=settings.get("processes", []).index(curr['製造工序']) if curr['製造工序'] in settings.get("processes", []) else 0)
                        if st.form_submit_button("儲存修改"):
                            requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": e_order, "製造工序": e_proc})
                            st.rerun()
                    if st.button("🗑️ 刪除此任務"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
            else: st.info("目前無待辦紀錄。")
        except: st.error("讀取失敗")

    # --- 7. ⚙️ 系統內容管理 (絕對不動) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("basic_settings"):
            n_orders = st.text_area("📦 製令清單", value=",".join(settings.get("orders", [])))
            n_assigners = st.text_area("🚩 派工人員", value=",".join(settings.get("assigners", [])))
            n_procs = st.text_area("⚙️ 製造工序", value=",".join(settings.get("processes", [])))
            if st.form_submit_button("💾 儲存名單"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in n_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in n_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in n_procs.split(",") if x.strip()]
                })
                st.rerun()
        
        st.markdown("---")
        target_a = st.selectbox("配置人員：", settings.get("assigners", []))
        with st.form("worker_cfg"):
            w_input = st.text_area(f"👷 {target_a} 的人員清單", value=",".join(settings.get("worker_map", {}).get(target_a, [])))
            if st.form_submit_button("💾 儲存人員配置"):
                wm = settings.get("worker_map", {})
                wm[target_a] = [x.strip() for x in w_input.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"worker_map": wm})
                st.rerun()
