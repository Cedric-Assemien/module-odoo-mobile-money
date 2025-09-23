# -*- coding: utf-8 -*-
from odoo import api, models


class MMStatsReport(models.AbstractModel):
    _name = "report.mm_manager.mm_stats_report_template"
    _description = "Rapport Statistiques Mobile Money"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        include = data.get("include", {})
        top_n = data.get("top_n", 10)
        ranking_metric = data.get("ranking_metric", "amount")

        transaction_obj = self.env["mm.transaction"]
        customer_obj = self.env["mm.customer"]
        agent_obj = self.env["mm.agent"]
        service_point_obj = self.env["mm.service.point"]

        domain_date = []
        if date_from:
            domain_date.append(("transaction_date", ">=", date_from))
        if date_to:
            domain_date.append(("transaction_date", "<=", date_to))

        txs = transaction_obj.search([("state", "=", "confirmed")] + domain_date)

        lines = []
        stats = {
            "total_transactions": 0,
            "total_depot": 0,
            "total_retrait": 0,
            "total_commission": 0,
        }
        idx = 1
        for trans in txs:
            lines.append(
                {
                    "idx": idx,
                    "date": trans.create_date,
                    "transaction_id": trans.id,
                    "client": trans.customer_id.name,
                    "agent": trans.agent_id.name,
                    "service_point": trans.service_point_id.name,
                    "type": dict(trans._fields["transaction_type"].selection).get(trans.transaction_type),
                    "amount": trans.amount,
                    "commission": trans.commission_amount,
                }
            )
            idx += 1
            stats["total_transactions"] += 1
            if trans.transaction_type == "deposit":
                stats["total_depot"] += trans.amount
            elif trans.transaction_type == "withdrawal":
                stats["total_retrait"] += trans.amount
            stats["total_commission"] += trans.commission_amount or 0.0

        if include.get("clients", True):
            stats["customers"] = {
                "count": customer_obj.search_count([]),
                "by_service_point": self._group_sum(txs, "customer_id", "amount"),
            }

        if include.get("agents", True):
            stats["agents"] = {
                "count": agent_obj.search_count([]),
                "by_agent_amount": self._group_sum(txs, "agent_id", "amount"),
                "by_agent_count": self._group_count(txs, "agent_id"),
            }
            # Liste exhaustive des agents (même sans activité)
            all_agents = agent_obj.search([])
            agents_all_list = []
            for ag in all_agents:
                name = ag.name or ag.user_id.name or "Sans nom"
                count = stats["agents"]["by_agent_count"].get(name, 0)
                amount = stats["agents"]["by_agent_amount"].get(name, 0.0)
                agents_all_list.append({"name": name, "count": count, "amount": amount})
            stats["agents"]["all"] = agents_all_list
            # Classement Top N
            if ranking_metric == "count":
                ranking_pairs = sorted(
                    stats["agents"]["by_agent_count"].items(), key=lambda kv: kv[1], reverse=True
                )
            else:
                ranking_pairs = sorted(
                    stats["agents"]["by_agent_amount"].items(), key=lambda kv: kv[1], reverse=True
                )
            stats["agents"]["top_ranking"] = ranking_pairs[:max(int(top_n or 10), 1)]

        if include.get("service_points", True):
            stats["service_points"] = {
                "count": service_point_obj.search_count([]),
                "by_point_amount": self._group_sum(txs, "service_point_id", "amount"),
                "by_point_count": self._group_count(txs, "service_point_id"),
            }

        # Résumé des transactions pour le template
        stats["transactions"] = {
            "count": stats["total_transactions"],
            "amount": stats["total_depot"] + stats["total_retrait"],
            "fees": sum(trans.fee_amount for trans in txs) if txs else 0.0,
            "net": sum(trans.net_amount for trans in txs) if txs else 0.0,
        }

        return {
            "doc_ids": docids,
            "doc_model": "mm.transaction",
            "docs": txs,
            "date_from": date_from,
            "date_to": date_to,
            "stats": stats,
            "top_n": top_n,
            "ranking_metric": ranking_metric,
            "lines": lines,
        }

    def _group_sum(self, records, group_field, sum_field):
        result = {}
        for rec in records:
            key = getattr(rec, group_field).name if getattr(rec, group_field) else "Non défini"
            result.setdefault(key, 0.0)
            result[key] += getattr(rec, sum_field) or 0.0
        return result

    def _group_count(self, records, group_field):
        result = {}
        for rec in records:
            key = getattr(rec, group_field).name if getattr(rec, group_field) else "Non défini"
            result.setdefault(key, 0)
            result[key] += 1
        return result
