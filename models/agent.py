# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MobileMoneyAgent(models.Model):
    _name = "mm.agent"
    _description = "Mobile Money Agent"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nom", compute="_compute_name", store=True)
    user_id = fields.Many2one(
        "res.users",
        string="Utilisateur",
        required=True,
        tracking=True,
        domain=[("share", "=", False)],
    )
    service_point_id = fields.Many2one("mm.service.point", string="Point de Service", tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True, index=True
    )

    transaction_ids = fields.One2many(
        "mm.transaction", "agent_id", string="Transactions"
    )
    transaction_count = fields.Integer(
        string="Nb. Transactions", compute="_compute_stats", store=False
    )
    transaction_total_amount = fields.Monetary(
        string="Total Montant", compute="_compute_stats", store=False, currency_field="currency_id"
    )
    last_transaction_date = fields.Date(
        string="Dernière Transaction", compute="_compute_stats", store=False
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True, readonly=True
    )

    _sql_constraints = [
        (
            "mm_agent_user_unique",
            "unique(user_id, company_id)",
            "Un agent par utilisateur et par société doit être unique.",
        ),
    ]

    @api.depends("user_id")
    def _compute_name(self):
        for rec in self:
            rec.name = (rec.user_id.name or "")

    def _compute_stats(self):
        for rec in self:
            txs = rec.transaction_ids.filtered(lambda t: t.state == "confirmed")
            rec.transaction_count = len(txs)
            rec.transaction_total_amount = sum(txs.mapped("amount"))
            rec.last_transaction_date = max(txs.mapped("transaction_date")) if txs else False

    def action_open_transactions(self):
        self.ensure_one()
        action = self.env.ref("mm_manager.mm_transaction_action").read()[0]
        action["domain"] = [
            ("agent_id", "=", self.user_id.id),
            ("state", "!=", "draft"),
        ]
        return action

    # --- Synchronisation des utilisateurs en agents ---
    @api.model
    def _create_from_user(self, user):
        """Créer un enregistrement mm.agent pour un utilisateur s'il n'existe pas.
        Respecte la contrainte d'unicité (user_id, company_id)."""
        if not user or user.share:
            return self.browse()
        company = user.company_id or self.env.company
        existing = self.search([
            ("user_id", "=", user.id), ("company_id", "=", company.id)
        ], limit=1)
        if existing:
            return existing
        return self.create({
            "user_id": user.id,
            "service_point_id": False,
            "company_id": company.id,
        })

    @api.model
    def sync_users_as_agents(self):
        """Créer les mm.agent manquants pour tous les utilisateurs internes (non-partagés)."""
        users = self.env["res.users"].search([("share", "=", False)])
        for u in users:
            self._create_from_user(u)
        # Désactiver le cron "une fois" après exécution pour émuler l'ancien numbercall=1
        try:
            cron = self.env.ref("mm_manager.ir_cron_mm_agent_sync_once", raise_if_not_found=False)
            if cron and cron.active:
                cron.active = False
        except Exception:
            # Ne jamais bloquer l'exécution si la référence n'existe pas
            pass
        return True
