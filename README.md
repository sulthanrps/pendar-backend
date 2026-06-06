# Pendar Backend API 🌟

Backend API untuk aplikasi **Pendar** (Productivity & Mental Well-being). Dibangun menggunakan **Flask (Python)**, **Supabase** (PostgreSQL & Auth), dan **XGBoost** untuk fitur prediksi *Mind Check*.

## 🚀 Base URL
- **Local:** `http://127.0.0.1:5000`
- **Production:** `To Be Written (nunggu deploy)`

## 🔐 Autentikasi (Penting untuk Frontend)
Semua *endpoint* **kecuali Auth (Login/Register)** wajib menyertakan token JWT di dalam *Headers*. Token ini didapatkan setelah *user* berhasil *Login*.

**Format Header:**
`Authorization: Bearer <access_token>`

---

## 📚 Daftar Endpoint API

### 1. Authentication (`/auth`)

#### A. Register
- **Method:** `POST`
- **Endpoint:** `/auth/register`
- **Body (JSON):**
  ```json
    {
        "email": "user@student.ub.ac.id",
        "password": "Password123!",
        "full_name": "Nama Lengkap",
        "institution": "Universitas Brawijaya"
    }
- **Success Response:** `201 Created`

### B. Login
- **Method:** `POST`
- **Endpoint:** `/auth/login`
- **Body (JSON):**
  ```json
    {
    "email": "user@student.ub.ac.id",
    "password": "Password123!"
    }
- **Success Response:** `200 OK`
- **Catatan:** `Akan mengembalikan access_token yang harus disimpan oleh FE di local storage atau secure storage.`

### 2. Mind Check / Machine Learning (`/mind-checks`)
> 🔒 Semua endpoint ini membutuhkan **Bearer Token**.

#### A. Submit Mind Check Baru
- **Method:** `POST`
- **Endpoint:** `/mind-checks`
- **Body (JSON):**
```json
  {
      "mental_health_index": 2,
      "depression_score": 21,
      "anxiety_score": 19,
      "stress_score": 14,
      "sleep_hours": 3,
      "study_hours": 14
  }
```
- **Success Response:** `201 Created`
- **Catatan:** Mengembalikan hasil prediksi AI berupa `focus_level_pct`, `burnout_level_pct`, dan `analysis_message`.

#### B. Get Riwayat Mind Check
- **Method:** `GET`
- **Endpoint:** `/mind-checks`
- **Success Response:** `200 OK`
- **Catatan:** Mengembalikan array riwayat check-in diurutkan dari yang terbaru.

---

### 3. Dashboard & Profile (`/dashboard`, `/profile`)
> 🔒 Semua endpoint ini membutuhkan **Bearer Token**.

#### A. Get Dashboard Agregasi
- **Method:** `GET`
- **Endpoint:** `/dashboard`
- **Success Response:** `200 OK`
- **Deskripsi:** Endpoint utama untuk halaman Home FE. Mengembalikan sapaan user, status mind check terbaru, serta daftar jurnal dan jadwal terdekat dalam satu tarikan data JSON.

#### B. Get User Profile
- **Method:** `GET`
- **Endpoint:** `/profile`
- **Success Response:** `200 OK`
- **Deskripsi:** Mengembalikan data profil user seperti `full_name` dan `institution` dari tabel `profiles`.

---

### 4. Schedules / Jadwal (`/schedules`)
> 🔒 Semua endpoint ini membutuhkan **Bearer Token**.

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/schedules` | Mengambil semua jadwal milik user yang sedang login. |
| `POST` | `/schedules` | Membuat jadwal baru. |
| `PUT` | `/schedules/<id>` | Mengedit jadwal yang sudah ada (membutuhkan ID jadwal). |
| `DELETE` | `/schedules/<id>` | Menghapus jadwal. |

**Format Body untuk `POST` / `PUT`:**
```json
{
    "task_name": "Laporan",
    "deadline": "2026-06-10 10:00:00",
    "priority": "High"
}
```

---

### 5. Journals / Jurnal (`/journals`)
> 🔒 Semua endpoint ini membutuhkan **Bearer Token**.

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/journals` | Mengambil semua entri jurnal milik user. |
| `POST` | `/journals` | Membuat jurnal baru. |
| `PUT` | `/journals/<id>` | Mengedit jurnal yang sudah ada (membutuhkan ID jurnal). |
| `DELETE` | `/journals/<id>` | Menghapus jurnal. |

**Format Body untuk `POST` / `PUT`:**
```json
{
    "title": "Hari yang lelah",
    "content": "Banyak revisi",
    "mood_emoji": "🥲"
}
```

---

## 🛠️ Status Codes yang Digunakan

| Kode | Status | Keterangan |
|------|--------|------------|
| `200` | OK | Request berhasil. |
| `201` | Created | Data baru berhasil dibuat (Register, POST jadwal/jurnal/mind check). |
| `400` | Bad Request | Ada format JSON yang salah atau body request kosong. |
| `401` | Unauthorized | Token tidak ada, *expired*, atau salah. FE harus mengarahkan user kembali ke halaman Login. |
| `404` | Not Found | URL tidak dikenali atau data tidak ditemukan (terutama saat akses Edit/Delete pada ID yang salah). |
| `422` | Unprocessable Entity | Field wajib pada input Mind Check ada yang terlewat. |
| `500` | Internal Server Error | Terjadi kesalahan pada server, ML Predictor, atau koneksi database Supabase. |