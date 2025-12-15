# Guide moderne : Gérer AWS S3 dans un projet Django (sans parler code)

> Ce guide est pensé pour un·e **admin**, un·e **lead dev** ou un·e **ops** qui doit
> configurer, sécuriser et surveiller S3 pour un projet Django déjà en place,
> sans rentrer dans les détails du code Python.

---

## 1. Résumé rapide

- **Objectif**  
  Mettre en place une gestion propre de S3 pour les fichiers médias d’un projet Django
  (images, documents, uploads), en gardant le code simple côté Django.

- **Ce que vous aurez à la fin**  
  - 1 bucket S3 bien organisé (dossiers médias / statiques)
  - 1 utilisateur IAM avec permissions minimales
  - Des politiques S3 cohérentes (public / privé)
  - Des variables d’environnement propres (local + Heroku)
  - Une stratégie de monitoring et de sécurité de base

- **Public ciblé**  
  - Admins / DevOps / développeurs backend
  - Personnes qui gèrent la prod (ou pré-prod) d’une app Django

- **Ne couvre PAS**  
  - Les détails de code Python (views, models, forms)
  - Front-end avancé

---

## 2. Vue d’ensemble : qui fait quoi ?

Dans cette architecture :

- **Django** gère :
  - La logique métier
  - Les formulaires d’upload
  - La génération d’URL pour les fichiers

- **`django-storages` + `boto3`** gèrent :
  - La connexion à S3
  - L’upload / suppression des fichiers
  - Les URLs signées pour les fichiers privés

- **AWS S3** gère :
  - Le stockage des fichiers
  - Les ACL (public / privé)
  - Les politiques de bucket
  - Les options de chiffrement et de cycle de vie

Résultat :  
**Django ne “voit” pas S3**, il voit juste un “storage” abstrait.  
Tout le travail d’administration se fait côté AWS (S3, IAM, Policies).

---

## 3. Pré-requis

Avant de commencer, vous devez avoir :

1. **Un compte AWS** actif
2. **Accès à la console AWS** :
   - S3
   - IAM
   - Billing (pour surveiller les coûts)
3. **Un projet Django** déjà configuré avec :
   - `django-storages`
   - `boto3`
4. **Un environnement de déploiement** :
   - local (virtualenv)
   - Heroku (ou autre PaaS)

> 💡 **Astuce**  
> Pour les tests, créez d’abord un **bucket de pré-production** (ex. `mon-app-staging-media`)
> avant d’attaquer directement la prod.

---

## 4. Créer et organiser le bucket S3

### 4.1. Créer le bucket

Sur la console AWS :

1. Ouvrez **S3** → **Create bucket**
2. Paramètres principaux :
   - **Bucket name** :  
     - Unique et en minuscules (ex. `mon-app-media`, `entreprise-portfolio-media`)
   - **Region** :  
     - Proche de vos utilisateurs (ex. `eu-west-3` pour Paris)
3. Laissez les autres options par défaut, sauf si vous savez ce que vous faites.

> ⚠️ **Important : nom du bucket**  
> Le nom est globalement unique **dans tout AWS**.  
> Si `mon-app-media` est déjà pris, choisissez une variante (ex. `mon-app-media-prod-2025`).

### 4.2. Organisation recommandée dans le bucket

Vous n’êtes pas obligé de créer ces dossiers à la main : Django les créera au fur et à mesure des uploads.

```text
votre-bucket/
├── media/              # Fichiers uploadés par Django
│   ├── blog/           # Images d’articles de blog
│   ├── products/       # Images de produits
│   ├── profile/        # Photos de profil
│   └── timeline/       # Images de timeline / parcours
├── static/             # Fichiers statiques (si vous utilisez S3 pour les staticfiles)
└── uploads/            # Uploads temporaires (ex. CKEditor)
```

> 💡 **Bonnes pratiques d’orga**
> - Réfléchissez en **domaines fonctionnels** (`blog/`, `profile/`, etc.)
> - Évitez de tout mettre en vrac à la racine de `media/`

---

## 5. IAM : créer un utilisateur dédié pour Django

### 5.1. Créer l’utilisateur IAM

1. Ouvrez **IAM** → **Users** → **Add users**
2. Nom suggéré : `django-s3-user` (ou similaire)
3. Type d’accès :
   - **Programmatic access** (accès via clés API, pas accès console)
