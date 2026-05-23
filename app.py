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
   
    "💡2o26上半年技能考核進度", 
    "🧾組長待辦事項",
    "📝每日6S任務回報", 
    "🎮6S戰境養成", 
    "📊 製造部派工專區", 
    "📜 完工紀錄查詢", 
    "🔧 固資&手工具紀錄表",
    "⚙️ 資產編輯清單", 
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


elif st.session_state.menu_selection == "📝每日6S任務回報":
        import requests
        import json
        from datetime import datetime, timedelta, timezone
        import time

        # 【修正】移除過多引號，確保 HTML 正確渲染
        st.markdown('''
            <div style="text-align:center; margin-bottom:2rem;">
                <h1 style="color:#60A5FA; font-weight:900; font-size: 3.5rem;">📋 每日 6S 任務回報中心</h1>
                <p style="color:#9CA3AF;">完成今日現場回報，即可領取 1 點自由屬性點數！</p>
            </div>
            ''', unsafe_allow_html=True)

        # 【安全路徑自適應】
        BASE_URL = globals().get('DB_URL') or globals().get('DB_BASE_URL') or "https://your-firebase-url"
        GAME_DB_URL = f"{BASE_URL}/game_rpg_data"
        REPORT_LOG_URL = f"{BASE_URL}/daily_6s_report_logs"

        tz_taiwan = timezone(timedelta(hours=8))
        today_tw_str = datetime.now(tz_taiwan).strftime("%Y-%m-%d")

        st.info(f"📅 任務結算基準日（台北時間）：**{today_tw_str}**")

        # 讀取後台名單
        raw_data_1 = requests.get(f"{BASE_URL}/leader_members.json").json() or ""
        
        leader_member_mapping = {}
        if isinstance(raw_data_1, str):
            for line in raw_data_1.splitlines():
                line = line.strip()
                if ':' in line:
                    parts = line.split(":")
                    l_name = parts[0].strip()
                    m_list = [m.strip() for m in parts[1].split(",") if m.strip()]
                    if l_name and m_list:
                        leader_member_mapping[l_name] = m_list

        leader_list = list(leader_member_mapping.keys()) or ["陳德文", "劉志偉", "吳政昌", "蘇萬紘", "陳文山", "李俊霖"]

        # 介面渲染
        st.markdown("### 🔍 第一步：確認您的身份")
        col_leader, col_member = st.columns(2)
        
        with col_leader:
            selected_leader = st.selectbox("👤 選擇所屬組長：", leader_list)
        
        with col_member:
            available_members = leader_member_mapping.get(selected_leader, [])
            if available_members:
                selected_user = st.selectbox("🎯 選擇回報同仁姓名：", available_members)
                has_members = True
            else:
                st.warning("⚠️ 此組長尚未在後台配置屬下同仁")
                selected_user = None
                has_members = False

        st.divider()
        st.markdown("### 🚀 第二步：送出回報領取獎勵")
        
        if not has_members:
            st.error("❌ 無法回報：請確認後台設定管理中的配置。")
        else:
            st.warning(f"⚠️ 每人每日限領一次。送出後【{selected_user}】將獲得 1 點獎勵。")

            if st.button(f"✨ 繳交今日 6S 成果", use_container_width=True, type="primary"):
                safe_user_key = str(selected_user).strip()
                # 檢查今日回報狀態
                check_exist = requests.get(f"{REPORT_LOG_URL}/{today_tw_str}/{safe_user_key}.json").json()

                if check_exist:
                    st.error(f"❌ 【{selected_user}】今日已完成過任務！")
                else:
                    # 紀錄回報
                    report_payload = {
                        "reported_at": datetime.now(tz_taiwan).strftime("%Y-%m-%d %H:%M:%S"),
                        "leader": selected_leader,
                        "status": "已完成"
                    }
                    requests.put(f"{REPORT_LOG_URL}/{today_tw_str}/{safe_user_key}.json", data=json.dumps(report_payload))

                    # 讀取並更新 RPG 數據
                    player_rpg_data = requests.get(f"{GAME_DB_URL}/{safe_user_key}.json").json() or {}
                    update_payload = {
                        "str": int(player_rpg_data.get("str", 0)),
                        "vit": int(player_rpg_data.get("vit", 0)),
                        "agi": int(player_rpg_data.get("agi", 0)),
                        "cha": int(player_rpg_data.get("cha", 0)),
                        "avail_pts": int(player_rpg_data.get("avail_pts", 0)) + 1
                    }
                    requests.put(f"{GAME_DB_URL}/{safe_user_key}.json", data=json.dumps(update_payload))

                    st.session_state.user = safe_user_key
                    st.balloons()
                    st.success(f"🎉 回報成功！點數已發放。")
                    time.sleep(1.2)
                    st.session_state.menu_selection = "🎮6S戰境養成"
                    st.rerun()
