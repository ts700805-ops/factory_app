import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 資料庫路徑設定 (維持原樣) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "12345"],
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

# --- 2. 介面樣式設定 (深度優化版本) ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    
    /* 製令卡片 */
    .order-card { 
        background: white; 
        border-radius: 16px; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 25px; 
        overflow: hidden; 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    /* 卡片標題區 */
    .order-header { 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
        color: white; 
        padding: 15px 20px; 
        font-weight: 900; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-size: 1.2rem;
    }
    
    /* 通電日期標籤 */
    .power-date-tag { 
        background: #fbbf24; 
        color: #1e3a8a; 
        padding: 5px 15px; 
        border-radius: 50px; 
        font-size: 14px; 
        font-weight: 800;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 工序行 */
    .proc-row-container {
        padding: 10px 20px;
        border-bottom: 1px solid #f1f5f9;
        transition: background 0.3s;
    }
    .proc-row-container:hover { background-color: #f8fafc; }
    
    .proc-name { 
        font-weight: 800; 
        color: #334155; 
        font-size: 16px;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
    }
    
    /* 人員標籤 */
    .staff-area { display: flex; flex-wrap: wrap; gap: 6px; }
    .badge-staff { 
        background: #dbeafe; 
        color: #1e40af; 
        padding: 4px 12px; 
        border-radius: 6px; 
        font-size: 13px; 
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    
    /* 狀態顯示 */
    .status-done { 
        color: #059669; 
        font-weight: 800; 
        font-size: 15px; 
        background: #ecfdf5;
        padding: 4px 12px;
        border-radius: 8px;
        display: inline-block;
    }
    .status-empty { color: #94a3b8; font-style: italic; font-size: 14px; }
    
    /* 按鈕容器微調 */
    .stButton>button { border-radius: 8px; }
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
if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

# --- 4. 登入介面 ---
if "user" not in st.session_state:
    st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-size:3rem;">⚓ 超慧科技</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#64748b;">生產管理系統 v2.0</p>', unsafe_allow_html=True)
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇您的組長姓名", sorted(all_leaders))
            if st.button("確認登入系統", use_container_width=True, type="primary"):
                st.session_state.user = u
                st.rerun()
else:
    st.sidebar.markdown(f"### 👤 當前人員：{st.session_state.user}")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900; margin-bottom:30px;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

        # --- 對話框 1：編輯人員 (邏輯不變) ---
        @st.dialog("👥 編輯施工人員", width="medium")
        def edit_staff_dialog(order_id, proc_name, current_data):
            st.subheader(f"🛠️ {proc_name}")
            current_leader = st.session_state.user
            my_team = staff_map.get(current_leader, [])
            display_options = my_team if my_team else all_staff
            options = ["NA"] + sorted(list(set(display_options)))

            with st.form("staff_edit_form"):
                st.write(f"📦 製令：{order_id}")
                st.write(f"👤 負責組長：**{current_leader}**")
                
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
                    if db_id and db_id != "NA":
                        requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                        st.success("✅ 人員更新成功！")
                        time.sleep(0.5); st.rerun()

        # --- 對話框 2：修改通電日期 (邏輯不變) ---
        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
            st.subheader(f"📦 製令：{order_id}")
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

        # --- 頁面篩選 ---
        my_procs = process_map.get(st.session_state.user, process_list)
        f_cols = st.columns([1, 1, 1])
        with f_cols[0]: s_order = st.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))))
        with f_cols[1]: s_staff = st.selectbox("👤 篩選人員", ["全部"] + sorted(all_staff))
        
        try:
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            r_finish = requests.get(f"{FINISH_URL}.json").json() or {}
            df_finish = pd.DataFrame([v for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            display_orders = sorted([o for o in set(order_list) if (s_order == "全部" or str(o) == str(s_order))])
            
            main_cols = st.columns(2)
            for idx, o_id in enumerate(display_orders):
                o_df = df_work[df_work["製令"] == str(o_id)]
                f_df_order = df_finish[df_finish["製令"] == str(o_id)]
                
                # 抓取日期
                p_date = "未設定"
                if not o_df.empty: p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                elif not f_df_order.empty: p_date = str(f_df_order.iloc[0].get("通電日期", "未設定"))

                with main_cols[idx % 2]:
                    # 卡片頭部
                    st.markdown(f'''
                        <div class="order-card">
                            <div class="order-header">
                                <span>📦 製令：{o_id}</span>
                                <span class="power-date-tag">⚡ 預計通電：{p_date}</span>
                            </div>
                    ''', unsafe_allow_html=True)
                    
                    # 修改日期按鈕 (放在頭部下方一點)
                    date_edit_col = st.columns([0.88, 0.12])
                    with date_edit_col[1]:
                        if st.button("📅", key=f"date_edit_{o_id}", help="修改通電日期"):
                            related = {k: v for k, v in r_work.items() if v.get("製令") == str(o_id)}
                            edit_power_date_dialog(o_id, p_date, related)

                    # 工序列表
                    for p_idx, proc in enumerate(my_procs):
                        u_key = f"v15_{str(o_id).replace('-','_')}_{p_idx}"
                        m_w = o_df[o_df["製造工序"] == proc]
                        m_f = f_df_order[f_df_order["製造工序"] == proc]
                        
                        is_assigned = False
                        is_done = not m_f.empty
                        target_row = m_w.iloc[0] if not m_w.empty else (m_f.iloc[0] if not m_f.empty else None)
                        
                        # 行佈局容器
                        st.markdown('<div class="proc-row-container">', unsafe_allow_html=True)
                        r_ui = st.columns([0.4, 0.4, 0.2])
                        
                        with r_ui[0]:
                            st.markdown(f'<div class="proc-name">{proc}</div>', unsafe_allow_html=True)
                        
                        with r_ui[1]:
                            html = ""
                            curr_data_dict = {}
                            if target_row is not None:
                                curr_data_dict = target_row.to_dict()
                                for i in range(1, 6):
                                    p = target_row.get(f"人員{i}")
                                    if p and p != "NA": 
                                        html += f'<div class="badge-staff">{p}</div>'
                                        is_assigned = True
                            if not html: 
                                st.markdown('<span class="status-empty">尚未派工</span>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="staff-area">{html}</div>', unsafe_allow_html=True)
                        
                        with r_ui[2]:
                            # 按鈕與狀態區
                            if is_done:
                                st.markdown('<div class="status-done">✅ 已完工</div>', unsafe_allow_html=True)
                            else:
                                btn_row = st.columns([1, 2])
                                with btn_row[0]:
                                    if st.button("✏️", key=f"eb_staff_{u_key}"):
                                        if m_w.empty:
                                            init_data = {"製令": str(o_id), "製造工序": proc, "組長": st.session_state.user, "通電日期": p_date, "人員1": "NA", "人員2": "NA", "人員3": "NA", "人員4": "NA", "人員5": "NA"}
                                            res = requests.post(f"{DB_URL}.json", data=json.dumps(init_data))
                                            init_data["db_id"] = res.json().get("name")
                                            edit_staff_dialog(o_id, proc, init_data)
                                        else:
                                            edit_staff_dialog(o_id, proc, curr_data_dict)
                                with btn_row[1]:
                                    if not is_assigned:
                                        st.write("⚠️ 請指派")
                                    else:
                                        if st.button("完工", key=f"db_{u_key}", type="primary"):
                                            dat = m_w.iloc[0].to_dict(); db_id = dat.pop('db_id')
                                            dat["完工時間"] = get_now_str(); dat["完工人員"] = st.session_state.user
                                            requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                            requests.delete(f"{DB_URL}/{db_id}.json")
                                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True) # 關閉容器
                    st.markdown('</div>', unsafe_allow_html=True) # 關閉卡片
        except Exception as e:
            st.error(f"讀取錯誤: {e}")

    # --- 其他頁面 (維持原樣) ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.title("📜 歷史完工紀錄")
        try:
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                f_df = pd.DataFrame([dict(v, db_id=k) for k, v in r.items() if v]).fillna("NA")
                f_df = f_df.sort_values("完工時間", ascending=False)
                keyword = st.text_input("🔍 搜尋 (輸入製令、工序、人員即時過濾)", key="instant_search").strip()

                if keyword:
                    mask = f_df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
                    display_df = f_df[mask]
                else:
                    display_df = f_df

                unique_orders = display_df["製令"].unique()
                if len(unique_orders) == 0:
                    st.warning(f"查無包含 '{keyword}' 的紀錄")
                else:
                    for o_id in unique_orders:
                        order_records = display_df[display_df["製令"] == o_id]
                        with st.expander(f"📦 製令：{o_id} (已完工 {len(order_records)} 項工序)", expanded=bool(keyword)):
                            st.dataframe(order_records.drop(columns=['db_id']), use_container_width=True)
                            # 提供單筆刪除功能 (維持原樣)
                            for _, row in order_records.iterrows():
                                if st.button(f"🗑️ 刪除 {row['製造工序']}", key=f"del_{row['db_id']}"):
                                    requests.delete(f"{FINISH_URL}/{row['db_id']}.json")
                                    st.rerun()
            else:
                st.info("目前無完工紀錄")
        except Exception as e:
            st.error(f"連線失敗: {e}")

    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派與編輯")
        current_leader = st.session_state.user
        my_bound_staff = staff_map.get(current_leader, all_staff)
        staff_options = ["NA"] + sorted(list(set(my_bound_staff)))
        
        with st.form("dispatch_form"):
            v1, v2 = st.columns(2)
            t_o = v1.selectbox("1. 選擇製令", order_list)
            t_p = v2.selectbox("2. 選擇工序", process_list)
            v3, v4 = st.columns(2)
            t_l = v3.selectbox("3. 負責組長", all_leaders, index=all_leaders.index(current_leader) if current_leader in all_leaders else 0)
            t_d = v4.date_input("4. 預計通電日期")
            wk = []
            cols = st.columns(5)
            for i in range(5):
                wk.append(cols[i].selectbox(f"人員 {i+1}", staff_options, key=f"form_staff_{i}"))
            
            if st.form_submit_button("🚀 確認發布任務", use_container_width=True):
                payload = {
                    "製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), 
                    "最後更新": get_now_str(),
                    "人員1": wk[0], "人員2": wk[1], "人員3": wk[2], "人員4": wk[3], "人員5": wk[4]
                }
                r_c = requests.get(f"{DB_URL}.json").json() or {}
                ek = next((k for k, v in r_c.items() if v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None)
                if ek: requests.put(f"{DB_URL}/{ek}.json", data=json.dumps(payload))
                else: requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success("任務指派成功！")
                time.sleep(0.5); st.session_state.menu_selection = "📊 製造部派工專區"; st.rerun()

    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統設定")
        with st.form("config_form"):
            so = st.text_area("製令清單", ",".join(order_list))
            sl = st.text_area("組長清單", ",".join(all_leaders))
            ss = st.text_area("人員清單", ",".join(all_staff))
            sp = st.text_area("工序清單", ",".join(process_list))
            sm = st.text_area("組長:工序綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            staff_in = st.text_area("組長:人員綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in staff_map.items()]))
            
            if st.form_submit_button("💾 儲存設定"):
                def split_s(s): return [x.strip() for x in s.split(",") if x.strip()]
                new_proc_map = {}
                for line in sm.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1); new_proc_map[k.strip()] = split_s(v)
                new_staff_map = {}
                for line in staff_in.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1); new_staff_map[k.strip()] = split_s(v)
                final_conf = {
                    "order_list": split_s(so), "all_leaders": split_s(sl), "all_staff": split_s(ss),
                    "processes": split_s(sp), "process_map": new_proc_map, "staff_map": new_staff_map
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(final_conf))
                st.success("設定已更新"); time.sleep(0.8); st.rerun()
