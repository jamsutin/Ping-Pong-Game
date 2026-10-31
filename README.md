# 🏓 Ping-Pong Game — Cinematic Skill Edition

Game ping-pong klasik yang dikembangkan menjadi permainan desktop dengan tampilan modern, efek visual, pilihan arena, karakter, dan kemampuan khusus.

Repository ini dibuat sebagai proyek tugas sekolah. Konsep dan ide permainan dikembangkan oleh **jamsutin**, dengan bantuan **Claude AI** sebagai asisten selama proses coding.

## ✨ Fitur

- Mode **1 pemain** melawan komputer.
- Mode **2 pemain** menggunakan satu keyboard.
- Pilihan karakter, skin, aksesori, dan nama pemain.
- Enam arena: Neon Arena, Jalan Raya, Gunung Volcano, Pasar Tradisional, Lab Kimia, dan Medan Perang.
- Tujuh kemampuan khusus melalui Mystery Box.
- Efek visual, animasi, dan latar arena yang dibuat melalui kode.
- Musik latar dan efek suara yang dibuat secara otomatis oleh program.
- Pengaturan permainan disimpan secara lokal dalam `ping_pong_settings.json`.

> Catatan: suara dibuat oleh program. Repository tidak memerlukan file audio eksternal.

## 🧰 Teknologi

- Python 3
- Pygame

## 📋 Persyaratan

Sebelum menjalankan game, pastikan komputer sudah memiliki:

1. Python 3 yang terpasang.
2. `pip` untuk memasang library Python.
3. Sistem operasi desktop yang mendukung Pygame (Windows, macOS, atau Linux).
4. Keyboard untuk mengontrol permainan.

## 🚀 Instalasi dan Cara Menjalankan

### 1. Unduh repository

Klik tombol **Code** pada halaman GitHub, lalu pilih **Download ZIP**. Ekstrak file ZIP ke folder yang mudah ditemukan.

Alternatif menggunakan Git:

```bash
git clone https://github.com/jamsutin/Ping-Pong-Game.git
cd Ping-Pong-Game
```

### 2. Buka terminal di folder proyek

Pastikan terminal berada di folder yang berisi `ping_pong_cinematic.py` dan `requirements.txt`.

### 3. (Disarankan) Buat virtual environment

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Pasang dependensi

Windows:

```powershell
py -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m pip install -r requirements.txt
```

### 5. Jalankan game

Windows:

```powershell
py ping_pong_cinematic.py
```

macOS / Linux:

```bash
python3 ping_pong_cinematic.py
```

## 🎮 Kontrol Permainan

### Menu

| Tombol | Fungsi |
|---|---|
| `TAB` | Berpindah halaman menu |
| `↑` / `↓` | Memilih baris menu |
| `←` / `→` | Mengubah pilihan |
| Ketik | Mengisi nama pemain |
| `ENTER` | Memulai permainan |

### Mode 1 pemain

| Tombol | Fungsi |
|---|---|
| `↑` / `W` | Menggerakkan paddle ke atas |
| `↓` / `S` | Menggerakkan paddle ke bawah |
| `SPACE` | Menggunakan skill |
| `P` atau `ESC` | Pause |

### Mode 2 pemain (satu keyboard)

| Pemain | Tombol | Fungsi |
|---|---|---|
| Pemain 1 (kiri) | `W` | Bergerak ke atas |
| Pemain 1 (kiri) | `S` | Bergerak ke bawah |
| Pemain 1 (kiri) | `D` | Menggunakan skill |
| Pemain 2 (kanan) | `P` | Bergerak ke atas |
| Pemain 2 (kanan) | `L` | Bergerak ke bawah |
| Pemain 2 (kanan) | `K` | Menggunakan skill |
| Semua pemain | `ESC` | Pause |

### Tombol umum

| Tombol | Fungsi |
|---|---|
| `M` | Mengaktifkan / menonaktifkan suara |
| `F11` | Mengaktifkan / menonaktifkan fullscreen |
| `ENTER` | Bermain kembali setelah game over |
| `ESC` | Kembali ke menu setelah game over |

**Target kemenangan:** pemain pertama yang mencapai 5 poin akan memenangkan pertandingan.

## 🧩 Kemampuan Khusus

Mystery Box dapat memberikan salah satu kemampuan berikut:

1. **Lightning Shot** — pukulan berikutnya menjadi tembakan petir yang sangat cepat.
2. **Za Warudo** — memperlambat gerakan lawan.
3. **Kagebunsin** — membuat klon paddle dengan gerakan terbalik.
4. **Nano Shield** — perlindungan sementara agar tidak kebobolan.
5. **Fish Throw** — melempar ikan untuk membuat lawan terkena stun.
6. **Light Speed** — meningkatkan kecepatan pemain sementara.
7. **Black Hole** — kemampuan langka yang dapat memenangkan ronde.

## 🗺️ Arena dan Event

| Arena | Event |
|---|---|
| Neon Arena | Arena standar tanpa event khusus |
| Jalan Raya | Kendaraan melintas dan dapat membuat pemain terkena stun |
| Gunung Volcano | Semburan lava dapat memperlambat pemain |
| Pasar Tradisional | Barang yang dilempar dapat menonaktifkan skill sementara |
| Lab Kimia | Botol racikan dapat membalik kontrol pemain |
| Medan Perang | Serangan proyektil dan bom dapat mengganggu pemain |

## 📁 Struktur Repository

```text
Ping-Pong-Game/
├── ping_pong_cinematic.py   # Kode utama permainan
├── README.md                # Dokumentasi proyek
├── requirements.txt         # Dependensi Python
├── .gitignore               # File yang tidak perlu diunggah
└── ping_pong_settings.json  # Dibuat otomatis saat game menyimpan pengaturan
```

`ping_pong_settings.json` merupakan file pengaturan lokal yang dibuat oleh game. File tersebut tidak wajib diunggah ke repository.

## ⚙️ Penyimpanan Pengaturan

Pengaturan seperti nama, karakter, skin, dan map disimpan secara lokal di `ping_pong_settings.json`. Jika file belum ada, game akan membuatnya ketika diperlukan.

## 🛠️ Pemecahan Masalah

**Error `No module named 'pygame'`**

Pasang dependensi dengan:

```bash
py -m pip install -r requirements.txt
```

**Perintah `py` tidak dikenali**

Pastikan Python sudah terpasang dan masuk ke PATH. Pada macOS/Linux, gunakan `python3` sebagai pengganti `py`.

**Game tidak terbuka atau langsung berhenti**

- Jalankan game dari terminal agar pesan error terlihat.
- Pastikan terminal berada di folder yang sama dengan `ping_pong_cinematic.py`.
- Pastikan Pygame berhasil dipasang pada interpreter Python yang digunakan untuk menjalankan game.

## 👨‍💻 Kredit

- **Pengembang:** jamsutin
- **Asisten coding AI:** Claude AI
- **Jenis proyek:** Tugas sekolah / proyek pembelajaran pemrograman

Ide dan konsep proyek merupakan karya pengembang. AI digunakan sebagai alat bantu selama proses pengembangan.

---

Terima kasih telah mengunjungi repository ini. Selamat bermain! 🏓
