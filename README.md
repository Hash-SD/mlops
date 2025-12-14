# 🚀 Sentiment Analysis MLOps Pipeline: Continuous Learning System
<!-- Badges: Project tech stack & status -->
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-True-orange?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Scikit-learn](https://img.shields.io/badge/scikit--learn-0.24%2B-lightgrey?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Supabase](https://img.shields.io/badge/supabase-cloud-2EA44F?logo=supabase&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/docker-container-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![PyTest](https://img.shields.io/badge/pytest-tests-4B32C3?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![release](https://img.shields.io/github/v/release/Hash-SD/mlops?label=latest%20release)](https://github.com/Hash-SD/mlops/releases   )

Sistem Klasifikasi Sentimen End-to-End yang "Hidup": Mampu memprediksi, menerima umpan balik pengguna, memantau performa, dan melakukan pelatihan ulang (Retraining) secara mandiri.

## 📖 Latar Belakang Masalah

Model Machine Learning tradisional bersifat statis. Setelah di-deploy, performanya sering kali menurun seiring waktu karena perubahan tren bahasa atau konteks data (Data Drift). Proyek ini menyelesaikan masalah tersebut dengan pendekatan Closed-Loop MLOps, di mana model terus belajar dari interaksi pengguna.

Baik, sekarang jelas 👍
Kamu **SUDAH punya gambarnya**, dan kamu ingin:

1. **Gambar benar-benar muncul di README**
2. **Kode Markdown utuh**
3. **Disertai analisis akademik / teknis dari gambar tersebut**
4. Fokus pada **The Big Picture Architecture**

Di bawah ini adalah **jawaban final siap tempel ke README.md** tanpa asumsi apa pun.

---

## 🏗️ Arsitektur Sistem (The Big Picture)

Gambar berikut menunjukkan arsitektur sistem Sentiment Analysis berbasis MLOps yang dirancang sebagai **end-to-end continuous learning system**, mulai dari interaksi pengguna hingga penyimpanan log dan pembaruan model.

### 📌 The Big Picture Architecture

<img src="docs/The Big Picture Architecture1.jpg" alt="Monitoring Dashboard Screenshot 1" width="600">
<img src="docs/The Big Picture Architecture2.jpg" alt="Monitoring Dashboard Screenshot 2" width="600">

### 🔍 Analisis Arsitektur Sistem

Arsitektur ini terdiri dari tiga lapisan utama yang saling terintegrasi secara real-time:

#### 1️⃣ Client Layer – Streamlit App (Frontend)

* **Peran utama:** Media interaksi pengguna
* Pengguna memasukkan teks ulasan melalui antarmuka Streamlit.
* Streamlit bertindak sebagai client yang mengirimkan request ke backend.
* Selain menampilkan hasil prediksi, frontend juga menyediakan mekanisme **feedback (Benar / Salah)** sebagai bagian dari human-in-the-loop.

**Nilai MLOps:**
Frontend tidak hanya untuk inferensi, tetapi juga berfungsi sebagai sumber data pelatihan berkelanjutan.

---

#### 2️⃣ Server Layer – Prediction Service (Backend)

* **Peran utama:** Core inference engine
* Backend memuat model machine learning dalam format `.pkl`.
* Model melakukan klasifikasi sentimen berdasarkan input pengguna.
* Hasil prediksi dikirim kembali ke frontend.
* Semua aktivitas inferensi dicatat sebagai log.

**Nilai MLOps:**
Backend dirancang stateless terhadap UI namun stateful terhadap model, sehingga model dapat diganti tanpa mengubah frontend.

---

#### 3️⃣ Storage Layer – Supabase (Database & Logs)

* **Peran utama:** Single source of truth
* Menyimpan:

  * Log prediksi
  * Feedback pengguna
  * Metadata model
* Database ini menjadi dasar untuk monitoring performa dan retraining.

**Nilai MLOps:**
Supabase berfungsi sebagai jembatan antara inference dan learning, memungkinkan closed-loop learning.


### 🔁 Feedback Loop (Human-in-the-Loop)
<img src="docs/Feedback Loop.jpg" alt="Monitoring Dashboard Screenshot 2" width="600">

Alur feedback membentuk siklus pembelajaran berkelanjutan:

1. Model melakukan prediksi
2. Pengguna mengevaluasi hasil
3. Feedback disimpan di database
4. Data baru digunakan untuk evaluasi performa
5. Model dilatih ulang jika diperlukan

Hal ini memastikan sistem **adaptif terhadap data drift dan perubahan bahasa pengguna**.



## 🔁 Model Evolution (Continuous Learning Lifecycle)

Bagian ini menjelaskan bagaimana model machine learning dalam sistem Sentiment Analysis **berevolusi dari waktu ke waktu** melalui mekanisme feedback pengguna, monitoring performa, dan retraining otomatis. Konsep ini merupakan inti dari pendekatan **MLOps berbasis continuous learning**.

### 📌 Diagram Model Evolution


<img src="docs/model evolution.jpg" alt="Monitoring Dashboard Screenshot 2" width="600">
## 🔍 Analisis Model Evolution

Model Evolution menggambarkan bahwa model **tidak bersifat statis**, melainkan terus diperbarui untuk menjaga performa seiring perubahan data dan konteks bahasa.



### 1️⃣ Prediction Service (Inferensi Model)

Siklus dimulai ketika **Prediction Service** menggunakan model aktif untuk melakukan inferensi terhadap input pengguna.

* Model menghasilkan prediksi sentimen
* Hasil prediksi dikirim ke frontend
* Semua prediksi dicatat ke database

Tahap ini merepresentasikan **model versi aktif** (misalnya Model v1).


### 2️⃣ Supabase Database (Data & Feedback)

Semua data hasil inferensi disimpan di **Supabase Database**, termasuk:

* Input teks pengguna
* Label prediksi model
* Feedback pengguna (benar / salah)
* Waktu dan metadata model

Database ini berfungsi sebagai **sumber data dinamis** untuk evaluasi performa dan pelatihan ulang.

---

### 3️⃣ Feedback (Human-in-the-Loop)

Feedback dari pengguna menjadi komponen kunci dalam evolusi model.

* Jika prediksi salah, user memberikan label yang benar
* Feedback disimpan sebagai data terverifikasi
* Data ini meningkatkan kualitas dataset pelatihan

**Nilai MLOps:**
Human-in-the-loop membantu mengurangi error sistematis dan bias model.



### 4️⃣ Monitoring Performance

Monitoring Service secara berkala mengevaluasi performa model menggunakan data terbaru.

Indikator yang dimonitor antara lain:

* Akurasi prediksi
* Rasio feedback salah
* Volume data baru
* Tren penurunan performa (data drift)

Tahap ini menentukan apakah model masih layak digunakan atau perlu diperbarui.


### 5️⃣ Trigger Retraining

Retraining dipicu oleh dua kondisi utama:

* **Penurunan akurasi** di bawah ambang batas tertentu
* **Jadwal retraining berkala** (misalnya mingguan)

Trigger ini mencegah retraining berlebihan sekaligus memastikan model tetap relevan.


### 6️⃣ Train New Model

Pada tahap ini:

* Data lama digabung dengan data feedback terbaru
* Model dilatih ulang menggunakan pipeline yang sama
* Model baru dihasilkan (misalnya Model v2)

Proses ini memastikan **reproducibility dan konsistensi eksperimen**.



### 7️⃣ Updated Model (Model Baru)

Model hasil retraining:

* Disimpan sebagai model versi terbaru
* Menggantikan model lama
* Digunakan kembali oleh Prediction Service

Siklus kemudian kembali ke tahap inferensi dan terus berulang.


## 🧠 Makna Model Evolution dalam MLOps

Model Evolution memastikan bahwa sistem:

* Adaptif terhadap **data drift**
* Tidak mengalami **model decay**
* Terus meningkat kualitasnya dari waktu ke waktu
* Siap digunakan dalam skenario produksi nyata

Pendekatan ini membedakan sistem MLOps modern dari pipeline machine learning tradisional yang statis.












  

**Komponen Utama:**

- Frontend (Streamlit): Antarmuka interaktif untuk pengguna melakukan prediksi sentimen dan memberikan feedback.
- Prediction Service: Layanan backend yang memuat model .pkl dan menangani logika inferensi.
- Feedback Loop: Mekanisme "Human-in-the-loop" yang memungkinkan pengguna mengoreksi prediksi model yang salah.
- Supabase Cloud: Database PostgreSQL untuk menyimpan log prediksi, feedback pengguna, dan metadata model.
- Automated Retraining: Layanan yang dipicu kondisi tertentu untuk melatih ulang model menggunakan data terbaru.

## 🔄 Siklus Hidup MLOps (Operational Workflow)

Diagram di bawah ini menjelaskan alur operasional sistem ("The Brain of MLOps"), mulai dari prediksi hingga pembaruan model otomatis.

```mermaid
graph TD
    %% Alur utama dari input pengguna sampai hasil
    UserInput[User Input Text]
    ValidateInput{Validasi Input}
    ClickAnalyze[Klik Analisis]
    LoadModel[Load Model Aktif]
    Inference[Preprocessing dan Inference]
    Confidence[Hitung Confidence]
    Consent{User Consent}
    Anonymize[Anonymize Data]
    Database[(Supabase Database)]
    ShowResult[Tampilkan Hasil]
    History[Riwayat Prediksi]

    %% Alur MLOps
    Monitor[Monitoring Performa]
    Drift[Deteksi Drift]
    RetrainTrigger{Trigger Retraining}
    FetchData[Ambil Data Terbaru]
    SplitData[Split Train dan Test]
    TrainModel[Train Model Baru]
    Evaluate[Evaluasi Model]
    ValidateModel[Validasi Model]
    ArchiveModel[Archive Model Lama]
    DeployModel[Deploy Model Baru]

    %% Flow utama
    UserInput --> ValidateInput
    ValidateInput -- Valid --> ClickAnalyze
    ValidateInput -- Tidak Valid --> UserInput
    ClickAnalyze --> LoadModel
    LoadModel --> Inference
    Inference --> Confidence
    Confidence --> Consent

    %% Logging dan tampilan
    Consent -- Ya --> Anonymize
    Anonymize --> Database
    Consent -- Tidak --> ShowResult
    Database --> ShowResult
    ShowResult --> History

    %% Flow MLOps
    Database --> Monitor
    Monitor --> Drift
    Drift --> RetrainTrigger
    RetrainTrigger -- Ya --> FetchData
    FetchData --> SplitData
    SplitData --> TrainModel
    TrainModel --> Evaluate
    Evaluate --> ValidateModel
    ValidateModel --> ArchiveModel
    ArchiveModel --> DeployModel
    DeployModel --> LoadModel
````

**Penjelasan Alur:**

- Input dan Validasi: Pengguna memasukkan teks ulasan, kemudian sistem melakukan validasi awal untuk memastikan input sesuai kriteria sebelum diproses lebih lanjut.
- Inference dan Confidence: Setelah validasi berhasil, model aktif dimuat dan melakukan preprocessing serta inferensi untuk menghasilkan prediksi sentimen beserta nilai confidence.
- Consent dan Logging Data: Sistem meminta persetujuan pengguna sebelum menyimpan data. Jika disetujui, data dianonimkan lalu disimpan ke database sebagai riwayat prediksi.
- Monitoring Performa: Data historis digunakan oleh sistem monitoring untuk mengevaluasi performa model secara berkala dan mendeteksi potensi data drift.
- Retraining dan Update Model: Apabila terdeteksi penurunan performa atau drift melewati ambang batas, sistem memicu proses retraining, mengevaluasi model baru, mengarsipkan model lama, dan mendistribusikan model terbaru ke layanan prediksi.

## 📸 Fitur & Demo Aplikasi

1. Prediksi & Koreksi (Active Learning)

Antarmuka pengguna dirancang untuk mempermudah validasi hasil model.

<img src="docs/home.jpg" alt="Homepage Screenshot" width="600">

Halaman utama menampilkan antarmuka analisis sentimen yang sederhana dan intuitif. Pengguna dapat memasukkan teks ulasan (minimal 7 kata), kemudian sistem akan menampilkan hasil prediksi sentimen (Positif/NegatifNetral) beserta tingkat confidence. Aplikasi juga menyediakan tombol contoh teks untuk demonstrasi cepat dan menampilkan riwayat prediksi terakhir untuk referensi.

<!--
🔴 [INSTRUKSI UNTUK VISUALISASI - GAMBAR 2]
Masukkan Screenshot Halaman Utama (Main Area) di sini.
Pastikan terlihat: Input teks, Hasil Prediksi, dan Tombol Feedback "Benar/Salah".
-->

2. Monitoring Dashboard

Admin dapat memantau kesehatan model secara transparan melalui grafik real-time.

<img src="docs/monitoring-1.jpg" alt="Monitoring Dashboard Screenshot 1" width="600">

Dashboard monitoring menampilkan metrik utama seperti Total Prediksi, Rata-rata Latency, dan Drift Score Global. Sistem juga menampilkan deteksi data drift yang membantu mengidentifikasi kapan model perlu di-retrain berdasarkan perubahan distribusi data.

<img src="docs/monitoring-2.jpg" alt="Monitoring Dashboard Screenshot 2" width="600">

Halaman monitoring juga menampilkan tabel evaluasi model yang membandingkan akurasi dan F1 Score antar versi model, serta grafik frekuensi prediksi per versi model untuk analisis penggunaan.

<img src="docs/monitoring-3.jpg" alt="Monitoring Dashboard Latency Distribution Screenshot" width="600">

Dashboard juga menyediakan visualisasi distribusi latency melalui histogram yang menampilkan sebaran waktu respons prediksi. Grafik ini dilengkapi dengan threshold untuk mengidentifikasi prediksi yang melebihi batas waktu yang ditentukan, serta statistik lengkap seperti nilai minimum, rata-rata, maksimum, dan jumlah prediksi di atas threshold.

## 🛠️ Teknologi (Tech Stack)

| Kategori      | Teknologi             | Kegunaan Utama                         |
| ------------- | --------------------- | -------------------------------------- |
| Frontend      | Streamlit             | UI Interaktif & Visualisasi Data       |
| Backend Logic | Python 3.9+           | Core Services (Prediction, Retraining) |
| ML Framework  | Scikit-learn          | Naive Bayes, TF-IDF, Pipeline          |
| Database      | Supabase (PostgreSQL) | Menyimpan Dataset & Feedback Log       |
| Environment   | Docker / DevContainer | Isolasi Environment & Reproducibility  |
| Testing       | Pytest                | Unit Testing & Integration Testing     |

## 🚀 Cara Menjalankan (Quick Start)

Ikuti langkah-langkah berikut untuk menjalankan sistem ini di mesin lokal Anda.

**Prasyarat**

- Python 3.9 atau lebih baru.
- Akun Supabase (Gratis) untuk database.

1. Clone Repository

```bash
git clone https://github.com/username/mlops-sentiment-project.git
cd mlops-sentiment-project
```

2. Konfigurasi Environment

Salin file contoh .env dan isi kredensial Supabase Anda.

```bash
cp .env.example .env
# Edit file .env dan isi SUPABASE_URL serta SUPABASE_KEY
```

3. Setup Database

Buka dashboard Supabase Anda, masuk ke SQL Editor, dan jalankan script yang ada di file:
`database/schema.sql`

4. Install Dependencies

```bash
pip install -r requirements.txt
```

5. Jalankan Aplikasi

```bash
streamlit run app.py
```

## 📂 Struktur Proyek

Kode diorganisir berdasarkan prinsip Separation of Concerns untuk skalabilitas.

```
mlops-project/
├── 📂 services/           # LOGIKA BISNIS UTAMA
│   ├── prediction_service.py   # Menangani inferensi model
│   ├── monitoring_service.py   # Menghitung metrik performa real-time
│   └── retraining_service.py   # Logika pelatihan ulang otomatis
├── 📂 models/             # MODEL REGISTRY
│   ├── saved_model/            # Direktori model aktif (.pkl)
│   └── model_updater.py        # Script aman untuk mengganti model
├── 📂 ui/                 # FRONTEND (STREAMLIT)
│   ├── main_area.py            # Komponen halaman prediksi
│   └── monitoring.py           # Komponen dashboard monitoring
├── 📂 database/           # DATA LAYER
│   └── db_manager_supabase.py  # Koneksi & query ke Supabase
└── app.py                 # Entry point aplikasi
```

## 🧪 Testing

Proyek ini mencakup automated testing untuk memastikan integritas sistem sebelum deployment.

**Menjalankan seluruh test suite**

```bash
pytest
```

**Menjalankan test spesifik**

```bash
pytest tests/test_services/
```

<p align="center">
Dibuat dengan ❤️ untuk Tugas Besar MLOps
</p>
```
