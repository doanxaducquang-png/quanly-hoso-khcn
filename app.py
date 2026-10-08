import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
from utils import (
    LIST_LINH_VUC, LIST_LOAI_HINH, LIST_HT_TRIEN_KHAI_1, LIST_HT_TRIEN_KHAI_2,
    LIST_HT_XET, LIST_PHAN_LOAI_CN, LIST_HOC_HAM, LIST_TRANG_THAI, LIST_NEN_TANG_SO,
    parse_bm09_word, load_data, save_new_record
)

st.set_page_config(page_title="Hệ thống Quản lý Hồ sơ KH&CN", page_icon="📊", layout="wide")

if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "show_validation_errors" not in st.session_state:
    st.session_state.show_validation_errors = False

st.title("📌 HỆ THỐNG QUẢN LÝ & BÁO CÁO HỒ SƠ ĐĂNG KÝ KH&CN")
st.markdown("---")

col_head1, col_head2 = st.columns([8, 2])
with col_head2:
    if st.button("🔄 Cập nhật dữ liệu từ Google Sheets"):
        st.cache_data.clear()
        st.rerun()

df_data = load_data()

def get_col_name(df, keyword):
    for col in df.columns:
        if keyword.lower() in col.lower():
            return col
    return None

def get_col_sum(df, keyword):
    col = get_col_name(df, keyword)
    return df[col].sum() if col else 0.0

tab_dashboard, tab_report, tab_search, tab_input = st.tabs([
    "📊 Dashboard Trực Quan", 
    "📑 Báo Cáo Tổng Hợp", 
    "🔍 Tra Cứu & Quản Lý Hồ Sơ", 
    "➕ Nhập Hồ Sơ Mới"
])

