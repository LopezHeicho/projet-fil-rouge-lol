#!/usr/bin/env python3
"""
fetch_player_matches.py

Recupere l'historique de parties de "joueurs lambda" (non-pro) via l'API
officielle Riot Games (match-v5 + account-v1), pour le module 1 de ton appli
Streamlit ("Stats joueur & parties").

PREREQUIS INDISPENSABLE : une cle API Riot.
  1. Va sur https://developer.riotgames.com/ et connecte-toi avec ton compte
     League/Riot.
  2. Accepte les conditions, tu arrives sur ton dashboard developpeur.
  3. Copie la "Development API Key" affichee (bouton "Regenerate API Key" si
     besoin). ATTENTION : elle expire toutes les 24h, il faudra la
     regenerer et relancer le script avec la nouvelle si tu reviens le
     lendemain.
  4. Ne la mets JAMAIS en dur dans un fichier versionne sur GitHub. Passe-la
     via la variable d'environnement RIOT_API_KEY (recommande) ou --api-key.

Deux facons d'obtenir un echantillon de joueurs "normaux" (au choix, meme
script) :

  A) Liste de comptes que tu fournis toi-meme (le plus simple, le plus
     maitrise) : remplis un CSV avec les Riot ID (Pseudo#TAG) des comptes qui
     t'interessent (toi, des amis...) et lance :
       python fetch_player_matches.py --accounts accounts.csv --out data/

  B) Depart de ton propre compte + expansion organique : le script part de
     ton compte, recupere tes dernieres games, et ajoute automatiquement a
     l'echantillon les autres joueurs croises dans ces games (jusqu'a
     --max-accounts comptes au total). Donne un echantillon plus large sans
     avoir a chercher des pseudos toi-meme :
       python fetch_player_matches.py --riot-id "TonPseudo#TAG" --region europe \
           --expand --max-accounts 30 --out data/

Installation :
    pip install requests pandas pyarrow

Sorties :
    data/player_matches.parquet / .csv
    cache/matches/<matchId>.json   (cache brut, un match ne change jamais une
    fois joue donc on ne le re-telecharge jamais deux fois, meme entre deux
    joueurs qui partagent la meme partie)
    cache/league_ranks/<puuid>.json (cache brut du rang solo/flex d'un
    joueur -- cf section rang plus bas)
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import quote

import requests
import pandas as pd

# Routing "continental" utilise par account-v1 et match-v5 (pas les codes de
# serveur classiques type euw1/na1). Mapping stable depuis la consolidation
# Riot de 2023 -- si Riot a change ca d'ici que tu lances le script, la
# reference a jour est https://developer.riotgames.com/docs/lol#routing-values
REGIONS = {"americas", "asia", "europe", "sea"}

# Data Dragon (pas d'auth necessaire, contrairement a l'API Riot match-v5) :
# sert a resoudre les noms de runes a partir des ID renvoyes par le match
# (perkPrimaryStyle, perkPrimaryKeystone...). Meme CDN que lol_meta_dataset.py.
DDRAGON_BASE = "https://ddragon.leagueoflegends.com"

# Les "stat shards" (les 3 petites runes de stats en bas de chaque arbre,
# ex. Force Adaptative/Vitesse d'Attaque/Alteration des Sorts) ne sont PAS
# publiees par Data Dragon -- contrairement aux vraies runes/arbres, elles
# ne vivent que cote client du jeu. Mapping verifie le 2026-08-21 via le
# miroir de donnees statiques CommunityDragon (perks.json), qui reprend les
# memes fichiers que le client. Ces ID sont stables depuis la refonte des
# runes de 2017 et ne changent quasiment jamais ("Move Speed"/5010 est un
# ancien choix retire du choix par defaut du jeu mais qui peut encore
# apparaitre sur de vieux matchs).
STAT_SHARD_NAMES = {
    5001: "Health Scaling",
    5002: "Armor",
    5003: "Magic Resist",
    5005: "Attack Speed",
    5007: "Ability Haste",
    5008: "Adaptive Force",
    5010: "Move Speed",
    5011: "Health",
    5013: "Tenacity and Slow Resist",
}

_ddragon_session = None
_rune_lookup_cache = {}  # ddragon_version -> {perk_id: name}

RUNE_NAME_COLUMNS = [
    "perkPrimaryStyleName",
    "perkPrimaryKeystoneName",
    "perkPrimarySelectionsNames",
    "perkSubStyleName",
    "perkSubSelectionsNames",
    "perkStatOffenseName",
    "perkStatFlexName",
    "perkStatDefenseName",
]


def get_ddragon_session():
    """Session HTTP dediee a Data Dragon, separee de celle utilisee pour
    l'API Riot (qui porte le header d'authentification X-Riot-Token, inutile
    et hors-sujet ici). Meme User-Agent "navigateur" que lol_meta_dataset.py :
    le CDN (Akamai) bloque parfois le User-Agent par defaut de `requests`."""
    global _ddragon_session
    if _ddragon_session is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
            }
        )
        _ddragon_session = s
    return _ddragon_session


def build_rune_lookup(patch_major_minor, cache_dir: Path):
    """Construit {perk_id: nom} (arbres + runes + stat shards) pour un patch
    donne, avec cache memoire (par run) + cache disque (entre deux runs).
    Ne fait jamais planter le script : si Data Dragon est injoignable ou que
    le patch n'existe pas a cette adresse, les colonnes *Name resteront
    vides (NaN) pour les lignes de ce patch, avec juste un message
    d'avertissement -- c'est un enrichissement optionnel, pas une donnee
    critique."""
    if patch_major_minor in _rune_lookup_cache:
        return _rune_lookup_cache[patch_major_minor]

    lookup = dict(STAT_SHARD_NAMES)
    # Convention Data Dragon : la premiere version publiee d'un patch X.Y
    # est toujours "X.Y.1" (meme hypothese que lol_meta_dataset.py).
    ddragon_version = f"{patch_major_minor}.1"
    cache_path = cache_dir / f"{ddragon_version}.json"
    tree_data = None
    try:
        if cache_path.exists():
            tree_data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            url = f"{DDRAGON_BASE}/cdn/{ddragon_version}/data/en_US/runesReforged.json"
            r = get_ddragon_session().get(url, timeout=15)
            if r.status_code == 200:
                tree_data = r.json()
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(tree_data), encoding="utf-8")
            else:
                print(
                    f"  ! noms de runes indisponibles pour le patch {patch_major_minor} "
                    f"(Data Dragon a repondu {r.status_code} pour '{ddragon_version}') -- "
                    "colonnes *Name vides pour ce patch",
                    file=sys.stderr,
                )
    except requests.RequestException as e:
        print(
            f"  ! noms de runes indisponibles pour le patch {patch_major_minor} ({e}) -- "
            "colonnes *Name vides pour ce patch",
            file=sys.stderr,
        )

    if tree_data:
        for style in tree_data:
            lookup[style.get("id")] = style.get("name")
            for slot in style.get("slots", []) or []:
                for rune in slot.get("runes", []) or []:
                    lookup[rune.get("id")] = rune.get("name")

    _rune_lookup_cache[patch_major_minor] = lookup
    return lookup


def resolve_rune_names(row, cache_dir: Path):
    """Ajoute les colonnes RUNE_NAME_COLUMNS sur une ligne deja construite
    (qui contient donc deja patch_major_minor et les colonnes perk* brutes
    issues de extract_perks)."""
    lookup = build_rune_lookup(row.get("patch_major_minor"), cache_dir)

    def name_of(perk_id):
        if perk_id is None:
            return None
        return lookup.get(perk_id, lookup.get(str(perk_id)))

    def names_of(ids_str):
        if not ids_str:
            return ""
        resolved = []
        for x in ids_str.split(";"):
            if not x:
                continue
            try:
                resolved.append(lookup.get(int(x), x))
            except ValueError:
                resolved.append(x)
        return ";".join(str(n) for n in resolved)

    row["perkPrimaryStyleName"] = name_of(row.get("perkPrimaryStyle"))
    row["perkPrimaryKeystoneName"] = name_of(row.get("perkPrimaryKeystone"))
    row["perkPrimarySelectionsNames"] = names_of(row.get("perkPrimarySelections"))
    row["perkSubStyleName"] = name_of(row.get("perkSubStyle"))
    row["perkSubSelectionsNames"] = names_of(row.get("perkSubSelections"))
    row["perkStatOffenseName"] = name_of(row.get("perkStatOffense"))
    row["perkStatFlexName"] = name_of(row.get("perkStatFlex"))
    row["perkStatDefenseName"] = name_of(row.get("perkStatDefense"))
    return row

# Limites du cote de la cle de DEV (personnelle, gratuite). Une cle de
# PRODUCTION (validee par Riot pour un vrai produit) a des limites bien plus
# hautes et personnalisees -- ajuste ces deux constantes si tu en obtiens une.
DEV_KEY_LIMIT_PER_SEC = 20
DEV_KEY_LIMIT_PER_2MIN = 100
# On se garde une marge de securite (on ne vise pas pile la limite).
SAFE_PER_SEC = 18
SAFE_PER_2MIN = 92

POSITION_MAP = {
    "TOP": "top",
    "JUNGLE": "jng",
    "MIDDLE": "mid",
    "BOTTOM": "bot",
    "UTILITY": "sup",
}


class RateLimiter:
    """Respecte les deux fenetres glissantes de la cle de dev Riot en meme
    temps (X req/1s ET Y req/2min), en dormant juste ce qu'il faut avant
    chaque requete."""

    def __init__(self, per_sec=SAFE_PER_SEC, per_2min=SAFE_PER_2MIN):
        self.per_sec = per_sec
        self.per_2min = per_2min
        self._sec_hits = deque()
        self._min_hits = deque()

    def wait(self):
        now = time.monotonic()
        for dq, window, limit in (
            (self._sec_hits, 1.0, self.per_sec),
            (self._min_hits, 120.0, self.per_2min),
        ):
            while dq and now - dq[0] > window:
                dq.popleft()
            if len(dq) >= limit:
                sleep_for = window - (now - dq[0]) + 0.05
                if sleep_for > 0:
                    time.sleep(sleep_for)
        now = time.monotonic()
        self._sec_hits.append(now)
        self._min_hits.append(now)


def _http_get_json(session, limiter, url, params=None, max_retries=3):
    """Logique commune de requete HTTP + retry + respect du rate limit,
    partagee par RiotClient (routing "continental") et PlatformClient
    (routing "plateforme", cf plus bas) -- seule la session/le limiter/l'URL
    changent entre les deux, la gestion des codes d'erreur est identique."""
    for attempt in range(max_retries + 1):
        limiter.wait()
        r = session.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 403:
            sys.exit(
                "403 Forbidden : ta cle API est invalide ou expiree (les cles de dev "
                "expirent toutes les 24h) -- regenere-la sur developer.riotgames.com "
                "et relance le script avec la nouvelle."
            )
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            retry_after = float(r.headers.get("Retry-After", "5"))
            print(f"  ! 429 rate limit, pause {retry_after}s...", file=sys.stderr)
            time.sleep(retry_after + 0.5)
            continue
        if r.status_code >= 500 and attempt < max_retries:
            time.sleep(2 * (attempt + 1))
            continue
        print(f"  ! erreur {r.status_code} sur {url}: {r.text[:200]}", file=sys.stderr)
        return None
    return None


