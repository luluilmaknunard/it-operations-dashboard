import os
import pandas as pd

from src.ticket_classifier import train_ticket_classifier


# ============================================================
# FILE TRAINING
# ============================================================

FILE_PATH = "clean_mei-juni.xlsx"


print("=" * 60)
print("TRAINING IT TICKET CLASSIFIER")
print("=" * 60)


# ============================================================
# BACA DATA
# ============================================================

print("\n1. Membaca data...")

df = pd.read_excel(FILE_PATH)

print(
    f"Data berhasil dibaca: "
    f"{len(df):,} baris"
)

print(
    "\nKolom yang tersedia:"
)

for col in df.columns:
    print("-", col)


# ============================================================
# CEK LABEL
# ============================================================

if "ticket_type" not in df.columns:

    raise ValueError(
        "\nKolom 'ticket_type' tidak ditemukan.\n\n"
        "Data training harus memiliki label:\n"
        "Incident atau Request."
    )


print("\nDistribusi label:")

print(
    df["ticket_type"]
    .value_counts()
)


# ============================================================
# TRAIN MODEL
# ============================================================

print("\n2. Training model...")

model = train_ticket_classifier(
    df,
    label_column="ticket_type"
)


print("\n" + "=" * 60)
print("TRAINING SELESAI")
print("=" * 60)