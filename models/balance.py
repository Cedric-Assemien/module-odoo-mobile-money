# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyBalance(models.Model):
    _name = "mm.balance"
    _description = "Mobile Money Customer Balance per Network"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    customer_id = fields.Many2one("mm.customer", string="Client", required=True, ondelete="cascade", tracking=True)
    network_id = fields.Many2one("mm.network", string="Opérateur", required=True, tracking=True)
    balance = fields.Monetary(
        string="Solde", 
        default=0.0, 
        tracking=True, 
        currency_field="currency_id",
        help="Solde actuel du client pour cet opérateur"
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="customer_id.currency_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", 
        string="Société", 
        default=lambda self: self.env.company, 
        required=True, 
        index=True
    )
    display_name = fields.Char(string="Nom d'affichage", compute="_compute_display_name", store=True)
    last_update_date = fields.Datetime(string="Dernière mise à jour", default=fields.Datetime.now, tracking=True)
    active = fields.Boolean(string="Actif", default=True)

    _sql_constraints = [
        ("mm_balance_customer_network_unique", 
         "unique(customer_id, network_id, company_id)", 
         "Un client ne peut avoir qu'un seul solde par opérateur dans une société."),
        ("mm_balance_positive", 
         "check(balance >= 0)", 
         "Le solde ne peut pas être négatif."),
    ]

    @api.depends("customer_id.name", "network_id.name")
    def _compute_display_name(self):
        for record in self:
            if record.customer_id and record.network_id:
                record.display_name = f"{record.customer_id.name} - {record.network_id.name}"
            else:
                record.display_name = "Nouveau solde"

    @api.constrains("balance")
    def _check_balance_positive(self):
        for record in self:
            if record.balance < 0:
                raise ValidationError(f"Le solde pour {record.network_id.name} ne peut pas être négatif.")

    def add_amount(self, amount, description=None):
        """Ajouter un montant au solde (pour les dépôts)"""
        self.ensure_one()
        if amount <= 0:
            raise ValidationError("Le montant à ajouter doit être positif.")
        
        old_balance = self.balance
        self.balance += amount
        self.last_update_date = fields.Datetime.now()
        
        default_desc = f"Dépôt de {amount} {self.currency_id.symbol}"
        message = description or default_desc
        message += f". Ancien solde: {old_balance} {self.currency_id.symbol}, Nouveau solde: {self.balance} {self.currency_id.symbol}"
        
        self.message_post(body=message)

    def subtract_amount(self, amount, description=None):
        """Soustraire un montant du solde (pour les retraits)"""
        self.ensure_one()
        if amount <= 0:
            raise ValidationError("Le montant à soustraire doit être positif.")
        
        if self.balance < amount:
            raise ValidationError(
                f"Solde insuffisant sur {self.network_id.name}. "
                f"Solde actuel: {self.balance} {self.currency_id.symbol}, "
                f"Montant demandé: {amount} {self.currency_id.symbol}"
            )
        
        old_balance = self.balance
        self.balance -= amount
        self.last_update_date = fields.Datetime.now()
        
        default_desc = f"Retrait de {amount} {self.currency_id.symbol}"
        message = description or default_desc
        message += f". Ancien solde: {old_balance} {self.currency_id.symbol}, Nouveau solde: {self.balance} {self.currency_id.symbol}"
        
        self.message_post(body=message)

    def check_sufficient_balance(self, amount):
        """Vérifier si le solde est suffisant pour une transaction"""
        self.ensure_one()
        return self.balance >= amount

    @api.model
    def get_or_create_balance(self, customer_id, network_id):
        """Obtenir ou créer un solde pour un client et un opérateur donnés"""
        balance = self.search([
            ("customer_id", "=", customer_id),
            ("network_id", "=", network_id),
            ("company_id", "=", self.env.company.id)
        ], limit=1)
        
        if not balance:
            customer = self.env["mm.customer"].browse(customer_id)
            network = self.env["mm.network"].browse(network_id)
            balance = self.create({
                "customer_id": customer_id,
                "network_id": network_id,
                "balance": 0.0,
                "company_id": self.env.company.id,
            })
            balance.message_post(
                body=f"Création du solde pour {customer.name} - {network.name}"
            )
        
        return balance

    def action_view_transactions(self):
        """Voir les transactions liées à ce solde"""
        self.ensure_one()
        action = self.env.ref("mm_manager.mm_transaction_action").read()[0]
        action["domain"] = [
            ("customer_id", "=", self.customer_id.id),
            ("network_id", "=", self.network_id.id),
            ("state", "!=", "draft"),
        ]
        action["context"] = {
            "default_customer_id": self.customer_id.id,
            "default_network_id": self.network_id.id,
        }
        return action