class RiotClient:
    def __init__(self, api_key, region):
        if region not in REGIONS:
            sys.exit(f"--region doit etre l'une de {sorted(REGIONS)} (routing continental, pas un code serveur)")
        self.region = region
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": api_key})
        self.limiter = RateLimiter()

    def _get(self, url, params=None, max_retries=3):
        return _http_get_json(self.session, self.limiter, url, params, max_retries)

    def get_puuid(self, game_name, tag_line):
        url = (
            f"https://{self.region}.api.riotgames.com/riot/account/v1/accounts/"
            f"by-riot-id/{quote(game_name)}/{quote(tag_line)}"
        )
        data = self._get(url)
        return data["puuid"] if data else None

    def get_match_ids(self, puuid, count=10, queue=None, start=0):
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"start": start, "count": min(count, 100)}
        if queue:
            params["queue"] = queue
        data = self._get(url, params=params)
        return data or []

    def get_match(self, match_id, cache_dir: Path):
        cache_path = cache_dir / f"{match_id}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        data = self._get(url)
        if data:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(data), encoding="utf-8")
        return data


class PlatformClient:
    """Client pour les endpoints en routing "plateforme" (ex: euw1, na1,
    kr, jp1...), utilise par league-v4 -- DIFFERENT du routing "continental"
    (americas/europe/asia/sea) utilise par account-v1 et match-v5 dans
    RiotClient. Meme cle API (header X-Riot-Token), mais cote Riot chaque
    plateforme a son PROPRE quota de rate-limit, separe des autres et separe
    du routing continental -- d'ou une instance (et donc un RateLimiter)
    dediee par plateforme rencontree, creee a la volee.
    Le champ `platformId` de l'API match-v5 (ex. "EUW1", "NA1", "KR") est
    directement la valeur attendue ici, une fois mise en minuscules."""

    def __init__(self, api_key, platform):
        self.platform = platform.lower()
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": api_key})
        self.limiter = RateLimiter()

    def get_league_entries_by_puuid(self, puuid):
        """GET /lol/league/v4/entries/by-puuid/{puuid} -- endpoint league-v4
        base sur le PUUID (remplace depuis le 20/06/2025 l'ancien
        /entries/by-summoner/{encryptedSummonerId}, l'API Riot ne renvoyant
        plus d'ID invocateur exploitable). Renvoie une liste d'entrees (une
        par file classee ou le joueur a des games -- solo/duo et/ou flex),
        ou une liste vide si le joueur n'est classe dans aucune file."""
        url = f"https://{self.platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        data = _http_get_json(self.session, self.limiter, url)
        return data if data is not None else []


