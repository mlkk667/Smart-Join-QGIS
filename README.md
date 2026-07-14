# Smart-Join-QGIS
Plugin QGIS pour faire des jointures floues intelligentes et éviter les doublon


# Workflow de Développement : Plugin QGIS Jointure Intelligente (Fuzzy Join)

Ce document décrit les étapes pour créer un plugin QGIS permettant de joindre deux couches attributaires en utilisant un algorithme d'intelligence (Fuzzy Matching) pour gérer les erreurs de frappe, la casse et les variations de texte (ex: "dakar" vs "Region Dakar").

## Étape 1 : Validation de l'algorithme d'IA / Correspondance
1. **Objectif :** Choisir et tester la méthode de comparaison de texte.
2. **Outils :** Python, bibliothèque `thefuzz` (FuzzyWuzzy) ou `difflib`.
3. **Action :** Tester la distance de Levenshtein (calcul de similarité). Créer une fonction Python qui prend deux textes et renvoie un score de 0 à 100. Tester avec des exemples difficiles de vos données.

## Étape 2 : Création de l'interface graphique (UI)
1. **Objectif :** Permettre à l'utilisateur de configurer la jointure.
2. **Outils :** QGIS Plugin Builder 3, Qt Designer.
3. **Action :**
   - Générer le squelette du plugin.
   - Créer une fenêtre avec :
     - 2 listes déroulantes (ComboBox) pour choisir la **Couche 1** (Cible) et la **Couche 2** (Source).
     - 2 listes déroulantes pour choisir le **Champ 1** et le **Champ 2** sur lesquels faire la jointure.
     - 1 curseur (Slider) pour définir le **Seuil de tolérance** (ex: 80% de similarité requise pour accepter la jointure).
     - Un bouton "Exécuter".

## Étape 3 : Logique de jointure (PyQGIS)
1. **Objectif :** Lire les données de QGIS et appliquer l'algorithme.
2. **Outils :** API PyQGIS (`QgsFeatureRequest`, `QgsVectorLayer`).
3. **Action :**
   - Récupérer toutes les valeurs du *Champ 2* (Source) et les stocker dans un dictionnaire.
   - Parcourir chaque entité de la *Couche 1*.
   - Prendre la valeur du *Champ 1*, utiliser l'algorithme (ex: `process.extractOne` de `thefuzz`) pour trouver la meilleure correspondance dans le dictionnaire Source.
   - Si le score est supérieur au seuil choisi par l'utilisateur, associer les attributs.

## Étape 4 : Création de la couche de résultat
1. **Objectif :** Sauvegarder la nouvelle donnée sans détruire l'ancienne.
2. **Action :**
   - Créer une nouvelle couche en mémoire (`memory`).
   - Copier les géométries de la *Couche 1*.
   - Ajouter les champs de la *Couche 1* PLUS les champs correspondants trouvés dans la *Couche 2*.
   - Insérer les nouvelles entités et afficher la couche sur la carte.

## Étape 5 : Finalisation
1. **Action :**
   - Gérer les correspondances multiples (cas où deux textes sont très proches).
   - Ajouter un rapport à la fin ("X entités ont été jointes avec succès, Y n'ont pas trouvé de correspondance").
