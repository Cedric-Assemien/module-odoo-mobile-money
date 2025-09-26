# mm_manager

Ce module Odoo gère la supervision et le reporting des opérations Mobile Money pour les agents et les clients. Il est conçu pour répondre aux besoins de gestion, de suivi et d’analyse des transactions, des politiques de limitation, des réseaux et des points de service.

## Fonctionnalités principales

### 1. Gestion des Agents

- Création, modification et suppression d’agents Mobile Money
- Synchronisation des agents via des fichiers XML
- Attribution de réseaux et de points de service aux agents

### 2. Gestion des Clients

- Enregistrement et gestion des clients
- Visualisation des transactions associées à chaque client

### 3. Politiques de Limitation

- Définition de politiques de limitation pour les transactions
- Gestion des plafonds et des exceptions
- Déplafonnement via wizard dédié

### 4. Réseaux Mobile Money

- Gestion des réseaux (MTN, Orange, Moov, etc.)
- Association des agents et des points de service aux réseaux

### 5. Points de Service

- Création et gestion des points de service
- Attribution des agents et des réseaux

### 6. Transactions

- Enregistrement des transactions Mobile Money
- Suivi des montants, dates, agents et clients impliqués
- Statistiques et reporting sur les transactions

### 7. Reporting & Statistiques

- Génération de rapports statistiques personnalisés
- Filtres par période, agent, réseau, point de service
- Export des rapports
- Wizards pour la génération de rapports

### 8. Sécurité & Accès

- Gestion fine des droits d’accès (admin, utilisateur, etc.)
- Sécurisation des opérations sensibles

### 9. Interface Utilisateur

- Vues personnalisées pour agents, clients, transactions, politiques, réseaux, points de service
- Tableaux de bord pour la supervision
- Menus dédiés pour chaque entité

### 10. Extensibilité

- Architecture modulaire compatible avec d’autres modules Odoo
- Facilité d’ajout de nouvelles fonctionnalités

## Structure du module

- **models/** : Modèles de données (agent, client, transaction, etc.)
- **views/** : Vues XML pour l’interface utilisateur
- **wizard/** : Wizards pour les opérations avancées (déplafonnement, reporting)
- **report/** : Templates et actions de rapports
- **data/** : Données de base et synchronisation
- **security/** : Fichiers de sécurité et gestion des accès
- **static/** : Ressources statiques (icônes, images)

## Cas d’utilisation

- Supervision des agents Mobile Money
- Analyse des transactions et détection des fraudes
- Gestion des plafonds et déplafonnements
- Reporting avancé pour la direction

## Auteur

Cedric Assemien

---

Ce README est conçu pour servir de base à une présentation PowerPoint. Il met en avant les points clés et la structure du module pour faciliter la communication et la valorisation du projet.