# ==========================================
# 🎮 頁面二：6S 戰境養成與決鬥系統
# ==========================================
    elif st.session_state.menu_selection == "🎮6S戰境養成":
        import random
        import time
        import json # 確保有載入 json 模組

        st.markdown(
            '''
            <div style="text-align:center; margin-bottom:2rem;">
                <h1 style="color:#FBBF24 !important; font-weight:900 !important; font-size: 4.5rem !important; display:inline-block;">
                    🎮 6S 戰境養成系統
                </h1>
            </div>
            ''',
            unsafe_allow_html=True
        )

        # 【安全路徑自適應】
        if 'DB_URL' in globals() or 'DB_URL' in locals():
            GAME_DB_URL = f"{DB_URL}/game_rpg_data"
            GAME_CONFIG_URL = f"{DB_URL}/game_config"
        elif 'DB_BASE_URL' in globals() or 'DB_BASE_URL' in locals():
            GAME_DB_URL = f"{DB_BASE_URL}/game_rpg_data"
            GAME_CONFIG_URL = f"{DB_BASE_URL}/game_config"
        else:
            GAME_DB_URL = "https://your-firebase-url/game_rpg_data"
            GAME_CONFIG_URL = "https://your-firebase-url/game_config"

        # 讀取後台設定稱謂門檻
        config_data = requests.get(f"{GAME_CONFIG_URL}.json").json() or {}
        lv1_pts = int(config_data.get("lv1_pts", 0))
        lv2_pts = int(config_data.get("lv2_pts", 10))
        lv3_pts = int(config_data.get("lv3_pts", 30))
        lv4_pts = int(config_data.get("lv4_pts", 60))
        
        lv1_name = str(config_data.get("lv1_name", "🌾 平民"))
        lv2_name = str(config_data.get("lv2_name", "🧹 6S見習騎士"))
        lv3_name = str(config_data.get("lv3_name", "⚔️ 現場巡檢戰士"))
        lv4_name = str(config_data.get("lv4_name", "👑 乾淨整潔大宗師"))

        # 獲取當前連動登入同仁
        current_user = str(st.session_state.user).strip() if st.session_state.get("user") else "未登入同仁"
        all_players_data = requests.get(f"{GAME_DB_URL}.json").json() or {}
        
        # 新玩家自動無痛初始化
        if current_user != "未登入同仁" and current_user not in all_players_data:
            init_payload = {"str": 0, "vit": 0, "agi": 0, "cha": 0, "avail_pts": 5}
            requests.put(f"{GAME_DB_URL}/{current_user}.json", data=json.dumps(init_payload))
            all_players_data[current_user] = init_payload

        user_stats = all_players_data.get(current_user, {"str": 0, "vit": 0, "agi": 0, "cha": 0, "avail_pts": 0})
        u_str = int(user_stats.get("str", 0))
        u_vit = int(user_stats.get("vit", 0))
        u_agi = int(user_stats.get("agi", 0))
        u_cha = int(user_stats.get("cha", 0))
        u_pts = int(user_stats.get("avail_pts", 0))
        u_total = u_str + u_vit + u_agi + u_cha

        def get_title(total_pts):
            if total_pts >= lv4_pts: return lv4_name
            elif total_pts >= lv3_pts: return lv3_name
            elif total_pts >= lv2_pts: return lv2_name
            else: return lv1_name

        current_title = get_title(u_total)

        st.markdown(f"### 👤 我的個人戰力面板：【{current_title}】— 身份：【{current_user}】")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="💪 力量 (攻擊力)", value=f"{u_str} 點", delta=f"+{u_str * 5} ATK")
            if u_pts > 0 and current_user != "未登入同仁":
                if st.button("➕ 加力量", key="add_str"):
                    requests.patch(f"{GAME_DB_URL}/{current_user}.json", data=json.dumps({"str": u_str+1, "avail_pts": u_pts-1}))
                    st.rerun()
        with col2:
            st.metric(label="🔋 體力 (生命值)", value=f"{u_vit} 點", delta=f"+{u_vit * 30} HP")
            if u_pts > 0 and current_user != "未登入同仁":
                if st.button("➕ 加體力", key="add_vit"):
                    requests.patch(f"{GAME_DB_URL}/{current_user}.json", data=json.dumps({"vit": u_vit+1, "avail_pts": u_pts-1}))
                    st.rerun()
        with col3:
            st.metric(label="⚡ 敏捷 (閃避率)", value=f"{u_agi} 點", delta=f"+{u_agi * 2} %")
            if u_pts > 0 and current_user != "未登入同仁":
                if st.button("➕ 加敏捷", key="add_agi"):
                    requests.patch(f"{GAME_DB_URL}/{current_user}.json", data=json.dumps({"agi": u_agi+1, "avail_pts": u_pts-1}))
                    st.rerun()
        with col4:
            st.metric(label="✨ 魅力 (召喚率)", value=f"{u_cha} 點", delta=f"+{u_cha * 5} %")
            if u_pts > 0 and current_user != "未登入同仁":
                if st.button("➕ 加魅力", key="add_cha"):
                    requests.patch(f"{GAME_DB_URL}/{current_user}.json", data=json.dumps({"cha": u_cha+1, "avail_pts": u_pts-1}))
                    st.rerun()
        with col5:
            st.markdown(f"<div style='background-color:#1e3a8a; padding:10px; border-radius:5px; text-align:center;'><b style='color:#FBBF24;'>剩餘自由點數</b><br><span style='font-size:2rem; font-weight:900; color:#fff;'>{u_pts}</span></div>", unsafe_allow_html=True)

        st.divider()

