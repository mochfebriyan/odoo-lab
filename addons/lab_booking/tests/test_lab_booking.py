from datetime import datetime, timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestLabBooking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.student_a = new_test_user(cls.env, login="mhs_a", groups="lab_booking.group_lab_student")
        cls.student_b = new_test_user(cls.env, login="mhs_b", groups="lab_booking.group_lab_student")
        cls.head = new_test_user(cls.env, login="kalab", groups="lab_booking.group_lab_head")
        cls.room = cls.env["lab.room"].create(
            {"name": "Lab Test", "code": "TEST", "capacity": 10}
        )
        cls.start = datetime.now().replace(microsecond=0) + timedelta(days=1)

    def _booking(self, user, start, hours=2, **kw):
        vals = {
            "room_id": self.room.id,
            "start_datetime": start,
            "end_datetime": start + timedelta(hours=hours),
            "purpose": "test",
        }
        vals.update(kw)
        return self.env["lab.booking"].with_user(user).create(vals)

    def test_sequence_and_owner(self):
        b = self._booking(self.student_a, self.start)
        self.assertTrue(b.name.startswith("LAB/"))
        self.assertEqual(b.user_id, self.student_a)

    def test_end_before_start(self):
        with self.assertRaises(ValidationError):
            self._booking(self.student_a, self.start, hours=-1)

    def test_capacity(self):
        with self.assertRaises(ValidationError):
            self._booking(self.student_a, self.start, participant_count=99)

    def test_overlap_blocked_on_submit(self):
        b1 = self._booking(self.student_a, self.start)
        b1.action_submit()
        b2 = self._booking(self.student_b, self.start + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            b2.action_submit()

    def test_student_cannot_see_others(self):
        self._booking(self.student_a, self.start)
        visible = self.env["lab.booking"].with_user(self.student_b).search([])
        self.assertFalse(visible)

    def test_only_head_can_approve(self):
        b = self._booking(self.student_a, self.start)
        b.action_submit()
        with self.assertRaises(AccessError):
            b.action_approve()
        b.with_user(self.head).action_approve()
        self.assertEqual(b.state, "approved")
        self.assertEqual(b.approver_id, self.head)

    def test_receipt_pdf_only_when_approved(self):
        b = self._booking(self.student_a, self.start)
        report = self.env["ir.actions.report"]
        with self.assertRaises(UserError):
            report._render_qweb_html("lab_booking.report_booking_receipt", b.ids)
        b.action_submit()
        b.with_user(self.head).action_approve()
        html, _fmt = report.with_user(self.student_a)._render_qweb_html(
            "lab_booking.report_booking_receipt", b.ids
        )
        self.assertIn(b.name, html.decode())
