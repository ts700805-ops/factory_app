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
    """獲取台灣時間字串"""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    """從 Firebase 讀取系統設定"""
    default_settings = {
        "all_leaders": ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "12345"],
        "leader_map": {},
        "process_map": {
            "陳德文": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢"],
            "吳政昌": ["S.T作業"],
            "劉志偉": ["收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"]
        }
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return data
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
    .badge-main { background: #f59e0b; color: white; padding: 2px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; }
    .badge-sub { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-other { background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #cbd5e1; }
    .status-done { color: #10b981; font-weight: bold; font-size: 14px; }
    .status-empty { color: #cbd5e1; font-style: italic; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定與狀態初始化 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
leader_map = settings.get("leader_map", {})
process_map = settings.get("process_map", {})

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

# --- 4. 登入邏輯 ---
if "user" not in st.session_state:
    st.markdown('<h1 style="text-align:center; color:#1e3a8a;">⚓ 超慧科技管理系統</h1>', unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("👤 請選擇組長登入")
        # 綁定只顯示組長清單
        u = st.selectbox("組長姓名", sorted(all_leaders))
        if st.button("確認進入系統", use_container_width=True, type="primary"):
            st.session_state.user = u
            st.rerun()
else:
    # --- 側邊欄導覽 ---
    st.sidebar.markdown(f"### 👤 目前使用者：{st.session_state.user}")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度專區</h1>', unsafe_allow_html=True)
        
        # 獲取目前組長綁定的工序
        current_user = st.session_state.user
        my_procs = process_map.get(current_user, process_list)

        c1, c2 = st.columns(2)
        s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
        s_staff = c2.selectbox("👤 篩選人員", ["全部"] + sorted(all_staff))

        try:
            # 讀取資料
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            r_finish = requests.get(f"{FINISH_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            df_finish = pd.DataFrame([dict(v, id=k) for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            display_orders = [o for o in order_list if (s_order == "全部" or str(o) == str(s_order))]
            
            cols = st.columns(2)
            for idx, o_id in enumerate(display_orders):
                o_df = df_work[df_work["製令"] == str(o_id)]
                
                # 過濾製令中的日期標記
                p_date = "未設定"
                if not o_df.empty: p_date = str(o_df.iloc[0].get("通電日期", "未設定"))

                with cols[idx % 2]:
                    st.markdown(f'<div class="order-card"><div class="order-header"><div>📦 製令：{o_id}</div><div class="power-date-tag">⚡ 通電：{p_date}</div></div>', unsafe_allow_html=True)
                    
                    # 只顯示該組員負責的工序
                    for proc in my_procs:
                        m_w = o_df[o_df["製造工序"] == proc]
                        m_f = df_finish[(df_finish["製令"] == str(o_id)) & (df_finish["製造工序"] == proc)] if not df_finish.empty else pd.DataFrame()

                        r_ui = st.columns([0.65, 0.1, 0.25])
                        with r_ui[0]:
                            html = ""
                            if not m_w.empty:
                                row = m_w.iloc[0]
                                leader_name = row.get("組長", "NA")
                                if leader_name != "NA": html += f'<div class="badge-main">L: {leader_name}</div>'
                                for i in range(1, 6):
                                    p = row.get(f"人員{i}")
                                    if p and p != "NA": html += f'<div class="badge-sub">{p}</div>'
                            elif not m_f.empty:
                                html = '<span class="status-done">✅ 已完工</span>'
                            else:
                                html = '<span class="status-empty">尚未派工</span>'
                            st.markdown(f'<div class="proc-row"><div class="proc-name">{proc}</div><div class="staff-area">{html}</div></div>', unsafe_allow_html=True)
                        
                        with r_ui[1]:
                            # 編輯按鈕：點擊後儲存目標並跳轉
                            if st.button("✏️", key=f"btn_ed_{o_id}_{proc}"):
                                st.session_state.edit_target = {"order": str(o_id), "proc": proc}
                                st.session_state.menu_selection = "📝 任務派發"
                                st.rerun()
                                
                        with r_ui[2]:
                            if not m_w.empty:
                                if st.button("確認完工", key=f"btn_ok_{o_id}_{proc}"):
                                    dat = m_w.iloc[0].to_dict()
                                    dat["完工時間"] = get_now_str()
                                    dat["完工人員"] = st.session_state.user
                                    requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                    requests.delete(f"{DB_URL}/{dat['id']}.json")
                                    st.success(f"{proc} 已完工")
                                    time.sleep(0.5)
                                    st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"資料讀取錯誤: {e}")

    # --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.title("📜 歷史完工紀錄")
        try:
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                f_df = pd.DataFrame([dict(v, id=k) for k, v in r.items() if v]).fillna("NA")
                st.dataframe(f_df.sort_values("完工時間", ascending=False), use_container_width=True)
            else:
                st.info("目前無完工紀錄")
        except:
            st.error("讀取失敗")

    # --- 📝 任務派發 (編輯功能回歸) ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派與編輯")
        
        # 檢查是否有從首頁點選編輯跳轉過來
        target_o = order_list[0] if order_list else ""
        target_p = process_list[0] if process_list else ""
        
        if st.session_state.edit_target:
            target_o = st.session_state.edit_target["order"]
            target_p = st.session_state.edit_target["proc"]
            st.warning(f"📍 正在編輯：製令 {target_o} 的 {target_p}")

        with st.form("dispatch_form"):
            v1, v2 = st.columns(2)
            t_o = v1.selectbox("1. 選擇製令", order_list, index=order_list.index(target_o) if target_o in order_list else 0)
            t_p = v2.selectbox("2. 選擇工序", process_list, index=process_list.index(target_p) if target_p in process_list else 0)
            
            v3, v4 = st.columns(2)
            t_l = v3.selectbox("3. 負責組長", all_leaders, index=all_leaders.index(st.session_state.user) if st.session_state.user in all_leaders else 0)
            t_d = v4.date_input("4. 預計通電日期")
            
            st.write("👥 人員指派：")
            wk = []
            cols = st.columns(5)
            for i in range(5):
                wk.append(cols[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"staff_sel_{i}"))
            
            if st.form_submit_button("🚀 確認發布/更新任務", use_container_width=True):
                payload = {
                    "製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), 
                    "最後更新": get_now_str(),
                    "人員1": wk[0], "人員2": wk[1], "人員3": wk[2], "人員4": wk[3], "人員5": wk[4]
                }
                # 檢查是否已存在，存在則更新，否則新增
                r_c = requests.get(f"{DB_URL}.json").json() or {}
                ek = next((k for k, v in r_c.items() if v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None)
                
                if ek: requests.put(f"{DB_URL}/{ek}.json", data=json.dumps(payload))
                else: requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                
                st.session_state.edit_target = None # 清除編輯狀態
                st.success("任務指派成功！")
                time.sleep(0.8)
                st.session_state.menu_selection = "📊 製造部派工專區"
                st.rerun()

    # --- ⚙️ 設定管理 ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統後台設定")
        with st.form("config_form"):
            st.info("請以半形逗號 (,) 分隔多個項目")
            txt_o = st.text_area("製令清單", ",".join(order_list))
            txt_l = st.text_area("組長清單", ",".join(all_leaders))
            txt_s = st.text_area("所有人員清單", ",".join(all_staff))
            txt_p = st.text_area("工序清單", ",".join(process_list))
            
            st.write("🔗 組長與工序綁定 (格式：組長:工序1,工序2)")
            txt_pmap = st.text_area("綁定設定", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            
            if st.form_submit_button("💾 儲存設定"):
                def split_s(s): return [x.strip() for x in s.split(",") if x.strip()]
                new_map = {}
                for line in txt_pmap.split("\n"):
                    if ":" in line:
                        k, v = line.split(":")
                        new_map[k.strip()] = split_s(v)
                
                final_conf = {
                    "order_list": split_s(txt_o),
                    "all_leaders": split_s(txt_l),
                    "all_staff": split_s(txt_s),
                    "processes": split_s(txt_p),
                    "process_map": new_map
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(final_conf))
                st.success("設定已更新")
                st.rerun()