# ==========================================
        # ⚔️ 擂台決鬥 PK 場 (修正版)
        # ==========================================
        st.markdown("### ⚔️ 尋找現場同仁發起決鬥")

        # 1. 抓取資料並嘗試解析人員配置
        mapping_raw = requests.get(f"{DB_BASE_URL}/config/employee_mapping.json").json()
        all_staff = set()
        
        # 嘗試從文字中提取人名
        if isinstance(mapping_raw, str):
            # 針對每一行，尋找冒號後的內容
            for line in mapping_raw.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)[1] # 取得冒號後方的所有文字
                    # 分割逗號或頓號
                    names = parts.replace('，', ',').replace('、', ',').split(',')
                    for name in names:
                        if name.strip():
                            all_staff.add(name.strip())
        
        # 如果解析出來的人數太少，或者資料結構不同，備援抓取已建立 RPG 角色的玩家
        if len(all_staff) < 2:
            all_staff.update(all_players_data.keys())

        # 2. 過濾自己與無效名稱
        opponents = sorted([n for n in all_staff if n != current_user and n != "未登入同仁" and n.strip()])
        
        if not opponents:
            st.warning("💡 目前暫無其他同仁名單可進行決鬥。")
        else:
            c_sel, c_btn = st.columns([3, 1])
            with c_sel:
                target_opp = st.selectbox("🎯 選擇決鬥目標對手：", opponents)
            with c_btn:
                st.write("")
                st.write("")
                start_battle = st.button("💥 發起決鬥！", use_container_width=True)

            if start_battle and current_user != "未登入同仁":
                # 自動初始化對手數據
                if target_opp not in all_players_data:
                    init_payload = {"str": 0, "vit": 0, "agi": 0, "cha": 0, "avail_pts": 5}
                    requests.put(f"{GAME_DB_URL}/{target_opp}.json", data=json.dumps(init_payload))
                    all_players_data[target_opp] = init_payload
                
                target_data = all_players_data.get(target_opp)

                # 執行戰鬥模擬
                @st.dialog("⚔️ 戰境決鬥場 ⚔️")
                def run_battle_simulation(p1, p2, p1_data, p2_data):
                    st.markdown("<style>div[data-modal-container] * { color: black !important; }</style>", unsafe_allow_html=True)
                    
                    # 計算數值邏輯...
                    p1_total = int(p1_data.get("str",0))+int(p1_data.get("vit",0))+int(p1_data.get("agi",0))+int(p1_data.get("cha",0))
                    p2_total = int(p2_data.get("str",0))+int(p2_data.get("vit",0))+int(p2_data.get("agi",0))+int(p2_data.get("cha",0))
                    
                    p1_name = f"【{get_title(p1_total)}】{p1}"
                    p2_name = f"【{get_title(p2_total)}】{p2}"

                    p1_hp = 100 + (int(p1_data.get("vit", 0)) * 30)
                    p1_atk = 15 + (int(p1_data.get("str", 0)) * 5)
                    p2_hp = 100 + (int(p2_data.get("vit", 0)) * 30)
                    p2_atk = 15 + (int(p2_data.get("str", 0)) * 5)

                    st.markdown("### 🥊 雙方數據就緒！")
                    st.write(f"🔴 **{p1_name}** (HP: {p1_hp} / ATK: {p1_atk})")
                    st.write(f"🔵 **{p2_name}** (HP: {p2_hp} / ATK: {p2_atk})")
                    st.divider()

                    battle_log = []
                    for r in range(1, 6):
                        dmg1 = random.randint(p1_atk-3, p1_atk+5)
                        p2_hp -= dmg1
                        battle_log.append(f"⚔️ 第 {r} 回合：{p1_name} 攻擊 {p2_name} 造成 {max(0, dmg1)} 點傷害！")
                        if p2_hp <= 0: break
                    
                    for log in battle_log: st.write(log)
                    if p2_hp <= 0: st.success(f"🏆 {p1_name} 獲勝！")
                    else: st.info("🤝 戰鬥平手收場！")

                run_battle_simulation(current_user, target_opp, user_stats, target_data)
        
        # ==========================================
        # ⚙️ 後台稱謂門檻設定區
        # ==========================================
        st.markdown("### ⚙️ 6S 戰境養成管理後台")
        with st.expander("🔒 稱謂晉升門檻點數自訂"):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                in_lv1 = st.text_input("等級1名稱", value=lv1_name)
                in_lv2 = st.text_input("等級2名稱", value=lv2_name)
                in_lv3 = st.text_input("等級3名稱", value=lv3_name)
                in_lv4 = st.text_input("等級4名稱", value=lv4_name)
            with f_col2:
                pt_lv1 = st.number_input("等級1所需配點總數", value=lv1_pts)
                pt_lv2 = st.number_input("等級2所需配點總數", value=lv2_pts)
                pt_lv3 = st.number_input("等級3所需配點總數", value=lv3_pts)
                pt_lv4 = st.number_input("等級4所需配點總數", value=lv4_pts)

            if st.button("💾 儲存後台配置設定", use_container_width=True):
                save_payload = {
                    "lv1_name": str(in_lv1), "lv1_pts": int(pt_lv1),
                    "lv2_name": str(in_lv2), "lv2_pts": int(pt_lv2),
                    "lv3_name": str(in_lv3), "lv3_pts": int(pt_lv3),
                    "lv4_name": str(in_lv4), "lv4_pts": int(pt_lv4),
                }
                requests.put(f"{GAME_CONFIG_URL}.json", data=json.dumps(save_payload))
                st.success("後台晉升設定更新完成！")
                time.sleep(0.5)
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
            
