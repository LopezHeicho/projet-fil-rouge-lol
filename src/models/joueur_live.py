import json
import sqlite3
from pathlib import Path
 
import pandas as pd
import streamlit as st
 
from models.joueur import nettoyer_donnees_joueur

RENOMMAGE_CHAMPIONS = {
    "AurelionSol": "Aurelion Sol",
    "Belveth": "Bel'Veth",
    "Chogath": "Cho'Gath",
    "DrMundo": "Dr. Mundo",
    "FiddleSticks": "Fiddlesticks",
    "JarvanIV": "Jarvan IV",
    "KSante": "K'Sante",
    "Kaisa": "Kai'Sa",
    "Khazix": "Kha'Zix",
    "KogMaw": "Kog'Maw",
    "Leblanc": "LeBlanc",
    "LeeSin": "Lee Sin",
    "MasterYi": "Master Yi",
    "MissFortune": "Miss Fortune",
    "MonkeyKing": "Wukong",
    "Nunu": "Nunu & Willump",
    "RekSai": "Rek'Sai",
    "Renata": "Renata Glasc",
    "TahmKench": "Tahm Kench",
    "TwistedFate": "Twisted Fate",
    "Velkoz": "Vel'Koz",
    "XinZhao": "Xin Zhao",
}

"""
Recherche live d'un joueur : va chercher ses
dernieres games + son rang actuel via l'API Riot, les stocke durablement,
et fournit le DataFrame complet (dataset statique + games recuperees en
direct) a toutes les fonctions de models/joueur.py.
"""
 
try:
    import fetch_player_matches as fpm
except ImportError as exc:
    raise ImportError(
        "fetch_player_matches.py introuvable dans le PYTHONPATH. Place-le a "
        "la racine du projet (a cote de main.py) -- voir le haut de ce "
        "fichier pour la mise en place complete."
    ) from exc
 
 
DB_PATH = "data/users.db"
TABLE_NAME = "player_live_matches"
STATIC_DATASET_PATH = "data/player_matches.parquet"
CACHE_MATCHES = Path("cache/matches")
CACHE_RUNES = Path("cache/ddragon_runes")
CACHE_RANKS = Path("cache/league_ranks")
 
 
class RechercheJoueurError(Exception):
    """Erreur "propre" avec un message directement affichable a
    l'utilisateur (st.error(str(exc))), par opposition a une exception
    technique brute qui remonterait jusqu'a planter la page."""
    pass
 
 
# ---------------------------------------------------------------------------
# Stockage (SQLite, connexion dediee avec requetes parametrees)
# ---------------------------------------------------------------------------
 
def _connexion():
    return sqlite3.connect(DB_PATH)
 
 
def _setup_table():
    conn = _connexion()
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ("
        "matchId TEXT NOT NULL, "
        "puuid TEXT NOT NULL, "
        "row_json TEXT NOT NULL, "
        "PRIMARY KEY (matchId, puuid))"
    )
    conn.commit()
    conn.close()
 
 
def _inserer_lignes(rows):
    """Insere les lignes en base ; celles dont (matchId, puuid) existe deja
    sont ignorees silencieusement (dedoublonnage). Renvoie le nombre de
    lignes reellement ajoutees."""
    if not rows:
        return 0
    _setup_table()
    conn = _connexion()
    avant = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    conn.executemany(
        f"INSERT OR IGNORE INTO {TABLE_NAME} (matchId, puuid, row_json) VALUES (?, ?, ?)",
        [(row.get("matchId"), row.get("puuid"), json.dumps(row, default=str)) for row in rows],
    )
    conn.commit()
    apres = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    conn.close()
    return apres - avant
 
 
def _lire_lignes_live():
    _setup_table()
    conn = _connexion()
    lignes = conn.execute(f"SELECT row_json FROM {TABLE_NAME}").fetchall()
    conn.close()
    return [json.loads(l[0]) for l in lignes]
 
 
# ---------------------------------------------------------------------------
# Chargement du dataset complet (CSV statique + base live), nettoye
# ---------------------------------------------------------------------------
 
@st.cache_data(show_spinner="Chargement du dataset joueurs...")
def _charger_csv_statique():
    df = pd.read_parquet(STATIC_DATASET_PATH)
    df["patch_major_minor"] = df["patch_major_minor"].astype(str)
    return df
 
 
