# --- 📜 完工紀錄查詢 ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data and isinstance(f_data, dict):
                all_finish_logs = [dict(v, id=k) for k, v in f_data.items() if v]
                f_df = pd.DataFrame(all_finish_logs).fillna("NA")

                st.markdown('<div class="search-panel">', unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                
                # 關鍵修改：移除 placeholder 之後的行為限制，text_input 預設就會在內容改變時觸發 rerun
                f_order_input = sc1.text_input("🔍 搜尋製令 (即時過濾)", value="", key="search_order_input")
                f_staff_s = sc2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 即時模糊搜尋邏輯：檢查輸入的文字是否包含在「製令」欄位中
                if f_order_input:
                    f_df = f_df[f_df["製令"].astype(str).str.contains(f_order_input, case=False, na=False)]
                
                if f_staff_s != "全部":
                    f_df = f_df[f_df[["人員1", "人員2", "人員3", "人員4", "人員5"]].apply(lambda x: f_staff_s in x.values, axis=1)]

                # 顯示過濾後的結果
                f_df = f_df.sort_values("完工時間", ascending=False)
                col_widths = [1.5, 1.2, 1.2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6]
                
                h_cols = st.columns(col_widths)
                headers = ["完工時間", "製令", "製造工序", "人員1", "人員2", "人員3", "人員4", "人員5", "管理"]
                for h_col, h_text in zip(h_cols, headers):
                    h_col.markdown(f'<div class="history-header">{h_text}</div>', unsafe_allow_html=True)

                for _, row in f_df.iterrows():
                    r_cols = st.columns(col_widths)
                    r_cols[0].write(row.get("完工時間", "NA"))
                    r_cols[1].write(row.get("製令", "NA"))
                    r_cols[2].write(row.get("製造工序", "NA"))
                    r_cols[3].write(row.get("人員1", "NA"))
                    r_cols[4].write(row.get("人員2", "NA"))
                    r_cols[5].write(row.get("人員3", "NA"))
                    r_cols[6].write(row.get("人員4", "NA"))
                    r_cols[7].write(row.get("人員5", "NA"))
                    
                    with r_cols[8]:
                        with st.popover("🗑️"):
                            st.write("確認刪除紀錄？")
                            pwd = st.text_input("輸入管理密碼", type="password", key=f"pwd_{row['id']}")
                            if st.button("確認執行", key=f"btn_{row['id']}"):
                                if pwd == "1111":
                                    requests.delete(f"{FINISH_URL}/{row['id']}.json")
                                    st.success("已刪除紀錄")
                                    st.rerun()
                                else: st.error("密碼錯誤")
            else: 
                st.info("💡 目前歷史紀錄為空")
        except Exception as e: 
            st.info(f"💡 目前無可顯示之歷史資料。")
