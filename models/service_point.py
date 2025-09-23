# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyServicePoint(models.Model):
    _name = "mm.service.point"
    _description = "Mobile Money Service Point"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nom", required=True, tracking=True)
    code = fields.Char(string="Code", required=True, tracking=True)
    owner_id = fields.Many2one(
        "res.users",
        string="Propriétaire",
        help="Utilisateur responsable du point de service.",
        tracking=True,
    )
    agent_ids = fields.Many2many(
        "res.users",
        relation="mm_service_point_agent_rel",
        column1="service_point_id",
        column2="user_id",
        string="Agents",
        domain=[("share", "=", False)],
        help="Agents autorisés à opérer sur ce point de service.",
    )
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company, index=True, required=True)
    network_ids = fields.Many2many(
        "mm.network",
        relation="mm_service_point_network_rel",
        column1="service_point_id",
        column2="network_id",
        string="Réseaux Supportés",
    )
    active = fields.Boolean(string="Actif", default=True)
    # Localisation
    street = fields.Char(string="Adresse")
    city = fields.Char(string="Ville")
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")

    # Statistiques
    agent_count = fields.Integer(string="Nombre d'agents", compute="_compute_counts", store=False)
    transaction_count = fields.Integer(string="Nb. transactions", compute="_compute_counts", store=False)
    transaction_total_amount = fields.Monetary(string="Total Montant", compute="_compute_total", store=False, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True, readonly=True)

    _sql_constraints = [
        ("mm_service_point_code_unique", "unique(code, company_id)", "Service point code must be unique per company."),
    ]

    @api.constrains("owner_id")
    def _check_owner_group(self):
        mm_manager_group = self.env.ref("mm_manager.mm_group_manager", raise_if_not_found=False)
        for record in self:
            if record.owner_id and mm_manager_group and mm_manager_group not in record.owner_id.groups_id:
                raise ValidationError("Le propriétaire doit faire partie du groupe Gestionnaire Mobile Money.")

    def _compute_counts(self):
        for rec in self:
            rec.agent_count = len(rec.agent_ids)
            rec.transaction_count = self.env["mm.transaction"].search_count([
                ("service_point_id", "=", rec.id), ("state", "=", "confirmed")
            ])

    def _compute_total(self):
        for rec in self:
            txs = self.env["mm.transaction"].search([
                ("service_point_id", "=", rec.id), ("state", "=", "confirmed")
            ])
            rec.transaction_total_amount = sum(txs.mapped("amount"))