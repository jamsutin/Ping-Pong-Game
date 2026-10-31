# Panduan Merapikan Repository Ping-Pong-Game

Panduan ini hanya mengatur nama/lokasi file dan dokumentasi. Jangan mengedit isi kode permainan.

## Target akhir

```text
Ping-Pong-Game/
├── ping_pong_cinematic.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Sebelum mulai

1. Buka repository `https://github.com/jamsutin/Ping-Pong-Game`.
2. Unduh salinan ZIP repository sebagai cadangan.
3. Ekstrak ZIP dan pastikan file sumber `Kode Game` terlihat.
4. Jangan menghapus file sumber lama sebelum file baru berhasil diunggah dan diperiksa.

## Langkah 1 — Ganti nama file kode

Ubah nama file `Kode Game` menjadi:

`ping_pong_cinematic.py`

Pastikan ekstensi `.py` benar-benar menjadi bagian nama file, bukan tersembunyi atau berubah menjadi `.py.txt`.

**Jangan mengubah isi kode.** Nama ini sesuai dengan perintah menjalankan yang tertulis di komentar kode.

## Langkah 2 — Pindahkan ke direktori utama

Unggah `ping_pong_cinematic.py` ke direktori utama repository (sejajar dengan `README.md`), bukan di dalam folder `Kode Game`.

Setelah file baru dipastikan tampil dan dapat dibuka di GitHub, hapus file lama `Kode Game` atau folder lama yang menampungnya. Jika GitHub menampilkan file lama sebagai satu file bernama `Kode Game`, hapus file tersebut setelah verifikasi.

## Langkah 3 — Ganti README

Buka `README.md` di direktori utama repository, pilih Edit, ganti seluruh isinya dengan file `README.md` yang disediakan dalam paket ini, lalu commit.

## Langkah 4 — Tambahkan requirements.txt

Buat file baru bernama `requirements.txt` di direktori utama. Isi dengan:

```text
pygame>=2.5.0
```

Commit perubahan.

## Langkah 5 — Tambahkan .gitignore

Buat file baru bernama `.gitignore` di direktori utama. Salin isi file `.gitignore` dari paket ini, lalu commit.

## Langkah 6 — Periksa repository

Pastikan halaman utama GitHub menampilkan:
- `ping_pong_cinematic.py`
- `README.md`
- `requirements.txt`
- `.gitignore`

Pastikan repository tetap berstatus **Public**.

## Langkah 7 — Uji dari salinan bersih

1. Unduh ZIP dari GitHub setelah perubahan selesai.
2. Ekstrak ke folder baru.
3. Buka terminal di folder tersebut.
4. Jalankan `py -m pip install -r requirements.txt`.
5. Jalankan `py ping_pong_cinematic.py`.
6. Coba menu, mode 1 pemain, mode 2 pemain, suara, fullscreen, serta simpan/muat pengaturan.

Jika ada error, salin pesan error lengkap dari terminal untuk ditelusuri.

## Catatan penting

- Jangan membuat file kode baru dari salinan yang sudah diedit sebagian. Gunakan file `Kode Game` asli dan hanya ubah namanya.
- Jangan mengunggah dua file kode utama dengan isi yang sama.
- Jangan commit folder `.venv/`, `__pycache__/`, atau file pengaturan pribadi.
- `LICENSE` tidak ditambahkan otomatis karena pemilihan lisensi menentukan izin penggunaan ulang kode. Tambahkan hanya setelah memilih lisensi yang sesuai.
- File audio eksternal tidak diperlukan menurut komentar kode sumber: efek suara dan musik dibuat oleh program.
