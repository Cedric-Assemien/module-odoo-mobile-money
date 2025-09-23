# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MobileMoneyDeplafonnementWizard(models.TransientModel):
    _name = "mm.deplafonnement.wizard"
    _description = "Deplafonnement Wizard"

    customer_id = fields.Many2one("mm.customer", required=True)
    identity_type = fields.Selection(
        selection=lambda self: self.env["mm.customer"].IDENTITY_TYPES,
        required=True,
    )
    identity_number = fields.Char(required=True)
    attachment_datas = fields.Binary(required=True, string="Identity Document")
    attachment_filename = fields.Char(string="Filename")
    notes = fields.Text()

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        customer = self.env["mm.customer"].browse(self.env.context.get("default_customer_id"))
        if customer:
            defaults.setdefault("customer_id", customer.id)
            defaults.setdefault("identity_type", customer.identity_type)
            defaults.setdefault("identity_number", customer.identity_number)
        return defaults

    def action_confirm(self):
        self.ensure_one()
        customer = self.customer_id
        if not self.attachment_datas:
            raise UserError("An identity document is required to request the deplafonnement.")

        attachment = customer.create_identity_attachment(self.attachment_datas, self.attachment_filename)
        customer.write({
            "identity_type": self.identity_type,
            "identity_number": self.identity_number,
            "status": "deplafonne",
        })
        customer.action_set_deplafonne_policy()

        message = (
            f"Deplafonnement requested for {customer.name}."
            f" Identity document stored as attachment '{attachment.name}'."
        )
        if self.notes:
            message += f" Notes: {self.notes}."
        customer.message_post(body=message)
        return customer.action_open_transactions()