# Les deux seules files classees "summoner's rift" -- League-Exp/TFT/arena
# ont leurs propres queueType, non geres ici (hors-sujet pour ce dataset).
RANK_QUEUE_PREFIX = {
    "RANKED_SOLO_5x5": "soloqueue",
    "RANKED_FLEX_SR": "flexqueue",
}
RANK_COLUMNS = [
    f"{prefix}_{field}"
    for prefix in RANK_QUEUE_PREFIX.values()
    for field in ("tier", "rank", "lp", "wins", "losses")
]

CACHE_MAX_AGE_SECONDS = 15 * 60  # 15 minutes

def resolve_rank(puuid, platform, platform_clients, api_key, cache_dir: Path):
    """Renvoie la liste brute d'entrees league-v4 d'un joueur (solo/flex),
    avec un cache disque -- UN FICHIER JSON PAR PUUID, exactement la meme
    logique que le cache des matchs (get_match ci-dessus). C'est ce cache
    qui rend la resolution REPRENABLE : si le script est interrompu (ou le
    terminal ferme) en plein milieu d'un run avec beaucoup de joueurs, il
    suffit de relancer EXACTEMENT LA MEME COMMANDE -- les joueurs deja
    resolus ne redeclenchent aucun appel reseau, seuls les joueurs restants
    sont interroges."""
    cache_path = cache_dir / f"{puuid}.json"
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            return json.loads(cache_path.read_text(encoding="utf-8"))

    if platform not in platform_clients:
        platform_clients[platform] = PlatformClient(api_key, platform)
    entries = platform_clients[platform].get_league_entries_by_puuid(puuid)

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(entries), encoding="utf-8")
    return entries


