from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

ACTIVE_STATES = ("submitted", "approved")


class LabBooking(models.Model):
    _name = "lab.booking"
    _description = "Peminjaman Lab"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(
        string="No. Peminjaman", default=lambda self: _("New"), readonly=True, copy=False
    )
    user_id = fields.Many2one(
        "res.users",
        string="Peminjam",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    room_id = fields.Many2one(
        "lab.room", string="Ruang / Alat", required=True, tracking=True
    )
    start_datetime = fields.Datetime(string="Mulai", required=True, tracking=True)
    end_datetime = fields.Datetime(string="Selesai", required=True, tracking=True)
    duration = fields.Float(string="Durasi (jam)", compute="_compute_duration", store=True)
    purpose = fields.Text(string="Keperluan", required=True)
    participant_count = fields.Integer(string="Jumlah Peserta", default=1)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Diajukan"),
            ("approved", "Disetujui"),
            ("rejected", "Ditolak"),
            ("done", "Selesai"),
            ("cancelled", "Dibatalkan"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    approver_id = fields.Many2one("res.users", string="Disetujui oleh", readonly=True, copy=False)
    reject_reason = fields.Text(string="Alasan Penolakan", copy=False)
    can_approve = fields.Boolean(compute="_compute_can_approve")

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = (
                    self.env["ir.sequence"].sudo().next_by_code("lab.booking") or _("New")
                )
        return super().create(vals_list)

    # -------------------------------------------------------------- compute
    @api.depends("start_datetime", "end_datetime")
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0.0

    @api.depends_context("uid")
    def _compute_can_approve(self):
        is_head = self.env.user.has_group("lab_booking.group_lab_head")
        for rec in self:
            rec.can_approve = is_head

    # ---------------------------------------------------------- constraints
    @api.constrains("start_datetime", "end_datetime")
    def _check_dates(self):
        for rec in self:
            if rec.end_datetime <= rec.start_datetime:
                raise ValidationError(_("Waktu selesai harus setelah waktu mulai."))

    @api.constrains("participant_count", "room_id")
    def _check_capacity(self):
        for rec in self:
            if rec.participant_count < 1:
                raise ValidationError(_("Jumlah peserta minimal 1."))
            cap = rec.room_id.capacity
            if cap and rec.participant_count > cap:
                raise ValidationError(
                    _("Jumlah peserta (%s) melebihi kapasitas %s (%s).")
                    % (rec.participant_count, rec.room_id.name, cap)
                )

    @api.constrains("room_id", "start_datetime", "end_datetime", "state")
    def _check_overlap(self):
        # sudo: mahasiswa tidak bisa membaca booking orang lain (record rule),
        # tapi bentrok jadwal tetap harus terdeteksi.
        Booking = self.sudo()
        for rec in self:
            if rec.state not in ACTIVE_STATES:
                continue
            clash = Booking.search(
                [
                    ("id", "!=", rec.id),
                    ("room_id", "=", rec.room_id.id),
                    ("state", "in", ACTIVE_STATES),
                    ("start_datetime", "<", rec.end_datetime),
                    ("end_datetime", ">", rec.start_datetime),
                ],
                limit=1,
            )
            if clash:
                raise ValidationError(
                    _("%s sudah dipesan pada rentang waktu tersebut (%s).")
                    % (rec.room_id.name, clash.name)
                )

    # -------------------------------------------------------------- helpers
    def _is_assistant(self):
        return self.env.user.has_group("lab_booking.group_lab_assistant")

    def _is_head(self):
        return self.env.user.has_group("lab_booking.group_lab_head")

    def _check_owner_or_assistant(self):
        if self._is_assistant():
            return
        for rec in self:
            if rec.user_id != self.env.user:
                raise AccessError(_("Anda hanya bisa mengubah peminjaman milik sendiri."))

    def _check_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(
                    _("Aksi ini tidak bisa dilakukan pada status '%s'.")
                    % dict(self._fields["state"].selection)[rec.state]
                )

    # -------------------------------------------------------------- actions
    def action_submit(self):
        self._check_owner_or_assistant()
        self._check_state(("draft",))
        self.write({"state": "submitted"})

    def action_approve(self):
        if not self._is_head():
            raise AccessError(_("Hanya Kepala Lab yang dapat menyetujui peminjaman."))
        self._check_state(("submitted",))
        self.write({"state": "approved", "approver_id": self.env.user.id, "reject_reason": False})

    def action_reject(self):
        if not self._is_head():
            raise AccessError(_("Hanya Kepala Lab yang dapat menolak peminjaman."))
        self._check_state(("submitted",))
        for rec in self:
            if not rec.reject_reason:
                raise UserError(_("Isi alasan penolakan terlebih dahulu."))
        self.write({"state": "rejected"})

    def action_done(self):
        if not self._is_assistant():
            raise AccessError(_("Hanya Asisten/Kepala Lab yang dapat menandai selesai."))
        self._check_state(("approved",))
        self.write({"state": "done"})

    def action_cancel(self):
        self._check_owner_or_assistant()
        self._check_state(("draft", "submitted", "approved"))
        # sudo: record rule mahasiswa hanya mengizinkan write saat draft
        self.sudo().write({"state": "cancelled"})

    def action_reset_draft(self):
        self._check_owner_or_assistant()
        self._check_state(("rejected", "cancelled"))
        self.sudo().write({"state": "draft", "approver_id": False})
