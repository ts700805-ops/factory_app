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

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card { background: white; border-radius: 8px; border: 2px solid #1e40af; margin-bottom: 20px; overflow: hidden; }
    .order-title { background: #1e40af; color: white; padding: 10px; font-weight: 900; display: flex; justify-content: space-between; }
    .power-date { background: #fbbf24; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 13px; }
    .table-row { display: flex; border-bottom: 1px solid #dee2e6; min-height: 48px; align-items: center; }
    .cell-proc { width: 110px; background: #f1f5f9; color: #1e40af; font-weight: 800; padding: 8px; border-right: 1px solid #dee2e6; }
    .cell-staff { flex-grow: 1; padding: 5px 10px; display: flex; flex-wrap: wrap; gap: 6px; }
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; border: 1px solid #cbd5e1; }
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    
    /* 網狀格線樣式 */
    .grid-table { 
        border: 1px solid #cbd5e1; 
        border-radius: 5px; 
        overflow: hidden; 
        margin-top: 10px;
    }
    .grid-header { 
        background-color: #1e40af; 
        color: white; 
        font-weight: bold; 
        padding: 10px;
        border-bottom: 1px solid #cbd5e1;
    }
    .grid-cell { 
        border: 1px solid #cbd5e1; 
        padding: 8px; 
        min-height: 45px;
        display: flex;
        align-items: center;
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 ---
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

    # --- 📊 製造部公佈欄 ---
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
                        st.markdown(f'<div class="order-card"><div class="order-title"><span>📦 製令：{o_id}</span><span class="power-date">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            row_cols = st.columns([0.85, 0.15])
                            if not match.empty:
                                row = match.iloc[0]
                                staff_html = f'<div class="badge-leader">L: {row.get("組長","")}</div>'
                                if row.get("人員1") != "NA": staff_html += f'<div class="badge-main">{row.get("人員1")}</div>'
                                for i in range(2, 6):
                                    if row.get(f"人員{i}") not in ["NA", ""]: staff_html += f'<div class="badge-sub">{row.get(f"人員{i}")}</div>'
                                
                                with row_cols[0]: st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                                with row_cols[1]:
                                    if st.button("✅", key=f"fin_{row['id']}"):
                                        clean_data = {k: (v if not (isinstance(v, float) and math.isnan(v)) else "NA") for k, v in row.to_dict().items()}
                                        clean_data["完工時間"] = get_now_str()
                                        clean_data["完工人員"] = st.session_state.user
                                        if requests.post(f"{FINISH_URL}.json", data=json.dumps(clean_data)).status_code == 200:
                                            requests.delete(f"{DB_URL}/{row['id']}.json")
                                            st.balloons()
                                            st.rerun()
                            else:
                                with row_cols[0]: st.markdown(f'<div class="table-row"><div class="cell-proc" style="color:#cbd5e1;">{proc}</div><div class="cell-staff" style="color:#cbd5e1; font-size:11px;">未派工</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            else: st.info("💡 目前無派工紀錄")
        except: st.error("❌ 連線異常，請檢查網路或資料庫設定")

    # --- 📜 完工紀錄查詢 (修正重點區塊) ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data:
                f_df = pd.DataFrame([dict(v, id=k) for k, v in f_data.items()]).fillna("NA")
                
                # 搜尋控制區
                st.markdown('<div class="search-panel">', unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                # 1. 修正：製令改為手動輸入搜尋
                f_order_input = sc1.text_input("🔍 手動輸入製令搜尋", placeholder="輸入製令關鍵字...")
                f_staff = sc2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 篩選邏輯
                if f_order_input: 
                    f_df = f_df[f_df["製令"].astype(str).str.contains(f_order_input, case=False)]
                if f_staff != "全部": 
                    f_df = f_df[f_df[["人員1", "人員2", "人員3", "人員4", "人員5"]].apply(lambda x: f_staff in x.values, axis=1)]

                # 顯示表格標題 (帶網格感)
                grid_cols = [1.5, 1, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6]
                names = ["完工時間", "製令", "工序", "人員1", "人員2", "人員3", "人員4", "人員5", "刪除"]
                
                # 標題列
                t_cols = st.columns(grid_cols)
                for i, n in enumerate(names):
                    t_cols[i].markdown(f'<div style="background:#1e40af; color:white; padding:8px; font-weight:bold; text-align:center; border:1px solid #cbd5e1;">{n}</div>', unsafe_allow_html=True)

                # 資料列 (加上網狀邊框)
                for _, row in f_df.sort_values("完工時間", ascending=False).iterrows():
                    rc = st.columns(grid_cols)
                    fields = ["完工時間", "製令", "製造工序", "人員1", "人員2", "人員3", "人員4", "人員5"]
                    
                    for i, field in enumerate(fields):
                        val = row.get(field, "NA")
                        rc[i].markdown(f'<div style="border:1px solid #cbd5e1; padding:8px; height:100%; text-align:center; background:white;">{val}</div>', unsafe_allow_html=True)
                    
                    # 刪除按鈕欄位也加上邊框
                    with rc[8]:
                        st.markdown('<div style="border:1px solid #cbd5e1; padding:3px; text-align:center; background:white;">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{row['id']}"):
                            st.session_state.delete_id = row['id']
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                if "delete_id" in st.session_state:
                    st.divider()
                    st.warning("⚠️ 確定刪除此紀錄？")
                    pwd = st.text_input("🔑 請輸入刪除密碼 (1111)", type="password")
                    c1, c2 = st.columns(2)
                    if c1.button("確認執行刪除"):
                        if pwd == "1111":
                            requests.delete(f"{FINISH_URL}/{st.session_state.delete_id}.json")
                            del st.session_state.delete_id
                            st.success("刪除成功")
                            st.rerun()
                        else: st.error("密碼錯誤！")
                    if c2.button("取消"):
                        del st.session_state.delete_id
                        st.rerun()
            else: st.info("目前無紀錄")
        except: st.error("讀取失敗")

    # --- 📝 任務派發 ---
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

    # --- ⚙️ 設定管理 ---
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