def rank_row_from_entries(entries):
    """Aplati la liste d'entrees league-v4 (0, 1 ou 2 elements : solo et/ou
    flex) en un seul dict de colonnes. Un joueur non classe dans une file
    (ou pas classe du tout) garde des None -> NaN une fois assemble dans un
    DataFrame, ce qui est le comportement attendu (pas une erreur)."""
    row = {col: None for col in RANK_COLUMNS}
    for e in entries or []:
        prefix = RANK_QUEUE_PREFIX.get(e.get("queueType"))
        if not prefix:
            continue
        row[f"{prefix}_tier"] = e.get("tier")
        row[f"{prefix}_rank"] = e.get("rank")
        row[f"{prefix}_lp"] = e.get("leaguePoints")
        row[f"{prefix}_wins"] = e.get("wins")
        row[f"{prefix}_losses"] = e.get("losses")
    return row


OBJECTIVE_KEYS = ["champion", "dragon", "baron", "tower", "inhibitor", "riftHerald", "horde"]

# Sous-ensemble utile des dizaines de stats DEJA calculees cote serveur par
# Riot dans participant["challenges"] (kda, kill participation, dmg/min...)
# -- evite de les recalculer a la main. ATTENTION : ce champ n'existe pas sur
# les tres vieux matchs (avant ~saison 11) ni sur certains modes hors-norme
# (Arena, modes d'evenement...) -- ces colonnes seront alors vides (NaN),
# ce n'est pas un bug du script.
CHALLENGE_KEYS = [
    "kda",
    "killParticipation",
    "teamDamagePercentage",
    "damagePerMinute",
    "goldPerMinute",
    "visionScorePerMinute",
    "soloKills",
    "turretPlatesTaken",
]


def extract_team_objectives(info):
    """Renvoie {teamId: {"dragonKills": n, "firstDragon": bool, ...}} a partir
    de info["teams"] -- ces compteurs (dragons/barons/tours/inhibiteurs...)
    sont au niveau EQUIPE dans la reponse de l'API, pas dans les stats
    individuelles de chaque joueur (participants[])."""
    result = {}
    for team in info.get("teams", []) or []:
        team_id = team.get("teamId")
        objectives = team.get("objectives", {}) or {}
        stats = {}
        for key in OBJECTIVE_KEYS:
            obj = objectives.get(key, {}) or {}
            stats[f"{key}Kills"] = obj.get("kills")
            stats[f"first{key[0].upper()}{key[1:]}"] = obj.get("first")
        result[team_id] = stats
    return result


