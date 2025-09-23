# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyNetwork(models.Model):
    _name = "mm.network"
    _description = "Mobile Money Network"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nom", required=True, tracking=True)
    code = fields.Char(string="Code", required=True, tracking=True)
    fee_percentage = fields.Float(
        string="Frais %",
        default=1.0,
        help="Pourcentage par défaut appliqué sur le montant pour calculer les frais.",
    )
    active = fields.Boolean(string="Actif", default=True)
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company, index=True)

    _sql_constraints = [
        ("mm_network_code_unique", "unique(code, company_id)", "The network code must be unique per company."),
    ]

    @api.constrains("fee_percentage")
    def _check_fee_percentage(self):
        for record in self:
            if record.fee_percentage < 0:
                raise ValidationError("Le pourcentage de frais ne peut pas être négatif.")