# =============================================================================
# TAB 1: DASHBOARD TRỰC QUAN
# =============================================================================
with tab_dashboard:
    st.header("📊 DASHBOARD TỔNG QUAN")
    if df_data.empty:
        st.warning("Chưa có dữ liệu trong Google Sheets hoặc không thể kết nối.")
    else:
        total_budget = get_col_sum(df_data, "Tổng kinh phí")
        total_nsnn = get_col_sum(df_data, "Kinh phí NSNN")
        total_ngoai = get_col_sum(df_data, "Ngoài NSNN")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng số hồ sơ", f"{len(df_data)} hồ sơ")
        c2.metric("Tổng kinh phí đề xuất", f"{total_budget:,.0f} VNĐ")
        c3.metric("Kinh phí NSNN", f"{total_nsnn:,.0f} VNĐ")
        c4.metric("Kinh phí Ngoài NSNN", f"{total_ngoai:,.0f} VNĐ")
        st.markdown("---")
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.subheader("1. Cơ cấu Kinh phí theo Lĩnh vực Nghiên cứu")
            col_lv = get_col_name(df_data, "lĩnh vực")
            col_nsnn = get_col_name(df_data, "Kinh phí NSNN")
            col_ngoai = get_col_name(df_data, "Ngoài NSNN")
            if col_lv and col_nsnn and col_ngoai:
                df_lv = df_data.groupby(col_lv)[[col_nsnn, col_ngoai]].sum().reset_index()
                fig_lv = px.bar(
                    df_lv, x=col_lv, y=[col_nsnn, col_ngoai],
                    title="Kinh phí NSNN & Ngoài NSNN theo Lĩnh vực", barmode="stack", text_auto='.2s',
                    color_discrete_sequence=["#1f77b4", "#ff7f0e"]
                )
                fig_lv.update_layout(xaxis_title="", yaxis_title="Kinh phí (VNĐ)", legend_title="Nguồn kinh phí")
                st.plotly_chart(fig_lv, use_container_width=True)

        with row1_col2:
            st.subheader("2. Số lượng hồ sơ theo Loại hình Nhiệm vụ")
            col_lh = get_col_name(df_data, "loại hình")
            if col_lh:
                df_lh = df_data[col_lh].value_counts().reset_index()
                df_lh.columns = ["Loại hình", "Số lượng"]
                fig_lh = px.pie(df_lh, names="Loại hình", values="Số lượng", title="Tỷ lệ Loại hình Nhiệm vụ", hole=0.4)
                st.plotly_chart(fig_lh, use_container_width=True)

        st.markdown("---")
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.subheader("3. Trình độ Chủ nhiệm Đề tài")
            col_hh = get_col_name(df_data, "học hàm") or get_col_name(df_data, "học vị")
            if col_hh:
                counts_hh = df_data[col_hh].astype(str).str.strip().value_counts()
                df_hh = pd.DataFrame({"Học hàm/Học vị": LIST_HOC_HAM})
                df_hh["Số lượng"] = df_hh["Học hàm/Học vị"].map(counts_hh).fillna(0).astype(int)
                fig_hh = px.bar(df_hh, x="Học hàm/Học vị", y="Số lượng", color="Học hàm/Học vị", text="Số lượng", category_orders={"Học hàm/Học vị": LIST_HOC_HAM})
                fig_hh.update_layout(showlegend=False, yaxis_title="Số lượng hồ sơ")
                st.plotly_chart(fig_hh, use_container_width=True)

        with row2_col2:
            st.subheader("4. Phân loại Chủ nhiệm Nhiệm vụ")
            col_pl = get_col_name(df_data, "phân loại chủ nhiệm")
            if col_pl:
                df_pl = df_data[col_pl].value_counts().reset_index()
                df_pl.columns = ["Phân loại", "Số lượng"]
                fig_pl = px.pie(df_pl, names="Phân loại", values="Số lượng", title="Phân loại Chủ nhiệm")
                st.plotly_chart(fig_pl, use_container_width=True)

        st.markdown("---")
        row3_col1, row3_col2, row3_col3 = st.columns(3)
        with row3_col1:
            st.subheader("5. Hình thức Triển khai 1")
            col_ht1 = get_col_name(df_data, "hình thức triển khai 1")
            if col_ht1:
                df_ht1 = df_data[col_ht1].value_counts().reset_index()
                df_ht1.columns = ["Hình thức 1", "Số lượng"]
                fig_ht1 = px.bar(df_ht1, x="Hình thức 1", y="Số lượng", color="Hình thức 1")
                fig_ht1.update_layout(showlegend=False)
                st.plotly_chart(fig_ht1, use_container_width=True)
            
        with row3_col2:
            st.subheader("6. Hình thức Xét")
            col_xet = get_col_name(df_data, "hình thức xét")
            if col_xet:
                df_xet = df_data[col_xet].value_counts().reset_index()
                df_xet.columns = ["Hình thức xét", "Số lượng"]
                fig_xet = px.pie(df_xet, names="Hình thức xét", values="Số lượng", hole=0.3)
                st.plotly_chart(fig_xet, use_container_width=True)

        with row3_col3:
            st.subheader("7. Trạng thái Hồ sơ")
            col_tt = get_col_name(df_data, "trạng thái")
            if col_tt:
                df_tt = df_data[col_tt].value_counts().reset_index()
                df_tt.columns = ["Trạng thái", "Số lượng"]
                fig_tt = px.bar(df_tt, x="Trạng thái", y="Số lượng", color="Trạng thái")
                fig_tt.update_layout(showlegend=False)
                st.plotly_chart(fig_tt, use_container_width=True)

