# 📚 Formule Initiation : Le Vibe Coding avec l'IA

## Formation Niveau 1 — 12 heures

**Public :** Grands débutants, aucune expérience requise
**Prérequis :** Un ordinateur (Windows, Mac ou Linux) + internet + un compte Google gratuit
**Outils :** Python + Antigravity (tous gratuits)
**Résultat :** Vous repartirez avec votre propre application web créée par vibe coding

---

# 🟢 MODULE 1 : Votre Environnement de Vibe Coding (2h)

## 1.1 — Le Vibe Coding, c'est quoi ?

### Concept

Le **vibe coding**, c'est une nouvelle façon de programmer : au lieu d'écrire chaque ligne de code vous-même, vous **décrivez ce que vous voulez à une IA**, et elle code pour vous.

Vous devenez le **chef d'orchestre** — l'IA est votre musicien.

### Exemples concrets

- ❌ Ancien monde : Apprendre la syntaxe Python pendant des semaines avant de faire quoi que ce soit
- ✅ Vibe coding : Dire à l'IA *"Crée-moi un site web avec une page d'accueil qui affiche mon nom et mes compétences"* et obtenir le résultat en 2 minutes

### Pourquoi ça change tout

- **Pas besoin de mémoriser** — l'IA connaît la syntaxe
- **Résultats immédiats** — vous voyez votre app tourner dès la première heure
- **Apprentissage par la pratique** — vous comprenez le code en le voyant généré
- **Focus sur la créativité** — vous pensez au "quoi", l'IA gère le "comment"

> 💡 **Le développeur du futur ne tape pas du code — il dirige l'IA.**

---

## 1.2 — Installation de Python

Python est le langage que l'IA va utiliser pour créer vos applications. Il faut l'installer sur votre ordinateur.

### 🪟 Sur Windows

1. Allez sur **https://www.python.org/downloads/**
2. Cliquez sur **"Download Python 3.14.x"** (le gros bouton jaune)
3. Lancez le fichier `.exe` téléchargé
4. ⚠️ **IMPORTANT :** Cochez la case **"Add python.exe to PATH"** en bas de la fenêtre
5. Cliquez sur **"Install Now"**
6. Attendez la fin de l'installation

**Alternative (encore plus simple) :**
- Ouvrez le **Microsoft Store** sur votre PC
- Cherchez **"Python 3.14"**
- Cliquez **Installer**

### 🍎 Sur Mac

1. Allez sur **https://www.python.org/downloads/**
2. Téléchargez la version macOS
3. Ouvrez le fichier `.pkg` et suivez les étapes

### 🐧 Sur Linux

Ouvrez un terminal et tapez :
```bash
sudo apt update && sudo apt install python3 python3-pip
```

### ✅ Vérification

Ouvrez un terminal (ou "Invite de commandes" sur Windows) et tapez :
```
python --version
```
Vous devez voir : `Python 3.14.x`

Si ça affiche une erreur, redémarrez votre ordinateur et réessayez.

> 🎥 **Vidéo : Installation de Python pas à pas** *(à venir)*

---

## 1.3 — Installation d'Antigravity

Antigravity est votre **IDE IA** — l'outil dans lequel vous allez coder avec l'intelligence artificielle. C'est fait par Google et c'est **100% gratuit**.

### Téléchargement

1. Allez sur **https://antigravity.google/download**
2. Le site détecte automatiquement votre système (Windows, Mac, Linux)
3. Cliquez sur **"Download"**

### Installation

**🪟 Windows :**
- Lancez le fichier `.exe`
- Si Windows Defender affiche un avertissement, cliquez **"Exécuter quand même"**
- Suivez les étapes d'installation

**🍎 Mac :**
- Ouvrez le fichier `.dmg`
- Glissez Antigravity dans le dossier **Applications**
- Au premier lancement, allez dans Préférences Système → Sécurité pour autoriser l'app

**🐧 Linux :**
```bash
sudo dpkg -i antigravity.deb
# ou
sudo rpm -i antigravity.rpm
```

### Premier lancement