def extract_team_bans(info):
    """Renvoie {teamId: "id1;id2;id3..."} -- les championId bannis par
    chaque equipe, dans l'ordre de ban (pickTurn). Un "ban" non utilise
    (mode blind pick, joueur absent...) apparait avec championId=-1 chez
    Riot ; on le filtre pour ne garder que les vrais bans. Pour retrouver le
    nom du champion a partir de son id, fais la jointure avec la colonne
    'key' de champions_by_patch.csv (meme id numerique cote Data Dragon)."""
    result = {}
    for team in info.get("teams", []) or []:
        team_id = team.get("teamId")
        bans = sorted(team.get("bans", []) or [], key=lambda b: b.get("pickTurn", 0))
        ids = [str(b.get("championId")) for b in bans if b.get("championId", -1) not in (None, -1)]
        result[team_id] = ";".join(ids)
    return result


def extract_perks(p):
    """Runes du joueur : arbre principal + rune cle (keystone), arbre
    secondaire, et les 3 "shards" de stats. Les valeurs sont des ID Riot
    (ex. arbre 8100 = Domination) -- pas de noms lisibles ici, il faudrait
    croiser avec runesReforged.json de Data Dragon (meme logique que
    champion.json/item.json, pas encore ajoute a lol_meta_dataset.py)."""
    perks = p.get("perks", {}) or {}
    stat_perks = perks.get("statPerks", {}) or {}
    styles = perks.get("styles", []) or []
    primary = next((s for s in styles if s.get("description") == "primaryStyle"), {}) or {}
    sub = next((s for s in styles if s.get("description") == "subStyle"), {}) or {}
    primary_sel = primary.get("selections", []) or []
    sub_sel = sub.get("selections", []) or []
    return {
        "perkPrimaryStyle": primary.get("style"),
        "perkPrimaryKeystone": primary_sel[0]["perk"] if primary_sel else None,
        "perkPrimarySelections": ";".join(str(s.get("perk")) for s in primary_sel),
        "perkSubStyle": sub.get("style"),
        "perkSubSelections": ";".join(str(s.get("perk")) for s in sub_sel),
        "perkStatOffense": stat_perks.get("offense"),
        "perkStatFlex": stat_perks.get("flex"),
        "perkStatDefense": stat_perks.get("defense"),
    }


def extract_challenges(p):
    challenges = p.get("challenges", {}) or {}
    return {key: challenges.get(key) for key in CHALLENGE_KEYS}