# =============================================================================
# TAB 2: BÁO CÁO TỔNG HỢP (10 MỤC)
# =============================================================================
with tab_report:
    st.header("📑 BÁO CÁO TỔNG HỢP HỒ SƠ ĐĂNG KÝ CHỦ TRÌ NHIỆM VỤ KH&CN")
    st.caption("Dữ liệu được thống kê tự động dựa trên dữ liệu Google Sheets.")
    
    if not df_data.empty:
        col_lv = get_col_name(df_data, "lĩnh vực")
        col_lh = get_col_name(df_data, "loại hình")
        col_pl = get_col_name(df_data, "phân loại chủ nhiệm")
        col_ht1 = get_col_name(df_data, "hình thức triển khai 1")
        col_ht2 = get_col_name(df_data, "hình thức triển khai 2")
        col_xet = get_col_name(df_data, "hình thức xét")
        col_hh = get_col_name(df_data, "học hàm") or get_col_name(df_data, "học vị")
        col_tt = get_col_name(df_data, "trạng thái")
        col_tong = get_col_name(df_data, "Tổng kinh phí")
        col_nsnn = get_col_name(df_data, "Kinh phí NSNN")
        col_ngoai = get_col_name(df_data, "Ngoài NSNN")

        st.subheader("I. TỔNG QUAN HỒ SƠ & KINH PHÍ")
        st.table(pd.DataFrame([
            {"Chỉ tiêu": "1. Tổng số hồ sơ tiếp nhận", "Giá trị": f"{len(df_data)} hồ sơ"},
            {"Chỉ tiêu": "2. Tổng kinh phí đề xuất", "Giá trị": f"{get_col_sum(df_data, 'Tổng kinh phí'):,.0f} VNĐ"},
            {"Chỉ tiêu": "3. Tổng kinh phí Ngân sách nhà nước (NSNN)", "Giá trị": f"{get_col_sum(df_data, 'Kinh phí NSNN'):,.0f} VNĐ"},
            {"Chỉ tiêu": "4. Tổng kinh phí Ngoài NSNN", "Giá trị": f"{get_col_sum(df_data, 'Ngoài NSNN'):,.0f} VNĐ"},
        ]))

        st.subheader("II. THỐNG KÊ THEO LĨNH VỰC NGHIÊN CỨU")
        df_lv_stat = []
        for idx, lv in enumerate(LIST_LINH_VUC, 1):
            sub = df_data[df_data[col_lv] == lv] if col_lv else pd.DataFrame()
            df_lv_stat.append({
                "STT & Lĩnh vực": f"{idx}. {lv}",
                "Số lượng hồ sơ": len(sub),
                "Tổng kinh phí (VNĐ)": f"{sub[col_tong].sum():,.0f}" if col_tong and not sub.empty else "0",
                "Kinh phí NSNN (VNĐ)": f"{sub[col_nsnn].sum():,.0f}" if col_nsnn and not sub.empty else "0",
                "Kinh phí Ngoài NSNN (VNĐ)": f"{sub[col_ngoai].sum():,.0f}" if col_ngoai and not sub.empty else "0"
            })
        st.dataframe(pd.DataFrame(df_lv_stat), use_container_width=True, hide_index=True)

        st.subheader("III. THỐNG KÊ THEO LOẠI HÌNH NHIỆM VỤ")
        df_lh_stat = []
        for idx, lh in enumerate(LIST_LOAI_HINH, 1):
            sub = df_data[df_data[col_lh] == lh] if col_lh else pd.DataFrame()
            df_lh_stat.append({
                "STT & Loại hình": f"{idx}. {lh}",
                "Số lượng hồ sơ": len(sub),
                "Tổng kinh phí (VNĐ)": f"{sub[col_tong].sum():,.0f}" if col_tong and not sub.empty else "0",
                "Kinh phí NSNN (VNĐ)": f"{sub[col_nsnn].sum():,.0f}" if col_nsnn and not sub.empty else "0",
                "Kinh phí Ngoài NSNN (VNĐ)": f"{sub[col_ngoai].sum():,.0f}" if col_ngoai and not sub.empty else "0"
            })
        st.dataframe(pd.DataFrame(df_lh_stat), use_container_width=True, hide_index=True)

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.subheader("IV. PHÂN LOẠI CHỦ NHIỆM NHIỆM VỤ")
            df_cn_stat = []
            for idx, pl in enumerate(LIST_PHAN_LOAI_CN, 1):
                count = len(df_data[df_data[col_pl] == pl]) if col_pl else 0
                df_cn_stat.append({"Phân loại Chủ nhiệm": f"{idx}. {pl}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_cn_stat), use_container_width=True, hide_index=True)

        with col_r2:
            st.subheader("V. TÌNH TRẠNG CẬP NHẬT NỀN TẢNG SỐ QUỐC GIA")
            c_tl = get_col_name(df_data, "tư cách pháp lý")
            c_tt = get_col_name(df_data, "tổ chức đề xuất")
            c_ll = get_col_name(df_data, "lý lịch cá nhân")
            full_updated = 0
            if c_tl and c_tt and c_ll:
                full_updated = len(df_data[(df_data[c_tl] == "Đã cập nhật") & (df_data[c_tt] == "Đã cập nhật") & (df_data[c_ll] == "Đã cập nhật")])
            not_full = len(df_data) - full_updated
            st.table(pd.DataFrame([
                {"Tình trạng": "1. Hồ sơ đã cập nhật hoàn thiện (Cả 3 mục)", "Số lượng hồ sơ": full_updated},
                {"Tình trạng": "2. Hồ sơ chưa cập nhật đủ thông tin", "Số lượng hồ sơ": not_full}
            ]))

        col_r3, col_r4 = st.columns(2)
        with col_r3:
            st.subheader("VI. HÌNH THỨC TRIỂN KHAI 1")
            df_ht1_stat = []
            for idx, ht in enumerate(LIST_HT_TRIEN_KHAI_1, 1):
                count = len(df_data[df_data[col_ht1] == ht]) if col_ht1 else 0
                df_ht1_stat.append({"Hình thức triển khai 1": f"{idx}. {ht}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_ht1_stat), use_container_width=True, hide_index=True)

        with col_r4:
            st.subheader("VII. HÌNH THỨC TRIỂN KHAI 2")
            df_ht2_stat = []
            for idx, ht in enumerate(LIST_HT_TRIEN_KHAI_2, 1):
                count = len(df_data[df_data[col_ht2] == ht]) if col_ht2 else 0
                df_ht2_stat.append({"Hình thức triển khai 2": f"{idx}. {ht}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_ht2_stat), use_container_width=True, hide_index=True)

        col_r5, col_r6, col_r7 = st.columns(3)
        with col_r5:
            st.subheader("VIII. HÌNH THỨC XẾT")
            df_xet_stat = []
            for idx, hx in enumerate(LIST_HT_XET, 1):
                count = len(df_data[df_data[col_xet] == hx]) if col_xet else 0
                df_xet_stat.append({"Hình thức xét": f"{idx}. {hx}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_xet_stat), use_container_width=True, hide_index=True)

        with col_r6:
            st.subheader("IX. TRÌNH ĐỘ CHỦ NHIỆM ĐỀ TÀI")
            df_hh_stat = []
            for idx, hh in enumerate(LIST_HOC_HAM, 1):
                count = len(df_data[df_data[col_hh] == hh]) if col_hh else 0
                df_hh_stat.append({"Học hàm / Học vị": f"{idx}. {hh}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_hh_stat), use_container_width=True, hide_index=True)

        with col_r7:
            st.subheader("X. TRẠNG THÁI HỒ SƠ")
            df_tt_stat = []
            for idx, tt in enumerate(LIST_TRANG_THAI, 1):
                count = len(df_data[df_data[col_tt] == tt]) if col_tt else 0
                df_tt_stat.append({"Trạng thái hồ sơ": f"{idx}. {tt}", "Số lượng hồ sơ": count})
            st.dataframe(pd.DataFrame(df_tt_stat), use_container_width=True, hide_index=True)

# =============================================================================
# TAB 3: TRA CỨU HỒ SƠ & BỘ LỌC ĐA TIÊU CHÍ
# =============================================================================
with tab_search:
    st.header("🔍 TRA CỨU HỒ SƠ & XUẤT DỮ LIỆU EXCEL")
    
    if not df_data.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_data.to_excel(writer, index=False, sheet_name='QUAN_LY_HO_SO')
        
        st.download_button(
            label="📥 Tải File Excel Dữ Liệu Hiện Tại (Xuất từ Google Sheets)",
            data=buffer.getvalue(),
            file_name=f"QuanLy_DonDangKy_KHCN_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        st.markdown("---")

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            search_keyword = st.text_input("🔑 Tìm tên nhiệm vụ / Chủ nhiệm / Tổ chức:")
        with col_s2:
            filter_linhvuc = st.multiselect("📂 Lọc Lĩnh vực:", options=LIST_LINH_VUC)
        with col_s3:
            filter_trangthai = st.multiselect("📌 Lọc Trạng thái:", options=LIST_TRANG_THAI)
        with col_s4:
            filter_loaihinh = st.multiselect("🎯 Lọc Loại hình:", options=LIST_LOAI_HINH)

        df_filtered = df_data.copy()
        col_ten = get_col_name(df_data, "tên nhiệm vụ")
        col_cn = get_col_name(df_data, "chủ nhiệm")
        col_tc = get_col_name(df_data, "tổ chức")
        col_lv = get_col_name(df_data, "lĩnh vực")
        col_tt = get_col_name(df_data, "trạng thái")
        col_lh = get_col_name(df_data, "loại hình")

        if search_keyword:
            kw = search_keyword.lower()
            cond_ten = df_filtered[col_ten].astype(str).str.lower().str.contains(kw) if col_ten else False
            cond_cn = df_filtered[col_cn].astype(str).str.lower().str.contains(kw) if col_cn else False
            cond_tc = df_filtered[col_tc].astype(str).str.lower().str.contains(kw) if col_tc else False
            df_filtered = df_filtered[cond_ten | cond_cn | cond_tc]

        if filter_linhvuc and col_lv:
            df_filtered = df_filtered[df_filtered[col_lv].isin(filter_linhvuc)]
        if filter_trangthai and col_tt:
            df_filtered = df_filtered[df_filtered[col_tt].isin(filter_trangthai)]
        if filter_loaihinh and col_lh:
            df_filtered = df_filtered[df_filtered[col_lh].isin(filter_loaihinh)]

        st.write(f"**Kết quả lọc:** {len(df_filtered)} / {len(df_data)} hồ sơ")
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Chưa có hồ sơ nào trong hệ thống.")

# =============================================================================
# TAB 4: FORM NHẬP HỒ SƠ MỚI ĐẦY ĐỦ BM-09
# =============================================================================
with tab_input:
    st.header("➕ NHẬP HỒ SƠ MỚI VÀO HỆ THỐNG")
    
    st.subheader("📄 TỰ ĐỘNG ĐIỀN TỪ FILE WORD ĐƠN ĐĂNG KÝ (BM-09)")
    uploaded_docx = st.file_uploader("Tải lên file Word Đơn đăng ký (.docx):", type=["docx"])
    
    if uploaded_docx is not None:
        try:
            st.session_state.form_data.update(parse_bm09_word(uploaded_docx))
            st.success("🎉 Đã đọc tự động file Word BM-09 thành công!")
        except Exception as e:
            st.error(f"Lỗi đọc file Word: {e}")

    st.markdown("---")
    fd = st.session_state.form_data
    next_stt = len(df_data) + 1
    st.info(f"💡 **Thông báo:** Số thứ tự (STT) tiếp theo được gán tự động là: **{next_stt}**")

    # 1. Thông tin chung Nhiệm vụ
    st.subheader("1. Thông tin chung Nhiệm vụ")
    c1, c2 = st.columns(2)
    with c1:
        ten_nhiem_vu = st.text_area("Tên nhiệm vụ / Cụm / Chuỗi (*)", value=fd.get("ten_nhiem_vu", ""), placeholder="Nhập tên nhiệm vụ...")
        linh_vuc = st.selectbox("Lĩnh vực (*)", LIST_LINH_VUC, index=LIST_LINH_VUC.index(fd.get("linh_vuc", LIST_LINH_VUC[0])))
        loai_hinh = st.selectbox("Loại hình nhiệm vụ (*)", LIST_LOAI_HINH, index=LIST_LOAI_HINH.index(fd.get("loai_hinh", LIST_LOAI_HINH[0])))
    with c2:
        ht_tk1 = st.selectbox("Hình thức triển khai 1 (*)", LIST_HT_TRIEN_KHAI_1, index=LIST_HT_TRIEN_KHAI_1.index(fd.get("ht_tk1", LIST_HT_TRIEN_KHAI_1[0])))
        ht_tk2 = st.selectbox("Hình thức triển khai 2 (*)", LIST_HT_TRIEN_KHAI_2, index=LIST_HT_TRIEN_KHAI_2.index(fd.get("ht_tk2", LIST_HT_TRIEN_KHAI_2[2])))
        ht_xet = st.selectbox("Hình thức xét (*)", LIST_HT_XET, index=LIST_HT_XET.index(fd.get("ht_xet", LIST_HT_XET[0])))
        trang_thai = st.selectbox("Trạng thái hồ sơ (*)", LIST_TRANG_THAI, index=LIST_TRANG_THAI.index(fd.get("trang_thai", LIST_TRANG_THAI[0])))

    st.markdown("---")
    # 2. Thông tin Tổ chức Chủ trì
    st.subheader("2. Thông tin Tổ chức Chủ trì")
    c3, c4 = st.columns(2)
    with c3:
        ten_tc = st.text_input("Tên tổ chức chủ trì (*)", value=fd.get("ten_tc", ""))
        dc_tc = st.text_input("Địa chỉ tổ chức (*)", value=fd.get("dc_tc", ""))
        dt_tc = st.text_input("Điện thoại tổ chức (Không bắt buộc)", value=fd.get("dt_tc", ""))
    with c4:
        dd_pl = st.text_input("Người đại diện pháp luật (*)", value=fd.get("dd_pl", ""))
        chuc_vu_dd = st.text_input("Chức vụ người đại diện (*)", value=fd.get("chuc_vu_dd", ""))
        tl_phap_ly = st.selectbox("Tài liệu chứng minh tư cách pháp lý (Nền tảng số) (*)", LIST_NEN_TANG_SO, index=LIST_NEN_TANG_SO.index(fd.get("tl_phap_ly", LIST_NEN_TANG_SO[1])))
        tt_tc_de_xuat = st.selectbox("Thông tin về tổ chức đề xuất (Nền tảng số) (*)", LIST_NEN_TANG_SO, index=LIST_NEN_TANG_SO.index(fd.get("tt_tc_de_xuat", LIST_NEN_TANG_SO[1])))

    st.markdown("---")
    # 3. Thông tin Chủ nhiệm Nhiệm vụ
    st.subheader("3. Thông tin Chủ nhiệm Nhiệm vụ")
    c5, c6 = st.columns(2)
    with c5:
        ho_ten_cn = st.text_input("Họ tên Chủ nhiệm (*)", value=fd.get("ho_ten_cn", ""))
        phan_loai_cn = st.selectbox("Phân loại Chủ nhiệm (*)", LIST_PHAN_LOAI_CN, index=LIST_PHAN_LOAI_CN.index(fd.get("phan_loai_cn", LIST_PHAN_LOAI_CN[2])))
        hoc_ham_hoc_vi = st.selectbox("Học hàm, học vị (*)", LIST_HOC_HAM, index=LIST_HOC_HAM.index(fd.get("hoc_ham_hoc_vi", LIST_HOC_HAM[2])))
        don_vi_ct = st.text_input("Đơn vị công tác (*)", value=fd.get("don_vi_ct", ""))
    with c6:
        email_cn = st.text_input("Email Chủ nhiệm (Không bắt buộc)", value=fd.get("email_cn", ""))
        dt_cn = st.text_input("Điện thoại Chủ nhiệm (*)", value=fd.get("dt_cn", ""))
        ly_lich_cn = st.selectbox("Lý lịch cá nhân (Nền tảng số) (*)", LIST_NEN_TANG_SO, index=LIST_NEN_TANG_SO.index(fd.get("ly_lich_cn", LIST_NEN_TANG_SO[1])))

    st.markdown("---")
    # 4. Kinh phí & Thời gian Thực hiện
    st.subheader("4. Kinh phí & Thời gian Thực hiện")
    c7, c8 = st.columns(2)
    with c7:
        tong_kinh_phi = st.number_input("Tổng kinh phí đề xuất (VNĐ) (*)", min_value=0.0, value=float(fd.get("tong_kinh_phi", 0.0)), step=1000000.0, format="%.0f")
        kinh_phi_nsnn = st.number_input("Kinh phí Ngân sách Nhà nước (NSNN) (VNĐ) (*)", min_value=0.0, value=float(fd.get("kinh_phi_nsnn", 0.0)), step=1000000.0, format="%.0f")
    with c8:
        kinh_phi_ngoai_nsnn = st.number_input("Kinh phí Ngoài NSNN (VNĐ) (Tự động tính)", min_value=0.0, value=max(0.0, tong_kinh_phi - kinh_phi_nsnn), step=1000000.0, format="%.0f", disabled=True)
        thoi_gian_th = st.number_input("Thời gian thực hiện (Tháng) (*)", min_value=1, value=int(fd.get("thoi_gian_th", 12)))

    ty_le_nsnn = (kinh_phi_nsnn / tong_kinh_phi) if tong_kinh_phi > 0 else 0.0
    ty_le_ngoai_nsnn = (kinh_phi_ngoai_nsnn / tong_kinh_phi) if tong_kinh_phi > 0 else 0.0
    st.info(f"📊 **Hệ thống tự động tính tỷ lệ:** Tỷ lệ NSNN: **{ty_le_nsnn*100:.2f}%** | Tỷ lệ Ngoài NSNN: **{ty_le_ngoai_nsnn*100:.2f}%**")

    st.markdown("---")
    if st.button("💾 LƯU HỒ SƠ VÀO GOOGLE SHEETS", type="primary", use_container_width=True):
        if not ten_nhiem_vu or not ten_tc or not ho_ten_cn or tong_kinh_phi <= 0:
            st.error("🚫 Vui lòng điền đầy đủ các thông tin bắt buộc!")
        else:
            new_data = {
                "STT": next_stt,
                "Tên nhiệm vụ / Cụm / Chuỗi": ten_nhiem_vu,
                "Lĩnh vực": linh_vuc,
                "Loại hình nhiệm vụ": loai_hinh,
                "Hình thức triển khai 1": ht_tk1,
                "Hình thức triển khai 2": ht_tk2,
                "Hình thức xét": ht_xet,
                "Tên tổ chức chủ trì": ten_tc,
                "Địa chỉ tổ chức": dc_tc,
                "Điện thoại tổ chức": dt_tc,
                "Người đại diện pháp luật": dd_pl,
                "Chức vụ người đại diện": chuc_vu_dd,
                "Tài liệu chứng minh tư cách pháp lý (Nền tảng số)": tl_phap_ly,
                "Thông tin về tổ chức đề xuất (Nền tảng số)": tt_tc_de_xuat,
                "Phân loại Chủ nhiệm": phan_loai_cn,
                "Họ tên Chủ nhiệm": ho_ten_cn,
                "Học hàm, học vị": hoc_ham_hoc_vi,
                "Đơn vị công tác": don_vi_ct,
                "Email Chủ nhiệm": email_cn,
                "Điện thoại Chủ nhiệm": dt_cn,
                "Lý lịch cá nhân (Nền tảng số)": ly_lich_cn,
                "Tổng kinh phí đề xuất (VNĐ)": tong_kinh_phi,
                "Tỷ lệ NSNN (%)": f"{ty_le_nsnn*100:.2f}%",
                "Kinh phí NSNN (VNĐ)": kinh_phi_nsnn,
                "Tỷ lệ Ngoài NSNN (%)": f"{ty_le_ngoai_nsnn*100:.2f}%",
                "Kinh phí Ngoài NSNN (VNĐ)": kinh_phi_ngoai_nsnn,
                "Thời gian thực hiện (Tháng)": thoi_gian_th,
                "Trạng thái hồ sơ": trang_thai
            }
            ok, msg = save_new_record(new_data)
            if ok:
                st.success(msg)
                st.balloons()
                st.session_state.form_data = {}
                st.rerun()
            else:
                st.error(msg)