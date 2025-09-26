# Gestion des Soldes Agents - Mobile Money Manager

## Vue d'ensemble

Cette mise à jour ajoute la fonctionnalité complète de gestion des soldes pour les agents de Mobile Money. Chaque agent peut maintenant avoir :

- **Soldes par opérateur** : Soldes séparés pour chaque opérateur (Wave, Orange Money, Moov Money, MTN Money)
- **Solde de caisse** : Liquidités physiques disponibles

## Architecture des Soldes Agents

### Types de Soldes

1. **Soldes Opérateurs (`network`)** :

   - Argent disponible sur chaque plateforme mobile money
   - Utilisé pour les retraits clients et transferts
   - Un solde par opérateur par agent

2. **Solde Caisse (`cash`)** :
   - Liquidités physiques de l'agent
   - Utilisé pour les dépôts clients
   - Un seul solde de caisse par agent

### Logique des Transactions

#### Dépôt Client

- **Client** : Gagne du solde sur l'opérateur sélectionné
- **Agent** :
  - Perd des liquidités de sa caisse (argent physique donné au client)
  - Gagne du solde sur l'opérateur (crédit mobile money)

#### Retrait Client

- **Client** : Perd du solde sur l'opérateur sélectionné
- **Agent** :
  - Perd du solde sur l'opérateur (débit mobile money)
  - Gagne des liquidités dans sa caisse (argent physique du client)

#### Transfert Client

- **Client** : Perd du solde sur l'opérateur (transfert sortant)
- **Agent** : Perd du solde sur l'opérateur (coût du transfert)

## Contrôles de Sécurité

### Vérifications Avant Transaction

1. **Soldes clients** : Vérification comme avant
2. **Soldes agents** :
   - **Dépôt** : L'agent doit avoir assez de liquidités en caisse
   - **Retrait** : L'agent doit avoir assez de solde sur l'opérateur
   - **Transfert** : L'agent doit avoir assez de solde sur l'opérateur

### Messages d'Erreur Agents

```
L'agent [Nom] n'a pas assez de liquidités en caisse.
Caisse disponible: [montant] [devise], Montant demandé: [montant] [devise]
```

```
L'agent [Nom] n'a pas assez de solde sur [Opérateur].
Solde disponible: [montant] [devise], Montant demandé: [montant] [devise]
```

## Interface Utilisateur

### Vue Agent Améliorée

#### Statistiques de Solde

- **Solde Total** : Somme de tous les soldes (opérateurs + caisse)
- **Caisse** : Liquidités physiques disponibles
- **Soldes Opérateurs** : Total des soldes mobile money

#### Nouveaux Boutons d'Action

- **Voir Soldes** : Accès à tous les soldes de l'agent
- **Gérer Caisse** : Ajouter/retirer des liquidités
- **Ajouter Solde** : Créer un solde pour un nouvel opérateur

#### Onglet "Soldes Agent"

- Liste complète des soldes par type
- Création/modification directe
- Accès aux transactions par solde

### Nouvelle Vue "Soldes Agents"

#### Vue Kanban

- Cartes visuelles par solde
- Distinction caisse/opérateur avec icônes
- Boutons rapides pour la gestion de caisse

#### Vue Liste

- Filtres par type de solde
- Recherche par agent/opérateur
- Groupement par agent/type/opérateur

#### Vue Pivot

- Analyse des soldes par agent
- Comparaison opérateurs vs caisse

## Utilisation Pratique

### Initialisation des Soldes Agent

1. **Création manuelle** :

   - Aller dans la fiche de l'agent
   - Onglet "Soldes Agent" → Ajouter une ligne
   - Sélectionner le type et l'opérateur
   - Saisir le solde initial

2. **Via les menus** :
   - "Opérations > Soldes Agents"
   - Créer les soldes nécessaires

### Gestion de la Caisse

1. **Depuis la fiche agent** :

   - Cliquer sur le bouton "Caisse"
   - Utiliser les boutons "Ajouter/Retirer Liquidités"

2. **Depuis la vue Kanban** :
   - Boutons rapides sur les cartes de caisse

### Surveillance des Soldes

1. **Vue d'ensemble** : Menu "Soldes Agents" → Vue Kanban
2. **Analyse** : Vue Pivot pour comparaisons
3. **Par agent** : Fiche agent → Statistiques

## Points Techniques

### Nouveaux Modèles

- `mm.agent.balance` : Gestion des soldes agents

### Modèles Modifiés

- `mm.agent` : Relations vers soldes et calculs
- `mm.transaction` : Contrôles et mises à jour soldes agents

### Contraintes de Base de Données

- Un seul solde par opérateur par agent
- Un seul solde de caisse par agent
- Soldes toujours positifs
- Type de solde cohérent avec opérateur

### Fichiers Créés/Modifiés

- `models/agent_balance.py` (nouveau)
- `views/mm_agent_balance_views.xml` (nouveau)
- `models/agent.py` (modifié)
- `models/transaction.py` (modifié)
- `views/mm_agent_views.xml` (modifié)
- `views/mm_menus.xml` (modifié)
- `security/ir.model.access.csv` (modifié)

## Workflow Complet

### Exemple : Dépôt de 10,000 FCFA

**Avant la transaction :**

- Client : 0 FCFA sur Orange Money
- Agent : 50,000 FCFA en caisse, 100,000 FCFA sur Orange Money

**Vérifications :**

- Agent a-t-il 10,000 FCFA en caisse ? ✅ (50,000 disponible)

**Après la transaction :**

- Client : 10,000 FCFA sur Orange Money
- Agent : 40,000 FCFA en caisse, 110,000 FCFA sur Orange Money

### Exemple : Retrait de 15,000 FCFA

**Avant la transaction :**

- Client : 20,000 FCFA sur Wave
- Agent : 30,000 FCFA en caisse, 80,000 FCFA sur Wave

**Vérifications :**

- Client a-t-il 15,000 FCFA sur Wave ? ✅ (20,000 disponible)
- Agent a-t-il 15,000 FCFA sur Wave ? ✅ (80,000 disponible)

**Après la transaction :**

- Client : 5,000 FCFA sur Wave
- Agent : 45,000 FCFA en caisse, 65,000 FCFA sur Wave

## Conseils d'Utilisation

1. **Initialisation** : Configurez les soldes de tous vos agents avant utilisation
2. **Surveillance** : Utilisez la vue Kanban pour un suivi visuel rapide
3. **Gestion de caisse** : Alimentez régulièrement les caisses des agents
4. **Reporting** : Utilisez la vue Pivot pour analyser la répartition des liquidités

Cette implémentation garantit un contrôle total des liquidités et empêche les transactions impossibles côté agent ! 🎯