@st.cache_data(show_spinner="Préparation des données joueur...")
def charger_dataset_complet():
    """DataFrame complet et nettoye (nettoyer_donnees_joueur appliquee une
    seule fois sur l'ensemble), pret pour toutes les fonctions de
    models/joueur.py. Mis en cache : appelle charger_dataset_complet.clear()
    juste apres une recherche qui a ajoute de nouvelles lignes pour que la
    suite de la session voie les nouvelles games (fait automatiquement par
    rechercher_et_recuperer ci-dessous)."""
    df_statique = _charger_csv_statique()
    lignes_live = _lire_lignes_live()
 
    if lignes_live:
        df_live = pd.DataFrame(lignes_live)
        df = pd.concat([df_statique, df_live], ignore_index=True)
        df = df.drop_duplicates(subset=["matchId", "puuid"], keep="first")
    else:
        df = df_statique.copy()

    df["championName"] = df["championName"].replace(RENOMMAGE_CHAMPIONS)
 
    return nettoyer_donnees_joueur(df)
 
 
# ---------------------------------------------------------------------------
# Recherche live
# ---------------------------------------------------------------------------
 
def rechercher_et_recuperer(game_name, tag_line, region="europe", count=20, queue=420):
    """Resout le Riot ID, recupere ses `count` dernieres games (+ son rang
    actuel), stocke tout en base (dedoublonne), invalide le cache du
    dataset complet, et renvoie un resume pret a afficher.
 
    Leve RechercheJoueurError (message utilisateur direct) si le Riot ID
    est introuvable, si la cle API est invalide/absente, ou si aucune game
    n'a pu etre recuperee -- jamais une exception technique brute."""
    api_key = st.secrets.get("RIOT_API_KEY") if hasattr(st, "secrets") else None
    if not api_key:
        raise RechercheJoueurError(
            "Aucune clé API Riot configurée (st.secrets['RIOT_API_KEY']). "
            "Ajoute-la dans .streamlit/secrets.toml."
        )
    if region not in fpm.REGIONS:
        raise RechercheJoueurError(f"Région invalide : {region} (attendu : {sorted(fpm.REGIONS)}).")
 
    client = fpm.RiotClient(api_key, region)
 
    try:
        puuid = client.get_puuid(game_name, tag_line)
    except SystemExit as exc:
        raise RechercheJoueurError(
            "La clé API Riot semble invalide ou expirée (403). Régénère-la sur "
            "developer.riotgames.com et mets à jour secrets.toml."
        ) from exc
 
    if not puuid:
        raise RechercheJoueurError(f"Riot ID introuvable : {game_name}#{tag_line} sur la région {region}.")
 
    try:
        match_ids = client.get_match_ids(puuid, count=count, queue=queue)
    except SystemExit as exc:
        raise RechercheJoueurError("La clé API Riot semble invalide ou expirée (403).") from exc
 
    if not match_ids:
        raise RechercheJoueurError(
            f"Aucune game classée solo/duo trouvée pour {game_name}#{tag_line}. "
            "Vérifie l'orthographe du pseudo/tag, ou ce compte n'a peut-être pas joué en classé solo/duo récemment."
        )
 
    all_rows = []
    for match_id in match_ids:
        try:
            match = client.get_match(match_id, CACHE_MATCHES)
        except SystemExit as exc:
            raise RechercheJoueurError("La clé API Riot semble invalide ou expirée (403).") from exc
        if not match:
            continue
        all_rows.extend(fpm.flatten_match(match, CACHE_RUNES))
 
    if not all_rows:
        raise RechercheJoueurError("Aucune donnée exploitable récupérée pour ces matchs.")
 
    lignes_joueur = [r for r in all_rows if r.get("puuid") == puuid]
    platform = (lignes_joueur[0].get("platformId") or "").upper() if lignes_joueur else None
 
    rang_row = {}
    if platform:
        try:
            entries = fpm.resolve_rank(puuid, platform, {}, api_key, CACHE_RANKS)
            rang_row = fpm.rank_row_from_entries(entries)
        except SystemExit as exc:
            raise RechercheJoueurError("La clé API Riot semble invalide ou expirée (403).") from exc
 
        for row in all_rows:
            if row.get("puuid") == puuid:
                row.update(rang_row)
 
    nb_inserees = _inserer_lignes(all_rows)
    if nb_inserees > 0:
        charger_dataset_complet.clear()
 
    return {
        "puuid": puuid,
        "region": region,
        "platform": platform,
        "riot_id_game_name": lignes_joueur[0].get("riotIdGameName") if lignes_joueur else game_name,
        "rang": rang_row,
        "nb_matchs_recuperes": len(match_ids),
        "nb_lignes_nouvelles": nb_inserees,
    }