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

# --- 2. 介面樣式設定 (全面升級為照片中的高質感深綠色漸層主題) ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    /* 全網頁背景改成深綠至黑綠色漸層 */
    .stApp { 
        background: linear-gradient(135deg, #04241a 0%, #01140f 100%) !important; 
        color: #e2e8f0 !important;
    }
    
    /* 側邊欄與相關表單文字顏色微調 */
    .stSidebar, [data-testid="stSidebarUserContent"] {
        background-color: #021a14 !important;
        color: #f0fdf4 !important;
    }
    
    /* 製令卡片改為深綠色帶金屬感的漸層外框 */
    .order-card { 
        background: linear-gradient(145deg, #083b2e 0%, #031c16 100%); 
        border-radius: 14px; 
        border: 1px solid #10b981; 
        margin-bottom: 25px; 
        overflow: hidden; 
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5); 
    }
    
    /* 卡片標頭：亮綠色漸層，配上清楚白字 */
    .order-header { 
        background: linear-gradient(90deg, #059669 0%, #047857 100%); 
        color: white; 
        padding: 14px 18px; 
        font-weight: 800; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-size: 1.25rem; 
        border-bottom: 1px solid #10b981;
    }
    
    /* 通電日期標籤改為顯眼明亮的冰藍或黃金配色 */
    .power-date-tag { 
        background: #06b6d4; 
        color: #ffffff; 
        padding: 4px 12px; 
        border-radius: 8px; 
        font-size: 0.9rem; 
        font-weight: 800; 
        display: flex; 
        align-items: center; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* 工序橫條：改為半透明深色底，帶有翠綠邊線 */
    .proc-row-container { 
        padding: 15px 18px; 
        border-bottom: 1px solid #064e3b; 
        background-color: rgba(2, 44, 34, 0.6); 
    }
    
    /* 工序名稱字體：亮白色，左邊改為亮綠色條 */
    .proc-name { 
        font-weight: 900; 
        color: #ffffff; 
        font-size: 1.1rem; 
        border-left: 5px solid #34d399; 
        padding-left: 12px; 
    }
    
    /* 人員標籤：優化背景與文字對比度，改為明亮清晰字體 */
    .badge-staff { 
        background: #059669; 
        color: #ffffff; 
        padding: 4px 10px; 
        border-radius: 6px; 
        font-size: 0.95rem; 
        font-weight: 700; 
        border: 1px solid #34d399; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 狀態框：已完工 (明亮綠) */
    .status-done-box { 
        background: #065f46; 
        color: #34d399; 
        font-weight: 800; 
        font-size: 0.9rem; 
        padding: 6px 12px; 
        border-radius: 6px; 
        border: 1px solid #34d399; 
        display: inline-block; 
        text-align: center;
    }
    
    /* 狀態框：請指派 (鮮艷橘黃) */
    .status-assign-box { 
        background: #78350f; 
        color: #fcd34d; 
        font-weight: 700; 
        padding: 6px 12px; 
        border-radius: 6px; 
        border: 1px solid #f59e0b; 
        font-size: 0.9rem; 
        text-align: center;
    }
    
    /* 修正下拉選單與一般標題文字在黑底下的顏色 */
    h1, h2, h3, p, label, .stWidgetLabel {
        color: #ffffff !important;
    }
    
    .status-empty { color: #cbd5e1; font-style: italic; font-weight: 700; font-size: 0.95rem; }
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
    st.markdown('<h1 style="text-align:center; color:#34d399; font-size:3rem; font-weight:900;">⚓ 超慧科技系統</h1>', unsafe_allow_html=True)
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
    "🧾 人員評核表",
    "⚙️ 資產編輯清單",
    "📝 任務派發", 
    "⚙️ 設定管理"

    ])
    
    # --- 登出系統按鈕（放到側邊欄 radio 下方，確保 100% 執行與顯示）---
    st.sidebar.markdown(
        """
        <div style="padding: 10px 0; text-align: center;">
            <a href="/?logout=true" target="_self" style="
                display: block; 
                padding: 12px; 
                color: #ffffff !important; 
                background-color: #dc2626 !important; 
                border-radius: 8px; 
                text-decoration: none !important; 
                font-size: 1.2rem; 
                font-weight: 900; 
                box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            ">🚪 點此登出系統</a>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # 檢查是否點擊了登出連結
    if "logout" in st.query_params:
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

    # 導航頁面重整判斷（移至登出按鈕下方，不阻斷程式執行）
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()
        
# --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#34d399; font-weight:900;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

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
                                    st.markdown('<div style="color:#cbd5e1; font-weight:700; font-size:0.95rem;">尚未派工</div>', unsafe_allow_html=True)
                            
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
# --- 📈 工時統計分析 (已修改為 📊 技能評核表) ---
    elif st.session_state.menu_selection == "📈 工時統計分析":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📊 員工技能評核表</h1>', unsafe_allow_html=True)
        
        # 1. 取得當前組長名字 (例如: 陳德文)
        current_leader = st.session_state.user 
        
        # 2. 針對您的 Firebase 結構做抓取
        display_list = []
        try:
            # 抓取 staff_map.json
            map_res = requests.get(f"{DB_BASE_URL}/settings/staff_map.json")
            if map_res.status_code == 200:
                staff_data = map_res.json() or {}
                
                # --- 直接用組長名字當 Key 抓取組員列表 ---
                my_team = staff_data.get(current_leader, [])
                
                if isinstance(my_team, list):
                    display_list = [str(member).strip() for member in my_team]
                
            # 保險：如果沒抓到，讓組長看到自己
            if not display_list:
                display_list = [current_leader]
        except Exception as e:
            st.error(f"連線失敗: {e}")
            display_list = [current_leader]

        st.markdown(f'<p style="font-size:1.2rem; font-weight:bold; color:#1e3a8a;">👥 {current_leader} 組長 的成員技能考核進度：</p>', unsafe_allow_html=True)
        st.divider()

        # 3. 並列由上往下列出該組所有員工，並顯示考核完成程度百分比表
        if display_list:
            for member in sorted(display_list):
                # 建立一個乾淨的員工區塊容器
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        # 放大顯示員工姓名
                        st.markdown(f'<p style="font-size:1.3rem; font-weight:900; color:#000000; margin-top:5px;">👤 {member}</p>', unsafe_allow_html=True)
                    
                    with col2:
                        # 這裡使用 slider 當作範例百分比控鍵（範圍 0-100%），之後您也可以直接綁定 Firebase 數值
                        # 為了避免 key 重複，使用 member 名字作為 key
                        score = st.slider(
                            "考核完成度", 
                            min_value=0, 
                            max_value=100, 
                            value=50,  # 預設 50%，您可以依照需求調整
                            step=5,
                            key=f"skill_{member}",
                            label_visibility="collapsed" # 隱藏欄位小標題讓畫面更乾淨
                        )
                        
                        # 顯示美觀的進度條
                        st.progress(score / 100)
                        st.markdown(f'<p style="text-align:right; font-weight:bold; color:#1e40af; margin-top:-10px;">目前進度: {score}%</p>', unsafe_allow_html=True)
                
                st.markdown('<hr style="margin:10px 0; border-top:1px dashed #cbd5e1;">', unsafe_allow_html=True)
        else:
            st.info("💡 目前此組別無成員資料。")

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
                    
                    # 1. 計算每筆工時(分)與總工時(分鐘數相加)
                    total_all_minutes = 0.0
                    if '秒數' in display_df.columns:
                        display_df['工時(分)'] = (display_df['秒數'] / 60).round(2)
                        total_all_minutes = round(display_df['工時(分)'].sum(), 2) # 找回原本 Minutes 相加功能
                        
                        # 2. 逆推開始時間
                        try:
                            temp_finish = pd.to_datetime(display_df['完工時間'])
                            display_df['開始時間'] = (temp_finish - pd.to_timedelta(display_df['秒數'], unit='s')).dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            display_df['開始時間'] = "計算失敗"

                    # 3. 在標題顯示 (找回原本的 總工時：xx 分鐘 顯示格式)
                    with st.expander(f"📦 製令：{o_id} ({len(group)} 項 | 總工時：{total_all_minutes} 分鐘)"):
                        
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

        # 注入全新「亮紫色」全網頁字體主題 CSS
        st.markdown("""
            <style>
            /* 1. 全網頁基本文字、單選鈕標籤、下拉選單標題等全面強制改為亮工紫色 */
            div[data-testid="stMarkdownContainer"] p, 
            .stRadio label, 
            label, 
            .stWidgetLabel p,
            span {
                color: #e879f9 !important; /* 明亮的紫羅蘭色 */
                font-weight: 800 !important;
            }
            
            /* 2. 修正分頁標籤（Tabs）選取與未選取文字，皆改為紫色系 */
            div[data-testid="stTabs"] button {
                font-size: 1.15rem !important;
                font-weight: 800 !important;
                color: #c084fc !important; /* 未選中時為淡紫色 */
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: #ff00ff !important; /* 選中時為極亮粉紫色 */
                font-weight: 900 !important;
                border-bottom: 3px solid #ff00ff !important;
            }
            
            /* 3. 修正折疊區塊 (例如: 蘇萬紘 👩‍🔧 標題) 文字顏色為亮紫色 */
            div[data-testid="stExpander"] details summary p {
                color: #ff00ff !important;
                font-weight: 900 !important;
                font-size: 1.15rem !important;
            }
            
            /* 4. 修正匯出按鈕的文字顏色與邊框顏色 */
            div.stDownloadButton button p {
                color: #ff00ff !important;
                font-weight: 900 !important;
            }
            div.stDownloadButton button {
                border: 2px solid #ff00ff !important;
                background-color: #ffffff !important;
            }
            div.stDownloadButton button:hover {
                background-color: #fdf4ff !important;
            }
            
            /* 5. 下拉選單與輸入框內部的選中文字優化（維持暗色便於白底閱讀） */
            .stSelectbox div div, .stTextInput div div input {
                color: #0f172a !important;
                font-weight: 700 !important;
            }
            
            /* 6. 小標題 */
            h3 {
                color: #ff00ff !important;
                font-weight: 900 !important;
            }
            
            /* 7. 卡片內部的專屬 class 強制覆寫為亮紫色（解決 C型板手 看不見的問題） */
            .t-title { 
                font-weight: 900 !important; 
                color: #ff00ff !important; /* 強制改亮紫色 */
                font-size: 1.15rem !important; 
            } 
            .t-qty { 
                color: #ff00ff !important; /* 數量也同步亮紫 */
                font-weight: 900 !important; 
                font-size: 1.2rem !important; 
                margin-left: 8px !important; 
                background: #fdf4ff !important; /* 淡紫色背景襯托 */
                padding: 2px 8px !important; 
                border-radius: 5px !important; 
            }
            .t-meta { 
                color: #e879f9 !important; /* 登記時間與人改為明亮紫 */
                font-size: 0.85rem !important; 
                margin-top: 5px !important; 
                font-weight: 700 !important; 
            }
            
            /* 卡片外框設定 */
            .card { background: #ffffff; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 2px solid #e879f9; box-shadow: 0 2px 4px rgba(0,0,0,0.05); } 
            .asset-card { border-left: 10px solid #7c3aed !important; background: #faf5ff !important; border-color: #d8b4fe; } 
            </style>
        """, unsafe_allow_html=True)

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

                    for person, group in display_df.groupby("人員"):
                        with st.expander(f"👩‍🔧 {person} ({len(group)} 項)", expanded=True):
                            for _, row in group.iterrows():
                                db_id = row['db_id']
                                is_a = "asset-card" if row['類型'] == "資產工具" else ""
                                st.markdown(f'<div class="card {is_a}">', unsafe_allow_html=True)
                                col1, col2 = st.columns([7.5, 2.5])
                                with col1:
                                    # 卡片內部的手工具名稱、數量、與登記資訊
                                    st.markdown(f'<div class="t-title">🛠️ {row["手工具名稱"]} <span class="t-qty">x {row["數量"]}</span></div>', unsafe_allow_html=True)
                                    st.markdown(f'<div class="t-meta">登記人: {row.get("登記人","-")} | 時間: {row["登記時間"]}</div>', unsafe_allow_html=True)
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
# --- 🧾 人員評核表 ---
    elif st.session_state.menu_selection == "🧾 人員評核表":
        import io

        st.markdown(
            '<h1 style="text-align:center; color:#7DD3FC; font-weight:900; font-size:2.5rem;">🧾 人員評核表</h1>',
            unsafe_allow_html=True
        )

        # 【安全修正】檢查並確保 EVALUATION_URL 存在，防止 NameError 報錯
        if 'EVALUATION_URL' not in globals() and 'EVALUATION_URL' not in locals():
            if 'DB_URL' in globals() or 'DB_URL' in locals():
                EVALUATION_URL = f"{DB_URL}/evaluation"
            else:
                EVALUATION_URL = "https://your-firebase-url/evaluation" # 防護備用機制

        # 注入優化 CSS：字體全面放大、改用顯眼的亮天藍色與冰藍色，確保深色背景清晰可讀
        st.markdown("""
            <style>
            /* 1. 讓表單內所有的普通文字、欄位標題、滑桿名稱、列表文字放大並變亮藍色 */
            div[data-testid="stMarkdownContainer"] p, 
            label, 
            .stWidgetLabel p,
            span,
            li {
                color: #7DD3FC !important; /* 高亮度冰藍色 */
                font-size: 1.15rem !important; /* 字體放大 */
                font-weight: 800 !important;
            }
            
            /* 2. 讓區域大標題（例如：新增評核、評核紀錄查詢）更亮、更大 */
            h3 {
                color: #38BDF8 !important; /* 亮天藍色 */
                font-size: 1.6rem !important; /* 標題放大 */
                font-weight: 900 !important;
                margin-top: 1rem !important;
            }
            
            /* 3. 修正明細折疊區塊 (st.expander) 的標題文字（放大且清晰） */
            div[data-testid="stExpander"] details summary p {
                color: #38BDF8 !important;
                font-weight: 900 !important;
                font-size: 1.25rem !important;
            }
            
            /* 4. 修正匯出按鈕的文字與外框 */
            div.stDownloadButton button p {
                color: #7DD3FC !important;
                font-weight: 900 !important;
                font-size: 1.1rem !important;
            }
            div.stDownloadButton button {
                border: 2px solid #38BDF8 !important;
                background-color: #052e16 !important;
            }
            div.stDownloadButton button:hover {
                background-color: #14532d !important;
            }
            
            /* 5. 輸入框與文字區域內的文字（讓使用者打字時看得很清楚） */
            div[data-baseweb="select"] > div, 
            div[data-testid="stTextInput"] div div input, 
            div[data-testid="stTextArea"] textarea {
                background-color: #052e16 !important; /* 維持深綠底 */
                color: #ffffff !important;           /* 輸入的文字用純白，最好讀 */
                border: 1px solid #38BDF8 !important; /* 改用天藍色邊框圍繞 */
                font-size: 1.1rem !important;
                font-weight: 700 !important;
            }

            /* 6. 下拉選單點開後的浮動視窗內部選項 */
            div[data-baseweb="menu"], 
            div[role="listbox"], 
            ul[role="listbox"],
            div[data-baseweb="popover"] ul {
                background-color: #052e16 !important;
                border: 1px solid #38BDF8 !important;
            }

            /* 選單內的每一行字體放大、變亮藍色 */
            div[role="option"], 
            li[role="option"],
            div[data-baseweb="menu"] li,
            div[data-baseweb="menu"] div {
                background-color: #052e16 !important;
                color: #7DD3FC !important;
                font-size: 1.1rem !important;
                font-weight: 700 !important;
            }

            /* 當滑鼠移到下拉選單選項上時 */
            div[role="option"]:hover, 
            li[role="option"]:hover,
            div[data-baseweb="menu"] li:hover,
            div[aria-selected="true"] {
                background-color: #38BDF8 !important; 
                color: #052e16 !important; /* 反白時字體變深綠色以利閱讀 */
            }

            /* 7. 「儲存評核」按鈕內的文字放大、變亮藍色 */
            div[data-testid="stForm"] div.stButton > button {
                background-color: #052e16 !important;
                color: #38BDF8 !important;
                border: 2px solid #38BDF8 !important;
                font-size: 1.2rem !important;
                font-weight: 900 !important;
                opacity: 1 !important; 
            }
            div[data-testid="stForm"] div.stButton > button:hover {
                background-color: #38BDF8 !important; 
                color: #052e16 !important;           
            }
            </style>
        """, unsafe_allow_html=True)

        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, [])

        if not my_team:
            st.warning("⚠️ 目前此組長尚未設定組員，請先到【設定管理】設定 staff_map。")
        else:
            # 讀取現有評核資料
            eval_raw = requests.get(f"{EVALUATION_URL}.json").json() or {}

            # --- 新增評核表單 ---
            st.markdown("### ✍️ 新增評核")
            with st.form("evaluation_form"):
                c1, c2 = st.columns(2)
                with c1:
                    eval_staff = st.selectbox("👤 評核人員", sorted(my_team))
                with c2:
                    eval_month = st.text_input("📅 評核月份", value=datetime.datetime.now().strftime("%Y-%m"))

                c3, c4, c5 = st.columns(3)
                with c3:
                    score_attendance = st.slider("出勤表現", 1, 10, 8)
                    score_quality = st.slider("品質表現", 1, 10, 8)
                with c4:
                    score_efficiency = st.slider("工作效率", 1, 10, 8)
                    score_cooperation = st.slider("團隊配合", 1, 10, 8)
                with c5:
                    score_discipline = st.slider("紀律態度", 1, 10, 8)
                    score_5s = st.slider("5S維護", 1, 10, 8)

                comment = st.text_area("📝 評語 / 改善建議", height=120)
                submitted = st.form_submit_button("💾 儲存評核", use_container_width=True)

                if submitted:
                    avg_score = round((
                        score_attendance +
                        score_quality +
                        score_efficiency +
                        score_cooperation +
                        score_discipline +
                        score_5s
                    ) / 6, 2)

                    payload = {
                        "組長": current_leader,
                        "人員": eval_staff,
                        "評核月份": eval_month,
                        "出勤表現": score_attendance,
                        "品質表現": score_quality,
                        "工作效率": score_efficiency,
                        "團隊配合": score_cooperation,
                        "紀律態度": score_discipline,
                        "5S維護": score_5s,
                        "平均分數": avg_score,
                        "評語": comment,
                        "建立時間": get_now_str()
                    }
                    requests.post(f"{EVALUATION_URL}.json", data=json.dumps(payload))
                    st.success(f"✅ {eval_staff} 的評核已儲存！平均分數：{avg_score}")
                    time.sleep(0.5)
                    st.rerun()

            st.divider()

            # --- 查詢與篩選 ---
            st.markdown("### 🔍 評核紀錄查詢")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                filter_staff = st.selectbox("篩選人員", ["全部"] + sorted(my_team), key="eval_filter_staff")
            with fc2:
                all_months = []
                if eval_raw:
                    all_months = sorted(list(set([
                        str(v.get("評核月份", ""))
                        for v in eval_raw.values()
                        if v.get("評核月份")
                    ])), reverse=True)
                filter_month = st.selectbox("篩選月份", ["全部"] + all_months, key="eval_filter_month")
            with fc3:
                keyword = st.text_input("關鍵字搜尋", key="eval_keyword")

            if eval_raw:
                eval_list = []
                for k, v in eval_raw.items():
                    row = v.copy()
                    row["db_id"] = k
                    eval_list.append(row)

                eval_df = pd.DataFrame(eval_list)

                # 安全檢查：確保 DataFrame 不為空且包含「組長」欄位時才進行篩選
                if not eval_df.empty and "組長" in eval_df.columns:
                    eval_df = eval_df[eval_df["組長"] == current_leader]
                else:
                    eval_df = pd.DataFrame()

                if not eval_df.empty and filter_staff != "全部" and "人員" in eval_df.columns:
                    eval_df = eval_df[eval_df["人員"] == filter_staff]

                if not eval_df.empty and filter_month != "全部" and "評核月份" in eval_df.columns:
                    eval_df = eval_df[eval_df["評核月份"] == filter_month]

                if not eval_df.empty and keyword:
                    eval_df = eval_df[
                        eval_df.astype(str).apply(
                            lambda x: x.str.contains(keyword, case=False, na=False)
                        ).any(axis=1)
                    ]

                if not eval_df.empty:
                    # 匯出 CSV
                    csv_data = eval_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "📄 匯出評核表 CSV",
                        data=csv_data,
                        file_name=f"人員評核表_{current_leader}.csv",
                        key="download_eval_csv"
                    )

                    st.markdown("### 📊 評核總覽")
                    
                    show_cols = [
                        "人員", "評核月份", "出勤表現", "品質表現", "工作效率",
                        "團隊配合", "紀律態度", "5S維護", "平均分數", "評語", "建立時間"
                    ]
                    available_cols = [c for c in show_cols if c in eval_df.columns]
                    
                    st.dataframe(
                        eval_df[available_cols],
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("### 👁️ 明細檢視 / 刪除")
                    for _, row in eval_df.sort_values(by="建立時間", ascending=False).iterrows():
                        with st.expander(f"👤 {row.get('人員', '未知')}｜📅 {row.get('評核月份', '')}｜⭐ 平均 {row.get('平均分數', 0)}"):
                            st.markdown(f"""
                            - **組長：** {row.get('組長', '-')}
                            - **出勤表現：** {row.get('出勤表現', '-')}
                            - **品質表現：** {row.get('品質表現', '-')}
                            - **工作效率：** {row.get('工作效率', '-')}
                            - **團隊配合：** {row.get('團隊配合', '-')}
                            - **紀律態度：** {row.get('紀律態度', '-')}
                            - **5S維護：** {row.get('5S維護', '-')}
                            - **平均分數：** {row.get('平均分數', '-')}
                            - **評語：** {row.get('評語', '-')}
                            - **建立時間：** {row.get('建立時間', '-')}
                            """)

                            del_col1, del_col2 = st.columns([3, 1])
                            with del_col2:
                                if st.button("🗑️ 刪除", key=f"del_eval_{row['db_id']}"):
                                    requests.delete(f"{EVALUATION_URL}/{row['db_id']}.json")
                                    st.success("已刪除該筆評核")
                                    time.sleep(0.5)
                                    st.rerun()
                else:
                    st.info("💡 查無符合條件的評核紀錄")
            else:
                st.info("💡 目前尚無評核資料")
# --- ⚙️ 編輯手工具清單 (修正 Duplicate ID 版本) ---
    elif st.session_state.menu_selection == "⚙️ 資產編輯清單":
        # 1. 補回關鍵的粉紅色 CSS 樣式 (優化對比度與文字清晰度)
        st.markdown("""
            <style>
            .pink-card {
                background-color: #fff1f2;
                border: 2px solid #f43f5e;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            .stButton>button {
                border-radius: 10px;
                font-weight: bold;
            }
            h3 {
                color: #be123c !important;
                font-weight: 900 !important;
            }
            label {
                color: #4c0519 !important;
                font-weight: bold !important;
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
                    c_t1.markdown(f"📍 **{v['no']}** - {v['name']}", help="資產項目")
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
