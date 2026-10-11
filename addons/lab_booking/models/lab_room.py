from odoo import api, fields, models


class LabRoom(models.Model):
    _name = "lab.room"
    _description = "Ruang / Alat Lab"
    _order = "code, name"

    name = fields.Char(string="Nama", required=True)
    code = fields.Char(string="Kode", required=True)
    resource_type = fields.Selection(
        [("room", "Ruang"), ("equipment", "Alat")],
        string="Jenis",
        default="room",
        required=True,
    )
    capacity = fields.Integer(
        string="Kapasitas",
        help="Jumlah maksimal peserta. Isi 0 jika tidak dibatasi.",
    )
    location = fields.Char(string="Lokasi")
    note = fields.Text(string="Catatan / Aturan Pemakaian")
    active = fields.Boolean(default=True)

    booking_ids = fields.One2many("lab.booking", "room_id", string="Peminjaman")
    booking_count = fields.Integer(compute="_compute_booking_count")

    _sql_constraints = [
        ("code_unique", "unique(code)", "Kode ruang/alat harus unik."),
        ("capacity_positive", "CHECK(capacity >= 0)", "Kapasitas tidak boleh negatif."),
    ]

    @api.depends("booking_ids")
    def _compute_booking_count(self):
        for rec in self:
            rec.booking_count = len(rec.booking_ids)

    def action_view_bookings(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Peminjaman",
            "res_model": "lab.booking",
            "view_mode": "tree,calendar,form",
            "domain": [("room_id", "=", self.id)],
            "context": {"default_room_id": self.id},
        }
