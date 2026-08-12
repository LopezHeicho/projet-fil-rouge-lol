#bin/bash

# On créé un environnement virtuel pour isoler les dépendances du projet
python3 -m venv venv
source venv/bin/activate

# On met à jour pip pour éviter les problèmes de compatibilité
pip install --upgrade pip

# On installe les dépendaces du projet
pip install -r requirements.txt

# On initialise le projet et la base de données
python3 setup.py 