{
    "name": "Mobile Money Manager",
    "summary": "Gestion des transactions Mobile Money avec plafonds et deplafonnement",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Cedric Assemien",
    "website": "",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "contacts",
        "web"
    ],
    "data": [
        "security/mm_security_admin.xml",
        "security/mm_security.xml",
        "security/ir.model.access.csv",
        "data/mm_sequences.xml",
        "data/mm_limit_policies.xml",
        "data/mm_network_data.xml",
        "data/mm_agent_sync.xml",

        "wizard/mm_deplafonnement_wizard_views.xml",
        "wizard/stats_report_wizard_views.xml",
        "views/mm_agent_views.xml",
        "views/mm_agent_balance_views.xml",
        "views/mm_customer_views.xml",
        "views/mm_balance_views.xml",
        "views/mm_transaction_views.xml",
        "views/mm_service_point_views.xml",
        "views/mm_policy_views.xml",
        "views/mm_network_views.xml",
        "views/mm_dashboard_views.xml",
        "views/mm_menus.xml",
        "report/mm_transaction_report_templates.xml",
        "report/mm_transaction_report_actions.xml",
        "report/mm_stats_report_templates.xml",
        "report/mm_stats_report_actions.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "mm_manager/static/src/css/dashboard.css",
            "mm_manager/static/src/js/dashboard.js",
            "mm_manager/static/src/xml/dashboard_templates.xml",
        ],
        "web.assets_frontend": [
            "mm_manager/static/src/css/dashboard.css",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False
}
