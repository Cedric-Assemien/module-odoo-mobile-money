# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta


class MobileMoneyDashboard(models.TransientModel):
    _name = "mm.dashboard"
    _description = "Mobile Money Dashboard"

    # Champs pour les statistiques
    transaction_count = fields.Integer(string="Nombre de transactions", compute="_compute_dashboard_stats", store=False)
    customer_count = fields.Integer(string="Nombre de clients", compute="_compute_dashboard_stats", store=False)
    agent_count = fields.Integer(string="Nombre d'agents", compute="_compute_dashboard_stats", store=False)
    service_point_count = fields.Integer(string="Nombre de points de service", compute="_compute_dashboard_stats", store=False)
    
    total_amount_today = fields.Monetary(string="Montant total aujourd'hui", compute="_compute_dashboard_stats", currency_field="currency_id", store=False)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)

    @api.depends()
    def _compute_dashboard_stats(self):
        for record in self:
            try:
                today = fields.Date.today()
                
                # Transactions aujourd'hui
                transactions_today = self.env['mm.transaction'].search([
                    ('transaction_date', '=', today),
                    ('state', '=', 'confirmed')
                ])
                record.transaction_count = len(transactions_today)
                record.total_amount_today = sum(transactions_today.mapped('amount')) if transactions_today else 0
                
                # Clients actifs
                record.customer_count = self.env['mm.customer'].search_count([('active', '=', True)])
                
                # Agents actifs
                record.agent_count = self.env['mm.agent'].search_count([('active', '=', True)])
                
                # Points de service actifs
                record.service_point_count = self.env['mm.service.point'].search_count([('active', '=', True)])
                
            except Exception:
                # En cas d'erreur, définir des valeurs par défaut
                record.transaction_count = 0
                record.customer_count = 0
                record.agent_count = 0
                record.service_point_count = 0
                record.total_amount_today = 0

    def action_view_transactions(self):
        """Action pour accéder aux transactions"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'mm.transaction',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {'search_default_filter_last_30_days': 1},
        }

    def action_view_customers(self):
        """Action pour accéder aux clients"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clients',
            'res_model': 'mm.customer',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_agents(self):
        """Action pour accéder aux agents"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agents',
            'res_model': 'mm.agent',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_service_points(self):
        """Action pour accéder aux points de service"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Points de Service',
            'res_model': 'mm.service.point',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_new_transaction(self):
        """Action pour créer une nouvelle transaction"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouvelle Transaction',
            'res_model': 'mm.transaction',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_transaction_date': fields.Date.today(),
                'default_state': 'draft',
            }
        }

    def action_new_customer(self):
        """Action pour créer un nouveau client"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouveau Client',
            'res_model': 'mm.customer',
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reports(self):
        """Action pour accéder aux rapports"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rapports',
            'res_model': 'mm.stats.report.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_sync_agents(self):
        """Action pour synchroniser les agents"""
        # Ici vous pouvez ajouter la logique de synchronisation
        self.env['mm.agent'].search([]).with_context(force_sync=True)._sync_agent_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Synchronisation',
                'message': 'Synchronisation des agents terminée avec succès',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def get_dashboard_data(self):
        """Retourne les données pour le dashboard"""
        today = fields.Date.today()
        
        # Statistiques générales
        stats = {
            'transactions_today': self.env['mm.transaction'].search_count([
                ('transaction_date', '=', today),
                ('state', '=', 'confirmed')
            ]),
            'customers_active': self.env['mm.customer'].search_count([('active', '=', True)]),
            'agents_active': self.env['mm.agent'].search_count([('active', '=', True)]),
            'service_points_active': self.env['mm.service.point'].search_count([('active', '=', True)]),
        }
        
        # Transactions par type pour le graphique
        transaction_types = self.env['mm.transaction'].read_group(
            [('transaction_date', '>=', today - timedelta(days=30))],
            ['amount:sum'],
            ['transaction_type']
        )
        
        # Évolution mensuelle
        monthly_data = self.env['mm.transaction'].read_group(
            [('transaction_date', '>=', today - timedelta(days=365))],
            ['amount:sum'],
            ['transaction_date:month']
        )
        
        return {
            'stats': stats,
            'transaction_types': transaction_types,
            'monthly_trend': monthly_data,
        }

    @api.model
    def default_get(self, fields_list):
        """Retourne des valeurs par défaut pour le dashboard"""
        result = super().default_get(fields_list)
        return result

