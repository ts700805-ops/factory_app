import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 (保持不變) ---
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
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}

# --- 2. 頁面配置 & CSS 優化 ---
st.set_page_config(page_title="超慧科技●現場派工系統", layout="wide")

st.markdown("""
    <style>
    /* 全域字體優化 */
    .main-title { font-size: 36px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    
    /* 看板卡片樣式 (核心修改點) */
    .task-card {
        background-color: #f8fafc;
        border-left: 6px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .task-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 8px; }
    .task-order { font-size: 20px; font-weight: bold; color: #1e40af; }
    .task-process { background: #dbeafe; color: #1e40af; padding: 2px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; }
    .task-body { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .task-label { color: #64748b; font-size: 14px; }
    .task-value { color: #1e293b; font-size: 18px; font-weight: bold; }
    .task-deadline { color: #ef4444; font-weight: bold; }

    /* 數據統計卡片 */
    .stat-card { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        border-top: 4px solid #1E3A8A; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        text-align: center; 
        margin-bottom: 20px;
    }
    .stat-label { font-size: 18px !important; font-weight: bold; color: #475569; }
    .stat-value { font-size: 32px !important; font-weight: bold; color: #1E3A8A; }
    
    .stSelectbox label { font-size: 18px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 超慧科技 控制系統登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "✅ 快速結案作業", "✅ 已完工歷史紀錄查詢", "📝 現場派工作業", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁 - 重新設計紅色框框處) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 超慧科技現場派工看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    if v:
                        v['db_key'] = k
                        all_logs.append(v)
                df = pd.DataFrame(all_logs).fillna("無")
                
                # 統計數據區
                c1, c2 = st.columns(2)
                with c1: 
                    st.markdown(f'''<div class="stat-card"><span class="stat-label">總派件數</span><br><span class="stat-value">{len(df)}</span> <span class="stat-unit">件</span></div>''', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'''<div class="stat-card"><span class="stat-label">動員人力</span><br><span class="stat-value">{worker_count}</span> <span class="stat-unit">人</span></div>''', unsafe_allow_html=True)
                
                # 篩選區
                with st.expander("🔍 快速篩選資料", expanded=False):
                    f1, f2, f3 = st.columns(3)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序篩選", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員篩選", ["全部"] + sorted(df["派工人員"].unique().tolist()))
                    
                    f4, f5, f6 = st.columns(3)
                    sel_worker = f4.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))
                    sel_assistant = f5.selectbox("按協助人員篩選", ["全部"] + sorted(df["協助人員"].unique().tolist()))
                    sel_deadline = f6.selectbox("按作業期限篩選", ["全部"] + sorted(df["作業期限"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]
                if sel_assistant != "全部": filtered_df = filtered_df[filtered_df["協助人員"] == sel_assistant]
                if sel_deadline != "全部": filtered_df = filtered_df[filtered_df["作業期限"] == sel_deadline]

                # --- 核心修改：重新設計的明細顯示 ---
                st.subheader("📑 待辦派工明細清單")
                
                # 採用雙欄或三欄卡片式佈局
                cols = st.columns(2) 
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div class="task-card">
                            <div class="task-header">
                                <span class="task-order">📦 {row['製令']}</span>
                                <span class="task-process">{row['製造工序']}</span>
                            </div>
                            <div class="task-body">
                                <div><span class="task-label">作業人員：</span><br><span class="task-value">👤 {row['作業人員']}</span></div>
                                <div><span class="task-label">協助人員：</span><br><span class="task-value">🤝 {row.get('協助人員', '無')}</span></div>
                                <div><span class="task-label">派工人員：</span><br><span class="task-value">🚩 {row['派工人員']}</span></div>
                                <div><span class="task-label">作業期限：</span><br><span class="task-value task-deadline">⏳ {row['作業期限']}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            else:
                st.info("目前尚無待辦派工。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. ✅ 快速結案作業 (保持功能) ---
    elif menu == "✅ 快速結案作業":
        st.markdown('<p class="main-title">✅ 現場快速結案中心</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    if v:
                        v['db_key'] = k
                        all_logs.append(v)
                df = pd.DataFrame(all_logs).fillna("無")

                for index, row in df.iterrows():
                    with st.container():
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"### 📦 製令：{row['製令']} | 👷 作業員：{row['作業人員']}")
                            st.caption(f"工序：{row['製造工序']} | 協助：{row.get('協助人員', '無')} | 期限：{row['作業期限']}")
                        if col_btn.button(f"✅ 標記完工", key=f"done_{row['db_key']}"):
                            done_data = row.to_dict()
                            db_key = done_data.pop('db_key')
                            done_data['實際完工時間'] = get_now_str()
                            final_data = {k: (v if pd.notna(v) else "無") for k, v in done_data.items()}
                            requests.post(f"{DONE_URL}.json", json=final_data)
                            requests.delete(f"{DB_URL}/{db_key}.json")
                            st.balloons()
                            st.rerun()
            else:
                st.info("目前尚無待辦派工。")
        except Exception as e:
            st.error(f"連線錯誤：{e}")

    # --- 5. ✅ 已完工歷史紀錄查詢 (保持功能) ---
    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = [v for v in done_data.values() if v]
                df_done = pd.DataFrame(done_list).fillna("無")
                if '實際完工時間' in df_done.columns:
                    df_done = df_done.sort_values(by='實際完工時間', ascending=False)
                st.dataframe(df_done, use_container_width=True, hide_index=True)
            else: st.info("無紀錄。")
        except: st.error("讀取失敗")

    # --- 6. 📝 現場派工作業 (發佈任務特效與功能保留) ---
    elif menu == "📝 現場派工作業":
        st.markdown('<p class="main-title">📝 建立新派工任務</p>', unsafe_allow_html=True)
        
        order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
        process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
        
        c1, c2, c3 = st.columns(3)
        assign_list = settings.get("assigners", [])
        assigner = c1.selectbox("🚩 派工人員", assign_list)
        
        my_workers = settings.get("worker_map", {}).get(assigner, [])
        worker = c2.selectbox("👷 主要人員", my_workers)
        assistant = c3.selectbox("🤝 協助人員", ["無"] + my_workers)
        deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
        
        if st.button("🚀 發布派工任務"):
            if not worker:
                st.error("請先設定作業人員")
            else:
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                res = requests.post(f"{DB_URL}.json", json=log)
                if res.status_code == 200:
                    st.balloons() # 保留氣球特效
                    st.success(f"任務 [{order_no}] 已成功發布！")

    # --- 7. 📝 編輯派工紀錄 (保持編輯功能) ---
    elif menu == "📝 編輯派工紀錄":
        st.markdown('<p class="main-title">📝 待辦派工紀錄維護</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                logs = [{"id": k, **v} for k, v in db_data.items() if v]
                log_opts = {l['id']: f"{l['製令']} | {l['作業人員']}" for l in logs}
                target_id = st.selectbox("選擇修改對象", options=list(log_opts.keys()), format_func=lambda x: log_opts[x])
                curr = next(l for l in logs if l['id'] == target_id)
                
                with st.form("edit_form"):
                    e_order = st.selectbox("修改製令", settings.get("orders", []), index=settings.get("orders", []).index(curr['製令']) if curr['製令'] in settings.get("orders", []) else 0)
                    e_assigner = st.selectbox("修改派工員", settings.get("assigners", []), index=settings.get("assigners", []).index(curr['派工人員']) if curr['派工人員'] in settings.get("assigners", []) else 0)
                    e_workers = settings.get("worker_map", {}).get(e_assigner, [])
                    e_worker = st.selectbox("修改主要人員", e_workers, index=e_workers.index(curr['作業人員']) if curr['作業人員'] in e_workers else 0)
                    
                    if st.form_submit_button("💾 儲存修改"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": e_order, "派工人員": e_assigner, "作業人員": e_worker})
                        st.success("已更新")
                        st.rerun()
                if st.button("🗑️ 刪除任務", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.rerun()
        except: st.error("讀取失敗")

    # --- 8. ⚙️ 系統內容管理 (優化排版) ---
    elif menu == "⚙️ 系統內容管理":
        st.markdown('<p class="main-title">⚙️ 系統內容管理</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 基礎名單管理", "👷 人員獨立配置"])
        
        with tab1:
            with st.form("basic_settings"):
                new_orders = st.text_area("📦 製令清單 (逗號隔開)", value=",".join(settings.get("orders", [])), height=150)
                new_assigners = st.text_area("🚩 派工人員清單 (逗號隔開)", value=",".join(settings.get("assigners", [])), height=150)
                new_processes = st.text_area("⚙️ 製造工序清單 (逗號隔開)", value=",".join(settings.get("processes", [])), height=150)
                if st.form_submit_button("💾 儲存基礎名單"):
                    settings["orders"] = [x.strip() for x in new_orders.split(",") if x.strip()]
                    settings["assigners"] = [x.strip() for x in new_assigners.split(",") if x.strip()]
                    settings["processes"] = [x.strip() for x in new_processes.split(",") if x.strip()]
                    requests.patch(f"{SETTING_URL}.json", json=settings)
                    st.rerun()

        with tab2:
            target_assigner = st.selectbox("請選擇派工人員", settings.get("assigners", []))
            worker_map = settings.get("worker_map", {})
            current_workers = worker_map.get(target_assigner, [])
            
            with st.form("worker_config"):
                worker_input = st.text_area(f"👷 編輯『{target_assigner}』的作業員 (逗號隔開)", value=",".join(current_workers), height=200)
                if st.form_submit_button(f"💾 儲存 {target_assigner} 的
