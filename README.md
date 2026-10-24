# 📊 IT Helpdesk & Operations Analytics Dashboard

Dashboard berbasis web interaktif yang dibangun menggunakan **Python** dan **Streamlit**. Aplikasi ini dirancang khusus untuk kebutuhan operasional internal perusahaan guna memantau, menganalisis, serta mengevaluasi kinerja Helpdesk IT secara transparan, akurat, dan *real-time*.

---

## 🔗 Live Demo
Kamu dapat melihat langsung versi yang sudah di-*hosting* di sini:
👉 [IT Operations Dashboard · Streamlit](https://ioc-dashboard.streamlit.app/)

---

## 🚀 Fitur & Modul Utama

Aplikasi ini dibagi menjadi beberapa halaman (*pages*) dan komponen modular untuk memudahkan pelacakan operasional IT:

### 1. 📥 Form Ingestion Data Raw (`views/page_upload.py`)
* **Unggah Data Fleksibel:** Mendukung pengunggahan file tiket mentah dalam format CSV maupun Excel (`.csv`, `.xlsx`).
* **Automasi Pipeline:** Begitu file diunggah, sistem otomatis menjalankan pembersihan data (*data cleaning*), transformasi, dan kalkulasi KPI.
* **Sinkronisasi Database:** Menyimpan salinan data yang telah diproses secara aman ke cloud database eksternal (**Supabase**).

### 2. 📊 Executive Overview (`views/page_overview.py`)
* **Ringkasan Eksekutif:** Menyediakan tampilan tingkat tinggi (*high-level summary*) bagi manajemen mengenai kondisi Helpdesk secara keseluruhan.
* **Scorecard Metrik:** Menampilkan kartu metrik utama seperti Total Tiket, Total Gangguan, Total Request, rata-rata MTTR, dan persentase pencapaian SLA.
* **Visualisasi Komprehensif:** Dilengkapi grafik donat distribusi tiket, tren harian, bar chart kategori gangguan, tingkat dampak (*impact*), departemen, hingga *Treemap* layanan terbanyak.

### 3. 🚨 Incident Analytics (`views/page_incident.py`)
* **Filter Mutlak (Guard Clause):** Halaman ini secara khusus memfilter dan hanya menampilkan tiket berjenis **Gangguan/Incident** (menyingkirkan tiket *Request*).
* **Calendar Heatmap:** Memetakan pola kemunculan gangguan berdasarkan kalender harian untuk mendeteksi hari-hari dengan lonjakan masalah.
* **Analisis 4 Bucket Utama:** Memecah masalah teknis ke dalam 4 kategori spesifik menggunakan *Bar Chart*: **Device**, **Network**, **Infrastruktur**, dan **Aplikasi**.

### 4. ⏳ Pending Investigation (`views/page_pending.py`)
* **Monitoring Tiket Tertunda:** Fokus melacak tiket-tiket yang sedang berstatus *Pending* dengan sistem prioritas bertingkat.
* **Deteksi Pelanggaran SLA:** Menghitung secara otomatis jumlah tiket tertunda yang melanggar batas waktu wajar SLA (>240 menit).
* **Analisis Lanjutan:** Menyediakan grafik tren harian tiket pending dan tabel rincian deskripsi masalah.

### 5. 🏆 IT Performance & SLA (`views/page_performance.py`)
* **Evaluasi Produktivitas Teknisi:** Membedah performa dan beban kerja dari masing-masing staf IT/teknisi (*agent/member*).
* **Interactive Slicer:** Dilengkapi dropdown pemilihan anggota untuk memfilter performa secara spesifik per-individu.
* **Metrik Individu:** Menampilkan peringkat penyelesaian tiket, pencapaian SLA individual, rata-rata waktu respons, dan distribusi durasi penyelesaian.

---

## 🛠️ Struktur Direktori Proyek

```text
documented_project/
│
├── views/                  # Modul halaman antarmuka (UI Views)
│   ├── page_upload.py      # Form ingestion & upload data mentah
│   ├── page_overview.py    # Halaman ringkasan eksekutif
│   ├── page_incident.py    # Analisis khusus insiden/gangguan
│   ├── page_pending.py     # Investigasi tiket tertunda (pending)
│   └── page_performance.py # Performa teknisi & kepatuhan SLA
│
├── components/             # Komponen UI yang dapat digunakan kembali (Reusable)
│   ├── sidebar.py          # Navigasi utama sidebar aplikasi
│   ├── filters.py          # Global cascading top filters (Bulan, Unit, Dept, Service)
│   ├── metrics.py          # Kalkulator & kartu scorecard KPI
│   └── charts.py           # Kumpulan fungsi grafik Plotly (Trend, Heatmap, Bar, Pie)
│
├── src/                    # Logika backend & pemrosesan data (Pipeline)
│   ├── data_cleaning.py    # Modul pembersihan data kotor/mentah
│   └── data_transformation.py # Modul transformasi & kalkulasi metrik 
│
└── app.py                  # Titik masuk utama (Main entry point) aplikasi Streamlit
