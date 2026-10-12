from odoo import _, api, models
from odoo.exceptions import UserError

PRINTABLE_STATES = ("approved", "done")


class ReportBookingReceipt(models.AbstractModel):
    _name = "report.lab_booking.report_booking_receipt"
    _description = "Bukti Peminjaman Lab"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["lab.booking"].browse(docids)
        # bukti hanya sah untuk peminjaman yang sudah disetujui,
        # termasuk saat dicetak lewat menu Print di tree view
        not_printable = docs.filtered(lambda b: b.state not in PRINTABLE_STATES)
        if not_printable:
            raise UserError(
                _("Bukti peminjaman hanya bisa dicetak untuk peminjaman yang sudah disetujui: %s")
                % ", ".join(not_printable.mapped("name"))
            )
        return {
            "doc_ids": docids,
            "doc_model": "lab.booking",
            "docs": docs,
        }
