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
        "staff_map": {} # 預設空的綁定名單
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
    .stApp { background-color: #f8fafc; }
    .order-card { 
        background: white; border-radius: 12px; border: 1px solid #e2e8f0; 
        margin-bottom: 20px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .order-header { 
        background: #1e3a8a; color: white; padding: 12px 20px; 
        font-weight: 900; display: flex; justify-content: space-between; align-items: center; 
    }
    .power-date-tag { 
        background: #facc15; color: #1e3a8a; padding: 4px 12px; 
        border-radius: 6px; font-size: 14px; font-weight: bold; 
    }
    .proc-row { 
        display: flex; align-items: center; 
        border-bottom: 1.5px solid #cbd5e1; 
        padding: 10px 15px;
    }
    .proc-row:last-child { border-bottom: none; }
    .proc-name { width: 160px; font-weight: 800; color: #1e3a8a; font-size: 15px; }
    .staff-area { flex-grow: 1; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .badge-staff { background: #1e40af; color: white; padding: 2px 10px; border-radius: 4px; font-size: 13px; }
    .status-done { color: #10b981; font-weight: bold; font-size: 14px; }
    .status-empty { color: #cbd5e1; font-style: italic; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定 (核心修正：確保變數順序) ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
process_map = settings.get("process_map", {})
staff_map = settings.get("staff_map", {}) # 修正：在這裡就先定義好，避免後面 NameError

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"

# --- 4. 登入介面 ---
if "user" not in st.session_state:
    st.markdown('<h1 style="text-align:center; color:#1e3a8a;">⚓ 超慧科技管理系統</h1>', unsafe_allow_html=True)
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇組長姓名登入", sorted(all_leaders))
            if st.button("確認進入", use_container_width=True, type="primary"):
                st.session_state.user = u
                st.rerun()
else:
    st.sidebar.markdown(f"### 👤 使用者：{st.session_state.user}")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度</h1>', unsafe_allow_html=True)

        @st.dialog("📝 編輯任務指派", width="large")
        def edit_task_dialog(order_id, proc_name, current_data):
            st.subheader(f"📦 製令：{order_id} | 🛠️ 工序：{proc_name}")
            
            # 從 staff_map 取得目前組長負責的人員名單
            current_leader = st.session_state.user
            my_bound_staff = staff_map.get(current_leader, all_staff)
            options = ["NA"] + sorted(list(set(my_bound_staff)))

            with st.form("dialog_edit_form"):
                col_left, col_right = st.columns([1, 2])
                with col_left:
                    st.markdown("### 📅 基本資訊")
                    st.text_input("負責組長", value=current_leader, disabled=True)
                    try:
                        d_str = current_data.get("通電日期", "未設定")
                        default_date = datetime.datetime.strptime(d_str, "%Y-%m-%d") if d_str != "未設定" else datetime.date.today()
                    except:
                        default_date = datetime.date.today()
                    d_date = st.date_input("預計通電日期", value=default_date)
                
                with col_right:
                    st.markdown(f"### 👥 {current_leader} 負責人員名單")
                    p_cols = st.columns(3); p_cols2 = st.columns(2)
                    all_p_cols = p_cols + p_cols2
                    new_wk = []
                    for i in range(5):
                        p_val = current_data.get(f"人員{i+1}", "NA")
                        sel = all_p_cols[i].selectbox(f"人員 {i+1}", options, index=options.index(p_val) if p_val in options else 0, key=f"dlg_sel_{i}")
                        new_wk.append(sel)
                
                if st.form_submit_button("💾 確認儲存修改", use_container_width=True):
                    new_payload = {
                        "製令": str(order_id), "製造工序": proc_name, "組長": current_leader, "通電日期": str(d_date), 
                        "最後更新": get_now_str(),
                        "人員1": new_wk[0], "人員2": new_wk[1], "人員3": new_wk[2], "人員4": new_wk[3], "人員5": new_wk[4]
                    }
                    db_id = current_data.get("db_id")
                    if db_id and db_id != "NA":
                        requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                    else:
                        requests.post(f"{DB_URL}.json", data=json.dumps(new_payload))
                    st.success("✅ 修改成功！")
                    time.sleep(0.5)
                    st.rerun()

        # 頁面顯示
        my_procs = process_map.get(st.session_state.user, process_list)
        c1, c2 = st.columns(2)
        s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))))
        s_staff = c2.selectbox("👤 篩選人員", ["全部"] + sorted(all_staff))

        try:
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            display_orders = sorted([o for o in set(order_list) if (s_order == "全部" or str(o) == str(s_order))])
            
            cols = st.columns(2)
            for idx, o_id in enumerate(display_orders):
                o_df = df_work[df_work["製令"] == str(o_id)]
                p_date = str(o_df.iloc[0].get("通電日期", "未設定")) if not o_df.empty else "未設定"
                with cols[idx % 2]:
                    st.markdown(f'<div class="order-card"><div class="order-header"><div>📦 製令：{o_id}</div><div class="power-date-tag">⚡ 通電：{p_date}</div></div>', unsafe_allow_html=True)
                    for p_idx, proc in enumerate(my_procs):
                        u_key = f"v8_{str(o_id).replace('-','_')}_{p_idx}"
                        m_w = o_df[o_df["製造工序"] == proc]
                        r_ui = st.columns([0.65, 0.1, 0.25])
                        with r_ui[0]:
                            html = ""
                            curr_data_dict = {} 
                            if not m_w.empty:
                                row = m_w.iloc[0]; curr_data_dict = row.to_dict()
                                for i in range(1, 6):
                                    p = row.get(f"人員{i}")
                                    if p and p != "NA": html += f'<div class="badge-staff">{p}</div>'
                            else: html = '<span class="status-empty">尚未派工</span>'
                            st.markdown(f'<div class="proc-row"><div class="proc-name">{proc}</div><div class="staff-area">{html}</div></div>', unsafe_allow_html=True)
                        with r_ui[1]:
                            if st.button("✏️", key=f"eb_{u_key}"):
                                if not curr_data_dict: curr_data_dict = {"製令": o_id, "製造工序": proc}
                                edit_task_dialog(o_id, proc, curr_data_dict)
                        with r_ui[2]:
                            if not m_w.empty and st.button("確認完工", key=f"db_{u_key}"):
                                dat = m_w.iloc[0].to_dict(); db_id = dat.pop('db_id')
                                dat["完工時間"] = get_now_str(); dat["完工人員"] = st.session_state.user
                                requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                requests.delete(f"{DB_URL}/{db_id}.json")
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"系統錯誤: {e}")
# --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.title("📜 歷史完工紀錄")
        try:
            # 直接從 Firebase 獲取資料
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                # 1. 建立 DataFrame 並清理欄位
                f_df = pd.DataFrame([dict(v, db_id=k) for k, v in r.items() if v]).fillna("NA")
                
                # 排序：按完工時間倒序 (最新的在上面)
                f_df = f_df.sort_values("完工時間", ascending=False)

                # --- 核心優化：即時搜尋框 ---
                # 只要內容改變，Streamlit 就會自動重新執行下方邏輯，達成「即時尋找」效果
                keyword = st.text_input("🔍 搜尋 (輸入製令、工序、人員即時過濾)", key="instant_search").strip()

                # 2. 進行篩選邏輯
                if keyword:
                    # 搜尋所有欄位字串，只要包含關鍵字就納入
                    mask = f_df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
                    display_df = f_df[mask]
                else:
                    display_df = f_df

                # 3. 依照「製令」分組顯示
                unique_orders = display_df["製令"].unique()

                if len(unique_orders) == 0:
                    st.warning(f"查無包含 '{keyword}' 的紀錄")
                else:
                    # 顯示搜尋結果統計
                    if keyword:
                        st.info(f"💡 關鍵字 '{keyword}': 找到 {len(display_df)} 筆工序，分布於 {len(unique_orders)} 個製令中")

                    for o_id in unique_orders:
                        order_records = display_df[display_df["製令"] == o_id]
                        
                        # 搜尋時自動展開 Expander (expanded=True)
                        with st.expander(f"📦 製令：{o_id} (已完工 {len(order_records)} 項工序)", expanded=bool(keyword)):
                            # 自定義表頭
                            h_cols = st.columns([1.5, 1.2, 1, 1, 1, 1, 1, 1.2, 1.8, 0.8])
                            header_names = ["工序", "通電日", "人1", "人2", "人3", "人4", "人5", "完工人員", "完工時間", "管理"]
                            for i, name in enumerate(header_names):
                                h_cols[i].markdown(f"**{name}**")
                            st.markdown("---")

                            # 顯示該製令下的明細
                            for _, row in order_records.iterrows():
                                r_cols = st.columns([1.5, 1.2, 1, 1, 1, 1, 1, 1.2, 1.8, 0.8])
                                
                                r_cols[0].write(row.get("製造工序", "NA"))
                                r_cols[1].write(row.get("通電日期", "NA"))
                                r_cols[2].write(row.get("人員1", ""))
                                r_cols[3].write(row.get("人員2", ""))
                                r_cols[4].write(row.get("人員3", ""))
                                r_cols[5].write(row.get("人員4", ""))
                                r_cols[6].write(row.get("人員5", ""))
                                r_cols[7].write(row.get("完工人員", "NA"))
                                r_cols[8].write(row.get("完工時間", "NA"))
                                
                                # 獨立刪除按鈕
                                if r_cols[9].button("🗑️", key=f"del_fin_{row['db_id']}"):
                                    if requests.delete(f"{FINISH_URL}/{row['db_id']}.json").status_code == 200:
                                        st.toast(f"已刪除 {o_id} 的一項紀錄")
                                        time.sleep(0.5)
                                        st.rerun()
            else:
                st.info("目前無完工紀錄")
        except Exception as e:
            st.error(f"連線資料庫錯誤: {e}")

    # --- 📝 任務派發 ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派與編輯")
        
        target_o = order_list[0] if order_list else ""
        target_p = process_list[0] if process_list else ""
        
        if st.session_state.edit_target:
            target_o = st.session_state.edit_target["order"]
            target_p = st.session_state.edit_target["proc"]
            st.info(f"📍 正在編輯：{target_o} - {target_p}")

        with st.form("dispatch_form"):
            v1, v2 = st.columns(2)
            t_o = v1.selectbox("1. 選擇製令", order_list, index=order_list.index(target_o) if target_o in order_list else 0)
            t_p = v2.selectbox("2. 選擇工序", process_list, index=process_list.index(target_p) if target_p in process_list else 0)
            
            v3, v4 = st.columns(2)
            t_l = v3.selectbox("3. 負責組長", all_leaders, index=all_leaders.index(st.session_state.user) if st.session_state.user in all_leaders else 0)
            t_d = v4.date_input("4. 預計通電日期")
            
            wk = []
            cols = st.columns(5)
            for i in range(5):
                wk.append(cols[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"form_staff_{i}"))
            
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
                
                st.session_state.edit_target = None
                st.success("任務指派成功！")
                time.sleep(0.5)
                st.session_state.menu_selection = "📊 製造部派工專區"
                st.rerun()
    # --- ⚙️ 設定管理 ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統設定")
        with st.form("config_form"):
            so = st.text_area("製令清單 (逗號隔開)", ",".join(order_list))
            sl = st.text_area("組長清單 (逗號隔開)", ",".join(all_leaders))
            ss = st.text_area("人員清單 (逗號隔開)", ",".join(all_staff))
            sp = st.text_area("工序清單 (逗號隔開)", ",".join(process_list))
            sm = st.text_area("組長:工序綁定 (格式 組長:工序1,工序2 每行一筆)", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            
            # --- 核心補回：人員綁定欄位 ---
            staff_in = st.text_area("組長:人員綁定 (格式 組長:人員1,人員2 每行一筆)", "\n".join([f"{k}:{','.join(v)}" for k, v in staff_map.items()]))
            
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
                st.success("設定已更新")
                time.sleep(0.8)
                st.rerun()
