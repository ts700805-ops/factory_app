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
        "🔧 人員手工具紀錄表",
        "⚙️ 編輯手工具清單",
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
            display_options = my_team if my_team else all_staff
            options = ["NA"] + sorted(list(set(display_options)))
            with st.form("staff_edit_form"):
                new_wk = []
                for i in range(5):
                    p_val = current_data.get(f"人員{i+1}", "NA")
                    d_idx = options.index(p_val) if p_val in options else 0
                    sel = st.selectbox(f"人員 {i+1}", options, index=d_idx, key=f"dlg_staff_{i}")
                    new_wk.append(sel)
                if st.form_submit_button("💾 儲存修改", use_container_width=True):
                    new_payload = current_data.copy()
                    new_payload.update({
                        "最後更新": get_now_str(),
                        "人員1": new_wk[0], "人員2": new_wk[1], "人員3": new_wk[2], "人員4": new_wk[3], "人員5": new_wk[4]
                    })
                    db_id = new_payload.pop("db_id", None)
                    requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                    st.success("✅ 人員更新成功！")
                    time.sleep(0.5); st.rerun()

        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
            try:
                default_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d") if current_date_str != "未設定" else datetime.date.today()
            except:
                default_date = datetime.date.today()
            new_date = st.date_input("請選擇新的通電日期", value=default_date)
            if st.button("💾 確認修改", use_container_width=True):
                for db_id, data in related_records.items():
                    data["通電日期"] = str(new_date); data["最後更新"] = get_now_str()
                    requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(data))
                st.success("✅ 日期已更新")
                time.sleep(0.5); st.rerun()

        # --- 頁面篩選列 ---
        my_procs = process_map.get(st.session_state.user, process_list)
        my_team_for_filter = staff_map.get(st.session_state.user, all_staff)
        
        f_cols = st.columns([1, 1, 1])
        with f_cols[0]: s_order = st.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))))
        with f_cols[1]: s_staff = st.selectbox("👤 篩選人員", ["全部"] + sorted(my_team_for_filter))
        
        try:
            r_work_raw = requests.get(f"{DB_URL}.json").json()
            r_work = r_work_raw if r_work_raw and isinstance(r_work_raw, dict) else {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            
            r_finish_raw = requests.get(f"{FINISH_URL}.json").json()
            r_finish = r_finish_raw if r_finish_raw and isinstance(r_finish_raw, dict) else {}
            df_finish = pd.DataFrame([v for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            base_orders = [str(o) for o in order_list]
            if s_order != "全部": base_orders = [str(s_order)]

            final_display_orders = []
            for o_id in base_orders:
                o_df = df_work[df_work["製令"] == str(o_id)] if not df_work.empty else pd.DataFrame()
                f_df_order = df_finish[df_finish["製令"] == str(o_id)] if not df_finish.empty else pd.DataFrame()
                if s_staff == "全部":
                    final_display_orders.append(o_id)
                else:
                    found = False
                    for df in [o_df, f_df_order]:
                        if not df.empty:
                            for i in range(1, 6):
                                if f"人員{i}" in df.columns and (df[f"人員{i}"] == s_staff).any():
                                    found = True; break
                    if found: final_display_orders.append(o_id)

            if not final_display_orders:
                st.info(f"💡 目前無符合條件的項目")
            else:
                main_cols = st.columns(3) 
                for idx, o_id in enumerate(final_display_orders):
                    o_df = df_work[df_work["製令"] == str(o_id)] if not df_work.empty else pd.DataFrame()
                    f_df_order = df_finish[df_finish["製令"] == str(o_id)] if not df_finish.empty else pd.DataFrame()
                    p_date = str(o_df.iloc[0].get("通電日期", "未設定")) if not o_df.empty else (str(f_df_order.iloc[0].get("通電日期", "未設定")) if not f_df_order.empty else "未設定")

                    with main_cols[idx % 3]:
                        st.markdown(f'<div class="order-card"><div class="order-header"><span>📦 製令：{o_id}</span><span class="power-date-tag">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)
                        if st.button("📅", key=f"date_edit_{o_id}"):
                            related = {k: v for k, v in r_work.items() if v.get("製令") == str(o_id)}
                            edit_power_date_dialog(o_id, p_date, related)

                        for p_idx, proc in enumerate(my_procs):
                            u_key = f"v21_{str(o_id).replace('-','_')}_{p_idx}"
                            m_w = o_df[o_df["製造工序"] == proc] if not o_df.empty else pd.DataFrame()
                            m_f = f_df_order[f_df_order["製造工序"] == proc] if not f_df_order.empty else pd.DataFrame()
                            is_done = not m_f.empty
                            target_row = m_w.iloc[0] if not m_w.empty else (m_f.iloc[0] if not m_f.empty else None)
                            
                            st.markdown('<div class="proc-row-container">', unsafe_allow_html=True)
                            r_ui = st.columns([3.2, 4.0, 0.8, 2.0])
                            with r_ui[0]: st.markdown(f'<div class="proc-name">{proc}</div>', unsafe_allow_html=True)
                            with r_ui[1]:
                                staff_html = "".join([f'<span class="badge-staff">{target_row.get(f"人員{i}")}</span> ' for i in range(1,6) if target_row is not None and target_row.get(f"人員{i}") != "NA"])
                                st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:4px;">{staff_html if staff_html else "尚未派工"}</div>', unsafe_allow_html=True)
                            with r_ui[2]:
                                if not is_done and st.button("✏️", key=f"eb_staff_{u_key}"):
                                    if m_w.empty:
                                        init_data = {"製令": str(o_id), "製造工序": proc, "組長": st.session_state.user, "通電日期": p_date, "人員1": "NA", "人員2": "NA", "人員3": "NA", "人員4": "NA", "人員5": "NA"}
                                        res = requests.post(f"{DB_URL}.json", data=json.dumps(init_data))
                                        init_data["db_id"] = res.json().get("name"); edit_staff_dialog(o_id, proc, init_data)
                                    else: edit_staff_dialog(o_id, proc, target_row.to_dict())
                            with r_ui[3]:
                                if is_done: st.markdown('<div class="status-done-box">✅ 已完工</div>', unsafe_allow_html=True)
                                elif target_row is not None and any(target_row.get(f"人員{i}") != "NA" for i in range(1,6)):
                                    if st.button("完工", key=f"db_{u_key}", type="primary", use_container_width=True):
                                        dat = m_w.iloc[0].to_dict(); db_id = dat.pop('db_id')
                                        dat["完工時間"] = get_now_str(); dat["完工人員"] = st.session_state.user
                                        requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                        requests.delete(f"{DB_URL}/{db_id}.json"); st.rerun()
                                else: st.markdown('<div class="status-assign-box">⚠️ 請指派</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except: st.warning("目前系統資料緩衝中。")

    # --- 📈 工時統計分析 ---
    elif st.session_state.menu_selection == "📈 工時統計分析":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">⏱️ 生產工時管理系統</h1>', unsafe_allow_html=True)
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
                    new_timer = {"製令": t_oid, "工序": t_proc, "status": "stop", "accumulated": 0, "start_time": 0}
                    requests.post(f"{TIMER_DB_URL}.json", data=json.dumps(new_timer))
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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
                        db_id, p_name, status, acc, start = task['db_id'], task.get("工序"), task.get("status"), task.get("accumulated", 0), task.get("start_time", 0)
                        st.components.v1.html(f"""
                            <div style="background:#f1f5f9; padding:10px; border-radius:8px; margin-bottom:10px; border-left:5px solid #3b82f6; display:flex; justify-content:space-between; align-items:center;">
                                <div style="font-weight:bold; color:#0f172a;">🛠️ {p_name}</div>
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
                        """, height=70)
                        b1, b2, b3 = st.columns([1, 1, 1])
                        with b1:
                            if status != 'running':
                                if st.button("▶️ 開始", key=f"s_{db_id}"):
                                    requests.patch(f"{TIMER_DB_URL}/{db_id}.json", data=json.dumps({"status": "running", "start_time": time.time()})); st.rerun()
                            else:
                                if st.button("⏸️ 暫停", key=f"p_{db_id}"):
                                    requests.patch(f"{TIMER_DB_URL}/{db_id}.json", data=json.dumps({"status": "paused", "accumulated": acc + (time.time() - start), "start_time": 0})); st.rerun()
                        with b2:
                            if st.button("⏹️ 結束", key=f"e_{db_id}"):
                                final_sec = acc + (time.time() - start if status == 'running' else 0)
                                requests.post(f"{FINISH_URL}.json", data=json.dumps({"製令": oid, "工序": p_name, "秒數": final_sec, "完工時間": get_now_str(), "人員1": st.session_state.user}))
                                requests.delete(f"{TIMER_DB_URL}/{db_id}.json"); st.rerun()
                        with b3:
                            if st.button("🗑️ 刪除", key=f"d_{db_id}"): requests.delete(f"{TIMER_DB_URL}/{db_id}.json"); st.rerun()
        else: st.info("💡 目前無進行中任務。")

    # --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📜 歷史完工紀錄</h1>', unsafe_allow_html=True)
        all_logs = requests.get(f"{FINISH_URL}.json").json()
        if all_logs:
            df = pd.DataFrame([dict(v, db_id=k) for k, v in all_logs.items()])
            search_q = st.text_input("🔍 搜尋 (輸入製令、工序或人員名稱)")
            if search_q: df = df[df.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
            if not df.empty:
                for o_id, group in df.groupby("製令"):
                    with st.expander(f"📦 製令：{o_id} (已完工 {len(group)} 項)"):
                        display_df = group.copy()
                        if '秒數' in display_df.columns: display_df['工時(分)'] = (display_df['秒數'] / 60).round(2)
                        st.table(display_df[["工序", "完工時間", "工時(分)"]] if "工序" in display_df.columns else display_df)
                        if st.button(f"🗑️ 刪除整個製令紀錄", key=f"del_group_{o_id}"):
                            for d_id in group['db_id']: requests.delete(f"{FINISH_URL}/{d_id}.json")
                            st.rerun()
            else: st.warning("查無紀錄。")
        else: st.info("💡 目前尚無紀錄。")

 # --- 🔧 人員手工具紀錄表 (粉色進階版：組員過濾 + 編輯功能) ---
    elif st.session_state.menu_selection == "🔧 人員手工具紀錄表":
        st.markdown('<h1 style="text-align:center; color:#db2777; font-weight:900; font-size:2.5rem;">🌸 人員手工具紀錄表</h1>', unsafe_allow_html=True)
        
        # 獲取當前組長的組員清單
        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, [])
        
        # 讀取資料
        user_tool_raw = requests.get(f"{USER_TOOLS_URL}.json").json()
        
        # 定義編輯視窗的邏輯
        @st.dialog("✏️ 修改領用紀錄")
        def edit_record(db_id, current_name, current_qty, person):
            st.markdown(f"正在編輯 **{person}** 的紀錄")
            new_name = st.text_input("工具名稱", value=current_name)
            new_qty = st.number_input("數量", min_value=1, value=int(current_qty))
            if st.button("💖 確認修改", use_container_width=True):
                update_data = {"手工具名稱": new_name, "數量": new_qty}
                requests.patch(f"{USER_TOOLS_URL}/{db_id}.json", data=json.dumps(update_data))
                st.success("修改成功！")
                time.sleep(0.5)
                st.rerun()

        if user_tool_raw:
            tool_data_list = []
            for k, v in user_tool_raw.items():
                item = v.copy()
                item['db_id'] = k
                tool_data_list.append(item)
            tool_df = pd.DataFrame(tool_data_list)

            # 樣式設定
            st.markdown("""
                <style>
                .stExpander { border: 2px solid #fbcfe8 !important; border-radius: 15px !important; background-color: #fff1f2 !important; }
                .tool-row { background-color: white; padding: 12px; border-radius: 10px; margin-bottom: 5px; border-left: 8px solid #f472b6; color: #831843; }
                .label-text { font-size: 1.2rem; font-weight: bold; color: #be185d; }
                </style>
            """, unsafe_allow_html=True)

            # 下拉選單：預設顯示「我的組員」，也可以切換看「全部」
            view_mode = st.radio("顯示範圍", ["僅顯示我的組員", "顯示全部人員"], horizontal=True)
            
            if view_mode == "僅顯示我的組員":
                tool_df = tool_df[tool_df["人員"].isin(my_team)]
                display_label = "我的組員"
            else:
                display_label = "全體人員"

            if not tool_df.empty:
                for person, group in tool_df.groupby("人員"):
                    with st.expander(f"👩‍🔧 {person} 的工具清單 (共 {len(group)} 項)", expanded=True):
                        # 表頭
                        h_cols = st.columns([3, 1, 3, 2])
                        h_cols[0].markdown("<p class='label-text'>工具名稱</p>", unsafe_allow_html=True)
                        h_cols[1].markdown("<p class='label-text'>數量</p>", unsafe_allow_html=True)
                        h_cols[2].markdown("<p class='label-text'>登記時間</p>", unsafe_allow_html=True)
                        h_cols[3].markdown("<p class='label-text'>操作</p>", unsafe_allow_html=True)
                        
                        for _, row in group.iterrows():
                            st.markdown(f'''
                                <div class="tool-row">
                                    <div style="display:flex; align-items:center;">
                                        <div style="flex:3; font-weight:600;">{row["手工具名稱"]}</div>
                                        <div style="flex:1;">{row["數量"]}</div>
                                        <div style="flex:3; font-size:0.9rem;">{row["登記時間"]}</div>
                                        <div style="flex:2;"></div>
                                    </div>
                                </div>
                            ''', unsafe_allow_html=True)
                            
                            # 按鈕列
                            btn_cols = st.columns([3, 1, 3, 1, 1])
                            if btn_cols[3].button("✏️", key=f"edit_{row['db_id']}"):
                                edit_record(row['db_id'], row['手工具名稱'], row['數量'], person)
                                
                            if btn_cols[4].button("🗑️", key=f"del_{row['db_id']}"):
                                requests.delete(f"{USER_TOOLS_URL}/{row['db_id']}.json")
                                st.toast(f"已刪除 {row['手工具名稱']}")
                                time.sleep(0.5)
                                st.rerun()
            else:
                st.info(f"💡 目前{display_label}中沒有任何領用紀錄。")
        else:
            st.info("🌸 系統目前沒有任何紀錄喔！")
   # --- ⚙️ 編輯手工具清單 (粉色系列) ---
    elif st.session_state.menu_selection == "⚙️ 編輯手工具清單":
        st.markdown('<h1 style="text-align:center; color:#db2777; font-weight:900; font-size:2.5rem;">✨ 手工具管理中心</h1>', unsafe_allow_html=True)
        
        tool_settings = requests.get(f"{TOOL_LIST_URL}.json").json() or {"tool_types": ["電鑽", "起子", "扳手"]}
        tool_types = tool_settings.get("tool_types", [])
        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, [])
        display_staff = sorted(list(set(my_team))) if my_team else sorted(all_staff)

        # 頁面背景修飾
        st.markdown("""
            <style>
            .pink-card { background-color: #ffffff; border: 3px solid #fce7f3; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(244, 114, 182, 0.2); }
            .stButton>button { background-color: #f472b6 !important; color: white !important; font-size: 1.2rem !important; border-radius: 10px !important; height: 3em !important; border: none !important; }
            .stButton>button:hover { background-color: #db2777 !important; border: none !important; }
            label { font-size: 1.4rem !important; color: #9d174d !important; font-weight: bold !important; }
            </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="pink-card">', unsafe_allow_html=True)
            st.subheader("🎀 編輯下拉選單內容")
            with st.form("edit_tool_types_form"):
                new_types_str = st.text_area("請輸入工具種類 (用逗號分開)", ",".join(tool_types), height=150)
                if st.form_submit_button("💗 儲存新清單", use_container_width=True):
                    updated_types = [x.strip() for x in new_types_str.split(",") if x.strip()]
                    requests.put(f"{TOOL_LIST_URL}.json", data=json.dumps({"tool_types": updated_types}))
                    st.success("清單更新成功！")
                    time.sleep(0.5); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="pink-card">', unsafe_allow_html=True)
            st.subheader("📝 新增領用紀錄")
            with st.form("user_tool_form"):
                t_staff = st.selectbox("選擇可愛的成員", display_staff)
                t_name = st.selectbox("選擇工具", tool_types)
                t_qty = st.number_input("數量", min_value=1, value=1)
                st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("🎉 確認新增紀錄", use_container_width=True):
                    tool_payload = {
                        "人員": t_staff,
                        "手工具名稱": t_name,
                        "數量": int(t_qty),
                        "登記時間": get_now_str(),
                        "登記人": current_leader
                    }
                    requests.post(f"{USER_TOOLS_URL}.json", data=json.dumps(tool_payload))
                    st.success(f"已幫 {t_staff} 紀錄好囉！")
                    time.sleep(0.5); st.rerun()
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
