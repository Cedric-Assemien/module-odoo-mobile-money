/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Composant Dashboard Mobile Money
 * Gère l'affichage interactif du tableau de bord avec statistiques en temps réel
 */
class MobileMoneyDashboard extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.notification = useService("notification");

    this.state = useState({
      stats: {
        transactions_today: 0,
        customers_active: 0,
        agents_active: 0,
        service_points_active: 0,
        total_amount_today: 0,
      },
      loading: false,
      lastUpdate: new Date(),
    });

    onWillStart(async () => {
      await this.loadDashboardData();
      this.startAutoRefresh();
    });
  }

  /**
   * Charge les données du dashboard depuis le serveur
   */
  async loadDashboardData() {
    this.state.loading = true;
    try {
      const data = await this.orm.call(
        "mm.dashboard",
        "get_dashboard_data",
        []
      );
      this.state.stats = data.stats;
      this.state.lastUpdate = new Date();
    } catch (error) {
      console.error("Erreur lors du chargement des données:", error);
      this.notification.add("Erreur lors du chargement des données", {
        type: "danger",
      });
    } finally {
      this.state.loading = false;
    }
  }

  /**
   * Démarre le rafraîchissement automatique toutes les 30 secondes
   */
  startAutoRefresh() {
    setInterval(() => {
      this.loadDashboardData();
    }, 30000); // 30 secondes
  }

  /**
   * Navigation vers les transactions
   */
  async openTransactions() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Transactions",
      res_model: "mm.transaction",
      view_mode: "tree,form",
      target: "current",
    });
  }

  /**
   * Navigation vers les clients
   */
  async openCustomers() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Clients",
      res_model: "mm.customer",
      view_mode: "tree,form",
      target: "current",
    });
  }

  /**
   * Navigation vers les agents
   */
  async openAgents() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Agents",
      res_model: "mm.agent",
      view_mode: "tree,form",
      target: "current",
    });
  }

  /**
   * Navigation vers les points de service
   */
  async openServicePoints() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Points de Service",
      res_model: "mm.service.point",
      view_mode: "tree,form",
      target: "current",
    });
  }

  /**
   * Crée une nouvelle transaction
   */
  async createTransaction() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Nouvelle Transaction",
      res_model: "mm.transaction",
      view_mode: "form",
      target: "current",
      context: {
        default_transaction_date: new Date().toISOString().split("T")[0],
        default_state: "draft",
      },
    });
  }

  /**
   * Crée un nouveau client
   */
  async createCustomer() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Nouveau Client",
      res_model: "mm.customer",
      view_mode: "form",
      target: "current",
    });
  }

  /**
   * Ouvre les rapports
   */
  async openReports() {
    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Rapports",
      res_model: "mm.stats.report.wizard",
      view_mode: "form",
      target: "new",
    });
  }

  /**
   * Synchronise les agents
   */
  async syncAgents() {
    this.state.loading = true;
    try {
      await this.orm.call("mm.agent", "sync_all_agents", []);
      this.notification.add("Synchronisation des agents terminée", {
        type: "success",
      });
      await this.loadDashboardData(); // Refresh data
    } catch (error) {
      console.error("Erreur lors de la synchronisation:", error);
      this.notification.add("Erreur lors de la synchronisation", {
        type: "danger",
      });
    } finally {
      this.state.loading = false;
    }
  }

  /**
   * Force le rafraîchissement des données
   */
  async refreshData() {
    await this.loadDashboardData();
    this.notification.add("Données actualisées", {
      type: "info",
    });
  }

  /**
   * Formate les nombres avec des séparateurs de milliers
   */
  formatNumber(num) {
    return new Intl.NumberFormat("fr-FR").format(num);
  }

  /**
   * Formate les montants en devise
   */
  formatCurrency(amount) {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "XOF", // Franc CFA (ajustez selon votre devise)
    }).format(amount);
  }

  /**
   * Formate l'heure de la dernière mise à jour
   */
  formatLastUpdate() {
    return this.state.lastUpdate.toLocaleTimeString("fr-FR");
  }
}

MobileMoneyDashboard.template = "mm_manager.DashboardTemplate";

// Enregistrement du composant
registry
  .category("actions")
  .add("mm_dashboard_component", MobileMoneyDashboard);

export default MobileMoneyDashboard;