# --- 📈💡2o26上半年技能考核進度 ---
    elif st.session_state.menu_selection == "💡2o26上半年技能考核進度":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">💡2o26上半年技能考核進度</h1>', unsafe_allow_html=True)
        
        # 1. 取得當前登入的組長名字
        logged_in_user = st.session_state.user 
        
        # 2. 先從資料庫抓取全體組長清單，做為切換選單的選項
        leader_options = []
        try:
            map_res = requests.get(f"{DB_BASE_URL}/settings/staff_map.json")
            if map_res.status_code == 200:
                staff_data = map_res.json() or {}
                # 抓出所有的組長鍵值 (Key)
                leader_options = sorted([str(k).strip() for k in staff_data.keys() if k])
        except Exception as e:
            st.error(f"無法讀取組長清單: {e}")
            
        # 防呆：如果資料庫撈不到，至少包含當前登入者
        if not leader_options:
            leader_options = [str(logged_in_user).strip()]
        elif str(logged_in_user).strip() not in leader_options:
            leader_options.insert(0, str(logged_in_user).strip())

        # --- 👑 【新增功能：切換組長選單】 ---
        try:
            default_leader_idx = leader_options.index(str(logged_in_user).strip())
        except:
            default_leader_idx = 0

        selected_leader = st.selectbox(
            "👑 請選擇要檢視/評核的組長：",
            options=leader_options,
            index=default_leader_idx,
            key="global_leader_selector"
        )

        # 3. 根據選定的組長，嚴格清洗並抓取該組長的組員名單
        display_list = []
        try:
            if map_res.status_code == 200:
                raw_team_data = staff_data.get(selected_leader, [])
                
                if isinstance(raw_team_data, list):
                    for item in raw_team_data:
                        item_str = str(item).strip()
                        if "," in item_str:
                            display_list.extend([x.strip() for x in item_str.split(",") if x.strip()])
                        else:
                            if item_str: display_list.append(item_str)
                elif isinstance(raw_team_data, str):
                    display_list = [x.strip() for x in raw_team_data.split(",") if x.strip()]
                
            if not display_list:
                display_list = [str(selected_leader).strip()]
        except:
            display_list = [str(selected_leader).strip()]

        # 去除重複的人員名稱
        display_list = sorted(list(set(display_list)))

        # --- 🌐 核心讀取：從 Firebase 讀取目前全體員工的最新考核分數 (讓資料永久存在) ---
        db_saved_scores = {}
        try:
            latest_eval_res = requests.get(f"{DB_BASE_URL}/skills_current_status.json")
            if latest_eval_res.status_code == 200:
                db_saved_scores = latest_eval_res.json() or {}
        except:
            pass

        st.markdown(f'<p style="font-size:1.2rem; font-weight:bold; color:#1e3a8a;">👥 正在檢視：【{selected_leader} 組長】的組員技能考核狀態 (每格刻度 10%)：</p>', unsafe_allow_html=True)
        st.divider()

        # 固定 0% 到 100% 的選單選項
        options_10 = [f"{x}%" for x in range(0, 101, 10)]

        # 4. 一個畫面左右與上下並列顯示（2列 × 4欄 = 8個人）
        if display_list:
            # 每 4 個人切換成一橫列
            for i in range(0, len(display_list), 4):
                chunk = display_list[i:i+4]
                cols = st.columns(4)  # 建立左右 4 個欄位
                
                for idx, member in enumerate(chunk):
                    m_name = str(member).strip()
                    if not m_name: continue
                    
                    # 優先從資料庫歷史紀錄讀取百分比，如果資料庫沒紀錄，預設才顯示 50%
                    member_score_in_db = db_saved_scores.get(m_name, {}).get("技能考核完成度", 0)
                    default_str = f"{member_score_in_db}%"
                    
                    # 確保數值在選單內，防呆機制
                    if default_str not in options_10:
                        default_str = "50%"
                    current_index = options_10.index(default_str)
                    
                    with cols[idx]:
                        # 精美黑框卡片外觀
                        st.markdown(f'<div style="background:#1e3a8a; color:white; padding:8px 10px; border-radius:10px 10px 0 0; font-weight:bold; font-size:1.1rem; text-align:center;">👤 {m_name}</div>', unsafe_allow_html=True)
                        
                        with st.container(border=True):
                            # 下拉式選單
                            selected_str = st.selectbox(
                                "技能考核進度",
                                options=options_10,
                                index=current_index,
                                key="pct_select_" + m_name,
                                label_visibility="collapsed"
                            )
                            
                            # 轉回純數字供圖表使用
                            pct_val = int(selected_str.replace("%", ""))
                            
                            # 【核心聯動】如果使用者調整了選單數值，立刻自動同步寫入 Firebase 更新，達到永久保存
                            if pct_val != member_score_in_db:
                                sync_url = f"{DB_BASE_URL}/skills_current_status/{m_name}.json"
                                sync_data = {
                                    "技能考核完成度": pct_val,
                                    "更新時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                requests.put(sync_url, data=json.dumps(sync_data))
                                st.rerun()
                            
                            # 根據百分比動態決定彩色圓形的顏色 (低於40紅, 40-70橘, 80以上綠)
                            if pct_val <= 30:
                                circle_color = "#ef4444"  # 紅色
                            elif pct_val <= 70:
                                circle_color = "#f97316"  # 橘色
                            else:
                                circle_color = "#22c55e"  # 綠色
                                
                            # 用 HTML/CSS 畫出彩色的圓形百分比圖表
                            st.components.v1.html(f"""
                                <div style="display: flex; justify-content: center; align-items: center; height: 110px; font-family: sans-serif;">
                                    <div style="position: relative; width: 90px; height: 90px; border-radius: 50%; background: conic-gradient({circle_color} {pct_val * 3.6}deg, #e2e8f0 0deg); display: flex; justify-content: center; align-items: center;">
                                        <div style="position: absolute; width: 72px; height: 72px; border-radius: 50%; background: white; display: flex; justify-content: center; align-items: center; flex-direction: column;">
                                            <span style="font-size: 1.4rem; font-weight: 900; color: #1e3a8a;">{pct_val}%</span>
                                            <span style="font-size: 0.65rem; color: #64748b; font-weight: bold; margin-top: 2px;">技能考核</span>
                                        </div>
                                    </div>
                                </div>
                            """, height=110)
                            
                            # 獨立的儲存核准歷史按鈕 (按下即發送一筆正式報表到歷史資料庫)
                            if st.button("💾 儲存歷史", key="save_btn_" + m_name, use_container_width=True, type="primary"):
                                eval_db_url = f"{DB_BASE_URL}/skills_evaluations"
                                new_eval = {
                                    "人員": m_name,
                                    "技能考核完成度": pct_val,
                                    "評核月份": datetime.datetime.now().strftime("%Y-%m"),
                                    "評核時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                try:
                                    res = requests.post(f"{eval_db_url}.json", data=json.dumps(new_eval))
                                    if res.status_code == 200:
                                        st.success(f"{m_name} 已存檔!")
                                    else:
                                        st.error("錯誤")
                                except Exception as save_err:
                                    st.error(f"出錯: {save_err}")
                
                st.markdown('<div style="margin-bottom:15px;"></div>', unsafe_allow_html=True)
        else:
            st.info("💡 目前此組別無成員資料。")

# --- 📜 完工紀錄查詢 (原功能完全保留，一律不修改) ---
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
                        total_all_minutes = round(display_df['工時(分)'].sum(), 2) 
                        
                        # 2. 逆推開始時間
                        try:
                            temp_finish = pd.to_datetime(display_df['完工時間'])
                            display_df['開始時間'] = (temp_finish - pd.to_timedelta(display_df['秒數'], unit='s')).dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            display_df['開始時間'] = "計算失敗"

                    # 3. 在標題顯示
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

# --- 🧾 組長待辦事項 ---
    elif st.session_state.menu_selection == "🧾組長待辦事項":
        import io

        # 1. 注入專屬設定，徹底移除會波及到左側選單的全局 CSS，只針對單一標題標籤進行強制放大
        st.markdown("""
            <style>
            /* 【核心修正】僅針對 #my-giant-main-title 這個專屬識別碼進行放大，絕對不會影響到左側導航與其他文字 */
            #my-giant-main-title {
                color: #7DD3FC !important;
                font-size: 3.5rem !important; /* 如果覺得不夠大，可以自行調整為 4.0rem 或 4.5rem */
                font-weight: 900 !important;
                text-align: center !important;
                margin-bottom: 2rem !important;
                display: block !important;
            }
            
            /* 針對各區段的中標題保持系統原樣 */
            h3 {
                color: #38BDF8 !important; 
                font-size: 1.8rem !important; 
                font-weight: 900 !important;
                margin-top: 1.2rem !important;
            }
            /* CSV 匯出按鈕文字 */
            div.stDownloadButton button p {
                color: #7DD3FC !important;
                font-weight: 900 !important;
                font-size: 1.2rem !important;
            }
            div.stDownloadButton button {
                border: 2px solid #38BDF8 !important;
                background-color: #052e16 !important;
            }
            /* 輸入框、下拉選單本體、日曆輸入框、以及網格編輯器內的文字 */
            div[data-baseweb="select"] > div, 
            div[data-testid="stTextInput"] div div input, 
            div[data-testid="stTextArea"] textarea,
            div[data-testid="stDateInput"] input,
            div[data-testid="stTable"] table,
            .stDataEditor div {
                background-color: #052e16 !important; 
                color: #ffffff !important;           
                border: 1px solid #38BDF8 !important; 
                font-size: 1.25rem !important; 
                font-weight: 700 !important;
            }
            /* 表單提交按鈕字體調整 */
            div[data-testid="stForm"] div.stButton > button {
                background-color: #052e16 !important;
                color: #38BDF8 !important;
                border: 2px solid #38BDF8 !important;
                font-size: 1.3rem !important;
                font-weight: 900 !important;
            }
            div[data-testid="stForm"] div.stButton > button:hover {
                background-color: #38BDF8 !important; 
                color: #052e16 !important;           
            }
            </style>
        """, unsafe_allow_html=True)

        # 2. 【核心修正】套用專屬識別碼，確保只有此行中間主標題放大
        st.markdown('<span id="my-giant-main-title">🧾 組長待辦事項</span>', unsafe_allow_html=True)

        # 【安全修正】檢查並確保 URL 存在，防止 NameError 報錯
        if 'TODO_DB_URL' not in globals() and 'TODO_DB_URL' not in locals():
            if 'DB_URL' in globals() or 'DB_URL' in locals():
                TODO_DB_URL = f"{DB_URL}/todo_tasks"
                TODO_DONE_URL = f"{DB_URL}/todo_completed"
            elif 'DB_BASE_URL' in globals() or 'DB_BASE_URL' in locals():
                TODO_DB_URL = f"{DB_BASE_URL}/todo_tasks"
                TODO_DONE_URL = f"{DB_BASE_URL}/todo_completed"
            else:
                TODO_DB_URL = "https://your-firebase-url/todo_tasks" 
                TODO_DONE_URL = "https://your-firebase-url/todo_completed"

        current_leader = st.session_state.user

        # 從 staff_map 自動抓取全體組長的清單
        all_leaders_list = []
        if 'staff_map' in globals() or 'staff_map' in locals():
            all_leaders_list = sorted([str(k).strip() for k in staff_map.keys() if k])
        
        if not all_leaders_list:
            all_leaders_list = [str(current_leader).strip()]
        elif str(current_leader).strip() not in all_leaders_list:
            all_leaders_list.insert(0, str(current_leader).strip())

        # 同時讀取「未完成待辦」與「已完成紀錄」歷史資料
        todo_raw = requests.get(f"{TODO_DB_URL}.json").json() or {}
        done_raw = requests.get(f"{TODO_DONE_URL}.json").json() or {}

        # ==========================================
        # 第一區：🔍 歷史交辦事項查詢與總覽
        # ==========================================
        st.markdown("### 🔍 歷史交辦事項查詢")
        filter_leader = st.selectbox("篩選負責組長", ["全部"] + all_leaders_list, key="todo_filter_leader")

        if todo_raw:
            todo_list = []
            for k, v in todo_raw.items():
                row = v.copy()
                row["db_id"] = k
                row["✅ 完成"] = False
                row["🗑️ 刪除"] = False
                todo_list.append(row)

            todo_df = pd.DataFrame(todo_list)

            # 進行組長過濾篩選
            if not todo_df.empty and filter_leader != "全部" and "組長" in todo_df.columns:
                todo_df = todo_df[todo_df["組長"] == filter_leader]

            if not todo_df.empty:
                # 徹底排除「指派人」欄位
                if "指派人" in todo_df.columns:
                    todo_df = todo_df.drop(columns=["指派人"])

                # 匯出 CSV 功能
                csv_data = todo_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📄 匯出待辦事項 CSV",
                    data=csv_data,
                    file_name=f"組長待辦事項總表.csv",
                    key="download_todo_csv"
                )

                st.markdown("### 📊 未完成事項總覽")
                
                # 排序：最新建立的在最上方
                todo_df = todo_df.sort_values(by="建立時間", ascending=False).reset_index(drop=True)

                # 定義要在網格中顯示的欄位，將操作按鈕放在最右側
                show_cols = ["組長", "交辦事項", "預計完成日期", "建立時間", "✅ 完成", "🗑️ 刪除"]
                available_cols = [c for c in show_cols if c in todo_df.columns]
                
                # 透過 st.data_editor 產生帶有精美網格線且可直接點選的整合介面
                edited_df = st.data_editor(
                    todo_df[available_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "組長": st.column_config.TextColumn("組長", disabled=True),
                        "交辦事項": st.column_config.TextColumn("交辦事項", disabled=True),
                        "預計完成日期": st.column_config.TextColumn("預計完成日期", disabled=True),
                        "建立時間": st.column_config.TextColumn("建立時間", disabled=True),
                        "✅ 完成": st.column_config.CheckboxColumn("✅ 完成", help="勾選以將此事項標記為完成", default=False),
                        "🗑️ 刪除": st.column_config.CheckboxColumn("🗑️ 刪除", help="勾選以刪除此事項", default=False),
                    },
                    key="todo_integrated_grid"
                )

                # 檢查網格內是否有觸發勾選動作
                for idx, row in edited_df.iterrows():
                    orig_row = todo_df[todo_df["建立時間"] == row["建立時間"]].iloc[0]
                    db_key = orig_row["db_id"]

                    # 處理邏輯 1：點選完成
                    if row["✅ 完成"]:
                        raw_dict = orig_row.to_dict()
                        done_payload = {}
                        for key, val in raw_dict.items():
                            if pd.isna(val):
                                done_payload[str(key)] = ""
                            else:
                                done_payload[str(key)] = str(val)

                        done_payload["完成時間"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        done_payload.pop("db_id", None)
                        done_payload.pop("✅ 完成", None)
                        done_payload.pop("🗑️ 刪除", None)
                        
                        requests.post(f"{TODO_DONE_URL}.json", data=json.dumps(done_payload))
                        requests.delete(f"{TODO_DB_URL}/{db_key}.json")
                        
                        st.success(f"🎉 事項【{orig_row.get('交辦事項')[:10]}...】已移入完成歷史紀錄！")
                        time.sleep(0.5)
                        st.rerun()

                    # 處理邏輯 2：點選刪除（彈出密碼輸入框）
                    if row["🗑️ 刪除"]:
                        st.warning(f"⚠️ 您正在準備刪除【{orig_row.get('組長')}】的項目：{orig_row.get('交辦事項')[:15]}...")
                        pwd_input = st.text_input("🔒 請輸入刪除權限密碼：", type="password", key=f"grid_pwd_{db_key}")
                        
                        if pwd_input == "0000":
                            requests.delete(f"{TODO_DB_URL}/{db_key}.json")
                            st.success("已成功刪除該筆交辦事項！")
                            time.sleep(0.5)
                            st.rerun()
                        elif pwd_input != "":
                            st.error("❌ 密碼錯誤，拒絕刪除！")
            else:
                st.info("💡 查無符合條件的待辦事項")
        else:
            st.info("💡 目前尚無任何未完成的交辦事項紀錄")

        st.divider()

        # ==========================================
        # 第二區：✍️ 新增組長交辦事項表單
        # ==========================================
        st.markdown("### ✍️ 新增組長交辦事項")
        with st.form("todo_input_form"):
            c1, c2 = st.columns(2)
            with c1:
                try:
                    default_idx = all_leaders_list.index(str(current_leader).strip())
                except:
                    default_idx = 0
                target_leader = st.selectbox("👤 負責組長", all_leaders_list, index=default_idx)
            with c2:
                # 保留日曆彈出視窗功能
                target_date_obj = st.date_input("📅 預計完成日期", value=datetime.date.today())
                target_deadline = target_date_obj.strftime("%Y-%m-%d")

            todo_content = st.text_area("📝 交辦事項內容 / 待辦備註", height=120, placeholder="請輸入需要交辦的事項內容...")
            submitted = st.form_submit_button("💾 儲存交辦事項", use_container_width=True)

            if submitted:
                if not todo_content.strip():
                    st.error("❌ 請輸入交辦事項內容，不能留空！")
                else:
                    payload = {
                        "組長": target_leader,
                        "交辦事項": todo_content.strip(),
                        "預計完成日期": target_deadline,
                        "建立時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    requests.post(f"{TODO_DB_URL}.json", data=json.dumps(payload))
                    st.success(f"✅ 已成功將交辦事項指派給 【{target_leader}】！")
                    time.sleep(0.5)
                    st.rerun()

        st.divider()

        # ==========================================
        # 第三區：🎉 已完成事項歷史紀錄
        # ==========================================
        st.markdown("### 🎉 已完成事項歷史紀錄")
        if done_raw:
            done_list = []
            for k, v in done_raw.items():
                row = v.copy()
                row["done_db_id"] = k
                done_list.append(row)
            
            done_df = pd.DataFrame(done_list)
            
            if not done_df.empty and filter_leader != "全部" and "組長" in done_df.columns:
                done_df = done_df[done_df["組長"] == filter_leader]
                
            if not done_df.empty:
                done_cols = ["組長", "交辦事項", "預計完成日期", "完成時間"]
                avail_done_cols = [c for c in done_cols if c in done_df.columns]
                
                st.dataframe(
                    done_df[avail_done_cols].sort_values(by="完成時間", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
                with st.expander("⚙️ 歷史紀錄清理區"):
                    for _, d_row in done_df.sort_values(by="完成時間", ascending=False).iterrows():
                        st.text(f"✔ {d_row.get('完成時間')} - 【{d_row.get('組長')}】{d_row.get('交辦事項')[:20]}...")
                        if st.button("🗑️ 永久抹除此完成紀錄", key=f"erase_done_{d_row['done_db_id']}"):
                            requests.delete(f"{TODO_DONE_URL}/{d_row['done_db_id']}.json")
                            st.success("紀錄已永久抹除！")
                            time.sleep(0.5)
                            st.rerun()
            else:
                st.info("💡 目前沒有對應組長的已完成事項紀錄。")
        else:
            st.info("💡 尚無任何已點選完成的事項紀錄，繼續大家辛苦了！")
    
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
