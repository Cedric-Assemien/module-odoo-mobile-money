# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MMStatsReportWizard(models.TransientModel):
    _name = "mm.stats.report.wizard"
    _description = "Assistant de génération de rapport statistiques"

    date_from = fields.Date(string="Du", default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string="Au", default=lambda self: fields.Date.context_today(self))
    include_clients = fields.Boolean(string="Inclure Clients", default=True)
    include_agents = fields.Boolean(string="Inclure Agents", default=True)
    include_service_points = fields.Boolean(string="Inclure Points de Service", default=True)
    include_transactions = fields.Boolean(string="Inclure Transactions", default=True)
    top_n = fields.Integer(string="Top N Agents", default=10)
    ranking_metric = fields.Selection(
        [
            ("amount", "Par Montant"),
            ("count", "Par Nombre de Transactions"),
        ],
        string="Critère de Classement",
        default="amount",
    )

    def action_generate(self):
        self.ensure_one()
        data = {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "include": {
                "clients": self.include_clients,
                "agents": self.include_agents,
                "service_points": self.include_service_points,
                "transactions": self.include_transactions,
            },
            "top_n": self.top_n or 10,
            "ranking_metric": self.ranking_metric or "amount",
        }
        return self.env.ref("mm_manager.mm_stats_report_action").report_action(self, data=data)
