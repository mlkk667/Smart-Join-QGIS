# Smart Join QGIS Plugin 🎯

Un plugin QGIS développé par **Malick Ndiaye** etudient à l'**Université Amadou Mahtar Mbow de Diamniadio (Dakar, Sénégal)**, conçu pour réaliser des jointures attributaires intelligentes (Fuzzy Matching).

## Pourquoi Smart Join ?
La jointure classique dans QGIS échoue à la moindre faute de frappe, erreur d'encodage ou différence de casse. Smart Join utilise un algorithme d'Intelligence Artificielle basé sur le **Token Set Ratio** pour relier automatiquement des données imparfaites.

Par exemple :
- `Dakar` se joindra parfaitement à `Département de Dakar` (100%)
- `Kébémer` se joindra à `KÃ©bÃ©mÃ©r` (malgré les erreurs d'encodage UTF-8)

## Fonctionnalités Principales ✨
1. **Jointure Tolérante aux Fautes :** Choisissez le pourcentage de tolérance (ex: 70%) pour accepter une jointure.
2. **Assignation Unique (1-à-1) :** Évite la duplication des données en forçant l'algorithme à faire correspondre une ligne source à un seul polygone cible (algorithme glouton de mariage stable).
3. **Double Vérification Optionnelle :** Permet d'ajouter une condition stricte sur un deuxième champ. Par exemple, si le nom du département est "Bakel", on peut vérifier que la "Région" correspond parfaitement pour éviter de le joindre à "Mbacké".

## Installation 🚀
1. Téléchargez le fichier `smart_join_plugin.zip` depuis cette page.
2. Ouvrez QGIS.
3. Allez dans le menu **Extensions > Installer/Gérer les extensions**.
4. Cliquez sur l'onglet **Installer depuis un fichier ZIP**.
5. Sélectionnez le fichier téléchargé et cliquez sur **Installer le plugin**.
6. Une nouvelle icône "Smart Join" (Q avec des anneaux) apparaîtra dans votre barre d'outils !

## Comment l'utiliser ?
1. Sélectionnez la couche cible (celle qui recevra la donnée) et le champ de nom.
2. Sélectionnez la couche source (CSV, Excel) et son champ de nom.
3. (Optionnel) Cochez la double vérification et choisissez le champ Région.
4. Ajustez le curseur de tolérance (70% ou 80% recommandés).
5. Cliquez sur OK ! Une nouvelle couche `_joined` sera générée avec les données.

## Auteur
- **Malick Ndiaye**
- Email : ndiaye.malick1@uam.edu.sn
- Institution : Université Amadou Mahtar Mbow (UAM)
