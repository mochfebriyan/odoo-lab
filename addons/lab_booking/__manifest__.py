{
    "name": "Lab Booking FIK",
    "summary": "Peminjaman ruang & alat laboratorium FIK UPNVJ",
    "description": """
MVP modul peminjaman ruang/alat laboratorium FIK.

- CRUD ruang/alat dan peminjaman
- Workflow: Draft -> Diajukan -> Disetujui/Ditolak -> Selesai
- 3 role: Mahasiswa, Asisten Lab, Kepala Lab
- Record rule: mahasiswa hanya melihat peminjaman miliknya
- Validasi jadwal bentrok & kapasitas ruang
    """,
    "version": "17.0.1.0.0",
    "category": "Services",
    "author": "Kelompok LabFIK - SI UPNVJ",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/lab_room_views.xml",
        "views/lab_booking_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "application": True,
    "installable": True,
}
