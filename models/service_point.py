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

    _sql_constraints = [
        ("mm_service_point_code_unique", "unique(code, company_id)", "Service point code must be unique per company."),
    ]

    @api.constrains("owner_id")
    def _check_owner_group(self):
        mm_manager_group = self.env.ref("mm_manager.mm_group_manager", raise_if_not_found=False)
        for record in self:
            if record.owner_id and mm_manager_group and mm_manager_group not in record.owner_id.groups_id:
                raise ValidationError("Le propriétaire doit faire partie du groupe Gestionnaire Mobile Money.")