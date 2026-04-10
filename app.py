import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
USER_DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/users"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_users():
    try:
        r = requests.get(f"{USER_DB_URL}.json")
        data = r.json()
        if data and isinstance(data, dict): return list(data.keys())
        return ["管理員", "賴智文", "黃沂澂"]
    except: return ["管理員", "賴智文", "黃沂澂"]

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json")
        data = r.json()
        return data if data else {"orders": []}
    except: return {"orders": []}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; }
    .stat-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-top: 5px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    user_list = get_users()
    u = st.selectbox("登入者姓名", user_list)
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航", use_container_width=True):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if '作業人員' in df.columns else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:40px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                st.write("")
                st.subheader("📑 派工明細清單")
                st.dataframe(df[["製令", "派工人員", "作業人員", "作業期限"]], use_container_width=True, height=500)
            else:
                st.info("目前尚無派工資料。")
        except: st.error("連線資料庫失敗")

    # --- 4. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        current_settings = get_settings()
        user_list = get_users()
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", current_settings.get("orders", ["(請設定製令)"]))
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", user_list, index=user_list.index(st.session_state.user) if st.session_state.user in user_list else 0)
            worker = c2.selectbox("👷 作業人員", user_list)
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務", use_container_width=True):
                log = {"製令": order_no, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務發布成功！")

    # --- 5. ⚙️ 系統內容管理 (後台：管理首頁紀錄 + 喜歡的製令編輯模式) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統內容維護後台")
        
        # 部份一：編輯/刪除 經營者看板上的紀錄 (針對老闆看的內容)
        st.subheader("📊 編輯經營者看板紀錄")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [{"id": k, **v} for k, v in db_data.items()]
                log_df = pd.DataFrame(all_logs)
                
                selected_log_id = st.selectbox("選擇要修改或刪除的紀錄 (依製令)", all_logs, format_func=lambda x: f"{x['製令']} - {x['作業人員']} ({x['作業期限']})")
                
                with st.expander("🛠️ 執行修改/刪除操作"):
                    c1, c2 = st.columns(2)
                    new_worker = c1.selectbox("修改作業人員", get_users(), index=get_users().index(selected_log_id['作業人員']) if selected_log_id['作業人員'] in get_users() else 0)
                    new_deadline = c2.date_input("修改作業期限", datetime.datetime.strptime(selected_log_id['作業期限'], '%Y-%m-%d').date())
                    
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.button("💾 儲存修改內容", use_container_width=True):
                        updated_data = {"作業人員": new_worker, "作業期限": str(new_deadline)}
                        requests.patch(f"{DB_URL}/{selected_log_id['id']}.json", json=updated_data)
                        st.success("紀錄已更新！")
                        st.rerun()
                    
                    if col_btn2.button("🗑️ 刪除此筆紀錄", use_container_width=True):
                        requests.delete(f"{DB_URL}/{selected_log_id['id']}.json")
                        st.warning("紀錄已從看板移除。")
                        st.rerun()
            else:
                st.info("看板目前沒有可管理的紀錄。")
        except: st.error("讀取紀錄失敗")

        st.write("---")

        # 部份二：您最喜歡的製令編輯模式 (大框框、逗號隔開)
        st.subheader("📦 下拉選單製令清單管理")
        current_settings = get_settings()
        with st.form("favorite_edit_mode"):
            existing_str = ",".join(current_settings.get("orders", []))
            new_orders_raw = st.text_area("編輯製令清單 (請用英文逗號 , 隔開)", value=existing_str, height=150)
            if st.form_submit_button("✅ 儲存並更新所有選單項目"):
                new_list = [x.strip() for x in new_orders_raw.split(",") if x.strip()]
                requests.patch(f"{SETTING_URL}.json", json={"orders": new_list})
                st.success("選單項目已重新同步！")
                st.rerun()
