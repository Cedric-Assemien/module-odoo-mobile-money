# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MobileMoneyCustomer(models.Model):
    _name = "mm.customer"
    _description = "Mobile Money Customer"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    STATUS_SELECTION = [
        ("standard", "Standard"),
        ("deplafonne", "Déplafonné"),
    ]

    IDENTITY_TYPES = [
        ("cni", "CNI"),
        ("passport", "Passeport"),
        ("permis", "Permis de conduire"),
        ("autre", "Autre"),
    ]

    name = fields.Char(string="Nom", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Partenaire", tracking=True)
    phone = fields.Char(string="Téléphone", tracking=True)
    status = fields.Selection(STATUS_SELECTION, string="Statut", default="standard", required=True, tracking=True)
    policy_id = fields.Many2one("mm.limit.policy", string="Politique", required=True, tracking=True)
    identity_type = fields.Selection(IDENTITY_TYPES, string="Type d'Identité", tracking=True)
    identity_number = fields.Char(string="Numéro d'Identité", tracking=True)
    identity_attachment_id = fields.Many2one("ir.attachment", string="Pièce d'Identité")
    agent_id = fields.Many2one("res.users", string="Agent", default=lambda self: self.env.user, tracking=True)
    owner_id = fields.Many2one(
        related="service_point_id.owner_id",
        store=True,
        string="Propriétaire",
        readonly=True,
    )
    service_point_id = fields.Many2one("mm.service.point", string="Point de Service", tracking=True)
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company, required=True, index=True)
    active = fields.Boolean(string="Actif", default=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="policy_id.currency_id",
        store=True,
        readonly=True,
    )
    transaction_ids = fields.One2many("mm.transaction", "customer_id", string="Transactions")
    balance_ids = fields.One2many("mm.balance", "customer_id", string="Soldes par Opérateur")
    monthly_transaction_total = fields.Monetary(string="Total Mensuel", compute="_compute_monthly_totals", store=False, currency_field="currency_id")
    monthly_transaction_count = fields.Integer(string="Nombre de Transactions Mensuelles", compute="_compute_monthly_totals", store=False)
    last_transaction_date = fields.Date(string="Dernière Transaction", compute="_compute_last_transaction", store=False)
    is_deplafonne = fields.Boolean(string="Est Déplafonné", compute="_compute_is_deplafonne", store=True)
    total_balance = fields.Monetary(string="Solde Total", compute="_compute_total_balance", store=False, currency_field="currency_id")

    _sql_constraints = [
        ("mm_customer_phone_unique", "unique(phone, company_id)", "A customer phone number must be unique per company."),
    ]

    @api.model
    def create(self, vals):
        status_code = vals.get("status") or "standard"
        if not vals.get("policy_id"):
            policy = self.env["mm.limit.policy"].get_policy_by_code(status_code)
            if policy:
                vals["policy_id"] = policy.id
        record = super().create(vals)
        if record.policy_id and record.status != record.policy_id.code:
            super(MobileMoneyCustomer, record).write({"status": record.policy_id.code})
        return record

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            if record.policy_id and record.status != record.policy_id.code:
                super(MobileMoneyCustomer, record).write({"status": record.policy_id.code})
        return res

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "policy_id" in fields_list and not defaults.get("policy_id"):
            policy = self.env["mm.limit.policy"].get_policy_by_code("standard")
            if policy:
                defaults["policy_id"] = policy.id
        return defaults

    @api.onchange("status")
    def _onchange_status(self):
        if self.status:
            policy = self.env["mm.limit.policy"].get_policy_by_code(self.status)
            if policy:
                self.policy_id = policy.id

    @api.onchange("policy_id")
    def _onchange_policy(self):
        if self.policy_id:
            self.status = self.policy_id.code

    @api.depends("policy_id")
    def _compute_is_deplafonne(self):
        for record in self:
            record.is_deplafonne = bool(record.policy_id and record.policy_id.code == "deplafonne")

    @api.depends("transaction_ids.state", "transaction_ids.transaction_date")
    def _compute_last_transaction(self):
        for record in self:
            confirmed = record.transaction_ids.filtered(lambda t: t.state == "confirmed")
            if confirmed:
                last_transaction = confirmed.sorted(
                    key=lambda t: t.transaction_date or fields.Date.context_today(record),
                    reverse=True,
                )[0]
                record.last_transaction_date = last_transaction.transaction_date
            else:
                record.last_transaction_date = False

    @api.depends("transaction_ids.amount", "transaction_ids.state", "transaction_ids.transaction_date")
    def _compute_monthly_totals(self):
        for record in self:
            total = 0.0
            count = 0
            today = fields.Date.context_today(record)
            if today:
                month_start = today.replace(day=1)
                for transaction in record.transaction_ids.filtered(lambda t: t.state == "confirmed"):
                    if transaction.transaction_date and month_start <= transaction.transaction_date <= today:
                        total += transaction.amount
                        count += 1
            record.monthly_transaction_total = total
            record.monthly_transaction_count = count

    def action_open_transactions(self):
        self.ensure_one()
        action = self.env.ref("mm_manager.mm_transaction_action").read()[0]
        action["domain"] = [
            ("customer_id", "=", self.id),
            ("state", "!=", "draft"),
        ]
        action["context"] = {"default_customer_id": self.id}
        return action

    def action_request_deplafonnement(self):
        self.ensure_one()
        return {
            "name": "Request Deplafonnement",
            "type": "ir.actions.act_window",
            "res_model": "mm.deplafonnement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customer_id": self.id,
                "default_identity_type": self.identity_type,
                "default_identity_number": self.identity_number,
            },
        }

    def action_set_standard_policy(self):
        policy = self.env["mm.limit.policy"].get_policy_by_code("standard")
        for record in self:
            if policy:
                record.policy_id = policy.id

    def action_set_deplafonne_policy(self):
        policy = self.env["mm.limit.policy"].get_policy_by_code("deplafonne")
        for record in self:
            if policy:
                record.policy_id = policy.id

    def create_identity_attachment(self, binary_content, filename):
        self.ensure_one()
        attachment = self.env["ir.attachment"].create({
            "name": filename or f"{self.name}-identity",
            "type": "binary",
            "datas": binary_content,
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/octet-stream",
        })
        self.identity_attachment_id = attachment.id
        return attachment

    @api.depends("balance_ids.balance")
    def _compute_total_balance(self):
        for record in self:
            record.total_balance = sum(record.balance_ids.mapped("balance"))

    def _get_monthly_total(self, date_from, date_to):
        self.ensure_one()
        domain = [
            ("customer_id", "=", self.id),
            ("state", "=", "confirmed"),
            ("transaction_date", "!=", False),
            ("transaction_date", ">=", date_from),
            ("transaction_date", "<=", date_to),
        ]
        return sum(self.env["mm.transaction"].search(domain).mapped("amount"))

    def get_balance_for_network(self, network_id):
        """Obtenir le solde pour un opérateur spécifique"""
        self.ensure_one()
        balance = self.balance_ids.filtered(lambda b: b.network_id.id == network_id)
        if balance:
            return balance[0].balance
        return 0.0

    def get_or_create_balance(self, network_id):
        """Obtenir ou créer un solde pour un opérateur donné"""
        self.ensure_one()
        balance = self.balance_ids.filtered(lambda b: b.network_id.id == network_id)
        if not balance:
            balance = self.env["mm.balance"].create({
                "customer_id": self.id,
                "network_id": network_id,
                "balance": 0.0,
            })
        else:
            balance = balance[0]
        return balance

    def action_view_balances(self):
        """Voir tous les soldes par opérateur"""
        self.ensure_one()
        action = {
            "name": "Soldes par Opérateur",
            "type": "ir.actions.act_window",
            "res_model": "mm.balance",
            "view_mode": "tree,form",
            "domain": [("customer_id", "=", self.id)],
            "context": {"default_customer_id": self.id},
        }
        return action

    def action_add_balance(self):
        """Ajouter un solde pour un nouvel opérateur"""
        self.ensure_one()
        return {
            "name": "Ajouter un Solde",
            "type": "ir.actions.act_window",
            "res_model": "mm.balance",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customer_id": self.id,
                "default_balance": 0.0,
            },
        }