4. Continuez jusqu’à l’étape des permissions.

### 5.2. Donner les bonnes permissions

#### Option simple (non recommandée en prod)

- Attacher la politique gérée `AmazonS3FullAccess`  
  → pratique pour les tests mais **trop large** en production.

#### Option propre (recommandée)

Créer une **politique personnalisée** avec **permissions minimales** :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:HeadObject",
        "s3:PutObjectAcl"
      ],
      "Resource": [
        "arn:aws:s3:::votre-bucket",
        "arn:aws:s3:::votre-bucket/*"
      ]
    }
  ]
}
```

> ⚠️ **Principe du moindre privilège**  
> - Ne donnez jamais `s3:*` si ce n’est pas indispensable.  
> - Limitez les `Resource` à **un bucket précis**, pas `*`.

### 5.3. Générer les clés d’accès

1. Sur la fiche de l’utilisateur IAM → onglet **Security credentials**
2. **Create access key**
3. Choisir : **Application running outside AWS**
4. Notez / téléchargez :
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

Ne les perdez pas, **on en aura besoin pour Django**.

---

## 6. Politiques de bucket : public vs privé

### 6.1. Règle générale

- **Fichiers “médias utilisateurs”** (photos de profil, documents, etc.) :
  - Généralement **privés**
  - Accès via **URLs signées** générées par `django-storages`

- **Fichiers “assets publics”** (images de blog, icônes, etc.) :
  - Peuvent être **publics** (lecture seule)
  - Servis directement par S3 (ou CloudFront)

### 6.2. Politique de lecture publique (exemple)

Pour rendre tous les fichiers sous `media/` lisibles publiquement :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicReadMedia",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::votre-bucket/media/*"
    }
  ]
}
```

À coller dans :  
**S3 → votre bucket → Permissions → Bucket policy**.

> ⚠️ **Attention**  
> Cette politique rend **tous les fichiers sous `media/` accessibles publiquement**.  
> Si vous stockez des fichiers sensibles, limitez le chemin (ex. `media/blog/*` seulement).

### 6.3. Bloquage d’accès public (Public Access Block)

Pour que la politique ci-dessus fonctionne, il faut parfois **relâcher** deux verrous :

1. S3 → votre bucket → **Permissions**
2. Section **Block public access (bucket settings)** → **Edit**
3. Décochez au minimum :
   - “Block public access to buckets and objects granted through new access control lists (ACLs)”
   - “Block public access to buckets and objects granted through any access control lists (ACLs)”

> ⚠️ **Sécurité**  
> - Ne faites cela que pour des buckets / préfixes vraiment destinés à être publics.  
> - Les fichiers **vraiment privés** doivent rester avec ACL `private` et n’être servis que via URLs signées.

---

## 7. Variables d’environnement : local & production

### 7.1. Variables minimales à définir

Dans votre `.env` local (jamais commité) et dans les Config Vars Heroku :

```text
AWS_ACCESS_KEY_ID=VOTRE_CLE
AWS_SECRET_ACCESS_KEY=VOTRE_CLE_SECRETE
AWS_STORAGE_BUCKET_NAME=votre-bucket
AWS_S3_REGION_NAME=eu-west-3
```

Optionnel pour forcer S3 même en local :

```text
USE_S3_STORAGE=True
```

> 💡 **Astuce**  
> - En dev, commencez sans `USE_S3_STORAGE` (stockage local)  
> - Puis activez `USE_S3_STORAGE=True` pour tester les uploads S3 depuis votre machine.

### 7.2. Sur Heroku

Via le dashboard :

1. **Settings** → **Config Vars** → **Reveal Config Vars**
2. Ajoutez les 4 variables AWS

Ou via CLI :

```bash
heroku config:set AWS_ACCESS_KEY_ID=VOTRE_CLE
heroku config:set AWS_SECRET_ACCESS_KEY=VOTRE_CLE_SECRETE
heroku config:set AWS_STORAGE_BUCKET_NAME=votre-bucket
heroku config:set AWS_S3_REGION_NAME=eu-west-3
```

---

## 8. Monitoring, coûts et logs

### 8.1. CloudWatch Metrics

