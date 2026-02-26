import streamlit as st
import pandas as pd
import datetime
import requests

# ==============================
# 1. 設定區
# ==============================
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"


# ==============================
# 2. Firebase 讀寫
# ==============================
def get_db(path):
    try:
        response = requests.get(f"{DB_URL}{path}.json")
        return response.json()
    except:
        return None


def save_db(path, data, method="post"):
    try:
        if method == "post":
            requests.post(f"{DB_URL}{path}.json", json=data)
        else:
            requests.put(f"{DB_URL}{path}.json", json=data)
    except:
        pass


# ==============================
# 3. 頁面配置
# ==============================
st.set_page_config(page_title="數位戰情室", layout="wide")

raw_users = get_db("users")

STAFF_DATA = {"管理員": "8888"}  # 永久保留管理員
if raw_users:
    STAFF_DATA.update(raw_users)


# ==============================
# 4. 登入系統
# ==============================
if "user" not in st.session_state:

    st.title("🔐 員工系統登入")

    with st.form("login"):
        input_name = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("輸入代碼", type="password")

        if st.form_submit_button("進入系統", use_container_width=True):
            if str(STAFF_DATA.get(input_name)) == input_code:
                st.session_state.user = input_name
                st.rerun()
            else:
                st.error("❌ 代碼錯誤")

# ==============================
# 5. 主系統
# ==============================
else:

    # ---------- 左側選單 ----------
    st.sidebar.title(f"👤 {st.session_state.user}")

    options = ["🏗️ 工時回報"]
    if st.session_state.user == "管理員":
        options += ["⚙️ 系統帳號管理", "📊 完整工時報表"]

    menu = st.sidebar.radio("功能選單", options)

    st.sidebar.divider()

    if st.sidebar.button("🚪 登出系統", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # =========================================================
    # A. 工時回報頁面
    # =========================================================
    if menu == "🏗️ 工時回報":

        st.header("🏗️ 生產日報回報")

        # 初始化 calc_hours（避免第一次報錯）
        if "calc_hours" not in st.session_state:
            st.session_state.calc_hours = 0.0

        # --------------------------
        # 工時計時器
        # --------------------------
        with st.expander("⏱️ 工時計時器", expanded=True):

            col_a, col_b = st.columns(2)

            if col_a.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.work_start = datetime.datetime.now()

            if col_b.button("⏹️ 結束計時", use_container_width=True):
                if "work_start" in st.session_state:
                    work_end = datetime.datetime.now()
                    duration = work_end - st.session_state.work_start

                    # ⭐ 直接寫入累計工時（取代綠色提示）
                    st.session_state.calc_hours = round(
                        duration.total_seconds() / 3600, 2
                    )
                else:
                    st.warning("請先按下『開始計時』")

        # --------------------------
        # 10欄位報工表單
        # --------------------------
        with st.form("work_form"):

            user_code = STAFF_DATA.get(st.session_state.user, "N/A")

            c1, c2, c3 = st.columns(3)
            status = c1.selectbox("狀態", ["作業中", "暫停", "下班", "完工"])
            order_no = c2.text_input("製令")
            pn = c3.text_input("P/N")

            c4, c5, c6 = st.columns(3)
            prod_type = c4.text_input("Type")
            stage = c5.text_input("工段名稱")

            # ⭐⭐⭐ 重點修改區（自動同步工時）
            hours = c6.number_input(
                "累計工時 (hr)",
                min_value=0.0,
                step=0.01,
                key="calc_hours"
            )

            st.write(f"📌 **工號：** {user_code} | **姓名：** {st.session_state.user}")

            start_str = st.session_state.get(
                "work_start",
                datetime.datetime.now()
            ).strftime("%Y-%m-%d %H:%M:%S")

            st.write(f"⏰ **本次開始時間：** {start_str}")

            # ---------- 提交 ----------
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):

                final_end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                log_data = {
                    "狀態": status,
                    "製令": order_no,
                    "P/N": pn,
                    "Type": prod_type,
                    "工段名稱": stage,
                    "工號": user_code,
                    "姓名": st.session_state.user,
                    "開始時間": start_str,
                    "結束時間": final_end,
                    "累計工時": hours,
                }

                save_db("work_logs", log_data)

                st.success("✅ 紀錄已成功提交！")
                st.session_state.calc_hours = 0.0
                st.balloons()

    # =========================================================
    # B. 帳號管理
    # =========================================================
    elif menu == "⚙️ 系統帳號管理":

        st.header("👤 系統帳號管理 (新增人員)")

        with st.container(border=True):

            new_n = st.text_input("新員工姓名")
            new_c = st.text_input("設定員工工號")

            if st.button("➕ 建立帳號並同步", use_container_width=True):
                if new_n and new_c:
                    save_db(f"users/{new_n}", new_c, method="put")
                    st.success(f"✅ 員工「{new_n}」帳號已建立！")
                    st.rerun()

    # =========================================================
    # C. 報表頁面
    # =========================================================
    elif menu == "📊 完整工時報表":

        st.header("📊 完整工時報表")

        raw_logs = get_db("work_logs")

        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient="index")

            cols = [
                "狀態", "製令", "P/N", "Type", "工段名稱",
                "工號", "姓名", "開始時間", "結束時間", "累計工時"
            ]

            existing = [c for c in cols if c in df.columns]

            df_display = df[existing]

            if "結束時間" in df_display.columns:
                df_display = df_display.sort_values(by="結束時間", ascending=False)

            st.dataframe(df_display, use_container_width=True)

        else:
            st.info("目前尚無報工紀錄。")
