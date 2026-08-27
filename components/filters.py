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

    Behavior:
    - Jika Unit = All      → data seluruh unit
    - Jika Unit dipilih    → seluruh data fokus ke unit tersebut
    - Department mengikuti Unit
    - Service mengikuti Unit + Department
    - Bulan membatasi seluruh filter berikutnya

    Metadata pilihan filter disimpan di:
        filtered_df.attrs["selected_month"]
        filtered_df.attrs["selected_unit"]
        filtered_df.attrs["selected_dept"]
        filtered_df.attrs["selected_service"]

    Ini bisa digunakan oleh metrics.py untuk membedakan
    MTTR keseluruhan dengan MTTR unit tertentu.
    """

    # ============================================================
    # 0. VALIDASI
    # ============================================================

    if df is None or df.empty:
        return df

    df_working = df.copy()

    # ============================================================
    # 1. HELPER CARI KOLOM
    # ============================================================

    def find_column(possible_names):

        normalized_targets = {
            str(x).strip().lower().replace(" ", "_")
            for x in possible_names
        }

        for col in df_working.columns:

            normalized_col = (
                str(col)
                .strip()
                .lower()
                .replace(" ", "_")
            )

            if normalized_col in normalized_targets:
                return col

        return None

    # ============================================================
    # 2. CARI KOLOM UTAMA
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
        "nama_department",
        "nama_departemen"
    ])

    unit_col = find_column([
        "unit_name",
        "unit",
        "nama_unit",
        "unitname"
    ])

    # ============================================================
    # 3. CARI KOLOM TANGGAL
    # ============================================================

    date_col = None

    if "date_created_at" in df_working.columns:
        date_col = "date_created_at"

    elif "Date" in df_working.columns:
        date_col = "Date"

    else:

        for col in df_working.columns:

            col_clean = (
                str(col)
                .strip()
                .lower()
            )

            if col_clean in [
                "created_at",
                "created_date",
                "tanggal",
                "date"
            ]:
                date_col = col
                break

    # ============================================================
    # 4. PREPARE DATETIME
    # ============================================================

    if date_col is not None:

        if pd.api.types.is_datetime64_any_dtype(
            df_working[date_col]
        ):

            df_working["datetime_filter"] = (
                df_working[date_col]
            )

        else:

            # Percobaan pertama
            df_working["datetime_filter"] = pd.to_datetime(
                df_working[date_col],
                format="%d.%m.%Y %H:%M:%S",
                errors="coerce"
            )

            # Fallback format lain
            null_mask = (
                df_working["datetime_filter"].isna()
            )

            if null_mask.any():

                df_working.loc[
                    null_mask,
                    "datetime_filter"
                ] = pd.to_datetime(
                    df_working.loc[
                        null_mask,
                        date_col
                    ],
                    dayfirst=True,
                    errors="coerce"
                )

        df_working["month_filter_name"] = (
            df_working["datetime_filter"]
            .dt.strftime("%B %Y")
        )

        df_working["month_sort_key"] = (
            df_working["datetime_filter"]
            .dt.strftime("%Y-%m")
        )

        valid_months = (
            df_working[
                [
                    "month_sort_key",
                    "month_filter_name"
                ]
            ]
            .dropna()
            .drop_duplicates()
            .sort_values("month_sort_key")
        )

        month_list = (
            ["All"]
            + valid_months[
                "month_filter_name"
            ].tolist()
        )

    else:

        month_list = ["All"]

    # ============================================================
    # 5. KEY WIDGET
    # ============================================================

    month_key = f"{key_prefix}_f_month"
    unit_key = f"{key_prefix}_f_unit"
    dept_key = f"{key_prefix}_f_dept"
    service_key = f"{key_prefix}_f_service"

    # ============================================================
    # 6. LAYOUT FILTER
    # ============================================================

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # ============================================================
    # 7. FILTER BULAN
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
    # 8. DATASET SETELAH BULAN
    # ============================================================

    df_after_month = df_working.copy()

    if (
        selected_month != "All"
        and "month_filter_name" in df_after_month.columns
    ):

        df_after_month = df_after_month[
            df_after_month["month_filter_name"]
            == selected_month
        ].copy()

    # ============================================================
    # 9. UNIT NAME
    #
    # UNIT SEKARANG MENGIKUTI BULAN
    # ============================================================

    if unit_col is not None:

        unit_values = (
            df_after_month[unit_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        unit_values = [
            value
            for value in unit_values.unique().tolist()
            if value
            and value.lower()
            not in [
                "nan",
                "none",
                "null",
                "-"
            ]
        ]

        unit_list = (
            ["All"]
            + sorted(unit_values)
        )

    else:

        unit_list = ["All"]

    # Reset state jika unit sudah tidak tersedia
    if (
        unit_key in st.session_state
        and st.session_state[unit_key] not in unit_list
    ):
        st.session_state[unit_key] = "All"

    with col_f4:

        selected_unit = st.selectbox(
            "Unit Name",
            unit_list,
            key=unit_key
        )

    # ============================================================
    # 10. DATASET SETELAH UNIT
    # ============================================================

    df_after_unit = df_after_month.copy()

    if (
        selected_unit != "All"
        and unit_col is not None
    ):

        df_after_unit = df_after_unit[
            df_after_unit[unit_col]
            .astype(str)
            .str.strip()
            == selected_unit
        ].copy()

    # ============================================================
    # 11. DEPARTMENT
    #
    # DEPARTMENT MENGIKUTI:
    # BULAN + UNIT
    # ============================================================

    if dept_col is not None:

        dept_values = (
            df_after_unit[dept_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        dept_values = [
            value
            for value in dept_values.unique().tolist()
            if value
            and value.lower()
            not in [
                "nan",
                "none",
                "null",
                "-"
            ]
        ]

        department_list = (
            ["All"]
            + sorted(dept_values)
        )

    else:

        department_list = ["All"]

    # Reset state jika department tidak tersedia
    if (
        dept_key in st.session_state
        and st.session_state[dept_key] not in department_list
    ):
        st.session_state[dept_key] = "All"

    with col_f3:

        selected_dept = st.selectbox(
            "Nama Department",
            department_list,
            key=dept_key
        )

    # ============================================================
    # 12. DATASET SETELAH DEPARTMENT
    # ============================================================

    df_after_dept = df_after_unit.copy()

    if (
        selected_dept != "All"
        and dept_col is not None
    ):

        df_after_dept = df_after_dept[
            df_after_dept[dept_col]
            .astype(str)
            .str.strip()
            == selected_dept
        ].copy()

    # ============================================================
    # 13. SERVICE / NAMA LAYANAN
    #
    # SERVICE MENGIKUTI:
    # BULAN + UNIT + DEPARTMENT
    # ============================================================

    if service_col is not None:

        service_values = (
            df_after_dept[service_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        service_values = [
            value
            for value in service_values.unique().tolist()
            if value
            and value.lower()
            not in [
                "nan",
                "none",
                "null",
                "-"
            ]
        ]

        service_list = (
            ["All"]
            + sorted(service_values)
        )

    else:

        service_list = ["All"]

    # Reset state jika service tidak tersedia
    if (
        service_key in st.session_state
        and st.session_state[service_key] not in service_list
    ):
        st.session_state[service_key] = "All"

    with col_f2:

        selected_service = st.selectbox(
            "Nama Layanan",
            service_list,
            key=service_key
        )

    # ============================================================
    # 14. FINAL FILTER
    # ============================================================

    filtered_df = df_working.copy()

    # ------------------------------------------------------------
    # BULAN
    # ------------------------------------------------------------

    if (
        selected_month != "All"
        and "month_filter_name" in filtered_df.columns
    ):

        filtered_df = filtered_df[
            filtered_df["month_filter_name"]
            == selected_month
        ].copy()

    # ------------------------------------------------------------
    # UNIT
    # ------------------------------------------------------------

    if (
        selected_unit != "All"
        and unit_col is not None
    ):

        filtered_df = filtered_df[
            filtered_df[unit_col]
            .astype(str)
            .str.strip()
            == selected_unit
        ].copy()

    # ------------------------------------------------------------
    # DEPARTMENT
    # ------------------------------------------------------------

    if (
        selected_dept != "All"
        and dept_col is not None
    ):

        filtered_df = filtered_df[
            filtered_df[dept_col]
            .astype(str)
            .str.strip()
            == selected_dept
        ].copy()

    # ------------------------------------------------------------
    # SERVICE
    # ------------------------------------------------------------

    if (
        selected_service != "All"
        and service_col is not None
    ):

        filtered_df = filtered_df[
            filtered_df[service_col]
            .astype(str)
            .str.strip()
            == selected_service
        ].copy()

    # ============================================================
    # 15. SIMPAN INFORMASI FILTER
    #
    # Digunakan metrics.py / page overview
    # untuk mengetahui apakah user memilih Unit tertentu.
    # ============================================================

    filtered_df.attrs["selected_month"] = selected_month
    filtered_df.attrs["selected_unit"] = selected_unit
    filtered_df.attrs["selected_dept"] = selected_dept
    filtered_df.attrs["selected_service"] = selected_service

    filtered_df.attrs["unit_filter_active"] = (
        selected_unit != "All"
    )

    filtered_df.attrs["department_filter_active"] = (
        selected_dept != "All"
    )

    filtered_df.attrs["service_filter_active"] = (
        selected_service != "All"
    )

    # ============================================================
    # 16. HAPUS KOLOM BANTU
    # ============================================================

    cols_to_drop = [
        "datetime_filter",
        "sort_key",
        "month_sort_key",
        "month_filter_name"
    ]

    cols_to_drop = [
        col
        for col in cols_to_drop
        if col in filtered_df.columns
    ]

    if cols_to_drop:

        filtered_df = filtered_df.drop(
            columns=cols_to_drop
        )

    # ============================================================
    # 17. PERTAHANKAN METADATA SETELAH DROP/COPY
    # ============================================================

    filtered_df.attrs["selected_month"] = selected_month
    filtered_df.attrs["selected_unit"] = selected_unit
    filtered_df.attrs["selected_dept"] = selected_dept
    filtered_df.attrs["selected_service"] = selected_service

    filtered_df.attrs["unit_filter_active"] = (
        selected_unit != "All"
    )

    filtered_df.attrs["department_filter_active"] = (
        selected_dept != "All"
    )

    filtered_df.attrs["service_filter_active"] = (
        selected_service != "All"
    )

    return filtered_df