def flatten_match(match, rune_cache_dir=None):
    info = match.get("info", {})
    metadata = match.get("metadata", {})
    match_id = metadata.get("matchId")
    team_objectives = extract_team_objectives(info)
    team_bans = extract_team_bans(info)
    rows = []
    for p in info.get("participants", []):
        team_position = (p.get("teamPosition") or "").upper()
        team_id = p.get("teamId")
        opp_team_id = 200 if team_id == 100 else (100 if team_id == 200 else None)
        own_obj = team_objectives.get(team_id, {})
        opp_obj = team_objectives.get(opp_team_id, {})
        row = {
                "matchId": match_id,
                "platformId": info.get("platformId"),
                "gameCreation": info.get("gameCreation"),
                "gameStartTimestamp": info.get("gameStartTimestamp"),
                "gameEndTimestamp": info.get("gameEndTimestamp"),
                "gameDuration": info.get("gameDuration"),
                "gameVersion": info.get("gameVersion"),
                # ex "16.16.593.1234" -> "16.16", pratique pour rejoindre avec
                # le dataset champions/items (colonne 'patch' -> meme prefixe)
                "patch_major_minor": ".".join((info.get("gameVersion") or "0.0").split(".")[:2]),
                "queueId": info.get("queueId"),
                "gameMode": info.get("gameMode"),
                "mapId": info.get("mapId"),
                "puuid": p.get("puuid"),
                "riotIdGameName": p.get("riotIdGameName"),
                "riotIdTagline": p.get("riotIdTagline"),
                "summonerLevel": p.get("summonerLevel"),
                "teamId": p.get("teamId"),
                "side": "Blue" if p.get("teamId") == 100 else ("Red" if p.get("teamId") == 200 else None),
                "win": p.get("win"),
                "championName": p.get("championName"),
                "championId": p.get("championId"),
                "champLevel": p.get("champLevel"),
                "champExperience": p.get("champExperience"),
                "teamPosition": team_position,
                "position": POSITION_MAP.get(team_position),
                "kills": p.get("kills"),
                "deaths": p.get("deaths"),
                "assists": p.get("assists"),
                "goldEarned": p.get("goldEarned"),
                "goldSpent": p.get("goldSpent"),
                "totalMinionsKilled": p.get("totalMinionsKilled"),
                "neutralMinionsKilled": p.get("neutralMinionsKilled"),
                "visionScore": p.get("visionScore"),
                "wardsPlaced": p.get("wardsPlaced"),
                "wardsKilled": p.get("wardsKilled"),
                "totalDamageDealtToChampions": p.get("totalDamageDealtToChampions"),
                "damageDealtToTurrets": p.get("damageDealtToTurrets"),
                "damageDealtToObjectives": p.get("damageDealtToObjectives"),
                # Volet "defensif" (2026-08-21) : degats subis, soins,
                # boucliers, mitigation -- absent des versions precedentes
                "totalDamageTaken": p.get("totalDamageTaken"),
                "physicalDamageTaken": p.get("physicalDamageTaken"),
                "magicDamageTaken": p.get("magicDamageTaken"),
                "trueDamageTaken": p.get("trueDamageTaken"),
                "damageSelfMitigated": p.get("damageSelfMitigated"),
                "totalHeal": p.get("totalHeal"),
                "totalHealsOnTeammates": p.get("totalHealsOnTeammates"),
                "totalDamageShieldedOnTeammates": p.get("totalDamageShieldedOnTeammates"),
                "totalTimeCCDealt": p.get("totalTimeCCDealt"),
                "timeCCingOthers": p.get("timeCCingOthers"),
                "turretTakedowns": p.get("turretTakedowns"),
                "inhibitorTakedowns": p.get("inhibitorTakedowns"),
                "item0": p.get("item0"),
                "item1": p.get("item1"),
                "item2": p.get("item2"),
                "item3": p.get("item3"),
                "item4": p.get("item4"),
                "item5": p.get("item5"),
                "item6": p.get("item6"),
                "summoner1Id": p.get("summoner1Id"),
                "summoner2Id": p.get("summoner2Id"),
                "doubleKills": p.get("doubleKills"),
                "tripleKills": p.get("tripleKills"),
                "quadraKills": p.get("quadraKills"),
                "pentaKills": p.get("pentaKills"),
                "largestKillingSpree": p.get("largestKillingSpree"),
                "largestMultiKill": p.get("largestMultiKill"),
                "longestTimeSpentLiving": p.get("longestTimeSpentLiving"),
                "firstBloodKill": p.get("firstBloodKill"),
                "gameEndedInSurrender": p.get("gameEndedInSurrender"),
                "timePlayed": p.get("timePlayed"),
        }
        # Runes (2026-08-21) : cf. extract_perks() -- IDs Riot bruts, puis
        # resolus en noms lisibles juste apres si rune_cache_dir est fourni
        # (cf. resolve_rune_names -- appel a Data Dragon, jamais a l'API Riot)
        row.update(extract_perks(p))
        if rune_cache_dir is not None:
            resolve_rune_names(row, rune_cache_dir)
        else:
            for col in RUNE_NAME_COLUMNS:
                row[col] = None
        # Stats derivees deja calculees par Riot (kda, kill participation,
        # dmg/min, gold/min...) -- cf. commentaire CHALLENGE_KEYS plus haut
        row.update(extract_challenges(p))
        # Objectifs d'equipe (dragons, barons, tours, inhibiteurs, heraut,
        # void grubs) : ceux de MON equipe tels quels, ceux de l'equipe
        # adverse prefixes "opp_" -- meme convention que ton dataset
        # Oracle's Elixir (colonnes dragons/opp_dragons, barons/opp_barons...)
        row.update(own_obj)
        row.update({f"opp_{k}": v for k, v in opp_obj.items()})
        # Bans d'equipe (2026-08-21) : identiques pour tous les joueurs d'une
        # meme equipe sur un match donne -- meme convention own/opp_
        row["bans"] = team_bans.get(team_id, "")
        row["opp_bans"] = team_bans.get(opp_team_id, "")
        rows.append(row)
    return rows


def read_accounts_csv(path):
    accounts = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("game_name") or not row.get("tag_line"):
                continue
            accounts.append(
                (row["game_name"].strip(), row["tag_line"].strip(), (row.get("region") or "").strip())
            )
    return accounts


