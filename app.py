import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math

# --- 1. 核心資料與設定 (功能保持不變) ---
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
        "all_staff": ["徐梓翔", "陳德文", "人員C"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01", "12345"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 (針對格線對齊與連結感優化) ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* 製令卡片主體 */
    .order-card { 
        background: white; 
        border-radius: 8px; 
        border: 2px solid #1e40af; 
        margin-bottom: 25px; 
        overflow: hidden; 
    }
    
    /* 標題列 */
    .order-title { 
        background: #1e40af; 
        color: white; 
        padding: 10px 15px; 
        font-weight: 900; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        border-bottom: 2px solid #1e40af;
    }
    .power-date { 
        background: #fbbf24; 
        color: #1e40af; 
        padding: 2px 10px; 
        border-radius: 4px; 
        font-size: 13px; 
        font-weight: bold;
    }
    
    /* 表格列與格線設計：確保格子大小一樣且連結在一起 */
    .table-row { 
        display: flex; 
        border-bottom: 1px solid #dee2e6; /* 底部邊框連結下一行 */
        height: 50px; /* 固定高度確保格子大小一致 */
        align-items: stretch; 
    }
    .table-row:last-child { border-bottom: none; } /* 最後一行不需底線 */

    .cell-proc { 
        width: 120px; 
        background: #f1f5f9; 
        color: #1e40af; 
        font-weight: 800; 
        padding: 0 10px;
        display: flex;
        align-items: center;
        border-right: 1px solid #dee2e6; /* 垂直分隔線 */
        font-size: 14px;
    }
    .cell-staff { 
        flex-grow: 1; 
        padding: 5px 10px; 
        display: flex; 
        align-items: center; 
        flex-wrap: wrap; 
        gap: 6px; 
        background: white;
    }
    
    /* 人員標籤 */
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; border: 1px solid #cbd5e1; }
    
    .no-dispatch { color: #cbd5e1; font-size: 12px; }
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    
    /* 修正按鈕在格子內的間距 */
    .stButton>button {
        margin-top: 5px !important;
        padding: 0px 10px !important;
        height: 35px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 (功能保持不變) ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄 - 登入")
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

    # --- 📊 製造部公佈欄 (顯示修正：格子大小一致與格線連結) ---
    if menu == "📊 製造部公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技製造部派工進度</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(list(set(all_leaders + all_staff))))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=10)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs).fillna("NA")
                
                unique_orders = df["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or str(o) == str(s_order))]
                
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered_orders):
                    o_df = df[df["製令"] == o_id]
                    if s_staff != "全部":
                        check_cols = ["組長", "人員1", "人員2", "人員3", "人員4", "人員5"]
                        if not o_df[[c for c in check_cols if c in o_df.columns]].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    with cols[idx % 3]:
                        # 製令標題
                        st.markdown(f'<div class="order-card"><div class="order-title"><span>📦 製令：{o_id}</span><span class="power-date">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)
                        
                        # 內容格子（緊密相連）
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            row_cols = st.columns([0.85, 0.15]) # 左右格子對齊
                            
                            if not match.empty:
                                row = match.iloc[0]
                                staff_html = f'<div class="badge-leader">L: {row.get("組長","")}</div>'
                                if row.get("人員1") not in ["NA", ""]: staff_html += f'<div class="badge-main">{row.get("人員1")}</div>'
                                for i in range(2, 6):
                                    p_val = row.get(f"人員{i}")
                                    if p_val not in ["NA", ""]: staff_html += f'<div class="badge-sub">{p_val}</div>'
                                
                                with row_cols[0]: 
                                    st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                                with row_cols[1]:
                                    # ✅ 按鈕放在獨立列，但視覺上緊貼右側格子
                                    if st.button("✅", key=f"fin_{row['id']}"):
                                        clean_data = {k: (v if not (isinstance(v, float) and math.isnan(v)) else "NA") for k, v in row.to_dict().items()}
                                        clean_data["完工時間"] = get_now_str()
                                        clean_data["完工人員"] = st.session_state.user
                                        if requests.post(f"{FINISH_URL}.json", data=json.dumps(clean_data)).status_code == 200:
                                            requests.delete(f"{DB_URL}/{row['id']}.json")
                                            st.balloons()
                                            st.rerun()
                            else:
                                with row_cols[0]: 
                                    st.markdown(f'<div class="table-row"><div class="cell-proc" style="color:#cbd5e1;">{proc}</div><div class="cell-staff no-dispatch">未派工</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            else: st.info("💡 目前無派工紀錄")
        except: st.error("❌ 連線異常，請檢查網路或資料庫設定")

    # --- 其餘功能模組 (保持原樣) ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data:
                f_df = pd.DataFrame([dict(v, id=k) for k, v in f_data.items()]).fillna("NA")
                st.markdown('<div class="search-panel">', unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                f_order_input = sc1.text_input("🔍 手動輸入製令搜尋", placeholder="輸入製令關鍵字...")
                f_staff = sc2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                st.markdown('</div>', unsafe_allow_html=True)
                
                if f_order_input: 
                    f_df = f_df[f_df["製令"].astype(str).str.contains(f_order_input, case=False)]
                if f_staff != "全部": 
                    f_df = f_df[f_df[["人員1", "人員2", "人員3", "人員4", "人員5"]].apply(lambda x: f_staff in x.values, axis=1)]

                st.dataframe(f_df.sort_values("完工時間", ascending=False), use_container_width=True)
            else: st.info("目前無紀錄")
        except: st.error("讀取失敗")

    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 / 內容修正</h2>', unsafe_allow_html=True)
        with st.form("dispatch_form"):
            c1, c2, c3, c4 = st.columns(4)
            t_o = c1.selectbox("1. 製令編號", order_list)
            t_p = c2.selectbox("2. 製造工序", process_list)
            t_l = c3.selectbox("3. 指派組長", all_leaders)
            t_d = c4.date_input("4. 通電日期")
            st.write("---")
            pc = st.columns(5)
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"w{i}") for i in range(5)]
            if st.form_submit_button("🚀 準備發布"):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "提交時間": get_now_str()}
                for i in range(5): payload[f"人員{i+1}"] = workers[i]
                try:
                    exist_r = requests.get(f"{DB_URL}.json").json()
                    target_key = next((k for k, v in exist_r.items() if v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None) if exist_r else None
                    if target_key: requests.put(f"{DB_URL}/{target_key}.json", data=json.dumps(payload))
                    else: requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                    st.balloons()
                    st.success(f"✅ 製令 {t_o} 發布完成！")
                except: st.error("發布失敗，請檢查連線")

    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        with st.form("admin_settings"):
            e_o = st.text_area("製令編號 (逗號分隔)", value=",".join(order_list))
            e_l = st.text_area("組長名單 (逗號分隔)", value=",".join(all_leaders))
            e_s = st.text_area("一般人員 (逗號分隔)", value=",".join(all_staff))
            e_p = st.text_area("工序流程 (逗號分隔)", value=",".join(process_list))
            if st.form_submit_button("💾 儲存更新"):
                new_cfg = {
                    "order_list": [x.strip() for x in e_o.split(",") if x.strip()],
                    "all_leaders": [x.strip() for x in e_l.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in e_s.split(",") if x.strip()],
                    "processes": [x.strip() for x in e_p.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                st.balloons()
                st.success("設定已更新")
                st.rerun()
