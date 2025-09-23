# -*- coding: utf-8 -*-
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyTransaction(models.Model):
    _name = "mm.transaction"
    _description = "Mobile Money Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "transaction_date desc, id desc"

    TRANSACTION_TYPES = [
        ("deposit", "Dépôt"),
        ("withdrawal", "Retrait"),
        ("transfer", "Transfert"),
        ("bill", "Paiement de Facture"),
        ("airtime", "Achat de Crédit"),
    ]

    STATE_SELECTION = [
        ("draft", "Brouillon"),
        ("confirmed", "Confirmée"),
        ("refused", "Refusée"),
    ]

    name = fields.Char(string="Référence", default="New", readonly=True, copy=False)
    transaction_date = fields.Date(string="Date de Transaction", default=lambda self: fields.Date.context_today(self), required=True, tracking=True)
    transaction_type = fields.Selection(TRANSACTION_TYPES, string="Type de Transaction", required=True, tracking=True)
    customer_id = fields.Many2one("mm.customer", string="Client", required=True, tracking=True)
    network_id = fields.Many2one("mm.network", string="Réseau", required=True, tracking=True)
    amount = fields.Monetary(string="Montant", required=True, tracking=True, currency_field="currency_id")
    fee_amount = fields.Monetary(string="Montant des Frais", compute="_compute_amounts", store=True, readonly=True, currency_field="currency_id")
    net_amount = fields.Monetary(string="Montant Net", compute="_compute_amounts", store=True, readonly=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        related="customer_id.currency_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company, required=True, index=True)
    agent_id = fields.Many2one("res.users", string="Agent", default=lambda self: self.env.user, tracking=True)
    service_point_id = fields.Many2one("mm.service.point", string="Point de Service", tracking=True)
    state = fields.Selection(STATE_SELECTION, string="État", default="draft", tracking=True)
    refusal_reason = fields.Char(string="Raison du Refus")
    reference = fields.Char(string="Référence Externe", help="Référence fournie par le fournisseur Mobile Money.")
    commission_amount = fields.Monetary(string="Montant de Commission",
        compute="_compute_commission",
        store=True,
        readonly=True,
        help="Commission perçue par le propriétaire du point de service.",
        currency_field="currency_id",
    )
    monthly_usage_percentage = fields.Float(compute="_compute_monthly_usage", store=False)

    _sql_constraints = [
        ("mm_transaction_amount_positive", "CHECK(amount > 0)", "Le montant de la transaction doit être strictement positif."),
    ]

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("mm.transaction") or "New"
        record = super().create(vals)
        record._post_monthly_threshold_notifications()
        return record

    def write(self, vals):
        result = super().write(vals)
        if any(field in vals for field in ("amount", "transaction_date", "state", "customer_id")):
            self._post_monthly_threshold_notifications()
        return result

    @api.depends("amount", "network_id.fee_percentage")
    def _compute_amounts(self):
        for record in self:
            fee = 0.0
            if record.network_id:
                fee = (record.amount or 0.0) * (record.network_id.fee_percentage or 0.0) / 100.0
            record.fee_amount = fee
            record.net_amount = (record.amount or 0.0) - fee

    @api.depends("fee_amount")
    def _compute_commission(self):
        for record in self:
            record.commission_amount = record.fee_amount

    def _compute_monthly_usage(self):
        for record in self:
            record.monthly_usage_percentage = record._calculate_monthly_usage_percentage()

    def action_confirm(self):
        for transaction in self:
            transaction._ensure_customer_in_company()
            transaction._check_plafonds()
            transaction.state = "confirmed"
            transaction.refusal_reason = False
            transaction._post_monthly_threshold_notifications()
        return True

    def action_refuse(self):
        for transaction in self:
            if not transaction.refusal_reason:
                raise ValidationError("Veuillez définir une raison de refus avant de refuser la transaction.")
            transaction.state = "refused"
            transaction._notify_refusal(transaction.refusal_reason)
        return True

    def action_reset_draft(self):
        for transaction in self:
            transaction.state = "draft"
            transaction.refusal_reason = False
        return True

    def _ensure_customer_in_company(self):
        for transaction in self:
            if transaction.customer_id.company_id != transaction.company_id:
                raise ValidationError("Incohérence entre la société du client et celle de la transaction.")

    def _get_month_limits(self):
        self.ensure_one()
        policy = self.customer_id.policy_id
        return policy.per_transaction_limit, policy.monthly_limit

    def _get_month_timeframe(self):
        self.ensure_one()
        t_date = self.transaction_date or date.today()
        month_start = t_date.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        return month_start, month_end

    def _check_plafonds(self):
        for transaction in self:
            per_transaction_limit, monthly_limit = transaction._get_month_limits()
            if transaction.amount > per_transaction_limit:
                raise ValidationError("Le montant de la transaction dépasse la limite par transaction pour la politique du client.")
            month_start, month_end = transaction._get_month_timeframe()
            domain = [
                ("customer_id", "=", transaction.customer_id.id),
                ("state", "=", "confirmed"),
                ("transaction_date", ">=", month_start),
                ("transaction_date", "<=", month_end),
                ("id", "!=", transaction.id),
            ]
            total = sum(self.env["mm.transaction"].search(domain).mapped("amount"))
            total += transaction.amount
            if total > monthly_limit:
                raise ValidationError("Limite mensuelle atteinte pour ce client.")

    def _calculate_monthly_usage_percentage(self):
        self.ensure_one()
        _, monthly_limit = self._get_month_limits()
        if not monthly_limit:
            return 0.0
        month_start, month_end = self._get_month_timeframe()
        domain = [
            ("customer_id", "=", self.customer_id.id),
            ("state", "=", "confirmed"),
            ("transaction_date", ">=", month_start),
            ("transaction_date", "<=", month_end),
            ("id", "!=", self.id),
        ]
        total = sum(self.env["mm.transaction"].search(domain).mapped("amount"))
        if self.state == "confirmed":
            total += self.amount
        return (total / monthly_limit) * 100.0 if monthly_limit else 0.0

    def _post_monthly_threshold_notifications(self):
        for transaction in self:
            if transaction.state != "confirmed":
                continue
            usage = transaction._calculate_monthly_usage_percentage()
            if usage < 80.0:
                continue
            transaction._notify_threshold(usage)

    def _notify_threshold(self, usage_percentage):
        self.ensure_one()
        message = f"Le client {self.customer_id.name} a atteint {usage_percentage:.2f}% de la limite mensuelle."
        followers = self._get_notified_partners()
        if followers:
            self.with_context(mail_post_autofollow=True).message_post(
                body=message,
                partner_ids=followers,
                subtype_xmlid="mail.mt_note",
            )
        self.customer_id.message_post(body=message)

    def _notify_refusal(self, reason):
        self.ensure_one()
        message = f"Transaction {self.name} refusée : {reason or 'Aucune raison fournie.'}"
        followers = self._get_notified_partners()
        if followers:
            self.message_post(body=message, partner_ids=followers, subtype_xmlid="mail.mt_note")
        self.customer_id.message_post(body=message)

    def _get_notified_partners(self):
        self.ensure_one()
        partner_ids = []
        if self.agent_id.partner_id:
            partner_ids.append(self.agent_id.partner_id.id)
        owner = self.customer_id.owner_id
        if owner and owner.partner_id:
            partner_ids.append(owner.partner_id.id)
        return list(set(partner_ids))