def add_rank_columns(df, api_key, rank_cache_dir: Path):
    """Resout le rang solo/flex de chaque joueur DISTINCT du DataFrame (une
    seule requete par puuid, meme s'il apparait dans plusieurs matchs), et
    fusionne les colonnes RANK_COLUMNS dedans (jointure gauche sur puuid --
    les joueurs pour qui la resolution echoue ou est encore a faire gardent
    des NaN, ils n'excluent jamais de lignes).

    C'est potentiellement l'etape la PLUS LONGUE du script : chaque joueur
    coute un appel API, et la cle de dev est limitee a ~18-20 requetes/s ET
    ~92-100 requetes/2min (le 2e plafond est souvent le plus contraignant en
    pratique) -- pour un echantillon de plusieurs dizaines de milliers de
    joueurs distincts, compte plusieurs HEURES. D'ou :
      - le cache disque par joueur (cf resolve_rank) qui rend un re-lancement
        de la MEME commande capable de reprendre exactement la ou on s'est
        arrete, sans rien re-demander pour les joueurs deja resolus ;
      - le fait d'intercepter Ctrl+C ici : une interruption volontaire (ou
        un plantage) n'empeche pas d'ecrire un fichier de sortie avec ce qui
        a deja ete resolu (colonnes de rang vides pour le reste), plutot que
        de tout perdre.
    """
    puuid_platform = (
        df.dropna(subset=["puuid", "platformId"])
        .assign(platformId=lambda d: d["platformId"].str.upper())
        .groupby("puuid")["platformId"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    total = len(puuid_platform)
    if total == 0:
        return df

    print(f"Resolution du rang (League-V4) pour {total} joueur(s) distinct(s)...", file=sys.stderr)
    platform_clients = {}
    rank_rows = {}
    start = time.monotonic()
    try:
        for idx, (puuid, platform) in enumerate(puuid_platform.items(), start=1):
            entries = resolve_rank(puuid, platform, platform_clients, api_key, rank_cache_dir)
            rank_rows[puuid] = rank_row_from_entries(entries)
            if idx % 50 == 0 or idx == total:
                elapsed = time.monotonic() - start
                rate = idx / elapsed if elapsed > 0 else 0
                eta_min = (total - idx) / rate / 60 if rate > 0 else float("nan")
                print(
                    f"  ... {idx}/{total} joueurs resolus "
                    f"({rate:.2f} req/s, ETA ~{eta_min:.0f} min)",
                    file=sys.stderr,
                )
    except KeyboardInterrupt:
        print(
            f"\n! Interrompu par l'utilisateur : {len(rank_rows)}/{total} joueurs resolus. "
            "Les rangs deja obtenus restent en cache sur disque et ne seront PAS "
            "re-demandes au prochain lancement -- relance exactement la meme commande "
            "pour reprendre la ou tu t'es arrete. Le fichier de sortie genere maintenant "
            "aura des colonnes de rang vides (NaN) pour les joueurs non encore resolus.",
            file=sys.stderr,
        )

    rank_df = pd.DataFrame.from_dict(rank_rows, orient="index")
    rank_df.index.name = "puuid"
    rank_df = rank_df.reset_index()
    return df.merge(rank_df, on="puuid", how="left")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--api-key", default=os.environ.get("RIOT_API_KEY"), help="Cle API Riot (ou variable d'env RIOT_API_KEY)")
    p.add_argument("--accounts", help="CSV avec colonnes game_name,tag_line,region (mode A)")
    p.add_argument("--riot-id", help='Un seul compte de depart, format "Pseudo#TAG" (mode B, avec --expand)')
    p.add_argument("--region", default="europe", choices=sorted(REGIONS), help="Routing continental (americas/asia/europe/sea)")
    p.add_argument("--expand", action="store_true", help="Ajoute automatiquement les co-joueurs croises dans les matchs recuperes")
    p.add_argument("--max-accounts", type=int, default=20, help="Nombre max de comptes distincts traites (securite anti-emballement avec --expand)")
    p.add_argument("--count", type=int, default=10, help="Nombre de matchs recents par compte")
    p.add_argument("--queue", type=int, default=None, help="Filtrer par queueId (ex: 420 = ranked solo/duo, 450 = ARAM). Vide = tout")
    p.add_argument("--out", default="data")
    p.add_argument("--cache", default="cache/matches")
    p.add_argument("--rune-cache", default="cache/ddragon_runes", help="Cache local pour les noms de runes (Data Dragon)")
    p.add_argument(
        "--no-rune-names",
        action="store_true",
        help="Ne pas resoudre les noms de runes (garde uniquement les ID bruts perk*, un peu plus rapide)",
    )
    p.add_argument(
        "--no-rank",
        action="store_true",
        help="Ne pas resoudre le rang (League-V4) des joueurs -- plus rapide (pas de "
        "colonnes soloqueue_*/flexqueue_*), utile pour un run rapide/exploratoire",
    )
    p.add_argument(
        "--rank-cache",
        default="cache/league_ranks",
        help="Cache local (un fichier JSON par joueur) pour la resolution du rang",
    )
    p.add_argument("--format", choices=["csv", "parquet", "both"], default="parquet")
    args = p.parse_args()

    if not args.api_key:
        sys.exit(
            "Pas de cle API. Passe --api-key TA_CLE ou fais "
            "'export RIOT_API_KEY=...' (Windows PowerShell: $env:RIOT_API_KEY=\"...\") avant de lancer le script."
        )
    if not args.accounts and not args.riot_id:
        sys.exit("Fournis soit --accounts fichier.csv, soit --riot-id \"Pseudo#TAG\"")

    client = RiotClient(args.api_key, args.region)
    cache_dir = Path(args.cache)
    rune_cache_dir = None if args.no_rune_names else Path(args.rune_cache)

    seeds = []
    if args.accounts:
        for game_name, tag_line, region in read_accounts_csv(args.accounts):
            seeds.append((game_name, tag_line, region or args.region))
    if args.riot_id:
        if "#" not in args.riot_id:
            sys.exit('--riot-id doit etre au format "Pseudo#TAG"')
        game_name, tag_line = args.riot_id.split("#", 1)
        seeds.append((game_name, tag_line, args.region))

    seen_puuids = set()
    seen_matches = set()
    queue_accounts = []  # liste de (puuid, region)

    print(f"Resolution de {len(seeds)} compte(s) de depart...", file=sys.stderr)
    for game_name, tag_line, region in seeds:
        c = client if region == client.region else RiotClient(args.api_key, region)
        puuid = c.get_puuid(game_name, tag_line)
        if not puuid:
            print(f"  ! Riot ID introuvable : {game_name}#{tag_line} ({region})", file=sys.stderr)
            continue
        if puuid not in seen_puuids:
            seen_puuids.add(puuid)
            queue_accounts.append((puuid, region))

    all_rows = []
    processed = 0
    i = 0
    while i < len(queue_accounts) and processed < args.max_accounts:
        puuid, region = queue_accounts[i]
        i += 1
        processed += 1
        c = client if region == client.region else RiotClient(args.api_key, region)

        print(f"[{processed}/{args.max_accounts}] compte {puuid[:8]}... ({region})", file=sys.stderr)
        match_ids = c.get_match_ids(puuid, count=args.count, queue=args.queue)

        for mid in match_ids:
            if mid in seen_matches:
                continue
            seen_matches.add(mid)
            match = c.get_match(mid, cache_dir)
            if not match:
                print(f"  ! match {mid} indisponible, ignore", file=sys.stderr)
                continue
            rows = flatten_match(match, rune_cache_dir)
            all_rows.extend(rows)

            if args.expand:
                for r in rows:
                    other_puuid = r["puuid"]
                    if other_puuid and other_puuid not in seen_puuids and len(queue_accounts) < args.max_accounts:
                        seen_puuids.add(other_puuid)
                        queue_accounts.append((other_puuid, region))

    df = pd.DataFrame(all_rows)
    if df.empty:
        sys.exit("Aucune donnee recuperee -- verifie ta cle API et tes Riot ID.")

    df = df.drop_duplicates(subset=["matchId", "puuid"])

    if not args.no_rank:
        df = add_rank_columns(df, args.api_key, Path(args.rank_cache))
    else:
        print("Resolution du rang desactivee (--no-rank) : pas de colonnes soloqueue_*/flexqueue_*.", file=sys.stderr)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.format in ("csv", "both"):
        # encoding explicite : sur Windows, to_csv() sans "encoding" utilise
        # l'encodage par defaut du systeme (souvent cp1252 en local francais),
        # qui ne sait pas representer certains caracteres Unicode presents
        # dans des pseudos de joueurs (symboles, alphabets non-latins...).
        # utf-8-sig = UTF-8 avec un BOM, qu'Excel sait aussi lire correctement.
        df.to_csv(out / "player_matches.csv", index=False, encoding="utf-8-sig")
    if args.format in ("parquet", "both"):
        df.to_parquet(out / "player_matches.parquet", index=False)

    print(
        f"OK : {len(df)} lignes, {df['matchId'].nunique()} matchs, "
        f"{df['puuid'].nunique()} joueurs distincts -> {out}/",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
