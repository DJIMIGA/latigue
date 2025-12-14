# Guide de Gestion AWS S3 pour un Projet Django

## Table des matières
1. [Introduction](#introduction)
2. [Prérequis](#prérequis)
3. [Configuration AWS](#configuration-aws)
4. [Gestion des Buckets](#gestion-des-buckets)
5. [Gestion des Permissions IAM](#gestion-des-permissions-iam)
6. [Gestion des Politiques de Bucket](#gestion-des-politiques-de-bucket)
7. [Gestion des Variables d'Environnement](#gestion-des-variables-denvironnement)
8. [Surveillance et Monitoring](#surveillance-et-monitoring)
9. [Bonnes Pratiques de Sécurité](#bonnes-pratiques-de-sécurité)
10. [Dépannage](#dépannage)

---

## Introduction

Ce guide explique comment gérer AWS S3 pour stocker les fichiers médias d'un projet Django. Il se concentre sur les aspects administratifs et de configuration, sans entrer dans les détails du code.

### Pourquoi utiliser S3 ?

- **Scalabilité** : Stockage illimité
- **Performance** : CDN intégré avec CloudFront
- **Coût** : Payez uniquement ce que vous utilisez
- **Fiabilité** : 99.999999999% (11 9's) de durabilité
- **Sécurité** : Contrôle d'accès granulaire

---

## Prérequis

Avant de commencer, vous devez avoir :

1. **Un compte AWS** actif
2. **Accès à la console AWS** (IAM, S3)
3. **Connaissances de base** sur AWS IAM et S3
4. **Votre projet Django** configuré avec `django-storages` et `boto3`

---

## Configuration AWS

### 1. Créer un Bucket S3

#### Via la Console AWS :

1. Connectez-vous à la [Console AWS S3](https://s3.console.aws.amazon.com/)
2. Cliquez sur **"Create bucket"**
3. Configurez le bucket :
   - **Nom du bucket** : Choisissez un nom unique (ex: `mon-projet-media`)
   - **Région** : Sélectionnez la région la plus proche de vos utilisateurs (ex: `eu-west-3` pour l'Europe)
   - **Paramètres par défaut** : Laissez les valeurs par défaut
4. **Paramètres de blocage d'accès public** :
   - Pour les fichiers privés : Gardez les blocages activés
   - Pour les fichiers publics : Désactivez les blocages nécessaires
5. Cliquez sur **"Create bucket"**

#### Bonnes Pratiques pour le Nom du Bucket :

- Utilisez des noms en minuscules
- Pas d'espaces ni de caractères spéciaux
- Nom unique globalement (tous les buckets S3 partagent le même espace de noms)
- Exemples : `mon-projet-media`, `entreprise-stockage-2024`

### 2. Configuration de la Région

**Régions recommandées :**
- **Europe** : `eu-west-3` (Paris), `eu-west-1` (Irlande)
- **Amérique du Nord** : `us-east-1` (Virginie), `us-west-2` (Oregon)
- **Asie** : `ap-southeast-1` (Singapour)

**Impact sur les coûts :**
- Choisir une région proche réduit la latence
- Les transferts de données entre régions peuvent avoir des coûts supplémentaires

---

## Gestion des Buckets

### Organisation des Dossiers

Structure recommandée dans votre bucket :

```
votre-bucket/
├── media/              # Fichiers médias uploadés par les utilisateurs
│   ├── blog/          # Images des articles de blog
│   ├── products/      # Images de produits
│   ├── profile/       # Photos de profil
│   └── timeline/      # Images de la timeline
├── static/            # Fichiers statiques (si vous utilisez S3 pour les statiques)
└── uploads/           # Fichiers temporaires ou uploads CKEditor
```

### Gestion du Cycle de Vie

Configurez des règles de cycle de vie pour optimiser les coûts :

1. Allez dans votre bucket → **"Management"** → **"Lifecycle rules"**
2. Créez une règle pour :
   - **Archiver les anciens fichiers** vers Glacier après X jours
   - **Supprimer automatiquement** les fichiers temporaires après X jours
   - **Transitions de classe de stockage** pour réduire les coûts

**Exemple de règle :**
- Fichiers dans `media/temp/` → Supprimer après 7 jours
- Fichiers dans `media/archive/` → Transférer vers Glacier après 90 jours

### Versioning

**Activer le versioning** pour :
- Protéger contre les suppressions accidentelles
- Conserver l'historique des modifications
- Faciliter la récupération

**Attention :** Le versioning augmente les coûts de stockage.

---

## Gestion des Permissions IAM

### Créer un Utilisateur IAM

1. Allez sur [Console IAM](https://console.aws.amazon.com/iam/)
2. **Users** → **"Add users"**
3. Nom d'utilisateur : `django-s3-user` (ou similaire)
4. Type d'accès : **"Programmatic access"** (pour obtenir les clés API)
5. Cliquez sur **"Next: Permissions"**

### Attacher une Politique

#### Option 1 : Politique Gérée AWS (Simple mais moins flexible)

- `AmazonS3FullAccess` : Accès complet (non recommandé pour la production)
- `AmazonS3ReadOnlyAccess` : Lecture seule

#### Option 2 : Politique Personnalisée (Recommandé)

Créez une politique avec les permissions minimales nécessaires :

**Permissions requises pour Django :**
- `s3:PutObject` - Uploader des fichiers
- `s3:GetObject` - Télécharger des fichiers
- `s3:DeleteObject` - Supprimer des fichiers
- `s3:ListBucket` - Lister les fichiers
- `s3:HeadObject` - Vérifier l'existence d'un fichier
- `s3:PutObjectAcl` - Modifier les ACL des objets
- `s3:PutBucketPolicy` - Modifier les politiques de bucket (optionnel)
- `s3:GetBucketPolicy` - Lire les politiques de bucket (optionnel)

**Exemple de politique minimale :**

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

### Générer les Clés d'Accès

1. Après avoir créé l'utilisateur, allez dans **"Security credentials"**
2. Cliquez sur **"Create access key"**
3. Choisissez **"Application running outside AWS"**
4. **Important** : Téléchargez et sauvegardez les clés immédiatement
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

⚠️ **Sécurité** : Ne partagez jamais ces clés et ne les commitez pas dans Git !

---

## Gestion des Politiques de Bucket

### Politique pour Accès Public (Lecture)

Si vous voulez que certains fichiers soient accessibles publiquement :

1. Allez dans votre bucket → **"Permissions"** → **"Bucket policy"**
2. Collez une politique comme celle-ci :

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::votre-bucket/media/*"
        }
    ]
}
```

**Note** : Cette politique rend tous les fichiers dans `media/` accessibles publiquement.

### Désactiver le Blocage d'Accès Public

Pour que la politique de bucket fonctionne :

1. Bucket → **"Permissions"** → **"Block public access (bucket settings)"**
2. Cliquez sur **"Edit"**
3. Décochez au minimum :
   - "Block public access to buckets and objects granted through new access control lists (ACLs)"
   - "Block public access to buckets and objects granted through any access control lists (ACLs)"
4. Cliquez sur **"Save changes"**

⚠️ **Attention** : Désactiver ces paramètres permet l'accès public. Assurez-vous que vos fichiers sensibles utilisent des ACL privées.

### Politique pour Fichiers Privés

Pour les fichiers privés (médias utilisateurs), utilisez :
- **ACL privée** : `private` (par défaut)
- **URLs signées** : Générées automatiquement par django-storages avec `querystring_auth = True`

Les URLs signées sont temporaires et sécurisées, même si le bucket autorise l'accès public.

---

## Gestion des Variables d'Environnement

### Variables Requises

Dans votre fichier `.env` (local) ou dans les Config Vars Heroku :

```
AWS_ACCESS_KEY_ID=votre_cle_acces
AWS_SECRET_ACCESS_KEY=votre_cle_secrete
AWS_STORAGE_BUCKET_NAME=votre-nom-bucket
AWS_S3_REGION_NAME=eu-west-3
```

### Variable Optionnelle pour Tests Locaux

```
USE_S3_STORAGE=True  # Pour forcer l'utilisation de S3 même en local
```

### Configuration sur Heroku

1. Allez sur [Heroku Dashboard](https://dashboard.heroku.com/)
2. Sélectionnez votre application
3. **Settings** → **Config Vars** → **"Reveal Config Vars"**
4. Ajoutez les 4 variables AWS

**Via CLI Heroku :**
```bash
heroku config:set AWS_ACCESS_KEY_ID=votre_cle
heroku config:set AWS_SECRET_ACCESS_KEY=votre_cle_secrete
heroku config:set AWS_STORAGE_BUCKET_NAME=votre-bucket
heroku config:set AWS_S3_REGION_NAME=eu-west-3
```

### Sécurité des Variables

- ✅ **Ne jamais** commiter le fichier `.env` dans Git
- ✅ Utiliser des clés IAM avec permissions minimales
- ✅ Roter les clés régulièrement (tous les 90 jours recommandé)
- ✅ Utiliser des secrets managers en production (AWS Secrets Manager, HashiCorp Vault)

---

## Surveillance et Monitoring

### CloudWatch Metrics

1. Allez sur [CloudWatch](https://console.aws.amazon.com/cloudwatch/)
2. **Metrics** → **S3**
3. Surveillez :
   - **BucketSizeBytes** : Taille totale du bucket
   - **NumberOfObjects** : Nombre d'objets
   - **AllRequests** : Nombre de requêtes

### Alertes de Coût

1. Allez sur [AWS Billing](https://console.aws.amazon.com/billing/)
2. **Budgets** → **"Create budget"**
3. Configurez une alerte pour :
   - Coûts S3 > X€ par mois
   - Taille du bucket > X GB

### Logs d'Accès

Activez les logs d'accès S3 :

1. Bucket → **"Management"** → **"Server access logging"**
2. Activez les logs vers un autre bucket
3. Analysez les logs pour détecter :
   - Accès suspects
   - Utilisation excessive
   - Erreurs fréquentes

---

## Bonnes Pratiques de Sécurité

### 1. Principe du Moindre Privilège

- Donnez uniquement les permissions nécessaires à l'utilisateur IAM
- Ne donnez jamais `s3:*` (toutes les permissions)

### 2. Rotation des Clés

- Changez les clés d'accès tous les 90 jours
- Créez une nouvelle clé avant de supprimer l'ancienne
- Testez avec la nouvelle clé avant de supprimer l'ancienne

### 3. Chiffrement

Activez le chiffrement pour votre bucket :

1. Bucket → **"Properties"** → **"Default encryption"**
2. Choisissez :
   - **AES-256** : Chiffrement géré par S3 (gratuit)
   - **AWS-KMS** : Chiffrement avec clés gérées (plus de contrôle, coût supplémentaire)

### 4. Versioning et MFA Delete

- Activez le versioning pour protéger contre les suppressions
- Activez MFA Delete pour protéger les suppressions de versions

### 5. Politique de Bucket Restrictive

Limitez l'accès public uniquement aux dossiers nécessaires :

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::votre-bucket/static/*"  // Seulement static/
        }
    ]
}
```

### 6. CORS (Cross-Origin Resource Sharing)

Si vous servez des fichiers depuis un domaine différent :

1. Bucket → **"Permissions"** → **"Cross-origin resource sharing (CORS)"**
2. Configurez les règles CORS pour autoriser uniquement vos domaines

---

## Dépannage

### Erreur 403 Forbidden

**Causes possibles :**
- Permissions IAM insuffisantes
- Politique de bucket trop restrictive
- Blocage d'accès public activé

**Solutions :**
1. Vérifiez les permissions IAM de l'utilisateur
2. Vérifiez la politique de bucket
3. Désactivez les blocages d'accès public si nécessaire

### Erreur : Bucket n'existe pas

**Solution :**
- Vérifiez le nom du bucket dans `AWS_STORAGE_BUCKET_NAME`
- Assurez-vous que le bucket existe dans la bonne région

### Fichiers non visibles dans S3

**Vérifications :**
1. Les fichiers sont peut-être dans un sous-dossier (ex: `media/blog/image.jpg`)
2. Vérifiez les filtres dans la console S3
3. Vérifiez les logs Django pour voir où les fichiers sont uploadés

### Coûts élevés

**Optimisations :**
1. Activez les règles de cycle de vie pour archiver les anciens fichiers
2. Utilisez la classe de stockage appropriée (Standard, Intelligent-Tiering, Glacier)
3. Supprimez les fichiers inutilisés
4. Utilisez CloudFront pour réduire les coûts de transfert

### Latence élevée

**Solutions :**
1. Choisissez une région proche de vos utilisateurs
2. Utilisez CloudFront comme CDN
3. Optimisez la taille des images avant upload

---

## Checklist de Déploiement

Avant de déployer en production :

- [ ] Bucket S3 créé dans la bonne région
- [ ] Utilisateur IAM créé avec permissions minimales
- [ ] Clés d'accès générées et stockées de manière sécurisée
- [ ] Variables d'environnement configurées sur Heroku
- [ ] Politique de bucket configurée (si nécessaire)
- [ ] Blocage d'accès public configuré selon les besoins
- [ ] Chiffrement activé sur le bucket
- [ ] Versioning activé (recommandé)
- [ ] Alertes de coût configurées
- [ ] Tests d'upload effectués
- [ ] Documentation mise à jour

---

## Ressources Utiles

- [Documentation AWS S3](https://docs.aws.amazon.com/s3/)
- [Documentation django-storages](https://django-storages.readthedocs.io/)
- [Calculateur de coûts AWS](https://calculator.aws/)
- [Meilleures pratiques S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

---

## Conclusion

La gestion de S3 pour Django nécessite une attention particulière sur :
- **Sécurité** : Permissions minimales, chiffrement, rotation des clés
- **Coûts** : Surveillance, optimisation, règles de cycle de vie
- **Performance** : Choix de région, utilisation de CDN
- **Maintenance** : Monitoring, logs, alertes

En suivant ce guide, vous devriez avoir une configuration S3 sécurisée et optimisée pour votre projet Django.

