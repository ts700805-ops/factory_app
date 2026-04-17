import streamlit as st
import pandas as pd
import datetime
import requests
import json

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
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}

# --- 2. 頁面配置 (保留您喜歡的樣式) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 36px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stat-card { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        border-top: 5px solid #1E3A8A; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); 
        text-align: center; 
        margin-bottom: 10px;
    }
    .stat-label { font-size: 18px !important; color: #555; font-weight: bold; }
    .stat-value { font-size: 32px !important; font-weight: 800; color: #1E3A8A; }
    .task-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #1E3A8A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .task-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }
    .task-order { font-size: 22px; font-weight: bold; color: #1e293b; }
    .task-badge { background-color: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; }
    .task-info { font-size: 18px; color: #334155; margin: 5px 0; }
    .task-footer { font-size: 14px; color: #64748b; margin-top: 10px; font-style: italic; }
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

    # --- 3. 📊 經營者看板 (首頁) ---
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
                with c1: 
                    st.markdown(f'''<div class="stat-card"><span class="stat-label">待處理總量</span><br><span class="stat-value">{len(df)}</span> <span style="font-size:20px">件</span></div>''', unsafe_allow_html=True)
                with c2:
                    all_workers = pd.concat([df['作業人員'], df.get('協助人員', pd.Series(['無']*len(df)))])
                    worker_count = all_workers[all_workers != "無"].nunique() if not df.empty else 0
                    st.markdown(f'''<div class="stat-card"><span class="stat-label">目前動員人數</span><br><span class="stat-value">{worker_count}</span> <span style="font-size:20px">人</span></div>''', unsafe_allow_html=True)
                
                with st.expander("🔍 快速篩選資料", expanded=False):
                    f1, f2, f3 = st.columns(3)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序篩選", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員篩選", ["全部"] + sorted(df["派工人員"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]

                st.markdown("---")
                st.subheader("📦 轉角遇到愛任務")

                for index, row in filtered_df.iterrows():
                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-header">
                            <span class="task-order">📦 製令：{row['製令']}</span>
                            <span class="task-badge">{row['製造工序']}</span>
                        </div>
                        <div class="task-info">👷 主手人員：<b>{row['作業人員']}</b></div>
                        <div class="task-info">🤝 協助人員：{row.get('協助人員', '無')}</div>
                        <div class="task-footer">⏳ 作業期限：{row['作業期限']} | 🚩 派工員：{row['派工人員']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"✅ 完成這筆紀錄 ({row['製令']})", key=f"btn_{row['db_key']}", use_container_width=True):
                        done_data = row.to_dict()
                        db_key = done_data.pop('db_key')
                        done_data['實際完工時間'] = get_now_str()
                        final_data = {str(k): (str(v) if pd.notna(v) else "無") for k, v in done_data.items()}
                        
                        # 【修正 1】：使用 Unicode 編碼發送完工紀錄
                        requests.post(f"{DONE_URL}.json", data=json.dumps(final_data, ensure_ascii=True))
                        requests.delete(f"{DB_URL}/{db_key}.json")
                        st.balloons()
                        st.rerun()
            else:
                st.info("目前尚無任務。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. 📝 現場派工作業 (關鍵修正處) ---
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
        
        if st.button("🚀 發布任務"):
            if not worker: st.error("請先配置作業人員。")
            else:
                # 【修正 2】：將日期與資料強制轉為字串並透過 Unicode 序列化發送
                log = {
                    "製令": str(order_no), 
                    "製造工序": str(process_name), 
                    "派工人員": str(assigner), 
                    "作業人員": str(worker), 
                    "協助人員": str(assistant), 
                    "作業期限": deadline.strftime("%Y-%m-%d"), 
                    "提交時間": get_now_str()
                }
                headers = {'Content-Type': 'application/json'}
                res = requests.post(f"{DB_URL}.json", data=json.dumps(log, ensure_ascii=True), headers=headers)
                
                if res.status_code == 200:
                    st.balloons(); st.success(f"任務 [{order_no}] 已發布！")
                else:
                    st.error(f"發布失敗：{res.text}")

    # --- 5. 其餘功能 (編輯/管理) 同步修正傳輸格式 ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 待辦派工紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"製令：{log.get('製令')} | 主要：{log.get('作業人員')}" for log in all_logs}
                target_id = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                if curr:
                    with st.expander("📝 編輯內容", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        edit_order = c1.selectbox("修改製令", settings.get("orders", []))
                        edit_proc = c2.selectbox("修改工序", settings.get("processes", []))
                        edit_assigner = c3.selectbox("修改派工員", settings.get("assigners", []))
                        
                        if st.button("💾 儲存修改"):
                            # 【修正 3】：Patch 也使用 Unicode 安全傳輸
                            patch_data = {"製令": str(edit_order), "製造工序": str(edit_proc), "派工人員": str(edit_assigner)}
                            requests.patch(f"{DB_URL}/{target_id}.json", data=json.dumps(patch_data, ensure_ascii=True))
                            st.success("更新成功！"); st.rerun()
                    if st.button("🗑️ 刪除此待辦", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json"); st.rerun()
        except: st.error("讀取錯誤")

    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("basic_settings"):
            new_orders = st.text_area("📦 編輯製令清單", value=",".join(settings.get("orders", [])))
            new_assigners = st.text_area("🚩 編輯派工人員", value=",".join(settings.get("assigners", [])))
            new_processes = st.text_area("⚙️ 編輯工序清單", value=",".join(settings.get("processes", ["預設工序"])))
            if st.form_submit_button("💾 儲存名單"):
                new_data = {
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                # 【修正 4】：系統設定儲存也採用 Unicode 安全模式
                requests.patch(f"{SETTING_URL}.json", data=json.dumps(new_data, ensure_ascii=True))
                st.rerun()
        
        st.markdown("---")
        target_assigner = st.selectbox("配置作業員：", settings.get("assigners", []))
        with st.form("worker_config"):
            worker_input = st.text_area(f"👷 {target_assigner} 的作業員", value=",".join(settings.get("worker_map", {}).get(target_assigner, [])))
            if st.form_submit_button("💾 儲存配置"):
                wm = settings.get("worker_map", {})
                wm[target_assigner] = [x.strip() for x in worker_input.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", data=json.dumps({"worker_map": wm}, ensure_ascii=True))
                st.rerun()

    elif menu == "✅ 已完工歷史紀錄查詢":
        # 此處保持讀取邏輯
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        r_done = requests.get(f"{DONE_URL}.json")
        if r_done.json():
            df_done = pd.DataFrame(list(r_done.json().values())).fillna("無")
            st.dataframe(df_done, use_container_width=True, hide_index=True)
