# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MobileMoneyAgentBalance(models.Model):
    _name = "mm.agent.balance"
    _description = "Mobile Money Agent Balance per Network and Cash"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    BALANCE_TYPES = [
        ("network", "Solde Opérateur"),
        ("cash", "Caisse Physique"),
    ]

    agent_id = fields.Many2one("mm.agent", string="Agent", required=True, ondelete="cascade", tracking=True)
    user_id = fields.Many2one(
        "res.users", 
        related="agent_id.user_id", 
        store=True, 
        readonly=True,
        string="Utilisateur Agent"
    )
    balance_type = fields.Selection(
        BALANCE_TYPES, 
        string="Type de Solde", 
        required=True, 
        default="network",
        tracking=True
    )
    network_id = fields.Many2one(
        "mm.network", 
        string="Opérateur", 
        tracking=True,
        help="Opérateur pour les soldes de type 'network'. Vide pour les soldes de caisse."
    )
    balance = fields.Monetary(
        string="Solde", 
        default=0.0, 
        tracking=True, 
        currency_field="currency_id",
        help="Montant disponible pour cet agent"
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="agent_id.currency_id",
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
        ("mm_agent_balance_network_unique", 
         "unique(agent_id, network_id, company_id) WHERE balance_type = 'network' AND network_id IS NOT NULL", 
         "Un agent ne peut avoir qu'un seul solde par opérateur dans une société."),
        ("mm_agent_balance_cash_unique", 
         "unique(agent_id, company_id) WHERE balance_type = 'cash'", 
         "Un agent ne peut avoir qu'un seul solde de caisse dans une société."),
        ("mm_agent_balance_positive", 
         "check(balance >= 0)", 
         "Le solde ne peut pas être négatif."),
        ("mm_agent_balance_network_required",
         "check((balance_type = 'network' AND network_id IS NOT NULL) OR (balance_type = 'cash' AND network_id IS NULL))",
         "Un solde de type 'network' doit avoir un opérateur, un solde de type 'cash' ne doit pas en avoir."),
    ]

    @api.depends("agent_id.name", "network_id.name", "balance_type")
    def _compute_display_name(self):
        for record in self:
            if record.agent_id:
                if record.balance_type == "cash":
                    record.display_name = f"{record.agent_id.name} - Caisse Physique"
                elif record.balance_type == "network" and record.network_id:
                    record.display_name = f"{record.agent_id.name} - {record.network_id.name}"
                else:
                    record.display_name = f"{record.agent_id.name} - Nouveau solde"
            else:
                record.display_name = "Nouveau solde agent"

    @api.constrains("balance")
    def _check_balance_positive(self):
        for record in self:
            if record.balance < 0:
                balance_desc = "Caisse" if record.balance_type == "cash" else record.network_id.name
                raise ValidationError(f"Le solde {balance_desc} ne peut pas être négatif.")

    @api.constrains("balance_type", "network_id")
    def _check_balance_type_consistency(self):
        for record in self:
            if record.balance_type == "network" and not record.network_id:
                raise ValidationError("Un solde de type 'Opérateur' doit avoir un opérateur sélectionné.")
            if record.balance_type == "cash" and record.network_id:
                raise ValidationError("Un solde de type 'Caisse' ne doit pas avoir d'opérateur sélectionné.")

    def add_amount(self, amount, description=None):
        """Ajouter un montant au solde"""
        self.ensure_one()
        if amount <= 0:
            raise ValidationError("Le montant à ajouter doit être positif.")
        
        old_balance = self.balance
        self.balance += amount
        self.last_update_date = fields.Datetime.now()
        
        balance_desc = "Caisse" if self.balance_type == "cash" else self.network_id.name
        default_desc = f"Ajout de {amount} {self.currency_id.symbol} au solde {balance_desc}"
        message = description or default_desc
        message += f". Ancien solde: {old_balance} {self.currency_id.symbol}, Nouveau solde: {self.balance} {self.currency_id.symbol}"
        
        self.message_post(body=message)

    def subtract_amount(self, amount, description=None):
        """Soustraire un montant du solde"""
        self.ensure_one()
        if amount <= 0:
            raise ValidationError("Le montant à soustraire doit être positif.")
        
        if self.balance < amount:
            balance_desc = "Caisse" if self.balance_type == "cash" else self.network_id.name
            raise ValidationError(
                f"Solde insuffisant ({balance_desc}). "
                f"Solde actuel: {self.balance} {self.currency_id.symbol}, "
                f"Montant demandé: {amount} {self.currency_id.symbol}"
            )
        
        old_balance = self.balance
        self.balance -= amount
        self.last_update_date = fields.Datetime.now()
        
        balance_desc = "Caisse" if self.balance_type == "cash" else self.network_id.name
        default_desc = f"Retrait de {amount} {self.currency_id.symbol} du solde {balance_desc}"
        message = description or default_desc
        message += f". Ancien solde: {old_balance} {self.currency_id.symbol}, Nouveau solde: {self.balance} {self.currency_id.symbol}"
        
        self.message_post(body=message)

    def check_sufficient_balance(self, amount):
        """Vérifier si le solde est suffisant pour une transaction"""
        self.ensure_one()
        return self.balance >= amount

    @api.model
    def get_or_create_agent_balance(self, agent_id, balance_type, network_id=None):
        """Obtenir ou créer un solde pour un agent"""
        domain = [
            ("agent_id", "=", agent_id),
            ("balance_type", "=", balance_type),
            ("company_id", "=", self.env.company.id)
        ]
        
        if balance_type == "network":
            if not network_id:
                raise ValidationError("Un ID d'opérateur est requis pour un solde de type 'network'.")
            domain.append(("network_id", "=", network_id))
        else:  # cash
            domain.append(("network_id", "=", False))
        
        balance = self.search(domain, limit=1)
        
        if not balance:
            agent = self.env["mm.agent"].browse(agent_id)
            vals = {
                "agent_id": agent_id,
                "balance_type": balance_type,
                "balance": 0.0,
                "company_id": self.env.company.id,
            }
            
            if balance_type == "network":
                vals["network_id"] = network_id
                network = self.env["mm.network"].browse(network_id)
                balance_desc = network.name
            else:
                balance_desc = "Caisse Physique"
            
            balance = self.create(vals)
            balance.message_post(
                body=f"Création du solde {balance_desc} pour l'agent {agent.name}"
            )
        
        return balance

    def action_view_transactions(self):
        """Voir les transactions liées à ce solde"""
        self.ensure_one()
        action = self.env.ref("mm_manager.mm_transaction_action").read()[0]
        
        domain = [("agent_id", "=", self.user_id.id), ("state", "!=", "draft")]
        
        if self.balance_type == "network":
            domain.append(("network_id", "=", self.network_id.id))
        
        action["domain"] = domain
        action["context"] = {
            "default_agent_id": self.user_id.id,
        }
        
        if self.balance_type == "network":
            action["context"]["default_network_id"] = self.network_id.id
        
        return action

    def action_add_cash(self):
        """Action pour ajouter de l'argent liquide à la caisse"""
        self.ensure_one()
        if self.balance_type != "cash":
            raise ValidationError("Cette action n'est disponible que pour les soldes de caisse.")
        
        return {
            "name": "Ajouter à la Caisse",
            "type": "ir.actions.act_window",
            "res_model": "mm.agent.cash.operation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_agent_balance_id": self.id,
                "default_operation_type": "add",
            },
        }

    def action_remove_cash(self):
        """Action pour retirer de l'argent liquide de la caisse"""
        self.ensure_one()
        if self.balance_type != "cash":
            raise ValidationError("Cette action n'est disponible que pour les soldes de caisse.")
        
        return {
            "name": "Retirer de la Caisse",
            "type": "ir.actions.act_window",
            "res_model": "mm.agent.cash.operation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_agent_balance_id": self.id,
                "default_operation_type": "remove",
            },
        }