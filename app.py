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
        if "worker_map" not in data:
            data["worker_map"] = {}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "worker_map": {}, "processes": ["預設工序"]}

# --- 2. 頁面配置 (強化 CSS 樣式) ---
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
        transition: transform 0.2s;
    }
    .task-card:hover { transform: translateY(-3px); }
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
    if st.button("我愛德文★志偉愛我"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁)", "✅ 已完工歷史紀錄查詢", "📝 愛的派工作業中心", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    if menu == "📊 控制塔台 (首頁)":
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

                    f4, f5, f6 = st.columns(3)
                    sel_worker = f4.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))
                    sel_assistant = f5.selectbox("按協助人員篩選", ["全部"] + sorted(df["協助人員"].unique().tolist()))
                    sel_deadline = f6.selectbox("按作業期限篩選", ["全部"] + sorted(df["作業期限"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部":
                    filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部":
                    filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部":
                    filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部":
                    filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]
                if sel_assistant != "全部":
                    filtered_df = filtered_df[filtered_df["協助人員"] == sel_assistant]
                if sel_deadline != "全部":
                    filtered_df = filtered_df[filtered_df["作業期限"] == sel_deadline]

                st.markdown("---")
                st.subheader("📦 轉角遇到💗德文與志偉💗" )

                for index, row in filtered_df.iterrows():
                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-header">
                            <span class="task-order">📦 製令：{row['製令']}</span>
                            <span class="task-badge">{row['製造工序']}</span>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-top:8px; font-size:18px; color:#334155;">
                            <div style="flex:1 1 220px;">👷 主手人員：<b>{row['作業人員']}</b></div>
                            <div style="flex:1 1 220px;">🤝 協助人員：{row.get('協助人員', '無')}</div>
                            <div style="flex:2 1 320px;">⏳ 作業期限：{row['作業期限']} | 🚩 派工員：{row['派工人員']}</div>
                            <div style="flex:0 0 auto; background:#fef3c7; color:#92400e; padding:4px 12px; border-radius:999px; font-size:14px; font-weight:700;">
                                超慧科技
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"✅ 完成這筆紀錄 ({row['製令']})", key=f"btn_{row['db_key']}", use_container_width=True):
                        done_data = row.to_dict()
                        db_key = done_data.pop('db_key')
                        done_data['實際完工時間'] = get_now_str()
                        final_data = {k: (v if pd.notna(v) else "無") for k, v in done_data.items()}
                        requests.post(f"{DONE_URL}.json", json=final_data)
                        requests.delete(f"{DB_URL}/{db_key}.json")
                        st.balloons()
                        st.rerun()
            else:
                st.info("目前尚無任務。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    elif menu == "✅ 已完工歷史紀錄查詢":
        st.markdown('<p class="main-title" style="color: #059669; border-bottom: 4px solid #059669;">✅ 已完工歷史紀錄查詢</p>', unsafe_allow_html=True)
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_data = r_done.json()
            if done_data:
                done_list = []
                for k, v in done_data.items():
                    if v:
                        v['done_key'] = k
                        done_list.append(v)
                if done_list:
                    df_done = pd.DataFrame(done_list).fillna("無")
                    if '實際完工時間' in df_done.columns:
                        df_done = df_done.sort_values(by='實際完工時間', ascending=False)
                    hist_display_cols = ["實際完工時間", "製令", "製造工序", "作業人員", "協助人員"]
                    st.dataframe(df_done[[c for c in hist_display_cols if c in df_done.columns]], use_container_width=True, height=300, hide_index=True)

                    st.markdown("---")
                    st.subheader("🛠️ 歷史紀錄管理 (編輯 / 刪除)")
                    hist_options = {row['done_key']: f"[{row.get('實際完工時間', '無')}] {row['製令']} - {row['作業人員']}" for _, row in df_done.iterrows()}
                    target_done_key = st.selectbox("請選擇要編輯或刪除的完工紀錄", options=list(hist_options.keys()), format_func=lambda x: hist_options[x])

                    curr_done = next((item for item in done_list if item["done_key"] == target_done_key), None)
                    if curr_done:
                        with st.expander("📝 編輯完工資訊"):
                            ec1, ec2 = st.columns(2)
                            p_assigner = curr_done.get('派工人員')
                            p_worker_list = settings.get("worker_map", {}).get(p_assigner, [])
                            h_worker = ec1.selectbox("修改人員", p_worker_list, index=p_worker_list.index(curr_done.get('作業人員')) if curr_done.get('作業人員') in p_worker_list else 0)
                            h_assistant = ec2.selectbox("修改協助人員", ["無"] + p_worker_list, index=(["無"] + p_worker_list).index(curr_done.get('協助人員')) if curr_done.get('協助人員') in (["無"] + p_worker_list) else 0)
                            if st.button("💾 儲存歷史修改"):
                                requests.patch(f"{DONE_URL}/{target_done_key}.json", json={"作業人員": h_worker, "協助人員": h_assistant})
                                st.success("歷史紀錄已更新！")
                                st.rerun()

                        st.markdown("⚠️ **刪除歷史紀錄**")
                        del_h_pass = st.text_input("輸入管理密碼以刪除紀錄", type="password", key=f"h_del_pwd_{target_done_key}")
                        if st.button("🗑️ 確認刪除此筆歷史紀錄", type="primary"):
                            if del_h_pass == "1234":
                                requests.delete(f"{DONE_URL}/{target_done_key}.json")
                                st.warning("紀錄已移除。")
                                st.rerun()
                            else:
                                st.error("密碼錯誤！")
                else:
                    st.info("目前尚無完工紀錄。")
            else:
                st.info("目前尚無完工紀錄。")
        except Exception as e:
            st.error(f"連線錯誤：{e}")

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
            if not worker:
                st.error("請先配置作業人員。")
            else:
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "協助人員": assistant, "作業期限": str(deadline), "提交時間": get_now_str()}
                res = requests.post(f"{DB_URL}.json", json=log)
                if res.status_code == 200:
                    st.balloons()
                    st.success(f"任務 [{order_no}] 已發布！")

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
                        edit_order = c1.selectbox("修改製令", settings.get("orders", []), index=settings.get("orders", []).index(curr.get('製令')) if curr.get('製令') in settings.get("orders", []) else 0)
                        edit_proc = c2.selectbox("修改工序", settings.get("processes", []), index=settings.get("processes", []).index(curr.get('製造工序')) if curr.get('製造工序') in settings.get("processes", []) else 0)
                        edit_assigner = c3.selectbox("修改派工員", settings.get("assigners", []), index=settings.get("assigners", []).index(curr.get('派工人員')) if curr.get('派工人員') in settings.get("assigners", []) else 0)

                        edit_worker_list = settings.get("worker_map", {}).get(edit_assigner, [])
                        c4, c5 = st.columns(2)
                        new_worker = c4.selectbox("修改主手", edit_worker_list, index=edit_worker_list.index(curr.get('作業人員')) if curr.get('作業人員') in edit_worker_list else 0)
                        new_assist = c5.selectbox("修改助手", ["無"] + edit_worker_list, index=(["無"] + edit_worker_list).index(curr.get('協助人員')) if curr.get('協助人員') in (["無"] + edit_worker_list) else 0)

                        if st.button("💾 儲存修改"):
                            requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": edit_order, "製造工序": edit_proc, "派工人員": edit_assigner, "作業人員": new_worker, "協助人員": new_assist})
                            st.success("更新成功！")
                            st.rerun()
                    if st.button("🗑️ 刪除此待辦", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
            else:
                st.info("無待辦紀錄。")
        except:
            st.error("讀取錯誤")

    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("basic_settings"):
            new_orders = st.text_area("📦 編輯製令清單", value=",".join(settings.get("orders", [])))
            new_assigners = st.text_area("🚩 編輯派工人員", value=",".join(settings.get("assigners", [])))
            new_processes = st.text_area("⚙️ 編輯工序清單", value=",".join(settings.get("processes", ["預設工序"])))
            if st.form_submit_button("💾 儲存名單"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                })
                st.rerun()

        st.markdown("---")
        target_assigner = st.selectbox("請選擇派工人員配置手下：", settings.get("assigners", []))
        with st.form("worker_config"):
            worker_input = st.text_area(f"👷 {target_assigner} 的作業員", value=",".join(settings.get("worker_map", {}).get(target_assigner, [])))
            if st.form_submit_button("💾 儲存配置"):
                wm = settings.get("worker_map", {})
                wm[target_assigner] = [x.strip() for x in worker_input.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"worker_map": wm})
                st.rerun()
