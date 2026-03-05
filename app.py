import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
USER_DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/users"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_users():
    try:
        r = requests.get(f"{USER_DB_URL}.json")
        data = r.json()
        if data and isinstance(data, dict): return data
        return {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澂": "000000"}
    except: return {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澂": "000000"}

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技工時登錄系統", layout="wide")
current_users = get_users()

if "user" not in st.session_state:
    st.title("🔐 超慧科技工時登錄系統")
    u = st.selectbox("選擇姓名", list(current_users.keys()))
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入", use_container_width=True):
        if u in current_users and p == current_users[u]:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    st.sidebar.markdown(f"## 👤 當前登錄者\n# {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢", "⚙️ 管理後台"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報 (維持原始計時器與表單) ---
    if menu == "🏗️ 工時回報":
        st.header(f"🏗️ {st.session_state.user} 的工時回報")
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時"):
                st.session_state.t1 = get_now_str()
                st.rerun()
            if c2.button("⏹️ 結束計時"):
                if 't1' in st.session_state:
                    st.session_state.t2 = get_now_str()
                    d1 = datetime.datetime.strptime(st.session_state.t1, "%Y-%m-%d %H:%M:%S")
                    d2 = datetime.datetime.strptime(st.session_state.t2, "%Y-%m-%d %H:%M:%S")
                    diff = d2 - d1
                    st.session_state.dur = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間"):
                for k in ['t1','t2','dur']: st.session_state.pop(k, None)
                st.rerun()
            
            t1_val = st.session_state.get('t1', '--')
            t2_val = st.session_state.get('t2', '--')
            st.markdown(f'<div style="display: flex; gap: 20px; margin-top: 10px;"><div style="background-color: #e8f4f8; padding: 10px 20px; border-radius: 10px; border-left: 5px solid #2980b9; flex: 1;"><span style="font-size: 14px; color: #555;">🕒 開始時間</span><br><b style="font-size: 18px; color: #2980b9;">{t1_val}</b></div><div style="background-color: #fff4e6; padding: 10px 20px; border-radius: 10px; border-left: 5px solid #e67e22; flex: 1;"><span style="font-size: 14px; color: #555;">⌛ 結束時間</span><br><b style="font-size: 18px; color: #e67e22;">{t2_val}</b></div></div>', unsafe_allow_html=True)

        with st.form("work_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('dur', "0小時 0分鐘"))
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log = {"姓名": st.session_state.user, "狀態": status, "製令": order, "PN": pn, "類型": tp, "工段名稱": stage, "累計工時": hours, "開始時間": st.session_state.get('t1', 'N/A'), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("✅ 紀錄已成功提交！")

    # --- 4. 歷史紀錄查詢 (核心修正：欄位大對齊) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄查詢")
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 資料區間篩選")
        today = datetime.date.today()
        start_date = st.sidebar.date_input("開始日期", today - datetime.timedelta(days=7))
        end_date = st.sidebar.date_input("結束日期", today)

        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                # 🛠️ 1. 強制讀取所有資料，不讓資料遺失
                raw_rows = []
                for k, v in data.items():
                    row = {"id": k}
                    row.update(v)
                    raw_rows.append(row)
                df = pd.DataFrame(raw_rows)

                # 🛠️ 2. 欄位大統一 (解決截圖中資料不見的問題)
                # 把所有舊的、英文的、帶冒號的欄位，全部合併到統一的名稱下
                mapping = {
                    "order_no": "製令", "製令:": "製令",
                    "pn": "PN", "PN:": "PN", "p/n": "PN",
                    "stage": "工段名稱", "工段名稱:": "工段名稱",
                    "status": "狀態", "狀態:": "狀態",
                    "type": "類型", "類型:": "類型", "Type": "類型",
                    "hours": "累計工時", "累計工時:": "累計工時",
                    "name": "姓名", "姓名:": "姓名",
                    "submit_time": "提交時間", "提交時間:": "提交時間", "time": "提交時間",
                    "start_time": "開始時間", "開始時間:": "開始時間", "startTime": "開始時間"
                }
                
                # 逐一處理對應，確保舊資料能顯示在新欄位
                for old_col, new_col in mapping.items():
                    if old_col in df.columns:
                        if new_col not in df.columns:
                            df[new_col] = df[old_col]
                        else:
                            # 如果兩個欄位都存在，把舊的填補到新的空缺處
                            df[new_col] = df[new_col].fillna(df[old_col])

                # 🛠️ 3. 只保留需要的標準欄位，並過濾掉重複與隱藏欄位
                final_cols = ["提交時間", "姓名", "狀態", "製令", "PN", "類型", "工段名稱", "累計工時", "開始時間"]
                # 只保留資料庫中確實存在的標準欄位
                existing_final_cols = [c for c in final_cols if c in df.columns]
                display_df = df[existing_final_cols].copy()
                
                # 🛠️ 4. 區間篩選與顯示
                if "提交時間" in display_df.columns:
                    display_df["提交時間"] = display_df["提交時間"].astype(str)
                    display_df["查詢日期"] = pd.to_datetime(display_df["提交時間"]).dt.date
                    mask = (display_df["查詢日期"] >= start_date) & (display_df["查詢日期"] <= end_date)
                    display_df = display_df.loc[mask].sort_values(by="提交時間", ascending=False)

                    st.info(f"📅 顯示區間：{start_date} 至 {end_date} (共 {len(display_df)} 筆紀錄)")
                    st.dataframe(display_df.drop(columns=['查詢日期'], errors='ignore'), use_container_width=True)
                    
                    st.write("---")
                    csv = display_df.drop(columns=['查詢日期'], errors='ignore').to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 匯出當前區間 CSV", data=csv, file_name=f"工時_{start_date}_{end_date}.csv")

                    with st.expander("🗑️ 刪除單筆紀錄"):
                        df_with_id = df.loc[mask].copy() # 帶有 ID 的資料
                        df_with_id["顯示選項"] = df_with_id["提交時間"].astype(str) + " (" + df_with_id["姓名"].astype(str) + ")"
                        selected = st.selectbox("請選擇要刪除的一筆紀錄", options=df_with_id["顯示選項"].tolist())
                        if st.button("確認刪除該筆資料", type="primary"):
                            tid = df_with_id[df_with_id["顯示選項"] == selected]["id"].values[0]
                            requests.delete(f"{DB_URL}/{tid}.json")
                            st.success("✅ 已刪除")
                            st.rerun()
            else: st.info("目前尚無資料。")
        except Exception as e: st.error(f"系統讀取發生錯誤：{e}")

    # --- 5. 管理後台 ---
    elif menu == "⚙️ 管理後台":
        st.header("⚙️ 人員帳號管理")
        with st.form("add_user_form"):
            st.subheader("➕ 新增人員")
            new_name = st.text_input("人員姓名")
            new_code = st.text_input("員工代碼 (密碼)")
            if st.form_submit_button("確認新增"):
                if new_name and new_code:
                    requests.patch(f"{USER_DB_URL}.json", json={new_name: new_code})
                    st.success(f"✅ 已新增人員：{new_name}")
                    st.rerun()
                else: st.warning("請填寫完整資訊")
        st.write("---")
        st.subheader("👤 現有人員清單")
        for name, code in current_users.items():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"👤 **{name}**")
            c2.write(f"🔑 `{code}`")
            if name != "管理員": 
                if c3.button("🗑️ 刪除", key=f"del_{name}"):
                    requests.delete(f"{USER_DB_URL}/{name}.json"); st.rerun()
