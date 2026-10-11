# Odoo Lab FIK — MVP `lab_booking`

Modul Odoo 17 untuk peminjaman ruang & alat laboratorium FIK UPNVJ.
MVP tahap awal proyek LabFIK Compliance.

## Struktur repo

```
odoo-lab/
├── docker-compose.yml          # Odoo 17 + PostgreSQL 16
├── config/
│   └── odoo.conf
├── addons/
│   └── lab_booking/
│       ├── __manifest__.py     # metadata & daftar file yg di-load
│       ├── __init__.py
│       ├── models/
│       │   ├── lab_room.py     # master ruang/alat
│       │   └── lab_booking.py  # peminjaman + workflow + validasi
│       ├── security/
│       │   ├── security.xml    # 3 group + record rules
│       │   └── ir.model.access.csv
│       ├── data/sequence.xml   # penomoran LAB/2026/0001
│       ├── views/              # tree, form, calendar, search, menu
│       ├── demo/demo.xml       # ruang, user per role, contoh booking
│       ├── tests/              # unit test
│       └── static/description/icon.png
├── .gitignore
└── .gitattributes
```

## Menjalankan

Prasyarat: Docker Desktop (Windows: backend WSL2, clone repo di dalam WSL).

```bash
docker compose up -d
```

Buka http://localhost:8069, buat database (centang **Demo data**), lalu
Apps → hapus filter "Apps" → cari **Lab Booking FIK** → Install.

## Akun demo (jika demo data aktif)

| Login | Password | Role |
|---|---|---|
| `mahasiswa` | `mahasiswa` | Mahasiswa |
| `asisten` | `asisten` | Asisten Lab |
| `kepala` | `kepala` | Kepala Lab |
| `admin` | (saat buat DB) | Kepala Lab + admin |

## Role & hak akses

| | Mahasiswa | Asisten Lab | Kepala Lab |
|---|---|---|---|
| Lihat peminjaman | milik sendiri | semua | semua |
| Buat/ubah peminjaman | milik sendiri, saat Draft | semua | semua |
| Hapus peminjaman | – | – | ✓ |
| Kelola ruang/alat | lihat saja | buat/ubah | penuh |
| Setujui / tolak | – | – | ✓ |
| Tandai selesai | – | ✓ | ✓ |

## Workflow

```
Draft → Diajukan → Disetujui → Selesai
             ↘ Ditolak (wajib alasan)
Draft/Diajukan/Disetujui → Dibatalkan
Ditolak/Dibatalkan → Draft
```

Validasi: waktu selesai > mulai, peserta ≤ kapasitas ruang,
dan tidak boleh bentrok dengan booking lain yang Diajukan/Disetujui di ruang yang sama.

## Perintah sehari-hari

```bash
# upgrade modul setelah ubah model/field/security
docker compose exec odoo odoo -d NAMA_DB -u lab_booking --stop-after-init --no-http
docker compose restart odoo

# jalankan unit test (pakai DB terpisah)
docker compose exec odoo odoo -d test_lab -i lab_booking --test-enable \
  --test-tags=/lab_booking --stop-after-init --no-http

# lihat log
docker compose logs -f odoo
```

Perubahan view XML cukup refresh browser (mode `--dev=reload,xml`).
