import os
import pandas as pd
from src.ticket_classifier import train_ticket_classifier
from src.network_classifier import train_network_classifier

# ============================================================
# FILE TRAINING
# ============================================================
FILE_PATH = "BI_mei-juni.xlsx"

print("=" * 60)
print("TRAINING IT TICKET & NETWORK CLASSIFIER")
print("=" * 60)

# ============================================================
# BACA DATA
# ============================================================
print("\n1. Membaca data...")
df = pd.read_excel(FILE_PATH)

print(f"Data berhasil dibaca: {len(df):,} baris")
print("\nKolom yang tersedia:")
for col in df.columns:
    print("-", col)

# ============================================================
# 1. TRAIN MODEL: TICKET TYPE (Incident / Request)
# ============================================================
print("\n" + "-" * 40)
print("A. TRAINING MODEL TICKET TYPE")
print("-" * 40)

if "ticket_type" not in df.columns:
    raise ValueError("\nKolom 'ticket_type' tidak ditemukan.")

print("Distribusi label ticket_type:")
print(df["ticket_type"].value_counts())

print("\nMelatih model Ticket Type...")
model_ticket = train_ticket_classifier(
    df,
    label_column="ticket_type"
)

# ============================================================
# 2. TRAIN MODEL: NETWORK COMPONENT
# ============================================================
print("\n" + "-" * 40)
print("B. TRAINING MODEL NETWORK COMPONENT")
print("-" * 40)

# Sesuaikan 'network_compo' dengan nama kolom label network di Excel kamu
NETWORK_LABEL_COL = "network_compo" if "network_compo" in df.columns else "cat_network"

if NETWORK_LABEL_COL not in df.columns:
    print(f"⚠️ Kolom '{NETWORK_LABEL_COL}' tidak ditemukan di Excel. Training Network dilewati.")
else:
    print(f"Distribusi label {NETWORK_LABEL_COL}:")
    print(df[NETWORK_LABEL_COL].value_counts())

    print("\nMelatih model Network Component...")
    model_network = train_network_classifier(
        df,
        label_column=NETWORK_LABEL_COL
    )

print("\n" + "=" * 60)
print("TRAINING ALL MODELS SELESAI")
print("=" * 60)