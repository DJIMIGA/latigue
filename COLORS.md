# 🎨 Palette de Couleurs - Djimiga Tech

## Vue d'ensemble

Cette palette de couleurs personnalisée a été créée pour harmoniser l'identité visuelle de votre portfolio. Elle combine des couleurs modernes et professionnelles avec des accents créatifs.

## 🎯 Couleurs Principales

### **Brand (Rose - Couleur de Marque)**
```css
brand-50:   #fdf2f8   /* Rose très clair */
brand-100:  #fce7f3   /* Rose clair */
brand-200:  #fbcfe8   /* Rose moyen-clair */
brand-300:  #f9a8d4   /* Rose moyen */
brand-400:  #f472b6   /* Rose */
brand-500:  #ec4899   /* Rose principal ⭐ */
brand-600:  #db2777   /* Rose foncé */
brand-700:  #be185d   /* Rose très foncé */
brand-800:  #9d174d   /* Rose sombre */
brand-900:  #831843   /* Rose très sombre */
brand-950:  #500724   /* Rose noir */
```

### **Accent (Violet - Couleur Secondaire)**
```css
accent-50:   #f5f3ff   /* Violet très clair */
accent-100:  #ede9fe   /* Violet clair */
accent-200:  #ddd6fe   /* Violet moyen-clair */
accent-300:  #c4b5fd   /* Violet moyen */
accent-400:  #a78bfa   /* Violet */
accent-500:  #8b5cf6   /* Violet principal ⭐ */
accent-600:  #7c3aed   /* Violet foncé */
accent-700:  #6d28d9   /* Violet très foncé */
accent-800:  #5b21b6   /* Violet sombre */
accent-900:  #4c1d95   /* Violet très sombre */
accent-950:  #2e1065   /* Violet noir */
```

## 🎨 Couleurs Neutres

### **Neutral (Gris Modernes)**
```css
neutral-50:   #f8fafc   /* Gris très clair */
neutral-100:  #f1f5f9   /* Gris clair */
neutral-200:  #e2e8f0   /* Gris moyen-clair */
neutral-300:  #cbd5e1   /* Gris moyen */
neutral-400:  #94a3b8   /* Gris */
neutral-500:  #64748b   /* Gris principal */
neutral-600:  #475569   /* Gris foncé */
neutral-700:  #334155   /* Gris très foncé */
neutral-800:  #1e293b   /* Gris sombre */
neutral-900:  #0f172a   /* Gris très sombre */
neutral-950:  #020617   /* Gris noir */
```

## 🚦 Couleurs d'Interaction

### **Success (Vert)**
```css
success-500: #22c55e   /* Vert principal */
success-600: #16a34a   /* Vert foncé */
```

### **Warning (Orange)**
```css
warning-500: #f59e0b   /* Orange principal */
warning-600: #d97706   /* Orange foncé */
```

### **Error (Rouge)**
```css
error-500: #ef4444     /* Rouge principal */
error-600: #dc2626     /* Rouge foncé */
```

## 🎨 Utilisation Recommandée

### **Gradients Principaux**
```css
/* Gradient de marque */
bg-gradient-to-r from-brand-500 to-accent-500

/* Gradient subtil */
bg-gradient-to-r from-brand-100 to-accent-100
```

### **Texte et Contenu**
```css
/* Texte principal */
text-neutral-800 dark:text-white

/* Texte secondaire */
text-neutral-600 dark:text-neutral-300

/* Accent de texte */
text-brand-600 dark:text-brand-400
```

### **Arrière-plans**
```css
/* Arrière-plan principal */
bg-white dark:bg-neutral-800

/* Arrière-plan secondaire */
bg-neutral-100 dark:bg-neutral-700
```

### **Boutons et Interactions**
```css
/* Bouton principal */
bg-gradient-to-r from-brand-500 to-accent-500

/* Hover states */
hover:bg-brand-100 dark:hover:bg-brand-900
hover:bg-accent-100 dark:hover:bg-accent-900
```

## 🎯 Cas d'Usage Spécifiques

### **Réseaux Sociaux**
- **TikTok** : `hover:bg-brand-100 dark:hover:bg-brand-900`
- **YouTube** : `hover:bg-error-100 dark:hover:bg-error-900`
- **X/Twitter** : `hover:bg-accent-100 dark:hover:bg-accent-900`
- **LinkedIn** : `hover:bg-accent-100 dark:hover:bg-accent-900`

### **Navigation**
- **Liens actifs** : `text-brand-600`
- **Hover** : `hover:text-brand-600`
- **Focus** : `focus:ring-brand-500`

### **Formulaires**
- **Bordure focus** : `focus:ring-brand-500`
- **Validation succès** : `border-success-500`
- **Validation erreur** : `border-error-500`

## 🔧 Configuration Tailwind

Cette palette est configurée dans `tailwind.config.js` et inclut :

- ✅ **Couleurs personnalisées** avec toutes les nuances
- ✅ **Gradients personnalisés**
- ✅ **Animations de gradient**
- ✅ **Compatibilité mode sombre**

## 📱 Accessibilité

Toutes les couleurs ont été choisies pour respecter les standards WCAG :
- **Contraste suffisant** entre texte et arrière-plan
- **Support du mode sombre**
- **Couleurs sémantiques** pour les états (succès, erreur, avertissement)

---

*Cette palette reflète l'identité moderne et créative de Djimiga Tech tout en maintenant un aspect professionnel.* 