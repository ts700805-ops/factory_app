import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心資料與設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    # 預設名單（當資料庫異常時保底用）
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                # 檢查必要鍵值是否存在，若無則補上預設值
                for key in default_settings:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 (表格格線版) ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card {
        background: #ffffff;
        border-radius: 8px;
        border: 2px solid #1e40af;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow: hidden;
    }
    .order-title {
        background-color: #1e40af;
        color: white;
        padding: 10px 15px;
        font-size: 18px;
        font-weight: 900;
        border-bottom: 2px solid #1e3a8a;
    }
    .table-row {
        display: flex;
        border-bottom: 1px solid #dee2e6;
        min-height: 40px;
        align-items: center;
    }
    .table-row:last-child { border-bottom: none; }
    .cell-proc {
        width: 120px;
        background-color: #f1f5f9;
        color: #1e40af;
        font-weight: 800;
        font-size: 13px;
        padding: 8px;
        border-right: 1px solid #dee2e6;
        flex-shrink: 0;
    }
    .cell-staff {
        flex-grow: 1;
        padding: 5px 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 14px; font-weight: 800; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 邏輯處理 ---
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄 - 登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("確認登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 超慧科技公佈欄", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 公佈欄看板 ---
    if menu == "📊 超慧科技公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員", ["全部"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, id=k) for k, v in data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                
                unique_orders = df["製令"].unique()
                filtered = [o for o in unique_orders if (s_order == "全部" or o == s_order)]
                
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered):
                    o_df = df[df["製令"] == o_id]
                    # 人員過濾邏輯
                    if s_staff != "全部":
                        check_cols = [f"人員{i}" for i in range(1, 6) if f"人員{i}" in o_df.columns]
                        if not o_df[check_cols].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    with cols[idx % 3]:
                        st.markdown(f'<div class="order-card"><div class="order-title">📦 製令：{o_id}</div>', unsafe_allow_html=True)
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                w1 = row.get("人員1", "-")
                                others = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                staff_html = f'<div class="badge-main">{w1}</div>' + "".join([f'<div class="badge-sub">{s}</div>' for s in others])
                            else:
                                staff_html = '<div style="color:#cbd5e1; font-size:12px;">未派工</div>'
                            
                            st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("目前尚無派工紀錄")

    # --- 📝 任務派發 (確保下拉選單存在) ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 新增派工任務</h2>', unsafe_allow_html=True)
        with st.form("dispatch_form"):
            c1, c2 = st.columns(2)
            o_sel = c1.selectbox("選擇製令", order_list)
            p_sel = c2.selectbox("選擇工序", process_list)
            st.write("---")
            st.write("人員分配 (第一位為主要負責人)")
            pc = st.columns(5)
            # 使用 list comprehension 確保 key 唯一且選單正確生成
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"ws_select_{i}") for i in range(5)]
            
            if st.form_submit_button("🚀 發布至公佈欄"):
                payload = {
                    "製令": o_sel, "製造工序": p_sel,
                    "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4],
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success(f"✅ {o_sel} - {p_sel} 派工成功")
                st.rerun()

    # --- ⚙️ 設定管理 (修正儲存後遺失選單的問題) ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料管理</h2>', unsafe_allow_html=True)
        with st.form("settings_form"):
            st.info("提示：多項資料請使用「半形逗號 , 」隔開")
            new_o = st.text_area("製令編號清單", value=",".join(order_list))
            new_s = st.text_area("派工人員名單", value=",".join(all_staff))
            new_p = st.text_area("工序流程清單", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並更新選單"):
                # 重新解析輸入內容
                updated_cfg = {
                    "order_list": [x.strip() for x in new_o.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in new_s.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_p.split(",") if x.strip()]
                }
                # 覆蓋儲存至資料庫
                requests.put(f"{SETTING_URL}.json", data=json.dumps(updated_cfg))
                st.success("✅ 設定已更新，下拉選單已同步找回！")
                st.rerun()
