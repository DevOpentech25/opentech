# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    uy_retention_perception_ids = fields.One2many(
        "uy.retention.perception", "payment_id", string="Retention/Perception"
    )
    uy_retention_perception_amount = fields.Monetary(
        string="Retention/Perception Amount",
        compute="_compute_uy_retention_perception_amount",
    )
    uy_is_cfe = fields.Boolean("Is CFE", compute="_cumpute_uy_is_cfe")
    # uy_is_refund = fields.Boolean("Is Refund")

    def action_uy_refund(self):
        payment_ids = self.env["account.payment"]
        payment_type = False
        for payment_id in self:
            if not payment_id.uy_is_cfe and not payment_id.state == "posted":
                raise UserError(_("Only CFE payments can be refunded"))
            if payment_id.reversed_entry_id:
                raise UserError(_("This payment has already been refunded"))
            vals = {}
            if payment_id.payment_type == "inbound" and not payment_type:
                payment_type = "inbound"
            vals["reversed_entry_id"] = payment_id.move_id.id
            if payment_id.payment_type == "inbound":
                vals["payment_type"] = "outbound"
            else:
                vals["payment_type"] = "inbound"
            vals["ref"] = payment_id.name
            payment_new_id = payment_id.copy()
            for retention_perception in payment_id.uy_retention_perception_ids:
                retention_perception.copy(default={"payment_id": payment_new_id.id})
            # payment_new_id._compute_outstanding_account_id()
            # payment_new_id._compute_destination_account_id()
            payment_new_id.write(vals)
            payment_ids |= payment_new_id
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_account_payments"
        )
        if len(payment_ids) > 1:
            action["domain"] = [("id", "in", payment_ids.ids)]
        elif len(payment_ids) == 1:
            form_view = [(self.env.ref("account.view_account_payment_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = payment_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        if payment_type:
            context = {
                "default_payment_type": "inbound",
                "default_partner_type": "customer",
                "search_default_inbound_filter": 1,
                "default_move_journal_types": ("bank", "cash"),
            }
        else:
            context = {
                "default_payment_type": "outbound",
                "default_partner_type": "supplier",
                "search_default_outbound_filter": 1,
                "default_move_journal_types": ("bank", "cash"),
            }
        if len(self) == 1:
            context.update(
                {
                    "default_partner_id": self.partner_id.id,
                    "default_ref": self.name,
                }
            )
        action["context"] = context
        return action

    @api.depends("uy_retention_perception_ids", "uy_retention_perception_ids.amount")
    def _compute_uy_retention_perception_amount(self):
        for record in self:
            record.uy_retention_perception_amount = sum(
                record.uy_retention_perception_ids.mapped("amount")
            )

    def action_post(self):
        for payment in self:
            if payment.uy_is_cfe and not payment.uy_retention_perception_ids:
                raise UserError(_("CFE must have Retention/Perception"))
            if (
                payment.uy_retention_perception_ids
                and payment.uy_is_cfe
                and round(payment.uy_retention_perception_amount, 2)
                != round(payment.amount, 2)
            ):
                payment.amount = payment.uy_retention_perception_amount
        res = super(AccountPayment, self).action_post()
        return res

    def _synchronize_to_moves(self, changed_fields):
        res = super(AccountPayment, self)._synchronize_to_moves(changed_fields)
        for pay in self.with_context(skip_account_move_synchronization=True):
            pay.move_id.with_context(skip_invoice_sync=True).write(
                {"uy_document_code": pay.journal_id.uy_document_code}
            )
        return res

    @api.depends("journal_id")
    def _cumpute_uy_is_cfe(self):
        for payment in self:
            payment.uy_is_cfe = bool(
                payment.journal_id.edi_format_ids.filtered(
                    lambda j: j.code == "edi_uy_cfe"
                )
            )
