import streamlit as st
import pandas as pd


def render_top_filters(df, key_prefix="default"):
    """
    Filter cascading:

    Bulan
       ↓
    Unit Name
       ↓
    Nama Department
       ↓
    Nama Layanan

    Ketika Unit dipilih:
    - Department hanya menampilkan department yang ada di Unit tersebut
    - Layanan hanya menampilkan layanan yang ada di Unit tersebut

    Ketika Department dipilih:
    - Layanan semakin dipersempit berdasarkan Unit + Department
    """

    if df is None or df.empty:
        return df

    df_working = df.copy()

    # ============================================================
    # HELPER: CARI NAMA KOLOM
    # ============================================================

    def find_column(possible_names):
        for col in df_working.columns:
            col_clean = str(col).strip().lower().replace(" ", "_")

            if col_clean in possible_names:
                return col

        return None

    # ============================================================
    # CARI KOLOM
    # ============================================================

    service_col = find_column([
        "service_name",
        "service",
        "nama_layanan",
        "layanan"
    ])

    dept_col = find_column([
        "department",
        "dept",
        "nama_department"
    ])

    unit_col = find_column([
        "unit_name",
        "unit",
        "nama_unit",
        "unitname"
    ])

    # ============================================================
    # KEY WIDGET
    # ============================================================

    month_key = f"{key_prefix}_f_month"
    unit_key = f"{key_prefix}_f_unit"
    dept_key = f"{key_prefix}_f_dept"
    service_key = f"{key_prefix}_f_service"

    # ============================================================
    # 1. PREPARE DATE / BULAN
    # ============================================================

    date_col = None

    if "date_created_at" in df_working.columns:
        date_col = "date_created_at"

    elif "Date" in df_working.columns:
        date_col = "Date"

    else:
        for col in df_working.columns:
            if str(col).strip().lower() in [
                "created_at",
                "created_date",
                "tanggal",
                "date"
            ]:
                date_col = col
                break

    if date_col:

        # Kalau sudah datetime, jangan parsing ulang
        if pd.api.types.is_datetime64_any_dtype(df_working[date_col]):
            df_working["datetime_filter"] = df_working[date_col]

        else:
            df_working["datetime_filter"] = pd.to_datetime(
                df_working[date_col],
                format="%d.%m.%Y %H:%M:%S",
                errors="coerce"
            )

            # Fallback kalau format berbeda
            null_mask = df_working["datetime_filter"].isna()

            if null_mask.any():
                df_working.loc[null_mask, "datetime_filter"] = (
                    pd.to_datetime(
                        df_working.loc[null_mask, date_col],
                        dayfirst=True,
                        errors="coerce"
                    )
                )

        df_valid = df_working.dropna(
            subset=["datetime_filter"]
        ).copy()

        if not df_valid.empty:

            df_valid["sort_key"] = (
                df_valid["datetime_filter"]
                .dt.strftime("%Y-%m")
            )

            df_valid["month_fmt"] = (
                df_valid["datetime_filter"]
                .dt.strftime("%B %Y")
            )

            unique_months = (
                df_valid[
                    ["sort_key", "month_fmt"]
                ]
                .drop_duplicates()
                .sort_values("sort_key")
                ["month_fmt"]
                .tolist()
            )

            month_list = ["All"] + unique_months

            df_working["month_filter_name"] = (
                df_working["datetime_filter"]
                .dt.strftime("%B %Y")
            )

        else:
            month_list = ["All"]

    else:
        month_list = ["All"]

    # ============================================================
    # COLUMNS UI
    # ============================================================

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # ============================================================
    # 2. BULAN
    # ============================================================

    with col_f1:

        if (
            month_key in st.session_state
            and st.session_state[month_key] not in month_list
        ):
            st.session_state[month_key] = "All"

        selected_month = st.selectbox(
            "Bulan",
            month_list,
            key=month_key
        )

    # ============================================================
    # 3. UNIT NAME
    #
    # UNIT HARUS DIPILIH TERLEBIH DAHULU
    # karena Department dan Service bergantung pada Unit.
    # ============================================================

    if unit_col:

        unit_list = (
            ["All"] +
            sorted(
                df_working[unit_col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    else:
        unit_list = ["All"]

    # Pastikan session state masih valid
    if (
        unit_key in st.session_state
        and st.session_state[unit_key] not in unit_list
    ):
        st.session_state[unit_key] = "All"

    # Render di kolom ke-4
    with col_f4:

        selected_unit = st.selectbox(
            "Unit Name",
            unit_list,
            key=unit_key
        )

    # ============================================================
    # DATASET SETELAH FILTER UNIT
    # ============================================================

    df_after_unit = df_working.copy()

    if selected_unit != "All" and unit_col:

        df_after_unit = df_after_unit[
            df_after_unit[unit_col]
            .astype(str)
            == selected_unit
        ]

    # ============================================================
    # 4. DEPARTMENT
    #
    # DEPARTMENT SEKARANG MENGIKUTI UNIT
    # ============================================================

    if dept_col:

        department_list = (
            ["All"] +
            sorted(
                df_after_unit[dept_col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    else:
        department_list = ["All"]

    # Reset pilihan Department jika sudah tidak tersedia
    if (
        dept_key in st.session_state
        and st.session_state[dept_key] not in department_list
    ):
        st.session_state[dept_key] = "All"

    # Render di kolom ke-3
    with col_f3:

        selected_dept = st.selectbox(
            "Nama Department",
            department_list,
            key=dept_key
        )

    # ============================================================
    # DATASET SETELAH UNIT + DEPARTMENT
    # ============================================================

    df_after_dept = df_after_unit.copy()

    if selected_dept != "All" and dept_col:

        df_after_dept = df_after_dept[
            df_after_dept[dept_col]
            .astype(str)
            == selected_dept
        ]

    # ============================================================
    # 5. SERVICE / NAMA LAYANAN
    #
    # SERVICE SEKARANG MENGIKUTI:
    # UNIT + DEPARTMENT
    # ============================================================

    if service_col:

        service_list = (
            ["All"] +
            sorted(
                df_after_dept[service_col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    else:
        service_list = ["All"]

    # Reset pilihan Service jika sudah tidak tersedia
    if (
        service_key in st.session_state
        and st.session_state[service_key] not in service_list
    ):
        st.session_state[service_key] = "All"

    # Render di kolom ke-2
    with col_f2:

        selected_service = st.selectbox(
            "Nama Layanan",
            service_list,
            key=service_key
        )

    # ============================================================
    # 6. FINAL FILTER
    # ============================================================

    filtered_df = df_working.copy()

    # ----------------------------
    # FILTER BULAN
    # ----------------------------

    if (
        selected_month != "All"
        and "month_filter_name" in filtered_df.columns
    ):
        filtered_df = filtered_df[
            filtered_df["month_filter_name"]
            == selected_month
        ]

    # ----------------------------
    # FILTER UNIT
    # ----------------------------

    if selected_unit != "All" and unit_col:

        filtered_df = filtered_df[
            filtered_df[unit_col]
            .astype(str)
            == selected_unit
        ]

    # ----------------------------
    # FILTER DEPARTMENT
    # ----------------------------

    if selected_dept != "All" and dept_col:

        filtered_df = filtered_df[
            filtered_df[dept_col]
            .astype(str)
            == selected_dept
        ]

    # ----------------------------
    # FILTER SERVICE
    # ----------------------------

    if selected_service != "All" and service_col:

        filtered_df = filtered_df[
            filtered_df[service_col]
            .astype(str)
            == selected_service
        ]

    # ============================================================
    # HAPUS KOLOM BANTU
    # ============================================================

    cols_to_drop = [
        "datetime_filter",
        "sort_key",
        "month_filter_name"
    ]

    cols_to_drop = [
        c for c in cols_to_drop
        if c in filtered_df.columns
    ]

    if cols_to_drop:
        filtered_df = filtered_df.drop(
            columns=cols_to_drop
        )

    return filtered_df