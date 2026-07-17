# Guide d'installation

Ce guide détaille l'installation complète de l'outil sur un poste Windows.
Compter environ 20 à 30 minutes pour une installation complète depuis zéro,
moins si Python est déjà installé.

---

## Sommaire

1. Prérequis logiciels
2. Installation de Python
3. Installation de pbi-tools
4. Installation de l'outil
5. Configuration
6. Vérification de l'installation

---

## 1. Prérequis logiciels

Avant de commencer, l'outil nécessite trois éléments installés sur la machine :

- **Python 3.11 ou plus récent** (moteur d'exécution du code)
- **pbi-tools Desktop CLI** (décomposition des fichiers .pbix)

Cet outil fonctionne uniquement sur **Windows**. Il n'est pas testé sur 
macOS ou Linux.

---

## 2. Installation de Python

### 2.1 Vérifier si Python est déjà installé

Ouvrir une invite de commande (touche Windows + R, taper `cmd`, Entrée) 
et exécuter :

```
python --version
```

Si une version 3.11 ou supérieure s'affiche (par exemple `Python 3.11.5`), 
passer directement à l'étape 3.

Si la commande n'est pas reconnue ou affiche une version antérieure à 3.11, 
suivre les étapes ci-dessous.

### 2.2 Télécharger Python

Se rendre sur https://www.python.org/downloads/ et télécharger la dernière 
version stable de Python 3 (3.11 ou plus récente).

### 2.3 Installer Python

Exécuter l'installateur téléchargé.

**Point critique** : cocher la case **"Add Python to PATH"** en bas de la 
première fenêtre de l'installateur. Sans cette case, la commande `python` 
ne sera pas reconnue dans l'invite de commande, et l'outil ne fonctionnera 
pas.

Cliquer ensuite sur **"Install Now"** pour une installation standard.

### 2.4 Vérifier l'installation

Fermer toutes les invites de commande ouvertes, puis en ouvrir une nouvelle 
et exécuter :

```
python --version
```

La version installée doit s'afficher.

---

## 3. Installation de pbi-tools

### 3.1 Télécharger pbi-tools

Se rendre sur https://pbi.tools et télécharger la version **Desktop CLI** 
(pas Core CLI ni Docker).

Choisir de préférence la version **Self-Contained** qui embarque toutes les 
dépendances .NET nécessaires et évite d'avoir à installer .NET séparément.

### 3.2 Décompresser dans un dossier stable

Créer un dossier permanent pour l'outil, par exemple :

```
C:\Outils\pbi-tools\
```

Éviter les dossiers avec des restrictions particulières comme 
`C:\Program Files\` qui demandent des droits administrateur à chaque 
opération.

Décompresser le contenu du ZIP directement dans ce dossier. Il devrait 
contenir un fichier `pbi-tools.exe` à la racine.

### 3.3 Vérifier l'installation

Ouvrir une invite de commande et exécuter :

```
"C:\Outils\pbi-tools\pbi-tools.exe" info
```

Une liste d'informations sur pbi-tools et les versions de Power BI Desktop 
détectées doit s'afficher.

### 3.4 Noter le chemin complet

Prendre note du chemin complet vers l'exécutable :

```
C:\Outils\pbi-tools\pbi-tools.exe
```

Ce chemin sera à renseigner dans le fichier de configuration à l'étape 5.

---

## 4. Installation de l'outil

### 4.1 Récupérer les fichiers

Copier le dossier complet de l'outil dans un emplacement permanent, par 
exemple :

```
C:\Outils\ExtractionMetadata\
```

### 4.2 Aucune dépendance externe à installer

L'outil utilise uniquement la bibliothèque standard de Python et ne 
nécessite l'installation d'aucun package supplémentaire via `pip`.

---

## 5. Configuration

### 5.1 Ouvrir le fichier config.ini

Naviguer dans le dossier où a été copié l'outil (par exemple 
`C:\Outils\ExtractionMetadata\`) et ouvrir le fichier `config.ini` avec 
le Bloc-notes ou tout éditeur de texte.

### 5.2 Adapter les chemins

Modifier les quatre chemins de la section `[Chemins]` selon 
l'environnement :

```ini
[Chemins]
dossier_rapports = C:\Rapports\AAutomatiser
dossier_sortie = C:\Rapports\Resultats
chemin_pbi_tools = C:\Outils\pbi-tools\pbi-tools.exe
dossier_temp = C:\Rapports\Temp
```

**`dossier_rapports`** : dossier dans lequel seront placés les fichiers 
`.pbix` et `.rdl` à documenter. Créer ce dossier s'il n'existe pas.

**`dossier_sortie`** : dossier où seront générés les fichiers CSV finaux. 
Ce dossier sera créé automatiquement au premier lancement s'il n'existe 
pas.

**`chemin_pbi_tools`** : chemin complet vers l'exécutable `pbi-tools.exe` 
noté à l'étape 3.4.

**`dossier_temp`** : dossier de travail temporaire pour les extractions 
intermédiaires. Ce dossier sera créé automatiquement.

### 5.3 Enregistrer le fichier

Enregistrer le fichier `config.ini` après modification. Vérifier que 
l'enregistrement se fait bien avec l'extension `.ini` et non `.txt`.

---

## 6. Vérification de l'installation

### 6.1 Lancer l'outil

Naviguer dans le dossier de l'outil et double-cliquer sur 
`LancerExtraction.bat`.

### 6.2 Vérifier les CSV générés

Ouvrir le dossier configuré comme `dossier_sortie`. Il doit contenir les 
fichiers CSV générés.

Ouvrir un des CSV dans Excel par un double-clic. Les colonnes doivent 
s'afficher correctement avec les caractères accentués préservés.

Si tout s'affiche correctement, l'installation est fonctionnelle.

---


## Installation terminée

L'outil est maintenant prêt à être utilisé. Se référer au fichier 
`README.md` pour les instructions d'utilisation quotidienne.