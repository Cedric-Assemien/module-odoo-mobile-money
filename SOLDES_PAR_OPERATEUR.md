# Gestion des Soldes par Opérateur - Mobile Money Manager

## Vue d'ensemble

Cette mise à jour ajoute la fonctionnalité de gestion des soldes par opérateur pour les clients de Mobile Money. Chaque client peut maintenant avoir des soldes séparés pour différents opérateurs (Wave, Orange Money, Moov Money, MTN Money, etc.).

## Nouvelles Fonctionnalités

### 1. Modèle de Solde (`mm.balance`)

Un nouveau modèle a été créé pour gérer les soldes des clients par opérateur :

- **Solde par opérateur** : Chaque client peut avoir un solde différent pour chaque opérateur
- **Contrôles de sécurité** : Le solde ne peut pas être négatif
- **Suivi des modifications** : Chaque modification de solde est tracée avec date et commentaire
- **Unicité** : Un client ne peut avoir qu'un seul solde par opérateur

### 2. Contrôles de Transaction

Les transactions sont maintenant contrôlées en fonction des soldes disponibles :

- **Retraits** : Vérification que le solde est suffisant avant de permettre le retrait
- **Transferts** : Vérification du solde pour les transferts sortants
- **Dépôts** : Mise à jour automatique du solde lors des dépôts

### 3. Interface Utilisateur

#### Vue Client Améliorée

- **Solde Total** : Affichage du solde total de tous les opérateurs
- **Onglet "Soldes par Opérateur"** : Nouvelle section pour voir tous les soldes
- **Boutons d'action** : Accès rapide pour consulter et ajouter des soldes

#### Nouvelle Vue Soldes

- **Vue Liste** : Affichage de tous les soldes avec filtres
- **Vue Kanban** : Vue en cartes pour une meilleure visualisation
- **Vue Formulaire** : Modification détaillée des soldes

### 4. Permissions et Sécurité

- **Utilisateurs** : Peuvent voir et modifier les soldes (lecture/écriture/création)
- **Managers** : Permissions complètes incluant la suppression
- **Contraintes** : Soldes positifs uniquement, unicité par client/opérateur

## Utilisation

### Création d'un Solde

1. Aller dans la fiche d'un client
2. Cliquer sur l'onglet "Soldes par Opérateur"
3. Cliquer sur "Ajouter une ligne"
4. Sélectionner l'opérateur et saisir le solde initial

### Consultation des Soldes

1. **Depuis la liste des clients** : Le solde total est affiché dans la liste
2. **Depuis la fiche client** :
   - Bouton "Solde Total" dans la zone des statistiques
   - Onglet "Soldes par Opérateur" pour le détail
3. **Menu dédié** : "Opérations > Soldes par Opérateur"

### Transactions avec Contrôle de Solde

1. **Dépôt** : Augmente automatiquement le solde de l'opérateur sélectionné
2. **Retrait** :
   - Vérifie que le solde est suffisant
   - Soustrait le montant du solde
   - Affiche une erreur si le solde est insuffisant
3. **Transfert** : Traité comme un retrait (soustraction du solde)

## Messages d'Erreur

### Solde Insuffisant

```
Solde insuffisant sur [Opérateur].
Solde disponible: [montant] [devise],
Montant demandé: [montant] [devise]
```

### Solde Négatif

```
Le solde pour [Opérateur] ne peut pas être négatif.
```

## Migration des Données Existantes

Pour les clients existants :

- Les soldes seront créés automatiquement lors de la première transaction
- Les soldes initiaux seront à 0 par défaut
- Il est recommandé de saisir manuellement les soldes existants

## Points Techniques

### Modèles Modifiés

- `mm.customer` : Ajout des relations vers les soldes et calculs de solde total
- `mm.transaction` : Ajout des contrôles et mises à jour de solde
- `mm.balance` : Nouveau modèle pour la gestion des soldes

### Fichiers Créés/Modifiés

- `models/balance.py` (nouveau)
- `views/mm_balance_views.xml` (nouveau)
- `models/customer.py` (modifié)
- `models/transaction.py` (modifié)
- `views/mm_customer_views.xml` (modifié)
- `views/mm_menus.xml` (modifié)
- `security/ir.model.access.csv` (modifié)
- `__manifest__.py` (modifié)

## Conseils d'Utilisation

1. **Initialisation** : Créez les soldes pour vos clients existants avant d'utiliser les contrôles
2. **Suivi** : Utilisez la vue Kanban pour un aperçu rapide des soldes
3. **Contrôle** : Les messages d'erreur guideront l'utilisateur en cas de problème
4. **Traçabilité** : Toutes les modifications de solde sont tracées dans le chatter

Cette implémentation garantit un contrôle strict des soldes tout en maintenant la flexibilité nécessaire pour la gestion multi-opérateurs.
