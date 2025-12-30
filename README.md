## Installation et Configuration

### Prérequis

- **Python** 3.11 ou supérieur
- **pip**
- **git**

### Étape 1: Cloner/Télécharger le Projet

```bash
# Si vous utilisez Git
git clone https://github.com/Adam-445/ci-cd-pert-cpm.git
cd ci-cd-pert-cpm

# Ou téléchargez et extrayez le ZIP

```

### Étape 2: Créer un Environnement Virtuel

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement
# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

```

### Étape 3: Installer les Dépendances

```bash
# Installation complète (package + dépendances)
pip install -e .

# OU installation des dépendances uniquement
pip install -r requirements.txt

```

### Vérification de l'Installation

```bash
# Vérifier que tout fonctionne
python3 -c "from src import GraphePERT, CalculateurPERT; print('Installation réussie!')"

```

## Utilisation

### Méthode 1: Script Principal (Recommandé)

```bash
python scripts/main.py

```

### Méthode 2: Utilisation Programmatique

```python
from pert_cpm import GraphePERT, CalculateurPERT
import pandas as pd

# 1. Charger le graphe PERT depuis CSV
graphe = GraphePERT("data/taches.csv")
graphe.afficher_resume()

# 2. Créer le calculateur
calculateur = CalculateurPERT(graphe)

# 3. Exécuter l'analyse complète
resultats = calculateur.executer_analyse_complete()

# 4. Accéder aux résultats
print(f"Durée totale: {calculateur.duree_totale} minutes")
print(f"Chemin critique: {' -> '.join(calculateur.chemin_critique)}")

# 5. Générer le tableau détaillé
df = pd.DataFrame(calculateur.generer_tableau_resultats())
print(df)

# 6. Sauvegarder les résultats
df.to_csv("resultats.csv", index=False)

```

### Méthode 3: Notebook Jupyter

```bash
# Lancer Jupyter
jupyter notebook notebooks/analyse_complete.ipynb

```

## Tests Unitaires

Le projet inclut une suite complète de **tests unitaires** couvrant toutes les fonctionnalités.

### Exécuter Tous les Tests

```bash
pytest

```

### Tests avec Couverture de Code

```bash
pytest --cov=pert_cpm --cov-report=html
# Ouvrir htmlcov/index.html pour voir le rapport

```

### Tests Spécifiques

```bash
# Tests du constructeur de graphe
pytest tests/test_graph_builder.py -v

# Tests du calculateur PERT
pytest tests/test_pert_calculator.py -v

# Test spécifique
pytest tests/test_graph_builder.py::TestGraphePERT::test_charger_donnees_csv -v

```
