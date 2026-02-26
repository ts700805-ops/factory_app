import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

# --- 2. 登入系統 ---
st.set_page_config(page_title="超慧科技工時登錄系統", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 超慧科技工時登錄系統")
    # ✅ 嚴格核對姓名：黃沂澂
    u = st.selectbox("選擇姓名", ["管理員", "李小龍", "賴智文", "黃沂澂"])
    p = st.text_input("輸入員工代碼", type="password")
    if st.button("登入", use_container_width=True):
        codes = {"管理員": "8888", "李小龍": "1234", "賴智文": "098057", "黃沂澂": "000000"}
        if u in codes and p == codes[u]:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ 代碼錯誤")
else:
    st.sidebar.markdown(f"## 👤 當前登錄者\n# {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報 ---
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
            
            # ✅ 重新設計的顯示區塊：增加間距、底色與邊框
            t1_val = st.session_state.get('t1', '--')
            t2_val = st.session_state.get('t2', '--')
            st.markdown(f"""
                <div style="display: flex; gap: 20px; margin-top: 10px;">
                    <div style="background-color: #e8f4f8; padding: 10px 20px; border-radius: 10px; border-left: 5px solid #2980b9; flex: 1;">
                        <span style="font-size: 14px; color: #555;">🕒 開始時間</span><br>
                        <b style="font-size: 18px; color: #2980b9;">{t1_val}</b>
                    </div>
                    <div style="background-color: #fff4e6; padding: 10px 20px; border-radius: 10px; border-left: 5px solid #e67e22; flex: 1;">
                        <span style="font-size: 14px; color: #555;">⌛ 結束時間</span><br>
                        <b style="font-size: 18px; color: #e67e22;">{t2_val}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

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
                log = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order,
                    "PN": pn, "類型": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": st.session_state.get('t1', 'N/A'),
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", json=log)
                st.success("✅ 紀錄已成功提交！")

    # --- 4. 歷史紀錄查詢 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 系統提交紀錄清單")
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                df = pd.DataFrame([{"id": k, **v} for k, v in data.items()])
                rename_map = {
                    "name": "姓名", "hours": "累計工時", "order_no": "製令", "製令:": "製令",
                    "pn": "PN", "PN:": "PN", "stage": "工段名稱", "工段名稱:": "工段名稱",
                    "status": "狀態", "狀態:": "狀態", "type": "類型", "類型:": "類型",
                    "submit_time": "提交時間", "time": "提交時間", "提交時間:": "提交時間",
                    "start_time": "開始時間", "startTime": "開始時間", "開始時間:": "開始時間",
                    "累計工時:": "累計工時", "姓名:": "姓名"
                }
                df = df.rename(columns=rename_map)
                df = df.stack().unstack()
                df = df.loc[:, ~df.columns.duplicated()]
                if "提交時間" in df.columns:
                    df = df.sort_values(by="提交時間", ascending=False)

                st.dataframe(df.drop(columns=['id', '顯示選項'], errors='ignore'), use_container_width=True)
                st.write("---")
                
                col_btn1, col_btn2 = st.columns([2, 3])
                csv = df.drop(columns=['id', '顯示選項'], errors='ignore').to_csv(index=False).encode('utf-8-sig')
                col_btn1.download_button("📥 匯出 CSV 檔", data=csv, file_name=f"工時紀錄_{get_now_str()}.csv", mime="text/csv")

                with st.expander("🗑️ 刪除單筆紀錄"):
                    df["顯示選項"] = df["提交時間"] + " (" + df["姓名"] + ")"
                    selected_option = st.selectbox("請選擇要刪除的一筆紀錄", options=df["顯示選項"].tolist())
                    if st.button("確認刪除該筆資料", type="primary"):
                        target_key = df[df["顯示選項"] == selected_option]["id"].values[0]
                        del_r = requests.delete(f"{DB_URL}/{target_key}.json")
                        if del_r.status_code == 200:
                            st.success(f"✅ 已成功刪除紀錄")
                            st.rerun()
                        else: st.error("❌ 刪除失敗")
            else: st.info("目前尚無資料。")
        except Exception as e: st.error(f"讀取失敗：{e}")