Dans **CloudWatch → Metrics → S3**, surveillez notamment :

- `BucketSizeBytes` : taille totale du bucket
- `NumberOfObjects` : nombre d’objets
- `AllRequests` : volume de requêtes

### 8.2. Budgets et alertes de coût

Dans **AWS Billing → Budgets** :

- Créez un budget :
  - **Budget S3 mensuel** (ex. 10–20 €)
  - Alerte email quand seuil dépassé

### 8.3. Logs d’accès

Pour analyser qui accède à quoi :

1. S3 → votre bucket → onglet **Properties**
2. Section **Server access logging**
3. Activez et envoyez les logs vers **un autre bucket** (dédié aux logs)

---

## 9. Sécurité : check-list minimale

### 9.1. Principe du moindre privilège

- Les utilisateurs IAM ne doivent avoir accès **qu’aux buckets nécessaires**
- Évitez `AmazonS3FullAccess` en prod

### 9.2. Rotation des clés

- Changez régulièrement les clés IAM (ex. tous les 90 jours)
- Ne supprimez jamais une ancienne clé avant d’avoir vérifié que la nouvelle fonctionne

### 9.3. Chiffrement

Dans le bucket :

1. Onglet **Properties** → **Default encryption**
2. Choix :
   - `AES-256` (géré par S3, gratuit)
   - ou KMS si vous avez besoin de contrôle fin (payant)

### 9.4. Versioning & suppression

- Activez le **versioning** pour :
  - récupérer des fichiers supprimés par erreur
  - restaurer une version précédente
- Ajoutez éventuellement **MFA Delete** pour les environnements critiques.

---

## 10. Dépannage : erreurs typiques

### 10.1. Erreur 403 Forbidden (accès refusé)

Causes possibles :

- Permissions IAM insuffisantes
- Politique de bucket trop restrictive
- Blocage d’accès public encore actif

Checklist :

1. Vérifier la **politique IAM** de l’utilisateur (`s3:PutObject`, `s3:GetObject`, etc.)
2. Vérifier la **Bucket policy**
3. Vérifier les **Public Access Block settings**

### 10.2. “The bucket does not exist”

Vérifications :

- Le nom dans `AWS_STORAGE_BUCKET_NAME` correspond exactement au nom du bucket
- La région (`AWS_S3_REGION_NAME`) est correcte

### 10.3. Fichiers bien uploadés mais invisibles dans la console S3

Pistes :

- Les fichiers sont rangés dans un **préfixe** (ex. `media/blog/…`)
- La console S3 filtre peut-être par **préfixe**
- Vérifiez les logs Django (ou la base) pour connaître le chemin exact.

### 10.4. Coûts S3 qui explosent

Actions possibles :

1. Mettre en place des **règles de cycle de vie** :
   - ex. supprimer `media/temp/` après 7 jours
   - archiver certains dossiers en Glacier après X jours
2. Supprimer les fichiers orphelins / non utilisés
3. Ajouter CloudFront pour réduire certains coûts de transfert

---

## 11. Checklist finale avant prod

- [ ] Bucket S3 créé dans la bonne région
- [ ] Utilisateur IAM dédié avec permissions minimales
- [ ] Clés IAM stockées de façon sécurisée (et pas dans Git)
- [ ] Variables d’environnement configurées (local + Heroku)
- [ ] Politique de bucket cohérente (public / privé)
- [ ] Blocage d’accès public configuré correctement
- [ ] Chiffrement par défaut activé
- [ ] Versioning activé (recommandé)
- [ ] Budgets & alertes de coût en place
- [ ] Test d’upload / suppression depuis Django
- [ ] Documentation interne mise à jour

---

## 12. Ressources utiles

- Documentation AWS S3  
  `https://docs.aws.amazon.com/s3/`
- Documentation `django-storages`  
  `https://django-storages.readthedocs.io/`
- Calculateur de coûts AWS  
  `https://calculator.aws/`
- Bonnes pratiques de sécurité S3  
  `https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html`

---

En suivant ce guide, vous avez une base solide pour :

- stocker vos fichiers Django sur S3 proprement,
- contrôler finement **qui a accès à quoi**,
- garder une bonne **maîtrise des coûts**,
- tout en restant aligné avec les bonnes pratiques de sécurité AWS.


