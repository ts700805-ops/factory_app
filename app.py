import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 (修正連線容錯) ---
# 這裡使用 Firebase 連結，確保設定為 public 即可免授權存取
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    """從資料庫抓取人員與工序清單，若失敗則回傳預設值以防止選單消失"""
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if not data: 
                return {"all_staff": ["管理員"], "processes": ["預設工序"]}
            
            # 確保必要欄位存在，避免 JSON 解析成功但內容缺失
            if "all_staff" not in data or not data["all_staff"]: 
                data["all_staff"] = ["管理員"]
            if "processes" not in data or not data["processes"]: 
                data["processes"] = ["預設工序"]
            return data
        else:
            return {"all_staff": ["管理員"], "processes": ["預設工序"]}
    except Exception as e:
        # 當網路斷線或 URL 錯誤時，這裡保證程式不會閃退
        return {"all_staff": ["管理員", "測試人員"], "processes": ["預設工序"]}

# --- 2. 頁面配置 (樣式維持原本設計) ---
st.set_page_config(page_title="大量科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 20px; }
    
    /* 製令看板卡片 */
    .order-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-top: 10px solid #1E3A8A;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .order-title { font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 15px; }
    
    /* 工序網格佈局 */
    .process-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
    }
    .process-box {
        background: #f8fafc;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .process-name { font-size: 14px; color: #64748b; margin-bottom: 5px; }
    .worker-name { font-size: 16px; font-weight: bold; color: #1e40af; }
    .na-tag { color: #cbd5e1; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# 讀取設定 (人員與工序)
settings = get_settings()
all_staff = settings.get("all_staff", ["管理員"])
process_list = settings.get("processes", ["預設工序"])

# 登入機制
if "user" not in st.session_state:
    st.title("⚓ 製造部控制塔台 - 登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("啟航登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁進度)", "📝 愛的派工中心", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁) ---
    if menu == "📊 控制塔台 (首頁進度)":
        st.markdown('<p class="main-title">📊 大量科技●控制塔台看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v]
                df = pd.DataFrame(all_logs)
                unique_orders = df["製令"].unique()
                
                for order in unique_orders:
                    order_df = df[df["製令"] == order]
                    st.markdown(f'''
                    <div class="order-container">
                        <div class="order-title">📦 製令單：{order}</div>
                        <div class="process-grid">
                    ''', unsafe_allow_html=True)
                    
                    for proc in process_list:
                        matched = order_df[order_df["製造工序"] == proc]
                        if not matched.empty:
                            worker_display = matched.iloc[0].get("人員1", "未知")
                            html_worker = f'<span class="worker-name">{worker_display}</span>'
                        else:
                            html_worker = '<span class="na-tag">NA</span>'
                        
                        st.markdown(f'''
                            <div class="process-box">
                                <div class="process-name">{proc}</div>
                                {html_worker}
                            </div>
                        ''', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("目前無任何派工紀錄。")
        except Exception as e:
            st.error(f"資料讀取失敗，請檢查網路連線。")

    # --- 4. 📝 愛的派工中心 (修正下拉選單) ---
    elif menu == "📝 愛的派工中心":
        st.markdown('<p class="main-title">📝 愛的派工中心 (新任務)</p>', unsafe_allow_html=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.text_input("📦 輸入製令編號", placeholder="例如: 1111")
            # 這裡的 process_list 是從 get_settings 抓來的
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.markdown("---")
            st.subheader("👥 主要人員與派工人員配置 (共5位)")
            pc1, pc2, pc3, pc4, pc5 = st.columns(5)
            # 確保選單資料 all_staff 存在
            w1 = pc1.selectbox("人員 1 (主)", all_staff, key="w1")
            w2 = pc2.selectbox("人員 2", all_staff, key="w2")
            w3 = pc3.selectbox("人員 3", all_staff, key="w3")
            w4 = pc4.selectbox("人員 4", all_staff, key="w4")
            w5 = pc5.selectbox("人員 5", all_staff, key="w5")
            
            # 自動帶入登入者作為派工人員
            user_idx = all_staff.index(st.session_state.user) if st.session_state.user in all_staff else 0
            assigner = st.selectbox("🚩 指定派工人員", all_staff, index=user_idx)
            
            if st.form_submit_button("🚀 發布任務"):
                if not order_no:
                    st.error("請輸入製令編號！")
                else:
                    log = {
                        "製令": order_no,
                        "製造工序": proc_name,
                        "人員1": w1, "人員2": w2, "人員3": w3, "人員4": w4, "人員5": w5,
                        "派工人員": assigner,
                        "提交時間": get_now_str()
                    }
                    try:
                        resp = requests.post(f"{DB_URL}.json", json=log, timeout=5)
                        if resp.status_code == 200:
                            st.success(f"製令 {order_no} 已同步至控制塔台！")
                            st.balloons()
                        else:
                            st.error(f"發送失敗，錯誤代碼：{resp.status_code}")
                    except:
                        st.error("發送失敗，請檢查資料庫連線。")

    # --- 5. 📝 編輯派工紀錄 ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 派工紀錄管理")
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')} - {log.get('人員1')}" for log in all_logs}
                target_id = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                
                if curr:
                    with st.expander("📝 編輯人員與資訊", expanded=True):
                        # 動態對齊索引值，避免找不到工序時報錯
                        def get_idx(val, lst):
                            return lst.index(val) if val in lst else 0

                        edit_proc = st.selectbox("修改工序", process_list, index=get_idx(curr.get('製造工序'), process_list))
                        
                        st.write("修改主要人員清單：")
                        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                        nw1 = ec1.selectbox("人員1", all_staff, index=get_idx(curr.get('人員1'), all_staff))
                        nw2 = ec2.selectbox("人員2", all_staff, index=get_idx(curr.get('人員2'), all_staff))
                        nw3 = ec3.selectbox("人員3", all_staff, index=get_idx(curr.get('人員3'), all_staff))
                        nw4 = ec4.selectbox("人員4", all_staff, index=get_idx(curr.get('人員4'), all_staff))
                        nw5 = ec5.selectbox("人員5", all_staff, index=get_idx(curr.get('人員5'), all_staff))
                        
                        if st.button("💾 儲存修改"):
                            update_data = {
                                "製造工序": edit_proc,
                                "人員1": nw1, "人員2": nw2, "人員3": nw3, "人員4": nw4, "人員5": nw5
                            }
                            requests.patch(f"{DB_URL}/{target_id}.json", json=update_data)
                            st.success("已更新！")
                            st.rerun()
                    
                    if st.button("🗑️ 刪除此筆紀錄", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json")
                        st.rerun()
            else:
                st.info("無待辦紀錄。")
        except:
            st.error("讀取錯誤")

    # --- 6. ⚙️ 系統內容管理 (這裡控制下拉選單的源頭) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統名單設定")
        with st.form("sys_config"):
            st.info("💡 這裡輸入的名單會直接影響「愛的派工中心」與「編輯」選單的選項內容。")
            st.write("⚠️ 注意：多個人員請以半形逗號 `,` 分隔")
            
            # 使用目前的 all_staff 作為預設顯示內容
            all_staff_str = st.text_area("👥 全體人員名單管理", value=",".join(all_staff))
            new_processes = st.text_area("⚙️ 編輯工序清單", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並更新所有選單"):
                new_data = {
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                # 使用 patch 更新 Firebase 內的 settings
                try:
                    requests.patch(f"{SETTING_URL}.json", json=new_data, timeout=5)
                    st.success("系統設定已成功更新！下拉選單現在應已恢復正常。")
                    st.rerun()
                except:
                    st.error("儲存失敗，請檢查資料庫權限或網路連線。")
