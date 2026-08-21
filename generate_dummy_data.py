import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

# Inisialisasi Faker Bahasa Indonesia
fake = Faker("id_ID")
Faker.seed(42)
random.seed(42)

TOTAL_ROWS = 70

# Opsi Kategori & Teks
departments = [
    "IT Infrastructure",
    "Application Support",
    "Network Operations",
    "Helpdesk",
]
services = [
    "Internet Access",
    "VPN Service",
    "Email & Workspace",
    "Database Server",
    "Hardware PC/Laptop",
]
sources = ["Portal Web", "Email", "Whatsapp", "Call Center"]
status_list = ["Resolved", "Closed", "Pending"]

# Sampel Kasus untuk menguji Network Component & Ticket Type (Gangguan vs Request)
issue_samples = [
    {
        "cat_name": "Jaringan > LAN > Port Switch",
        "symptom": "Kabel LAN tidak terdeteksi di PC",
        "summary": "Port switch indikator mati",
        "remark": "Ujung RJ45 longgar dan unplugged",
        "rootcause": "Kabel LAN terlepas dari port",
        "type": "Gangguan",
    },
    {
        "cat_name": "Jaringan > Internet > Koneksi Lambat",
        "symptom": "Internet down dan RTO",
        "summary": "Koneksi internet indihome putus",
        "remark": "Ping ke gateway tinggi",
        "rootcause": "FO Indihome sedang ada perbaikan",
        "type": "Gangguan",
    },
    {
        "cat_name": "Akses & Security > VPN > Forticlient",
        "symptom": "Gagal konek VPN Pritunl",
        "summary": "Forticlient error authentication",
        "remark": "Sertifikat vpn expired",
        "rootcause": "Perlu update konfigurasi vpn",
        "type": "Gangguan",
    },
    {
        "cat_name": "Akses & Security > IP Address > WhiteList",
        "symptom": "Permintaan allow akses IP public",
        "summary": "Minta permission IP public untuk server baru",
        "remark": "Penarikan data laporan berkala",
        "rootcause": "Permintaan akses dari departemen Finance",
        "type": "Request",
    },
    {
        "cat_name": "Aplikasi > Data > Recording",
        "symptom": "Permintaan rekording panggilan customer service",
        "summary": "Tarik data recording bulan lalu",
        "remark": "Minta data recording audio call center",
        "rootcause": "Kebutuhan audit internal",
        "type": "Request",
    },
    {
        "cat_name": "Sistem > Server > CMS",
        "symptom": "Server CMS tidak bisa diakses via browser",
        "summary": "Website portal internal error 500",
        "remark": "Service rabbit & server butuh restart",
        "rootcause": "Memory server penuh",
        "type": "Gangguan",
    },
]

data = []

start_base_date = datetime(2026, 8, 1, 8, 0, 0)

for i in range(1, TOTAL_ROWS + 1):
    issue = random.choice(issue_samples)

    # Tanggal Skenario
    date_created = start_base_date + timedelta(
        days=random.randint(0, 15), hours=random.randint(0, 10)
    )
    date_start_interaction = date_created + timedelta(
        minutes=random.randint(1, 15)
    )
    date_assigned = date_start_interaction + timedelta(
        minutes=random.randint(5, 30)
    )

    # 30% Kemungkinan Pending
    is_pending = random.random() < 0.3
    if is_pending:
        date_pending = date_assigned + timedelta(
            minutes=random.randint(10, 60)
        )
        date_last_update = date_pending + timedelta(
            minutes=random.randint(30, 300)
        )
    else:
        date_pending = None
        date_last_update = date_assigned + timedelta(
            minutes=random.randint(15, 200)
        )

    date_open = date_created

    # Nama dibuat bervariasi (panjang 3-4 kata & pendek 1-2 kata untuk tes pemotongan nama)
    created_by = (
        fake.name()
        if i % 2 == 0
        else f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"
    )
    updated_by = (
        fake.name()
        if i % 2 != 0
        else f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"
    )

    row = {
        "ticket_id": f"TCK-2026-{1000 + i}",
        "ticketId_masking": f"TCK-****-{1000 + i}",
        "department": random.choice(departments),
        "service_name": random.choice(services),
        "category_name": issue["cat_name"],
        "informant_name": fake.name(),
        "detailSubCategory2": "Detail Sub " + str(random.randint(1, 5)),
        "customer_email": fake.email(),
        "category": issue["cat_name"].split(" > ")[0],
        "subCategory": issue["cat_name"].split(" > ")[1]
        if " > " in issue["cat_name"]
        else "General",
        "detailSubCategory": issue["cat_name"].split(" > ")[2]
        if issue["cat_name"].count(" > ") >= 2
        else "Detail General",
        "ticket_source": random.choice(sources),
        "ticket_symptom": issue["symptom"],
        "ticket_summary": issue["summary"],
        "source_name": random.choice(sources),
        "remark": issue["remark"],
        "ticket_rootcouse": issue["rootcause"],
        "feedback": random.choice(["Sangat Baik", "Cukup", "Puas", None]),
        "impact_name": random.choice(["Low", "Medium", "High"]),
        "date_created_at": date_created.strftime("%Y-%m-%d %H:%M:%S"),
        "subject": issue["summary"],
        "created_by_id": f"EMP-{random.randint(100, 999)}",
        "created_by_name": created_by,
        "date_start_interaction": date_start_interaction.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "updated_by_id": f"EMP-{random.randint(100, 999)}",
        "updated_by_name": updated_by,
        "unit_id": f"UNT-{random.randint(10, 99)}",
        "unit_name": "Unit " + fake.city(),
        "ticket_status_name": "Pending"
        if is_pending and random.random() < 0.5
        else random.choice(status_list),
        "sla_second": random.choice([3600, 7200, 14400]),  # 1 jam, 2 jam, 4 jam
        "date_open": date_open.strftime("%Y-%m-%d %H:%M:%S"),
        "date_assigned": date_assigned.strftime("%Y-%m-%d %H:%M:%S"),
        "date_pending": date_pending.strftime("%Y-%m-%d %H:%M:%S")
        if date_pending
        else None,
        "channel_id": random.randint(1, 4),
        "date_last_update": date_last_update.strftime("%Y-%m-%d %H:%M:%S"),
        "ticket_rev_scope": "Internal",
        "ticket_rev_symptom": issue["symptom"],
        "count_merged": 0,
        "parent_id": None,
    }
    data.append(row)

df_dummy = pd.DataFrame(data)

# Simpan ke Excel
output_filename = "data_sample_test.xlsx"
df_dummy.to_excel(output_filename, index=False)
print(
    f"✅ Berhasil membuat {TOTAL_ROWS} baris data dummy di file: '{output_filename}'"
)