1. Ouvrez Antigravity
2. **Connectez-vous avec votre compte Google** (obligatoire pour accéder à l'IA)
3. L'application vous propose d'installer des extensions recommandées → **acceptez tout** (notamment l'extension Python)
4. Si vous avez déjà utilisé VS Code, Antigravity propose d'**importer vos paramètres** → pratique !

### L'interface

Antigravity a **deux vues principales** :

| Vue | Rôle |
|-----|------|
| **Editor** | Comme VS Code — vous écrivez et modifiez du code, avec l'IA qui vous assiste en temps réel |
| **Manager** | L'IA travaille en autonomie — vous lui donnez une mission, elle planifie et exécute |

> 🎥 **Vidéo : Installation et découverte d'Antigravity** *(à venir)*

---

## 1.4 — Votre Premier Prompt

C'est le moment magique : vous allez demander à l'IA de créer du code pour vous.

### Exercice 1 : Hello World en vibe coding

1. Dans Antigravity, ouvrez la **sidebar agent** (icône robot à droite)
2. Tapez dans le chat :

> **"Crée un fichier Python qui affiche 'Bonjour, je suis [votre prénom] et j'apprends le vibe coding !'"**

3. L'IA génère le code
4. Cliquez sur **"Accept"** pour accepter le code
5. Faites clic droit sur le fichier → **"Run Python"**
6. 🎉 Votre premier programme fonctionne !

### Exercice 2 : Un programme interactif

Tapez dans le chat de l'agent :

> **"Crée un programme Python qui demande le prénom de l'utilisateur, puis affiche un message de bienvenue personnalisé avec la date du jour"**

Observez :
- L'IA a importé le module `datetime` — vous n'avez pas eu besoin de le savoir
- Elle a utilisé `input()` pour demander le prénom
- Le code est propre et commenté

### Ce qu'il faut retenir

- **Un prompt = une instruction claire** de ce que vous voulez
- Plus votre description est **précise**, meilleur est le résultat
- Vous pouvez toujours **demander des modifications** : *"Change le message"*, *"Ajoute des couleurs"*, etc.

> 🎥 **Vidéo : Votre premier programme en vibe coding** *(à venir)*

---

# 🟡 MODULE 2 : Maîtriser les Agents IA (3h)

## 2.1 — Tab Completions : l'IA lit dans vos pensées

### Comment ça marche

Quand vous tapez du code dans Antigravity, l'IA **prédit ce que vous allez écrire** et vous propose la suite en gris. Appuyez sur **Tab** pour accepter.

### Exercice pratique

1. Créez un nouveau fichier `calcul.py`
2. Commencez à taper : `def calculer_`
3. L'IA propose la suite → appuyez **Tab**
4. Continuez à taper et observez comment l'IA complète intelligemment

### Astuces

- L'IA s'adapte au **contexte** de votre fichier
- Plus votre code est organisé, meilleures sont les suggestions
- Vous pouvez ignorer une suggestion en continuant à taper normalement
- **Tabulation = accepter**, **Escape = refuser**

> 🎥 **Vidéo : Les Tab completions en action** *(à venir)*

---

## 2.2 — Commandes Inline : modifier le code par le dialogue

### Le principe

Sélectionnez du code, puis utilisez le raccourci **Ctrl+I** (ou **Cmd+I** sur Mac) pour ouvrir un mini-chat. Décrivez ce que vous voulez changer — l'IA modifie le code sélectionné.

### Exemples de commandes inline

| Vous dites | L'IA fait |
|-----------|-----------|
| *"Ajoute une gestion d'erreurs"* | Entoure le code de try/except |
| *"Traduis les commentaires en français"* | Traduit tous les commentaires |
| *"Rends cette fonction plus rapide"* | Optimise l'algorithme |
| *"Ajoute des commentaires explicatifs"* | Commente chaque ligne |

### Exercice

1. Reprenez le fichier de l'exercice précédent
2. Sélectionnez tout le code
3. Tapez **Ctrl+I** puis : *"Ajoute une gestion d'erreurs si l'utilisateur entre un texte au lieu d'un nombre"*
4. Observez les modifications proposées
5. Acceptez ou demandez un ajustement

> 🎥 **Vidéo : Commandes inline et modification de code** *(à venir)*

---

## 2.3 — L'Art du Prompt : bien parler à l'IA

### Les règles d'or

**1. Soyez précis**
- ❌ *"Fais un truc avec des données"*
- ✅ *"Crée un programme qui lit un fichier CSV de contacts et affiche les noms triés par ordre alphabétique"*

**2. Donnez le contexte**
- ❌ *"Ajoute un bouton"*
- ✅ *"Ajoute un bouton 'Supprimer' rouge à côté de chaque élément de la liste, qui supprime l'élément au clic"*

**3. Procédez par étapes**
- Au lieu de demander une app complète d'un coup, construisez brique par brique
- *"D'abord, crée la page d'accueil"* → *"Maintenant, ajoute une barre de navigation"* → *"Ajoute un formulaire de contact"*

**4. Demandez des explications**
- *"Explique-moi ce que fait chaque ligne de ce code"*
- C'est comme ça que vous apprenez vraiment !

### Exercice : Le jeu du prompt

1. Objectif : créer un **convertisseur de devises** (EUR ↔ FCFA)
2. Essayez d'abord avec un prompt vague : *"Fais un convertisseur"*
3. Puis avec un prompt précis : *"Crée un programme Python qui convertit des euros en FCFA et inversement. Le taux est 1 EUR = 655,957 FCFA. Le programme demande le montant et la direction de conversion, puis affiche le résultat formaté avec le symbole de la devise."*
4. Comparez les deux résultats !

> 🎥 **Vidéo : L'art du prompt — parler à l'IA comme un pro** *(à venir)*

---

## 2.4 — Les Artifacts : les rapports de votre agent

### C'est quoi ?

Quand l'agent d'Antigravity travaille sur une tâche, il produit des **Artifacts** :
- 📋 **Plan d'action** — les étapes qu'il va suivre
- 📸 **Screenshots** — captures de l'app en cours
- 📊 **Rapports de progression** — ce qui est fait, ce qui reste
- 🎬 **Walkthroughs** — démonstrations vidéo du résultat

### Pourquoi c'est important

Les Artifacts vous permettent de **vérifier le travail de l'IA** sans lire chaque ligne de code. Vous voyez le résultat, pas le processus.

### Exercice

1. Ouvrez la vue **Manager** d'Antigravity
2. Tapez : *"Crée une page HTML moderne avec mon CV. Mon nom est [votre nom], je suis [votre métier]. Utilise un design sombre et professionnel."*
3. Observez l'agent travailler : il planifie → code → génère des artifacts
4. Consultez les artifacts pour vérifier le résultat avant de valider

> 🎥 **Vidéo : Comprendre et utiliser les Artifacts** *(à venir)*

---

## 2.5 — Exercice récapitulatif Module 2

### Projet : Un script Python utile

Créez **entièrement par le dialogue** (sans taper une seule ligne de code vous-même) un programme qui :

1. Demande à l'utilisateur un dossier sur son ordinateur
2. Liste tous les fichiers du dossier
3. Les trie par type (images, documents, vidéos, autres)
4. Affiche un résumé : combien de fichiers de chaque type

**Méthode :**
- Utilisez la sidebar agent
- Procédez étape par étape
- Demandez des explications sur le code généré
- Testez et itérez

> 🎥 **Vidéo : Créer un script complet en vibe coding** *(à venir)*

---

# 🔴 MODULE 3 : Votre Premier Projet Django en Vibe Coding (5h)

## 3.1 — C'est quoi Django ?

### En 30 secondes

**Django** est un framework Python pour créer des **sites web**. C'est comme un kit de construction : au lieu de tout fabriquer de zéro, Django fournit les briques de base (pages, base de données, formulaires, etc.).

### Pourquoi Django ?

- ✅ Utilisé par Instagram, Pinterest, Mozilla
- ✅ Gratuit et open source
- ✅ Parfait pour apprendre le développement web
- ✅ L'IA le connaît très bien → vibe coding ultra efficace

### Le trio magique de Django

```
URL  →  Vue  →  Template
```

1. **URL** : L'adresse web (ex: `monsite.com/accueil`)
2. **Vue** : La logique (quoi afficher, quelles données récupérer)
3. **Template** : Le HTML (comment ça s'affiche à l'écran)

> 💡 Pas besoin de tout mémoriser — l'IA gère. Mais comprendre ce trio vous aide à mieux guider l'IA.

---

## 3.2 — Créer un projet Django avec l'agent

### Installation de Django

Dans le terminal d'Antigravity :
```bash
pip install django
```

### Création du projet

Demandez à l'agent :

> **"Crée un nouveau projet Django appelé 'monsite'. Initialise-le avec une app appelée 'pages'. Crée une vue pour la page d'accueil qui affiche 'Bienvenue sur mon site !'."**

L'agent va :
1. Exécuter `django-admin startproject monsite`
2. Créer l'app `pages`
3. Configurer les URLs
4. Créer la vue
5. Créer le template HTML

### Lancer le serveur

```bash
cd monsite
python manage.py runserver
```

Ouvrez **http://127.0.0.1:8000** dans votre navigateur → 🎉 votre site tourne !

> 🎥 **Vidéo : Créer un projet Django en 5 minutes avec l'IA** *(à venir)*

---

## 3.3 — Générer vos vues par le dialogue

### Le principe

Au lieu d'écrire le code des vues vous-même, vous décrivez à l'IA ce que chaque page doit faire.

### Exercice : un site de 3 pages

Demandez à l'agent, **une page à la fois** :

**Page 1 — Accueil :**
> *"Crée une page d'accueil avec un titre de bienvenue, un paragraphe de présentation, et 3 cartes avec mes compétences"*

**Page 2 — À propos :**
> *"Crée une page 'À propos' avec ma photo (utilise un placeholder), mon parcours, et un lien vers mon CV"*

**Page 3 — Contact :**
> *"Crée une page contact avec un formulaire : nom, email, message. Pour l'instant, affiche juste un message de confirmation quand on soumet."*

### À chaque étape

- Vérifiez le résultat dans le navigateur (`python manage.py runserver`)
- Si quelque chose ne vous plaît pas, dites-le à l'IA : *"Le titre est trop petit"*, *"Change la couleur en bleu"*, etc.
- Demandez : *"Explique-moi comment cette vue fonctionne"*

> 🎥 **Vidéo : Créer des pages web par le dialogue** *(à venir)*

---

## 3.4 — Créer vos templates : le HTML généré par l'IA

### Concept

Les templates, c'est le **look** de votre site — le HTML et le CSS. L'IA est excellente pour ça !

### Exercice : rendre votre site beau

> *"Ajoute du style CSS à toutes les pages. Je veux un design moderne, sombre, avec la police 'Inter'. La navigation doit être fixe en haut avec des liens vers les 3 pages. Le site doit être responsive (s'adapter au mobile)."*

### Le template de base

Django utilise un système d'**héritage de templates** — un template parent dont tous les autres héritent. Demandez à l'IA :

> *"Crée un template de base `base.html` avec la navigation, le header et le footer. Les autres pages doivent en hériter."*

### Comprendre le résultat

Demandez : *"Explique-moi comment fonctionne l'héritage de templates dans Django avec des mots simples"*

L'IA vous expliquera les balises `{% block %}` et `{% extends %}`.

> 🎥 **Vidéo : Des pages web belles grâce à l'IA** *(à venir)*

---

## 3.5 — Le cycle URL → Vue → Template

### Récapitulatif visuel

```
L'utilisateur tape une URL dans son navigateur
        ↓
Django cherche l'URL dans urls.py
        ↓
Il trouve la vue associée (views.py)
        ↓
La vue prépare les données
        ↓
La vue envoie les données au template (HTML)
        ↓
Le navigateur affiche la page
```

### Exercice de compréhension

L'agent a créé du code pour vous. Maintenant, vous allez **le lire et le comprendre** :

1. Ouvrez `urls.py` → repérez les 3 URLs de vos pages
2. Ouvrez `views.py` → repérez les 3 fonctions correspondantes
3. Ouvrez les templates → voyez comment ils utilisent les données

Demandez à l'IA : *"Montre-moi le chemin complet quand quelqu'un visite /contact — quel fichier est lu en premier, puis lequel, etc."*

> 🎥 **Vidéo : Comprendre le cycle Django** *(à venir)*

---

## 3.6 — Itérer par le dialogue

### Le vrai pouvoir du vibe coding

Votre site est fonctionnel. Maintenant, **améliorez-le par le dialogue** :

| Vous dites | Résultat |
|-----------|----------|
| *"Ajoute des animations quand on scroll"* | Animations CSS/JS ajoutées |
| *"Met un compteur de visites sur la page d'accueil"* | Compteur fonctionnel |
| *"Ajoute un mode sombre / mode clair"* | Toggle dark/light mode |
| *"Rends le formulaire plus joli avec des icônes"* | Formulaire redesigné |
| *"Ajoute une section témoignages"* | Nouvelle section avec layout |

### Exercice libre (1h)

Améliorez votre site avec **au moins 5 modifications** demandées à l'IA. Soyez créatif !

> 🎥 **Vidéo : Itérer et améliorer son site en parlant à l'IA** *(à venir)*

---

# 🏆 MODULE 4 : Projet Final — Votre Application Personnelle (2h)

## 4.1 — Choisir votre projet

### Idées de projets

Choisissez **un projet qui vous motive** :

| Projet | Description | Difficulté |
|--------|-------------|------------|
| **Portfolio personnel** | Site vitrine avec vos compétences et projets | ⭐ |
| **Blog** | Articles, catégories, commentaires | ⭐⭐ |
| **To-do list** | Gérer des tâches avec ajout/suppression | ⭐⭐ |
| **Calculateur de budget** | Revenus, dépenses, graphiques | ⭐⭐ |
| **Annuaire de contacts** | CRUD complet (ajouter, lire, modifier, supprimer) | ⭐⭐⭐ |
| **Votre idée !** | Ce qui vous plaît | ? |

### Cadrage

Avant de commencer, décrivez votre projet en **3-5 phrases** :
- Qu'est-ce que l'app fait ?
- Qui va l'utiliser ?
- Quelles sont les pages principales ?

---

## 4.2 — Développement autonome avec l'agent

### Méthode recommandée

1. **Donnez la vision globale** à l'agent Manager :
> *"Je veux créer [description de votre projet]. Voici les pages que je veux : [liste]. Utilise Django, un design moderne et sombre."*

2. **Laissez l'agent planifier** — consultez le plan dans les Artifacts

3. **Validez étape par étape** — ne validez pas tout d'un coup

4. **Testez régulièrement** — `python manage.py runserver` après chaque étape

5. **Itérez** — *"Change ceci"*, *"Ajoute cela"*, *"Le bouton ne marche pas"*

### Checklist de votre projet

- [ ] Au moins 3 pages différentes
- [ ] Navigation entre les pages
- [ ] Un formulaire fonctionnel
- [ ] Un design soigné (responsive, moderne)
- [ ] Votre touche personnelle (couleurs, contenu, style)

---

## 4.3 — Présentation

### Format

Chaque participant présente son projet au groupe (5-10 min) :

1. **Montrez votre app** — démo live dans le navigateur
2. **Expliquez votre démarche** — quels prompts ont bien marché ? Lesquels ont dû être reformulés ?
3. **Ce que vous avez appris** — qu'est-ce qui vous a surpris ?
4. **Questions du groupe**

### Critères d'évaluation

- ✅ L'app fonctionne
- ✅ Le design est soigné
- ✅ Vous pouvez expliquer le fonctionnement général
- ✅ Vous avez itéré et amélioré votre projet

---

# 📎 RESSOURCES

## Liens utiles

| Ressource | Lien |
|-----------|------|
| **Python (téléchargement)** | https://www.python.org/downloads/ |
| **Antigravity (téléchargement)** | https://antigravity.google/download |
| **Django (documentation officielle)** | https://docs.djangoproject.com/fr/ |
| **Django (tutoriel officiel)** | https://docs.djangoproject.com/fr/stable/intro/tutorial01/ |

## Raccourcis clavier Antigravity

| Raccourci | Action |
|-----------|--------|
| **Tab** | Accepter la suggestion de l'IA |
| **Escape** | Refuser la suggestion |
| **Ctrl+I / Cmd+I** | Commande inline (modifier du code sélectionné) |
| **Ctrl+L / Cmd+L** | Ouvrir le chat agent |
| **Ctrl+`** | Ouvrir/fermer le terminal |

## Glossaire

| Terme | Définition |
|-------|------------|
| **Vibe coding** | Coder en décrivant ce qu'on veut à l'IA |
| **IDE** | Environnement de développement — l'outil où on code |
| **Prompt** | L'instruction que vous donnez à l'IA |
| **Framework** | Un kit de construction logiciel (Django est un framework) |
| **Template** | Un fichier HTML qui définit l'apparence d'une page |
| **Vue (View)** | La logique d'une page — quoi afficher |
| **URL** | L'adresse web d'une page |
| **Agent** | L'IA autonome qui code pour vous dans Antigravity |
| **Artifact** | Un rapport/capture produit par l'agent pour vérifier son travail |
| **Terminal** | L'interface en ligne de commande de votre ordinateur |

---

*Formation créée par Bolibana — https://bolibana.net*
*© 2026 Djimiga Tech — Tous droits réservés*
