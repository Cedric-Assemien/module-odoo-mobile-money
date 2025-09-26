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
    balance_ids = fields.One2many("mm.agent.balance", "agent_id", string="Soldes Agent")
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
    total_network_balance = fields.Monetary(
        string="Total Soldes Opérateurs", 
        compute="_compute_total_balances", 
        store=False, 
        currency_field="currency_id"
    )
    cash_balance = fields.Monetary(
        string="Solde Caisse", 
        compute="_compute_total_balances", 
        store=False, 
        currency_field="currency_id"
    )
    total_balance = fields.Monetary(
        string="Solde Total", 
        compute="_compute_total_balances", 
        store=False, 
        currency_field="currency_id"
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

    @api.depends("balance_ids.balance", "balance_ids.balance_type")
    def _compute_total_balances(self):
        for rec in self:
            network_balances = rec.balance_ids.filtered(lambda b: b.balance_type == "network")
            cash_balances = rec.balance_ids.filtered(lambda b: b.balance_type == "cash")
            
            rec.total_network_balance = sum(network_balances.mapped("balance"))
            rec.cash_balance = sum(cash_balances.mapped("balance"))  # Devrait être 1 seul solde de caisse
            rec.total_balance = rec.total_network_balance + rec.cash_balance

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

    def get_balance_for_network(self, network_id):
        """Obtenir le solde pour un opérateur spécifique"""
        self.ensure_one()
        balance = self.balance_ids.filtered(
            lambda b: b.balance_type == "network" and b.network_id.id == network_id
        )
        if balance:
            return balance[0].balance
        return 0.0

    def get_cash_balance(self):
        """Obtenir le solde de caisse"""
        self.ensure_one()
        balance = self.balance_ids.filtered(lambda b: b.balance_type == "cash")
        if balance:
            return balance[0].balance
        return 0.0

    def get_or_create_network_balance(self, network_id):
        """Obtenir ou créer un solde pour un opérateur donné"""
        self.ensure_one()
        return self.env["mm.agent.balance"].get_or_create_agent_balance(
            self.id, "network", network_id
        )

    def get_or_create_cash_balance(self):
        """Obtenir ou créer le solde de caisse"""
        self.ensure_one()
        return self.env["mm.agent.balance"].get_or_create_agent_balance(
            self.id, "cash"
        )

    def check_network_balance(self, network_id, amount):
        """Vérifier si l'agent a suffisamment de solde pour un opérateur"""
        self.ensure_one()
        balance_record = self.get_or_create_network_balance(network_id)
        return balance_record.check_sufficient_balance(amount)

    def check_cash_balance(self, amount):
        """Vérifier si l'agent a suffisamment de liquidités en caisse"""
        self.ensure_one()
        balance_record = self.get_or_create_cash_balance()
        return balance_record.check_sufficient_balance(amount)

    def action_view_balances(self):
        """Voir tous les soldes de l'agent"""
        self.ensure_one()
        action = {
            "name": "Soldes Agent",
            "type": "ir.actions.act_window",
            "res_model": "mm.agent.balance",
            "view_mode": "tree,form",
            "domain": [("agent_id", "=", self.id)],
            "context": {"default_agent_id": self.id},
        }
        return action

    def action_add_network_balance(self):
        """Ajouter un solde pour un nouvel opérateur"""
        self.ensure_one()
        return {
            "name": "Ajouter Solde Opérateur",
            "type": "ir.actions.act_window",
            "res_model": "mm.agent.balance",
            "view_mode": "form",
            "view_id": self.env.ref("mm_manager.mm_agent_balance_form_quick").id,
            "target": "new",
            "context": {
                "default_agent_id": self.id,
                "default_balance_type": "network",
                "default_balance": 0.0,
            },
        }

    def action_manage_cash(self):
        """Gérer la caisse de l'agent"""
        self.ensure_one()
        cash_balance = self.get_or_create_cash_balance()
        return {
            "name": "Gérer la Caisse",
            "type": "ir.actions.act_window",
            "res_model": "mm.agent.balance",
            "view_mode": "form",
            "res_id": cash_balance.id,
            "target": "current",
        }
