import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 資料庫路徑設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"
# 新增手工具相關路徑
TOOL_LIST_URL = f"{DB_BASE_URL}/tool_settings"     # 儲存手工具下拉選單內容
USER_TOOLS_URL = f"{DB_BASE_URL}/user_tool_logs"  # 儲存人員手工具紀錄表

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "12345", "77777"],
        "process_map": {
            "陳德文": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢"],
            "吳政昌": ["S.T作業"],
            "劉志偉": ["收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"]
        },
        "staff_map": {} 
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict): return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式設定 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .order-card { background: white; border-radius: 12px; border: 1px solid #cbd5e1; margin-bottom: 25px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .order-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 12px 18px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; font-size: 1.2rem; }
    .power-date-tag { background: #fbbf24; color: #1e3a8a; padding: 4px 12px; border-radius: 8px; font-size: 0.9rem; font-weight: 800; display: flex; align-items: center; }
    .proc-row-container { padding: 15px 18px; border-bottom: 1px solid #cbd5e1; background-color: #e2e8f0; }
    .proc-name { font-weight: 900; color: #0f172a; font-size: 1.05rem; border-left: 5px solid #ef4444; padding-left: 12px; }
    .badge-staff { background: #eff6ff; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-size: 0.95rem; font-weight: 700; border: 1px solid #bfdbfe; }
    .status-done-box { background: #dcfce7; color: #166534; font-weight: 800; font-size: 0.9rem; padding: 6px 12px; border-radius: 6px; border: 1px solid #bbf7d0; display: inline-block; }
    .status-assign-box { background: #fff9db; color: #854d0e; font-weight: 700; padding: 6px 12px; border-radius: 6px; border: 1px solid #ffe066; font-size: 0.9rem; }
    .status-empty { color: #64748b; font-style: italic; font-weight: 700; font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
process_map = settings.get("process_map", {})
staff_map = settings.get("staff_map", {}) 

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"

# --- 4. 登入介面 ---
if "user" not in st.session_state:
    st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-size:3rem; font-weight:900;">⚓ 超慧科技系統</h1>', unsafe_allow_html=True)
    with st.columns([1,1.2,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇組長姓名登入", sorted(all_leaders))
            if st.button("確認登入", use_container_width=True, type="primary"):
                st.session_state.user = u
                st.rerun()
else:
    # 側邊欄導航 (新增手工具相關選項)
    st.sidebar.markdown(f"### 👤 當前人員：**{st.session_state.user}**")
    nav = st.sidebar.radio("功能導航", [
        "📊 製造部派工專區", 
        "📈 工時統計分析", 
        "📜 完工紀錄查詢", 
        "🔧 固資&手工具紀錄表",
        "⚙️ 資產編輯清單",
        "📝 任務派發", 
        "⚙️ 設定管理"
    ])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()
# --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

        @st.dialog("👥 編輯施工人員", width="medium")
        def edit_staff_dialog(order_id, proc_name, current_data):
            st.subheader(f"🛠️ {proc_name}")
            current_leader = st.session_state.user
            my_team = staff_map.get(current_leader, [])
            # 💡 修正：確保 options 來源正確，如果沒組員就用全體人員
            display_options = my_team if my_team else all_staff
            options = ["NA"] + sorted(list(set(display_options)))
            
            with st.form(f"staff_edit_form_{order_id}_{proc_name}"):
                new_wk = []
                for i in range(5):
                    p_val = current_data.get(f"人員{i+1}", "NA")
                    d_idx = options.index(p_val) if p_val in options else 0
                    sel = st.selectbox(f"人員 {i+1}", options, index=d_idx, key=f"dlg_staff_{order_id}_{proc_name}_{i}")
                    new_wk.append(sel)
                
                if st.form_submit_button("💾 儲存修改", use_container_width=True):
                    new_payload = current_data.copy()
                    new_payload.update({
                        "最後更新": get_now_str(),
                        "人員1": new_wk[0], "人員2": new_wk[1], "人員3": new_wk[2], "人員4": new_wk[3], "人員5": new_wk[4]
                    })
                    db_id = new_payload.pop("db_id", None)
                    if db_id:
                        requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                        st.success("✅ 人員更新成功！")
                        time.sleep(0.5); st.rerun()

        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
            try:
                default_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d") if current_date_str != "未設定" else datetime.date.today()
            except:
                default_date = datetime.date.today()
            new_date = st.date_input("請選擇新的通電日期", value=default_date, key=f"date_inp_{order_id}")
            if st.button("💾 確認修改", use_container_width=True, key=f"conf_date_{order_id}"):
                for db_id, data in related_records.items():
                    data["通電日期"] = str(new_date)
                    data["最後更新"] = get_now_str()
                    requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(data))
                st.success("✅ 日期已更新")
                time.sleep(0.5); st.rerun()

        # --- 頁面篩選列 (放在 try 外面確保不會被 catch) ---
        my_procs = process_map.get(st.session_state.user, process_list)
        # 💡 這裡定義篩選用的名單
        my_team_for_filter = staff_map.get(st.session_state.user, all_staff)
        
        f_cols = st.columns([1, 1, 1])
        with f_cols[0]: 
            s_order = st.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))), key="filter_order")
        with f_cols[1]: 
            s_staff = st.selectbox("👤 篩選人員", ["全部"] + sorted(my_team_for_filter), key="filter_staff")
        
        # --- 資料讀取與顯示區 ---
        try:
            # 1. 抓取進行中資料
            r_work_raw = requests.get(f"{DB_URL}.json").json()
            r_work = r_work_raw if r_work_raw and isinstance(r_work_raw, dict) else {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]) if r_work else pd.DataFrame()
            if not df_work.empty: df_work = df_work.fillna("NA")

            # 2. 抓取已完工資料
            r_finish_raw = requests.get(f"{FINISH_URL}.json").json()
            r_finish = r_finish_raw if r_finish_raw and isinstance(r_finish_raw, dict) else {}
            df_finish = pd.DataFrame([v for k, v in r_finish.items()]) if r_finish else pd.DataFrame()
            if not df_finish.empty: df_finish = df_finish.fillna("NA")

            # 3. 決定要顯示的製令
            base_orders = [str(o) for o in order_list]
            if s_order != "全部": base_orders = [str(s_order)]

            final_display_orders = []
            for o_id in base_orders:
                # 篩選人員邏輯
                if s_staff == "全部":
                    final_display_orders.append(o_id)
                else:
                    found = False
                    o_df_tmp = df_work[df_work["製令"] == str(o_id)] if not df_work.empty and "製令" in df_work.columns else pd.DataFrame()
                    f_df_tmp = df_finish[df_finish["製令"] == str(o_id)] if not df_finish.empty and "製令" in df_finish.columns else pd.DataFrame()
                    for df in [o_df_tmp, f_df_tmp]:
                        if not df.empty:
                            for i in range(1, 6):
                                col_name = f"人員{i}"
                                if col_name in df.columns and (df[col_name] == s_staff).any():
                                    found = True; break
                    if found: final_display_orders.append(o_id)

            # 4. 渲染卡片
            if not final_display_orders:
                st.info(f"💡 目前無符合條件的項目")
            else:
                main_cols = st.columns(3) 
                for idx, o_id in enumerate(final_display_orders):
                    o_df = df_work[df_work["製令"] == str(o_id)] if not df_work.empty and "製令" in df_work.columns else pd.DataFrame()
                    f_df_order = df_finish[df_finish["製令"] == str(o_id)] if not df_finish.empty and "製令" in df_finish.columns else pd.DataFrame()
                    
                    # 抓取通電日期
                    p_date = "未設定"
                    if not o_df.empty and "通電日期" in o_df.columns:
                        p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    elif not f_df_order.empty and "通電日期" in f_df_order.columns:
                        p_date = str(f_df_order.iloc[0].get("通電日期", "未設定"))

                    with main_cols[idx % 3]:
                        st.markdown(f'<div class="order-card"><div class="order-header"><span>📦 製令：{o_id}</span><span class="power-date-tag">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)
                        if st.button("📅", key=f"date_edit_{o_id}"):
                            related = {k: v for k, v in r_work.items() if v.get("製令") == str(o_id)}
                            edit_power_date_dialog(o_id, p_date, related)

                        for p_idx, proc in enumerate(my_procs):
                            u_key = f"v21_{str(o_id).replace('-','_')}_{p_idx}"
                            m_w = o_df[o_df["製造工序"] == proc] if not o_df.empty and "製造工序" in o_df.columns else pd.DataFrame()
                            m_f = f_df_order[f_df_order["製造工序"] == proc] if not f_df_order.empty and "製造工序" in f_df_order.columns else pd.DataFrame()
                            
                            is_done = not m_f.empty
                            target_row = m_w.iloc[0] if not m_w.empty else (m_f.iloc[0] if not m_f.empty else None)
                            
                            st.markdown('<div class="proc-row-container">', unsafe_allow_html=True)
                            r_ui = st.columns([3.2, 4.0, 0.8, 2.0])
                            with r_ui[0]: st.markdown(f'<div class="proc-name">{proc}</div>', unsafe_allow_html=True)
                            with r_ui[1]:
                                if target_row is not None:
                                    staff_html = "".join([f'<span class="badge-staff">{target_row.get(f"人員{i}")}</span> ' for i in range(1,6) if target_row.get(f"人員{i}") not in ["NA", None]])
                                    st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:4px;">{staff_html if staff_html else "尚未派工"}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div style="color:gray; font-size:0.8rem;">尚未派工</div>', unsafe_allow_html=True)
                            
                            with r_ui[2]:
                                if not is_done and st.button("✏️", key=f"eb_staff_{u_key}"):
                                    if m_w.empty:
                                        init_data = {"製令": str(o_id), "製造工序": proc, "組長": st.session_state.user, "通電日期": p_date, "人員1": "NA", "人員2": "NA", "人員3": "NA", "人員4": "NA", "人員5": "NA"}
                                        res = requests.post(f"{DB_URL}.json", data=json.dumps(init_data))
                                        init_data["db_id"] = res.json().get("name")
                                        edit_staff_dialog(o_id, proc, init_data)
                                    else:
                                        edit_staff_dialog(o_id, proc, target_row.to_dict())
                            
                            with r_ui[3]:
                                if is_done: 
                                    st.markdown('<div class="status-done-box">✅ 已完工</div>', unsafe_allow_html=True)
                                elif target_row is not None and any(target_row.get(f"人員{i}") != "NA" for i in range(1,6)):
                                    if st.button("完工", key=f"db_{u_key}", type="primary", use_container_width=True):
                                        dat = m_w.iloc[0].to_dict()
                                        db_id = dat.pop('db_id')
                                        dat["完工時間"] = get_now_str()
                                        dat["完工人員"] = st.session_state.user
                                        requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                        requests.delete(f"{DB_URL}/{db_id}.json"); st.rerun()
                                else: 
                                    st.markdown('<div class="status-assign-box">⚠️ 請指派</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            # 💡 增加錯誤偵測，幫助開發者看到真正的問題
            st.error(f"系統偵測到錯誤：{str(e)}")
            st.warning("目前系統資料緩衝中，請稍後再試。")

# --- 📈 工時統計分析 ---
    elif st.session_state.menu_selection == "📈 工時統計分析":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">⏱️ 生產工時管理系統</h1>', unsafe_allow_html=True)
        
        # 1. 取得當前登入者 (組長)
        current_leader = st.session_state.user 
        
        # 2. 從 staff_map 篩選出屬於該組長的成員
        try:
            # 抓取對照表 (假設格式為 {"組員": "組長", ...})
            staff_map_res = requests.get(f"{DB_BASE_URL}/settings/staff_map.json")
            staff_map = staff_map_res.json() if staff_map_res.status_code == 200 else {}
            
            # --- 核心邏輯：找出誰的組長是我 ---
            my_staff_list = [member for member, leader in staff_map.items() if leader == current_leader]
            
            # 如果名單是空的，至少把組長自己放進去，避免選單壞掉
            if not my_staff_list:
                my_staff_list = [current_leader]
        except:
            my_staff_list = [current_leader]

        # 3. 顯示下拉選單 (只顯示該組長的成員)
        selected_worker = st.selectbox("👤 選擇執行組員 (您的組員)", sorted(my_staff_list), key="active_worker_select")
        st.divider()

        with st.container():
            st.markdown('<div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #dee2e6; margin-bottom:20px;">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                t_oid = st.selectbox("📦 選擇製令編號", sorted([str(o).strip() for o in order_list]), key="t_oid_select") if order_list else st.text_input("📦 手動輸入製令")
            with c2:
                t_proc = st.selectbox("🛠️ 選擇執行工序", process_list if process_list else ["預設工序"])
            with c3:
                st.write(" ")
                if st.button("➕ 加入看板", type="primary", use_container_width=True):
                    TIMER_DB_URL = f"{DB_BASE_URL}/active_timers"
                    # 加入看板時，存入選中的組員姓名
                    new_timer = {
                        "製令": t_oid, 
                        "工序": t_proc, 
                        "status": "stop", 
                        "accumulated": 0, 
                        "start_time": 0, 
                        "人員1": selected_worker 
                    }
                    requests.post(f"{TIMER_DB_URL}.json", data=json.dumps(new_timer))
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 顯示計時看板 ---
        TIMER_DB_URL = f"{DB_BASE_URL}/active_timers"
        active_timers = requests.get(f"{TIMER_DB_URL}.json").json() or {}
        
        if active_timers:
            grouped_timers = {}
            for db_id, task in active_timers.items():
                oid = task.get("製令", "未知製令")
                if oid not in grouped_timers: grouped_timers[oid] = []
                task['db_id'] = db_id
                grouped_timers[oid].append(task)

            for oid in sorted(grouped_timers.keys()):
                st.markdown(f'<div style="background:#1e3a8a; color:white; padding:8px 15px; border-radius:10px 10px 0 0; font-weight:bold; margin-top:20px;">📦 製令編號：{oid}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    for task in grouped_timers[oid]:
                        db_id = task['db_id']
                        p_name = task.get("工序")
                        status = task.get("status")
                        acc = task.get("accumulated", 0)
                        start = task.get("start_time", 0)
                        worker_name = task.get("人員1", "未指定") # 這裡會顯示是哪位組員

                        st.components.v1.html(f"""
                            <div style="background:#f1f5f9; padding:10px; border-radius:8px; margin-bottom:10px; border-left:5px solid #3b82f6; display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <div style="font-weight:bold; color:#0f172a;">🛠️ {p_name}</div>
                                    <div style="font-size:0.8rem; color:#64748b;">👤 執行人員: {worker_name}</div>
                                </div>
                                <div id="timer_{db_id}" style="color:#ef4444; font-family:monospace; font-size:1.5rem; font-weight:bold;">00:00:00</div>
                            </div>
                            <script>
                                (function() {{
                                    var acc = {acc}, start = {start}, status = '{status}', display = document.getElementById('timer_{db_id}');
                                    function update() {{
                                        var total = acc + (status === 'running' ? (Date.now() / 1000) - start : 0);
                                        var h = Math.floor(total / 3600).toString().padStart(2, '0'), m = Math.floor((total % 3600) / 60).toString().padStart(2, '0'), s = Math.floor(total % 60).toString().padStart(2, '0');
                                        display.innerText = h + ":" + m + ":" + s;
                                    }}
                                    setInterval(update, 1000); update();
                                }})();
                            </script>
                        """, height=85)
                        
                        b1, b2, b3 = st.columns([1, 1, 1])
                        with b1:
                            if status != 'running':
                                if st.button("▶️ 開始", key=f"s_{db_id}"):
                                    requests.patch(f"{TIMER_DB_URL}/{db_id}.json", data=json.dumps({"status": "running", "start_time": time.time()}))
                                    st.rerun()
                            else:
                                if st.button("⏸️ 暫停", key=f"p_{db_id}"):
                                    requests.patch(f"{TIMER_DB_URL}/{db_id}.json", data=json.dumps({"status": "paused", "accumulated": acc + (time.time() - start), "start_time": 0}))
                                    st.rerun()
                        with b2:
                            if st.button("⏹️ 結束", key=f"e_{db_id}"):
                                final_sec = acc + (time.time() - start if status == 'running' else 0)
                                requests.post(f"{FINISH_URL}.json", data=json.dumps({
                                    "製令": oid, "工序": p_name, "秒數": final_sec, 
                                    "完工時間": get_now_str(), "人員1": worker_name
                                }))
                                requests.delete(f"{TIMER_DB_URL}/{db_id}.json")
                                st.rerun()
                        with b3:
                            if st.button("🗑️ 刪除", key=f"d_{db_id}"):
                                requests.delete(f"{TIMER_DB_URL}/{db_id}.json")
                                st.rerun()
        else:
            st.info("💡 目前無進行中任務。")
# --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📜 歷史完工紀錄</h1>', unsafe_allow_html=True)
        
        all_logs = requests.get(f"{FINISH_URL}.json").json()
        if all_logs:
            df = pd.DataFrame([dict(v, db_id=k) for k, v in all_logs.items()])
            search_q = st.text_input("🔍 搜尋紀錄")
            if search_q: 
                df = df[df.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
            
            if not df.empty:
                for o_id, group in df.groupby("製令"):
                    display_df = group.copy()
                    
                    # 1. 計算工時(分)與總秒數
                    total_all_seconds = 0
                    if '秒數' in display_df.columns:
                        display_df['工時(分)'] = (display_df['秒數'] / 60).round(2)
                        total_all_seconds = int(display_df['秒數'].sum()) # 取得該製令總秒數
                        
                        # 2. 逆推開始時間
                        try:
                            temp_finish = pd.to_datetime(display_df['完工時間'])
                            display_df['開始時間'] = (temp_finish - pd.to_timedelta(display_df['秒數'], unit='s')).dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            display_df['開始時間'] = "計算失敗"

                    # 3. 將總秒數轉換為「xx小時 xx分 xx秒」
                    hrs = total_all_seconds // 3600
                    mins = (total_all_seconds % 3600) // 60
                    secs = total_all_seconds % 60
                    time_str = f"{hrs}小時 {mins}分 {secs}秒"

                    # 4. 在標題顯示 (包含您紅框要求的總工時，格式改為時分秒)
                    with st.expander(f"📦 製令：{o_id} ({len(group)} 項 | 總工時：{time_str})"):
                        
                        # 設定表格順序
                        cols = ["工序", "開始時間", "完工時間", "工時(分)"]
                        existing_cols = [c for c in cols if c in display_df.columns]
                        
                        st.table(display_df[existing_cols])
                        
                        if st.button(f"🗑️ 刪除紀錄", key=f"del_{o_id}"):
                            for d_id in group['db_id']: requests.delete(f"{FINISH_URL}/{d_id}.json")
                            st.rerun()
            else: st.warning("查無紀錄。")
        else: st.info("💡 目前尚無紀錄。")
# --- 🔧 人員手工具紀錄表 (修正版：恢復資產匯出 + 移除重複) ---
    elif st.session_state.menu_selection == "🔧 固資&手工具紀錄表":
        import io
        st.markdown('<h1 style="text-align:center; color:#db2777; font-weight:900; font-size:2.5rem;">🌸 超慧固資&手工具紀錄表</h1>', unsafe_allow_html=True)
        
        # 1. 讀取資料
        user_tool_raw = requests.get(f"{USER_TOOLS_URL}.json").json() or {}
        asset_tools_raw = requests.get(f"{DB_URL}/asset_tools.json").json() or {}
        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, [])

        # 2. 安全修改與刪除彈窗
        @st.dialog("🔒 安全驗證與修改")
        def edit_record_dialog(db_id, current_name, current_qty, person):
            try:
                t_res = requests.get(f"{TOOL_LIST_URL}.json").json() or {}
                all_tools = t_res.get("tool_types", [])
            except: all_tools = []
            if current_name and current_name not in all_tools: all_tools.append(current_name)

            st.markdown(f"**正在修改 {person} 的紀錄**")
            pwd = st.text_input("請輸入驗證碼", type="password", key=f"fixed_dlg_pwd_{db_id}")
            new_name = st.selectbox("修改工具名稱", options=all_tools, index=all_tools.index(current_name) if current_name in all_tools else 0, key=f"fixed_dlg_name_{db_id}")
            new_qty = st.number_input("修改數量", min_value=1, value=int(current_qty), key=f"fixed_dlg_qty_{db_id}")
            if st.button("💗 確認修改", use_container_width=True, key=f"fixed_dlg_btn_{db_id}"):
                if pwd == "0000":
                    requests.patch(f"{USER_TOOLS_URL}/{db_id}.json", data=json.dumps({"手工具名稱": new_name, "數量": int(new_qty)}))
                    st.success("修改成功！"); time.sleep(0.5); st.rerun()
                else: st.error("驗證碼錯誤")

        @st.dialog("🔒 刪除紀錄確認")
        def delete_record_dialog(db_id, tool_name):
            st.warning(f"確定要刪除「{tool_name}」嗎？")
            pwd = st.text_input("請輸入驗證碼", type="password", key=f"fixed_del_pwd_{db_id}")
            if st.button("❌ 確定刪除", use_container_width=True, key=f"fixed_del_btn_{db_id}"):
                if pwd == "0000":
                    requests.delete(f"{USER_TOOLS_URL}/{db_id}.json")
                    st.success("已刪除！"); time.sleep(0.5); st.rerun()
                else: st.error("驗證碼錯誤")

        # 3. 建立分頁
        tab1, tab2 = st.tabs(["👥 人員紀錄", "🛡️ 資產總覽"])

        with tab1:
            # --- 唯一篩選區 ---
            st.markdown("### 🔍 查詢與清點")
            c1, c2 = st.columns(2)
            with c1:
                filter_type = st.radio("篩選範圍", ["我的組員", "全廠人員搜尋"], horizontal=True, key="unique_filter_radio")
            with c2:
                if filter_type == "我的組員":
                    search_staff = st.selectbox("👤 選擇組員", ["顯示全組"] + sorted(my_team), key="unique_sel_team")
                else:
                    search_staff = st.selectbox("🌍 選擇全廠人員", ["顯示全部"] + sorted(list(all_staff)), key="unique_sel_all")

            if user_tool_raw:
                t_data = []
                for k, v in user_tool_raw.items():
                    item = v.copy(); item['db_id'] = k
                    item['類型'] = "資產工具" if "【資產】" in str(v.get('手工具名稱','')) else "一般工具"
                    t_data.append(item)
                tool_df = pd.DataFrame(t_data)

                if filter_type == "我的組員":
                    display_df = tool_df[tool_df["人員"].isin(my_team)] if search_staff == "顯示全組" else tool_df[tool_df["人員"] == search_staff]
                else:
                    display_df = tool_df if search_staff == "顯示全部" else tool_df[tool_df["人員"] == search_staff]

                if not display_df.empty:
                    csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(label="📄 匯出人員清點表", data=csv_data, file_name="人員工具清點.csv", key="p_csv_btn")

                    st.markdown("""<style>.card { background: white; border-radius: 8px; padding: 10px; margin-bottom: 5px; border: 1px solid #fce7f3; } .asset-card { border-left: 8px solid #8b5cf6 !important; background: #f5f3ff !important; } .t-title { font-weight: 800; color: #1f2937; } .t-qty { color: #db2777; margin-left: 5px; }</style>""", unsafe_allow_html=True)

                    for person, group in display_df.groupby("人員"):
                        with st.expander(f"👩‍🔧 {person} ({len(group)} 項)", expanded=True):
                            for _, row in group.iterrows():
                                db_id = row['db_id']
                                is_a = "asset-card" if row['類型'] == "資產工具" else ""
                                st.markdown(f'<div class="card {is_a}">', unsafe_allow_html=True)
                                col1, col2 = st.columns([7.5, 2.5])
                                with col1:
                                    st.markdown(f'<div class="t-title">🛠️ {row["手工具名稱"]} <span class="t-qty">x {row["數量"]}</span></div>', unsafe_allow_html=True)
                                    st.markdown(f'<div style="color:gray; font-size:0.8rem;">登記人: {row.get("登記人","-")} | {row["登記時間"]}</div>', unsafe_allow_html=True)
                                with col2:
                                    sc1, sc2 = st.columns(2)
                                    if sc1.button("✏️", key=f"e_{db_id}"): edit_record_dialog(db_id, row['手工具名稱'], row['數量'], person)
                                    if sc2.button("🗑️", key=f"d_{db_id}"): delete_record_dialog(db_id, row['手工具名稱'])
                                st.markdown('</div>', unsafe_allow_html=True)
                else: st.info("💡 目前無紀錄")
            else: st.info("🌸 系統無資料")

        with tab2:
            st.markdown("### 🏢 全廠資產清冊")
            if asset_tools_raw:
                asset_df = pd.DataFrame(list(asset_tools_raw.values()))
                # 恢復資產匯出功能
                csv_asset = asset_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📄 匯出全廠資產清單", data=csv_asset, file_name="全廠資產總表.csv", key="ast_csv_btn")
                st.dataframe(asset_df, use_container_width=True, hide_index=True)
            else:
                st.info("💡 目前無資產資料")
        
# --- ⚙️ 編輯手工具清單 (修正 Duplicate ID 版本) ---
    elif st.session_state.menu_selection == "⚙️ 資產編輯清單":
        # 1. 補回關鍵的粉紅色 CSS 樣式
        st.markdown("""
            <style>
            .pink-card {
                background-color: #fff1f2;
                border: 2px solid #fda4af;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            .stButton>button {
                border-radius: 10px;
                font-weight: 600;
            }
            h3 {
                color: #db2777 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<h1 style="text-align:center; color:#db2777; font-weight:900; font-size:2.5rem;">✨ 超慧資產管理中心</h1>', unsafe_allow_html=True)
        
        # 2. 讀取資料
        tool_settings = requests.get(f"{TOOL_LIST_URL}.json").json() or {"tool_types": []}
        tool_types = tool_settings.get("tool_types", [])
        asset_tools_raw = requests.get(f"{DB_URL}/asset_tools.json").json() or {}
        
        current_user = st.session_state.user
        my_team = staff_map.get(current_user, [])
        staff_options = sorted(list(set(my_team))) if my_team else sorted(list(all_staff))

        # --- 資產編輯 Dialog ---
        @st.dialog("✏️ 修改資產內容")
        def edit_asset_dialog(db_id, current_val):
            new_n = st.text_input("修改名稱", value=current_val.get('name', ''))
            new_no = st.text_input("修改編號", value=current_val.get('no', ''))
            new_adm = st.selectbox("修改管理人", staff_options, index=staff_options.index(current_val.get('管理人員')) if current_val.get('管理人員') in staff_options else 0)
            
            if st.button("💾 儲存修改", use_container_width=True, key="save_edit_asset"):
                updated_payload = {
                    "name": new_n,
                    "no": new_no,
                    "管理人員": new_adm,
                    "建立時間": current_val.get('建立時間', get_now_str())
                }
                requests.put(f"{DB_URL}/asset_tools/{db_id}.json", data=json.dumps(updated_payload))
                st.success("修改成功！"); time.sleep(0.5); st.rerun()

        col1, col2 = st.columns(2)
        
        # --- 左側：管理區 ---
        with col1:
            # A. 🛠️ 編輯一般工具
            st.markdown('<div class="pink-card">', unsafe_allow_html=True)
            st.subheader("🛠️ 編輯一般工具清單")
            current_tools_str = "，".join(tool_types)
            new_tools_input = st.text_area("工具清單 (逗號分隔)", value=current_tools_str, height=120)
            
            # 修正處：加上唯一的 key="btn_save_general_tools"
            if st.button("💾 儲存工具清單", use_container_width=True, key="btn_save_general_tools"):
                import re
                new_list = [t.strip() for t in re.split(r'[，,]', new_tools_input) if t.strip()]
                requests.put(f"{TOOL_LIST_URL}.json", data=json.dumps({"tool_types": new_list}))
                st.success("工具清單已更新"); time.sleep(0.5); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # B. 📋 編輯資產手工具
            st.markdown('<div class="pink-card">', unsafe_allow_html=True)
            st.subheader("📋 編輯資產手工具")
            c_a1, c_a2 = st.columns(2)
            a_name = c_a1.text_input("資產名稱", key="input_a_name")
            a_no = c_a2.text_input("資產編號", key="input_a_no")
            a_admin = st.selectbox("指定管理人", staff_options, key="select_a_admin")
            
            if st.button("➕ 新增資產", use_container_width=True, key="btn_add_asset"):
                if a_name and a_no:
                    payload = {"name": a_name, "no": a_no, "管理人員": a_admin, "建立時間": get_now_str()}
                    requests.post(f"{DB_URL}/asset_tools.json", data=json.dumps(payload))
                    st.success("資產已建立"); time.sleep(0.5); st.rerun()
                else: st.warning("請填寫完整資訊")
            
            if asset_tools_raw:
                st.write("---")
                for k, v in asset_tools_raw.items():
                    c_t1, c_t2, c_t3 = st.columns([4, 1, 1])
                    c_t1.markdown(f"📍 **{v['no']}** - {v['name']}")
                    if c_t2.button("✏️", key=f"edit_ast_{k}"):
                        edit_asset_dialog(k, v)
                    if c_t3.button("🗑️", key=f"del_ast_{k}"):
                        requests.delete(f"{DB_URL}/asset_tools/{k}.json")
                        st.success("已刪除"); time.sleep(0.5); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 右側：新增領用紀錄 ---
        with col2:
            st.markdown('<div class="pink-card">', unsafe_allow_html=True)
            st.subheader("📝 新增領用紀錄")
            
            final_tool_options = tool_types 
            
            with st.form("user_tool_form"):
                t_staff = st.selectbox("選擇成員", staff_options)
                t_name = st.selectbox("選擇工具", final_tool_options) 
                t_qty = st.number_input("數量", min_value=1, value=1)
                # Form 內的 Submit 按鈕
                if st.form_submit_button("🎉 確認新增紀錄", use_container_width=True):
                    tool_payload = {
                        "人員": t_staff,
                        "手工具名稱": t_name,
                        "數量": int(t_qty),
                        "登記時間": get_now_str(),
                        "登記人": current_user
                    }
                    requests.post(f"{USER_TOOLS_URL}.json", data=json.dumps(tool_payload))
                    st.success(f"已紀錄！"); time.sleep(0.5); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    # --- 📝 任務派發 ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派與編輯")
        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, all_staff)
        with st.form("dispatch_form"):
            t_o = st.selectbox("1. 選擇製令", order_list)
            t_p = st.selectbox("2. 選擇工序", process_list)
            t_l = st.selectbox("3. 負責組長", all_leaders, index=all_leaders.index(current_leader) if current_leader in all_leaders else 0)
            t_d = st.date_input("4. 預計通電日期")
            wk = [st.selectbox(f"人員 {i+1}", ["NA"] + sorted(list(set(my_team))), key=f"form_staff_{i}") for i in range(5)]
            if st.form_submit_button("🚀 確認發布任務", use_container_width=True):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "最後更新": get_now_str()}
                for i, w in enumerate(wk): payload[f"人員{i+1}"] = w
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success("任務指派成功！"); time.sleep(0.5); st.session_state.menu_selection = "📊 製造部派工專區"; st.rerun()

    # --- ⚙️ 設定管理 ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統核心設定")
        with st.form("config_form"):
            so = st.text_area("製令清單 (以逗號隔開)", ",".join(order_list))
            sl = st.text_area("組長清單 (以逗號隔開)", ",".join(all_leaders))
            ss = st.text_area("人員清單 (以逗號隔開)", ",".join(all_staff))
            sp = st.text_area("工序清單 (以逗號隔開)", ",".join(process_list))
            sm = st.text_area("組長對應工序 (組長:工序1,工序2)", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            staff_in = st.text_area("組長屬下人員 (組長:人員1,人員2)", "\n".join([f"{k}:{','.join(v)}" for k, v in staff_map.items()]))
            if st.form_submit_button("💾 儲存所有設定"):
                def split_s(s): return [x.strip() for x in s.split(",") if x.strip()]
                new_proc_map = {line.split(":")[0].strip(): split_s(line.split(":")[1]) for line in sm.split("\n") if ":" in line}
                new_staff_map = {line.split(":")[0].strip(): split_s(line.split(":")[1]) for line in staff_in.split("\n") if ":" in line}
                final_conf = {"order_list": split_s(so), "all_leaders": split_s(sl), "all_staff": split_s(ss), "processes": split_s(sp), "process_map": new_proc_map, "staff_map": new_staff_map}
                requests.put(f"{SETTING_URL}.json", data=json.dumps(final_conf))
                st.success("設定已存入資料庫"); time.sleep(0.8); st.rerun()
