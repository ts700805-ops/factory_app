import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math

# --- 1. 核心資料與設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01", "12345"],
        "leader_map": {},
        "process_map": {}
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for key in ["all_leaders", "all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                if "leader_map" not in data or not isinstance(data["leader_map"], dict): data["leader_map"] = {}
                if "process_map" not in data or not isinstance(data["process_map"], dict): data["process_map"] = {}
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card { background: white; border-radius: 8px; border: 2px solid #1e40af; margin-bottom: 25px; overflow: hidden; }
    .order-title { background: #1e40af; color: white; padding: 10px 15px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e40af; }
    .power-date { background: #fbbf24; color: #1e40af; padding: 2px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; }
    .table-row-container { border-bottom: 1px solid #dee2e6; display: flex; align-items: stretch; }
    .cell-proc { width: 100px; min-width: 100px; background: #f1f5f9; color: #1e40af; font-weight: 800; padding: 10px; display: flex; align-items: center; border-right: 1px solid #dee2e6; font-size: 14px; }
    .cell-staff { flex-grow: 1; padding: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; background: white; }
    .badge-leader { background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-main { background: #1e40af; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 5px; border-radius: 4px; font-size: 10px; border: 1px solid #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
leader_map = settings.get("leader_map", {})
process_map = settings.get("process_map", {})

if "user" not in st.session_state:
    st.title("⚓ 超慧科技管理系統 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", sorted(list(set(all_leaders + all_staff))))
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 製造部公佈欄", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部公佈欄 (省略邏輯保持不變) ---
    if menu == "📊 製造部公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技製造部派工進度</h1>', unsafe_allow_html=True)
        # ... (此部分邏輯與您提供的相同)
        try:
            r = requests.get(f"{DB_URL}.json", timeout=10)
            db_data = r.json()
            if db_data and isinstance(db_data, dict):
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs).fillna("NA")
                # ... (後續渲染邏輯)
                st.info("資料載入成功，請於介面查看。")
            else: st.info("💡 目前資料庫為空")
        except: st.warning("💡 無法連結資料庫。")

    # --- ⚙️ 設定管理 (重點修正區) ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        
        with st.expander("📌 基本名單設定", expanded=False):
            with st.form("admin_settings"):
                e_o = st.text_area("製令編號 (逗號隔開)", value=",".join(order_list))
                e_l = st.text_area("組長名單 (逗號隔開)", value=",".join(all_leaders))
                e_s = st.text_area("一般人員 (逗號隔開)", value=",".join(all_staff))
                e_p = st.text_area("工序流程 (逗號隔開)", value=",".join(process_list))
                if st.form_submit_button("💾 儲存基本名單"):
                    new_cfg = settings.copy()
                    new_cfg.update({
                        "order_list": [x.strip() for x in e_o.replace("，", ",").split(",") if x.strip()],
                        "all_leaders": [x.strip() for x in e_l.replace("，", ",").split(",") if x.strip()],
                        "all_staff": [x.strip() for x in e_s.replace("，", ",").split(",") if x.strip()],
                        "processes": [x.strip() for x in e_p.replace("，", ",").split(",") if x.strip()]
                    })
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("基本名單更新成功")
                    st.rerun()

        st.markdown("---")
        
        # 🛠️ 組長工序綁定修正
        st.markdown("### 🛠️ 組長與工序對應綁定")
        p_map_text_list = [f"{leader}:{','.join(procs)}" for leader, procs in process_map.items()]
        current_p_map_str = "\n".join(p_map_text_list)
        
        with st.form("process_binding_form"):
            st.info("💡 格式：組長姓名:工序1,工序2 (支援全形符號)")
            new_p_map_str = st.text_area("工序綁定清單區", value=current_p_map_str, height=150)
            submitted = st.form_submit_button("🔗 儲存工序綁定")
            
            if submitted:
                new_p_map = {}
                parse_error = False
                lines = [l.strip() for l in new_p_map_str.split("\n") if l.strip()]
                for line in lines:
                    line = line.replace("：", ":")
                    if ":" in line:
                        l_part, p_part = line.split(":", 1)
                        new_p_map[l_part.strip()] = [x.strip() for x in p_part.replace("，", ",").split(",") if x.strip()]
                    else:
                        parse_error = True
                
                if not parse_error:
                    new_cfg = settings.copy()
                    new_cfg["process_map"] = new_p_map
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("✅ 工序連動已更新！")
                    st.rerun()
                else:
                    st.error("❌ 格式錯誤：請確保每一行都有冒號 (組長姓名:工序)")

        st.markdown("---")
        
        # 👥 組長人員綁定修正
        st.markdown("### 👥 組長與人員對應綁定")
        map_text_list = [f"{leader}:{','.join(staff_list)}" for leader, staff_list in leader_map.items()]
        current_map_str = "\n".join(map_text_list)
        
        with st.form("leader_binding_quick_form"):
            new_map_str = st.text_area("組員綁定清單區", value=current_map_str, height=200)
            submitted_staff = st.form_submit_button("🔗 儲存人員綁定")
            
            if submitted_staff:
                new_map = {}
                parse_error = False
                lines = [l.strip() for l in new_map_str.split("\n") if l.strip()]
                for line in lines:
                    line = line.replace("：", ":")
                    if ":" in line:
                        leader_part, staff_part = line.split(":", 1)
                        new_map[leader_part.strip()] = [x.strip() for x in staff_part.replace("，", ",").split(",") if x.strip()]
                    else:
                        parse_error = True
                
                if not parse_error:
                    new_cfg = settings.copy()
                    new_cfg["leader_map"] = new_map
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("✅ 人員綁定已更新！")
                    st.rerun()
                else:
                    st.error("❌ 格式錯誤：請確保每一行都有冒號 (組長姓名:組員1,組員2)")
