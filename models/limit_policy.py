# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyLimitPolicy(models.Model):
    _name = "mm.limit.policy"
    _description = "Mobile Money Limit Policy"
    _rec_name = "display_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nom", required=True, tracking=True)
    code = fields.Selection(
        selection=[("standard", "Standard"), ("deplafonne", "Déplafonné")],
        string="Code",
        required=True,
        tracking=True,
    )
    per_transaction_limit = fields.Monetary(string="Limite par Transaction", required=True, tracking=True, currency_field="currency_id")
    monthly_limit = fields.Monetary(string="Limite Mensuelle", required=True, tracking=True, currency_field="currency_id")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Actif", default=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        string="Devise",
    )
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company, index=True, required=True)
    display_name = fields.Char(string="Nom d'Affichage", compute="_compute_display_name", store=True)
    requires_identity_attachment = fields.Boolean(
        string="Nécessite une Pièce d'Identité",
        help="Indique si la politique nécessite le téléchargement d'une pièce d'identité scannée.",
    )

    _sql_constraints = [
        ("mm_limit_policy_code_unique", "unique(code, company_id)", "Only one policy per status is allowed per company."),
    ]

    @api.depends("name", "code")
    def _compute_display_name(self):
        for record in self:
            label = dict(self._fields["code"].selection).get(record.code or False, "")
            if record.name and label:
                record.display_name = f"{record.name} ({label})"
            else:
                record.display_name = record.name or label

    @api.constrains("per_transaction_limit", "monthly_limit")
    def _check_limits(self):
        for record in self:
            if record.per_transaction_limit <= 0:
                raise ValidationError("Per transaction limit must be strictly positive.")
            if record.monthly_limit <= 0:
                raise ValidationError("Monthly limit must be strictly positive.")
            if record.per_transaction_limit > record.monthly_limit:
                raise ValidationError("Monthly limit must be greater than or equal to the per transaction limit.")

    @api.model
    def get_policy_by_code(self, code):
        return self.search([
            ("code", "=", code),
            ("company_id", "=", self.env.company.id),
            ("active", "=", True),
        ], limit=1)