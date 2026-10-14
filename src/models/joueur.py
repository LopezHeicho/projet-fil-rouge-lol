import pandas as pd

from utils import patch_to_tuple
from models.esport import changements_champion_et_spell
from models.item import classement_buff_nerf_item
 
 
# ---------------------------------------------------------------------------
# Nettoyage / enrichissement (a appliquer UNE FOIS sur le DataFrame complet)
# ---------------------------------------------------------------------------
 
def nettoyer_donnees_joueur(df):
    """ A appliquer sur la concatenation du CSV statique + des games recuperees en direct
    (colonnes brutes identiques des deux cotes, cf. joueur_live.py), jamais sur les deux sources separement."""
    df = df.copy()
 
    df["win"] = df["win"].replace({True: 1, False: 0})
    df["gameDurationMinute"] = (df["gameDuration"] // 60).astype(str) + "m" + (df["gameDuration"] % 60).astype(str) + "s"
    df = df.rename(columns={"totalMinionsKilled": "MinionsKilled"})
    df["totalMinionsKilled"] = df["MinionsKilled"] + df["neutralMinionsKilled"]
    df["CSM"] = df["totalMinionsKilled"] / (df["gameDuration"] / 60)
    df["WPM"] = df["wardsPlaced"] / (df["gameDuration"] / 60)
    df["gameDate"] = pd.to_datetime(df["gameStartTimestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Paris")
    df["annee_semaine"] = df["gameDate"].dt.strftime("%Y-S%U")
    df["jour_semaine"] = df["gameDate"].dt.day_name()
    df["heure"] = df["gameDate"].dt.hour
 
    colonnes_float = df.select_dtypes(include="float").columns
    df[colonnes_float] = df[colonnes_float].round(2)
 
    return df
 
 
# ---------------------------------------------------------------------------
# Radar de stats (comparaison joueur / joueur ou joueur / rang)
# ---------------------------------------------------------------------------
 
def calc_stats_joueur(df, player_name_1, player_name_2=None, position=None, season="16", queue_id=420,
                       df_esport=None, comparer_pro=False, pro_player=None, ligue_pro=None):
    """Retourne (labels, values_1, values_2, nom_2)."""
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_filtre = df_queue[df_queue["position"] == position] if position else df_queue

    KDA = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["kda"].mean().round(2)
    KP = (df_filtre[df_filtre["riotIdGameName"] == player_name_1]["killParticipation"] * 100).mean().round(2)
    GM = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["goldPerMinute"].mean().round(2)
    DM = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["damagePerMinute"].mean().round(2)
    VSM = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["visionScorePerMinute"].mean().round(2)
    CSM = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["CSM"].mean().round(2)
    WPM = df_filtre[df_filtre["riotIdGameName"] == player_name_1]["WPM"].mean().round(2)

    if comparer_pro and df_esport is not None:
        df_pro = df_esport[df_esport["position"] == position] if position else df_esport
        if ligue_pro:
            df_pro = df_pro[df_pro["league"] == ligue_pro]

        if pro_player:
            df_cible = df_pro[df_pro["playername"] == pro_player]
            nom_2 = pro_player
        else:
            df_cible = df_pro
            nom_2 = f"Moyenne pro ({ligue_pro})" if ligue_pro else "Moyenne pro (toutes ligues)"

        KDA_2 = ((df_cible["kills"].mean() + df_cible["assists"].mean()) / df_cible["deaths"].mean()).round(2)
        KP_2 = (((df_cible["kills"].mean() + df_cible["assists"].mean()) / df_cible["teamkills"].mean()) * 100).round(2)
        GM_2 = df_cible["earned gpm"].mean().round(2)
        DM_2 = df_cible["dpm"].mean().round(2)
        VSM_2 = df_cible["vspm"].mean().round(2)
        CSM_2 = df_cible["cspm"].mean().round(2)
        WPM_2 = df_cible["wpm"].mean().round(2)
    elif player_name_2:
        KDA_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["kda"].mean().round(2)
        KP_2 = (df_filtre[df_filtre["riotIdGameName"] == player_name_2]["killParticipation"] * 100).mean().round(2)
        GM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["goldPerMinute"].mean().round(2)
        DM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["damagePerMinute"].mean().round(2)
        VSM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["visionScorePerMinute"].mean().round(2)
        CSM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["CSM"].mean().round(2)
        WPM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["WPM"].mean().round(2)
        nom_2 = player_name_2
    else:
        rang_df_joueur = df_filtre[df_filtre["riotIdGameName"] == player_name_1].dropna(subset=["soloqueue_tier"])
        if rang_df_joueur.empty:
            return None

        rang = rang_df_joueur.sort_values("gameStartTimestamp", ascending=False)["soloqueue_tier"].iloc[0]
        rang_df = df_filtre[df_filtre["soloqueue_tier"] == rang]
 
        KDA_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["kda"].mean().round(2)
        KP_2 = (rang_df[rang_df["riotIdGameName"] != player_name_1]["killParticipation"] * 100).mean().round(2)
        GM_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["goldPerMinute"].mean().round(2)
        DM_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["damagePerMinute"].mean().round(2)
        VSM_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["visionScorePerMinute"].mean().round(2)
        CSM_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["CSM"].mean().round(2)
        WPM_2 = rang_df[rang_df["riotIdGameName"] != player_name_1]["WPM"].mean().round(2)
        nom_2 = f"Moyenne dans {rang}"
 
    labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute", "Wards / Minute"]
    values_1 = [KDA, KP, GM, DM, VSM, CSM, WPM]
    values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, CSM_2, WPM_2]
 
    return labels, values_1, values_2, nom_2
 
 
# ---------------------------------------------------------------------------
# Champions
# ---------------------------------------------------------------------------
 
def calc_meilleurs_champions(df, player, nombre=10, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    df_winrate = df_player.groupby("championName").agg(
        victory=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
    df_winrate["winrate"] = ((df_winrate["victory"] / df_winrate["nb_played"]) * 100).round(2)
    df_winrate = df_winrate[df_winrate["nb_played"] >= 3]
    df_winrate = df_winrate.sort_values(ascending=False, by="nb_played")
    df_winrate = df_winrate.head(nombre)
    df_winrate = df_winrate.sort_values(ascending=False, by="winrate")
 
    return df_winrate
 
 
def best_champion_table(df, player, nombre=10, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    df_winrate = df_player.groupby("championName").agg(
        nb_played=("win", "count"),
        Victory=("win", "sum"),
        KDA=("kda", "mean"),
        KP=("killParticipation", "mean"),
        csm=("CSM", "mean"),
        dm=("damagePerMinute", "mean"),
        vm=("visionScorePerMinute", "mean")
    ).reset_index()
    df_winrate["Winrate (%)"] = ((df_winrate["Victory"] / df_winrate["nb_played"]) * 100).round(2)
    df_winrate["KP"] = df_winrate["KP"] * 100
    df_winrate = df_winrate.round(2)
    df_winrate = df_winrate[df_winrate["nb_played"] >= 3]
    df_winrate = df_winrate.sort_values(ascending=False, by="nb_played")
    df_winrate = df_winrate.head(nombre)
    df_winrate = df_winrate.sort_values(ascending=False, by="Winrate (%)")
 
    df_winrate = df_winrate.rename(columns={
        "dm": "Damage / Minute",
        "vm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "nb_played": "Nombre game"
    })
 
    return df_winrate
 
 
def builds_frequents_champion(df, df_items, player, champion, season="16", queue_id=420, min_games=2):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_player = df_queue[df_queue["riotIdGameName"] == player]
    df_champ = df_player[df_player["championName"] == champion].copy()

    nb_games_total = len(df_champ)
    if nb_games_total == 0:
        return pd.DataFrame(columns=["Item", "Nombre de games", "% des games", "Winrate (%)"])

    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    lignes = df_champ.melt(id_vars=["win"], value_vars=colonnes_items, value_name="item_id")
    lignes = lignes[lignes["item_id"] != 0].copy()
    lignes["item_id"] = lignes["item_id"].astype(str)

    df_build = lignes.groupby("item_id").agg(
        victory=("win", "sum"),
        nb_played=("win", "count"),
    ).reset_index()

    df_build["winrate"] = ((df_build["victory"] / df_build["nb_played"]) * 100).round(2)
    df_build["pourcentage_games"] = ((df_build["nb_played"] / nb_games_total) * 100).round(1)
    df_build = df_build[df_build["nb_played"] >= min_games]
    df_build = df_build.sort_values(by="nb_played", ascending=False)

    # Reference "etat le plus recent" de chaque item_id : triee chronologiquement
    # (patch_to_tuple, pas un tri alphabetique) puis keep="last" -- necessaire
    # car un item peut changer de statut "complet" au fil des saisons (ex.
    # Voltaic Cyclosword construisait vers un autre item a sa sortie, plus
    # aujourd'hui). Prendre la premiere ligne rencontree (ordre par defaut du
    # CSV, chronologique croissant) donnerait le statut le plus ANCIEN, pas le
    # statut actuel.
    df_items_tries = df_items.sort_values("patch", key=lambda s: s.map(patch_to_tuple))
    df_items_ref = df_items_tries.drop_duplicates(subset="item_id", keep="last").set_index("item_id")
    # On ne garde que les items "complets" : ceux qui ne construisent plus vers
    # autre chose, sauf les bottes -- une botte de tier 2 (ex. "Boots of
    # Swiftness") est deja un choix final en pratique, meme si elle peut
    # encore etre enchantee en tier 3. Les composants (Long Sword, B.F. Sword,
    # Cloak of Agility, Pickaxe...) ont un "into" rempli et ne sont pas des
    # bottes -> exclus. Piege verifie le 2026-10-14 : "into" ne vaut jamais
    # NaN ni 0 apres charger_donnees_items(), c'est une chaine vide "" pour
    # un item sans suite (le CSV d'origine donnait l'impression de voir du
    # NaN a la lecture, mais ca vient juste de read_csv() qui convertit les
    # cases vides en NaN -- le Parquet, utilise par l'appli, garde "" tel
    # quel). Donc "vide" se teste avec `== ""`. Un item_id absent de df_items
    # (deja filtre en amont, ex. Control Ward consommable) est exclu aussi.
    item_complet = (df_items_ref["into"] == "") | df_items_ref["tags"].fillna("").str.contains("Boots")
    df_build = df_build[df_build["item_id"].map(item_complet).fillna(False)]
    df_build["Item"] = df_build["item_id"].map(df_items_ref["name"])

    df_build = df_build[["Item", "nb_played", "pourcentage_games", "winrate"]]
    df_build = df_build.rename(columns={"nb_played": "Nombre de games", "pourcentage_games": "% des games", "winrate": "Winrate (%)"})
    return df_build


def meilleurs_items_champion_role(df, df_items, champion, role, rang=None, season="16", queue_id=420, min_games=10):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_champ = df_queue[df_queue["championName"] == champion]
    df_role = df_champ[df_champ["position"] == role]
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role
    df_rang = df_rang[df_rang["gameDuration"] >= 900].copy()

    nb_games_total = len(df_rang)
    if nb_games_total == 0:
        return pd.DataFrame(columns=["Item", "Nombre de games", "% des games", "Winrate (%)"])

    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    lignes = df_rang.melt(id_vars=["win"], value_vars=colonnes_items, value_name="item_id")
    lignes = lignes[lignes["item_id"] != 0].copy()
    lignes["item_id"] = lignes["item_id"].astype(str)

    df_build = lignes.groupby("item_id").agg(
        victory=("win", "sum"),
        nb_played=("win", "count"),
    ).reset_index()

    df_build["winrate"] = ((df_build["victory"] / df_build["nb_played"]) * 100).round(2)
    df_build["pourcentage_games"] = ((df_build["nb_played"] / nb_games_total) * 100).round(1)
    df_build = df_build[df_build["nb_played"] >= min_games]
    df_build = df_build.sort_values(by="nb_played", ascending=False)

    df_items_tries = df_items.sort_values("patch", key=lambda s: s.map(patch_to_tuple))
    df_items_ref = df_items_tries.drop_duplicates(subset="item_id", keep="last").set_index("item_id")
    # Meme filtre "item complet" que dans builds_frequents_champion ci-dessus
    # (voir commentaire detaille la-bas) : exclut les composants non finis,
    # garde les bottes meme enchantables, se base sur l'etat du patch le plus
    # recent par item_id, et teste "into == ''" (voir le commentaire detaille
    # dans builds_frequents_champion pour le pourquoi).
    item_complet = (df_items_ref["into"] == "") | df_items_ref["tags"].fillna("").str.contains("Boots")
    df_build = df_build[df_build["item_id"].map(item_complet).fillna(False)]
    df_build["Item"] = df_build["item_id"].map(df_items_ref["name"])

    df_build = df_build[["Item", "nb_played", "pourcentage_games", "winrate"]]
    df_build = df_build.rename(columns={"nb_played": "Nombre de games", "pourcentage_games": "% des games", "winrate": "Winrate (%)"})
    return df_build


def classement_pickrate_champion(df, role=None, rang=None, season="16", queue_id=420, top_n=15):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_role = df_queue[df_queue["position"] == role] if role else df_queue
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role

    nb_total = len(df_rang)
    if nb_total == 0:
        return pd.DataFrame(columns=["champion", "nb_picks", "pickrate"])

    classement = df_rang.groupby("championName").size().reset_index(name="nb_picks")
    classement = classement.rename(columns={"championName": "champion"})
    classement["pickrate"] = (classement["nb_picks"] / nb_total * 100).round(2)
    classement = classement.sort_values("pickrate", ascending=False).head(top_n).reset_index(drop=True)
    return classement


def classement_winrate_champion(df, role=None, rang=None, season="16", queue_id=420, min_games=20, top_n=15):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_role = df_queue[df_queue["position"] == role] if role else df_queue
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role

    classement = df_rang.groupby("championName").agg(
        victoires=("win", "sum"),
        nb_played=("win", "count"),
    ).reset_index().rename(columns={"championName": "champion"})
    classement["winrate"] = ((classement["victoires"] / classement["nb_played"]) * 100).round(2)
    classement = classement[classement["nb_played"] >= min_games]
    classement = classement.sort_values("winrate", ascending=False).head(top_n).reset_index(drop=True)
    return classement[["champion", "nb_played", "winrate"]]


# ---------------------------------------------------------------------------
# Evolution / historique / repartition
# ---------------------------------------------------------------------------
 
def calc_evolution_winrate(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    df_winrate = df_player.groupby("annee_semaine").agg(
        victory=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
    df_winrate["winrate"] = ((df_winrate["victory"] / df_winrate["nb_played"]) * 100).round(2)
 
    return df_winrate
 
 
def historique_joueur(df, player, nombre_game=5, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    df_player = df_player.sort_values(ascending=False, by="gameStartTimestamp")
 
    tableau = df_player[
        ["gameDate", "position", "championName", "win", "kda", "kills", "deaths", "assists", "totalMinionsKilled", "gameDurationMinute" ,"matchId"]
        ].head(nombre_game).copy()
    tableau["gameDate"] = tableau["gameDate"].dt.strftime("%d/%m/%Y %H:%M")
 
    tableau["win"] = tableau["win"].replace({
        0: "Défaite",
        1: "Victoire"
    })
 
    tableau = tableau.rename(columns={
        "gameDate": "Date et heure",
        "position": "Role",
        "championName": "Champion",
        "win": "Resultat",
        "kda": "KDA",
        "kills": "Kills",
        "deaths": "Deaths",
        "assists": "Assists",
        "totalMinionsKilled": "Creep",
        "gameDurationMinute": "Durée de la game",
    })
 
    return tableau

def details_game(df, df_items, match_id):
    df_match_id = df[df["matchId"] == match_id]

    df_match_id = df_match_id[
        ["side", "riotIdGameName", "championName", "position", "kills", "deaths", "assists",
         "goldEarned", "totalDamageDealtToChampions", "item0", "item1", "item2", "item3","item4", "item5", "item6",
         "summoner1Id", "summoner2Id", "kda", "killParticipation", "teamDamagePercentage", "totalMinionsKilled", "win", "gameDurationMinute"]
        ].copy()

    noms_items = df_items.drop_duplicates(subset="item_id").set_index("item_id")["name"]
    noms_items.index = noms_items.index.astype(int)

    for i in range(7):
        col = f"item{i}"
        df_match_id[col] = df_match_id[col].map(noms_items).fillna("")

    blue_side = df_match_id[df_match_id["side"] == "Blue"]
    red_side = df_match_id[df_match_id["side"] == "Red"]

    return blue_side, red_side 
 
def stat_par_role(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    df_role = df_player.groupby("position").agg(
        victory=("win", "sum"),
        nb_played=("win", "count"),
        kda=("kda", "mean"),
        kp=("killParticipation", "mean"),
        csm=("CSM", "mean"),
        dm=("damagePerMinute", "mean"),
        gm=("goldPerMinute", "mean"),
    ).reset_index()
 
    df_role = df_role[df_role["nb_played"] >= 5]
 
    df_role["Winrate (%)"] = ((df_role["victory"] / df_role["nb_played"]) * 100).round(2)
    df_role = df_role.round(2)
 
    df_role = df_role.rename(columns={
        "position": "Role",
        "dm": "Damage / Minute",
        "kp": "Kill participation",
        "csm": "Creeps / Minute",
        "gm": "Gold / Minute",
        "nb_played": "Nombre game"
    })
 
    return df_role
 
 
def bilan_par_side_joueur(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player].copy()
 
    df_player["side"] = df_player["teamId"].map({100: "Bleu", 200: "Rouge"})
 
    df_side = df_player.groupby("side").agg(
        victoires=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
    df_side = df_side.rename(columns={
        "nb_played": "Nombre game"})
    df_side["winrate"] = ((df_side["victoires"] / df_side["Nombre game"]) * 100).round(2)
    return df_side
 
 
def recap_multikills_joueur(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]
 
    recap = {
        "Pentakills": df_player["pentaKills"].sum(),
        "Quadrakills": df_player["quadraKills"].sum(),
        "Triplekills": df_player["tripleKills"].sum(),
        "Doublekills": df_player["doubleKills"].sum(),
        "Plus longue killing spree": df_player["largestKillingSpree"].max(),
        "Plus gros multikill": df_player["largestMultiKill"].max()
    }
    return pd.Series(recap, name="Récap multikills")
 
 
def profil_objectifs_joueur(df, player, role=None, season="16", queue_id=420):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
 
    df_player = df_queue[df_queue["riotIdGameName"] == player]
    if role:
        df_player = df_player[df_player["position"] == role]

    # Meme garde-fou que calc_stats_joueur : une game en cache sans rang
    # resolu (echec ponctuel de l'API au moment du fetch) ne doit pas etre
    # prise comme "derniere game" pour determiner le rang du joueur.
    rang_df_joueur = df_player.dropna(subset=["soloqueue_tier"])
    if rang_df_joueur.empty:
        return pd.DataFrame()

    rang = rang_df_joueur.sort_values("gameStartTimestamp", ascending=False)["soloqueue_tier"].iloc[0]
 
    df_comparaison = df_queue[df_queue["soloqueue_tier"] == rang]
    df_comparaison = df_comparaison[df_comparaison["riotIdGameName"] != player]
    if role:
        df_comparaison = df_comparaison[df_comparaison["position"] == role]
 
    colonnes_stats = {
        "Kills / game": "kills",
        "Dragons / game": "dragonKills",
        "Barons / game": "baronKills",
        "Tourelles prises / game": "turretTakedowns",
        "Kill participation (%)": "killParticipation"
    }
 
    lignes = []
    for nom_affiche, colonne in colonnes_stats.items():
        valeur_joueur = df_player[colonne].mean()
        valeur_moyenne = df_comparaison[colonne].mean()
        if colonne == "killParticipation":
            valeur_joueur *= 100
            valeur_moyenne *= 100
        lignes.append({
            "Statistique": nom_affiche,
            player: round(valeur_joueur, 2),
            f"Moyenne {rang}": round(valeur_moyenne, 2)
        })
 
    return pd.DataFrame(lignes)
 
 
def winrate_par_categorie(df_player, colonne, nom_colonne_affichee=None):
    table = df_player.groupby(colonne, observed=True).agg(
        victoires=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
    table["winrate"] = ((table["victoires"] / table["nb_played"]) * 100).round(2)
    renames = {"victoires": "Nombre victoire", "nb_played": "Nombre de game", "winrate": "Winrate"}
    if nom_colonne_affichee is not None:
        renames[colonne] = nom_colonne_affichee
    table = table.rename(columns=renames)

    return table
 
 
def habitudes_jeu_joueur(df, player, season="16", queue_id=420):
    """Retourne (par_moment, par_jour)."""
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_player = df_queue[df_queue["riotIdGameName"] == player].copy()
 
    dates = pd.to_datetime(df_player["gameStartTimestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Paris")
    df_player["heure"] = dates.dt.hour
    df_player["jour_num"] = dates.dt.dayofweek
 
    bins = [0, 6, 12, 18, 24]
    labels_moment = ["Nuit (0h-6h)", "Matin (6h-12h)", "Après-midi (12h-18h)", "Soir (18h-24h)"]
    df_player["moment_journee"] = pd.cut(df_player["heure"], bins=bins, labels=labels_moment, right=False, include_lowest=True)
 
    jours = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    df_player["jour_semaine"] = df_player["jour_num"].map(jours)
 
    par_moment = winrate_par_categorie(df_player, "moment_journee", "Moment de la journée")
    par_jour = winrate_par_categorie(df_player, "jour_semaine", "Jour de la semaine")
    par_jour["Jour de la semaine"] = pd.Categorical(par_jour["Jour de la semaine"], categories=list(jours.values()), ordered=True)
    par_jour = par_jour.sort_values("Jour de la semaine")
 
    return par_moment, par_jour

def habitudes_jeu_joueur_heatmap(df, player, season="16", queue_id=420):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_player = df_queue[df_queue["riotIdGameName"] == player].copy()

    dates = pd.to_datetime(df_player["gameStartTimestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Paris")
    df_player["heure"] = dates.dt.hour
    df_player["jour_num"] = dates.dt.dayofweek

    bins = [0, 6, 12, 18, 24]
    labels_moment = ["Nuit (0h-6h)", "Matin (6h-12h)", "Après-midi (12h-18h)", "Soir (18h-24h)"]
    df_player["moment_journee"] = pd.cut(df_player["heure"], bins=bins, labels=labels_moment, right=False, include_lowest=True)

    jours = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    df_player["jour_semaine"] = df_player["jour_num"].map(jours)

    table = winrate_par_categorie(df_player, ["jour_semaine", "moment_journee"])

    grille = table.pivot(index="jour_semaine", columns="moment_journee", values="Winrate")
    grille = grille.reindex(index=list(jours.values()), columns=labels_moment)

    grille_nb = table.pivot(index="jour_semaine", columns="moment_journee", values="Nombre de game")
    grille_nb = grille_nb.reindex(index=list(jours.values()), columns=labels_moment)

    return grille, grille_nb

def nombre_game_dispo(df, player, season="16", queue_id=420):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_player = df_queue[df_queue["riotIdGameName"] == player]

    return len(df_player)

def items_achetes_avec_efficacite(df, df_items, role=None, rang=None, joueur=None, season="16", queue_id=420):
    df_saison = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_saison[df_saison["queueId"] == queue_id] if queue_id else df_saison
    df_joueur = df_queue[df_queue["riotIdGameName"] == joueur] if joueur else df_queue
    df_role = df_joueur[df_joueur["position"] == role] if role else df_joueur
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role
    df_rang = df_rang[df_rang["gameDuration"] >= 900]

    df_items = df_items.copy()
    df_items["patch_majmin"] = df_items["patch"].str.extract(r"^(\d+\.\d+)\.")[0]
    df_items = df_items.sort_values("patch", key=lambda s: s.map(patch_to_tuple))
    df_items_dernier = df_items.drop_duplicates(subset=["patch_majmin", "item_id"], keep="last").set_index(["patch_majmin", "item_id"])
    efficacite_ref = df_items_dernier["efficiency_gold"]
    noms_ref = df_items_dernier["name"]

    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    lignes = df_rang.melt(
        id_vars=["patch_major_minor", "soloqueue_tier", "position"],
        value_vars=colonnes_items, value_name="item_id",
    )
    lignes = lignes[lignes["item_id"] != 0].copy()
    lignes["item_id"] = lignes["item_id"].astype(str)
    cles = list(zip(lignes["patch_major_minor"], lignes["item_id"]))
    lignes["efficiency_gold"] = [efficacite_ref.get(c) for c in cles]
    lignes["name"] = [noms_ref.get(c) for c in cles]
    lignes = lignes.dropna(subset=["efficiency_gold", "name"])

    return lignes


def items_achetes_joueur(df, df_items, joueur, role=None, season="16", queue_id=420, top_n=15):
    lignes = items_achetes_avec_efficacite(df, df_items, role=role, joueur=joueur, season=season, queue_id=queue_id)

    resultat = lignes.groupby("name").agg(
        nb_achats=("efficiency_gold", "count"),
        efficacite_moyenne=("efficiency_gold", "mean"),
    ).reset_index()
    resultat["efficacite_moyenne"] = resultat["efficacite_moyenne"].round(2)
    resultat = resultat.sort_values("nb_achats", ascending=False).head(top_n).reset_index(drop=True)

    return resultat


# ---------------------------------------------------------------------------
# Impact des changements de patch sur le jeu d'un joueur
# ---------------------------------------------------------------------------

def pickrate_joueur_champion_patch(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]

    nb_total = df_player.groupby("patch_major_minor").size()
    nb_pick = df_player.groupby(["patch_major_minor", "championName"]).size()
    pickrate = nb_pick.div(nb_total, level="patch_major_minor").reset_index(name="pickrate")
    pickrate["pickrate"] = (pickrate["pickrate"] * 100).round(2)
    return pickrate.rename(columns={"championName": "champion", "patch_major_minor": "patch_majmin"})


def impact_patch_pickrate_joueur(df, df_champions, df_spells, player, season="16", queue_id=420):
    changements = changements_champion_et_spell(df_champions, df_spells)
    pickrate = pickrate_joueur_champion_patch(df, player, season=season, queue_id=queue_id)
    all_patchs = sorted(pickrate["patch_majmin"].unique(), key=patch_to_tuple)

    resultats = []
    for _, ligne in changements.iterrows():
        champion, patch = ligne["name"], ligne["patch_majmin"]
        if patch not in all_patchs:
            continue
        idx = all_patchs.index(patch)
        if idx == 0:
            continue
        patch_avant = all_patchs[idx - 1]

        pick_apres = pickrate[(pickrate["patch_majmin"] == patch) & (pickrate["champion"] == champion)]
        pick_avant = pickrate[(pickrate["patch_majmin"] == patch_avant) & (pickrate["champion"] == champion)]
        if pick_apres.empty and pick_avant.empty:
            continue

        pickrate_apres = pick_apres["pickrate"].sum() if not pick_apres.empty else 0
        pickrate_avant = pick_avant["pickrate"].sum() if not pick_avant.empty else 0
        resultats.append({
            "champion": champion, "patch": patch,
            "nb_buffs": ligne["nb_buffs"], "nb_nerfs": ligne["nb_nerfs"], "score": ligne["score"],
            "pickrate_avant": round(pickrate_avant, 2), "pickrate_apres": round(pickrate_apres, 2),
            "delta_pickrate": round(pickrate_apres - pickrate_avant, 2),
        })
    return pd.DataFrame(resultats)


def achats_joueur_item_patch(df, player, season="16", queue_id=420):
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player].copy()

    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    lignes = df_player.melt(id_vars=["patch_major_minor"], value_vars=colonnes_items, value_name="item_id")
    lignes = lignes[lignes["item_id"] != 0].copy()
    lignes["item_id"] = lignes["item_id"].astype(str)

    nb_total = df_player.groupby("patch_major_minor").size()
    nb_achat = lignes.groupby(["patch_major_minor", "item_id"]).size()
    frequence = nb_achat.div(nb_total, level="patch_major_minor").reset_index(name="frequence")
    frequence["frequence"] = (frequence["frequence"] * 100).round(2)
    return frequence.rename(columns={"patch_major_minor": "patch_majmin"})


def impact_patch_items_joueur(df, df_items, player, season="16", queue_id=420):
    _, resultats = classement_buff_nerf_item(df_items)
    changements = resultats.dropna(subset=["type_changement"]).copy()
    changements["patch_majmin"] = changements["patch"].str.extract(r"^(\d+\.\d+)\.")[0]
    changements["item_id"] = changements["item_id"].astype(str)
    score = changements.groupby(["item_id", "patch_majmin"]).agg(
        nb_buffs=("type_changement", lambda x: (x == "buff").sum()),
        nb_nerfs=("type_changement", lambda x: (x == "nerf").sum()),
    ).reset_index()
    score["score"] = score["nb_buffs"] - score["nb_nerfs"]

    frequence = achats_joueur_item_patch(df, player, season=season, queue_id=queue_id)
    all_patchs = sorted(frequence["patch_majmin"].unique(), key=patch_to_tuple)
    noms_items = df_items.drop_duplicates(subset="item_id").set_index("item_id")["name"]

    resultats_finaux = []
    for _, ligne in score.iterrows():
        item_id, patch = ligne["item_id"], ligne["patch_majmin"]
        if patch not in all_patchs:
            continue
        idx = all_patchs.index(patch)
        if idx == 0:
            continue
        patch_avant = all_patchs[idx - 1]

        freq_apres = frequence[(frequence["patch_majmin"] == patch) & (frequence["item_id"] == item_id)]
        freq_avant = frequence[(frequence["patch_majmin"] == patch_avant) & (frequence["item_id"] == item_id)]
        if freq_apres.empty and freq_avant.empty:
            continue

        frequence_apres = freq_apres["frequence"].sum() if not freq_apres.empty else 0
        frequence_avant = freq_avant["frequence"].sum() if not freq_avant.empty else 0
        resultats_finaux.append({
            "item": noms_items.get(item_id, f"Item {item_id}"), "patch": patch,
            "nb_buffs": ligne["nb_buffs"], "nb_nerfs": ligne["nb_nerfs"], "score": ligne["score"],
            "frequence_avant": round(frequence_avant, 2), "frequence_apres": round(frequence_apres, 2),
            "delta_frequence": round(frequence_apres - frequence_avant, 2),
        })
    return pd.DataFrame(resultats_finaux)


def impact_patch_performance_joueur(df, df_champions, df_spells, player, season="16", queue_id=420, min_games=3):
    changements = changements_champion_et_spell(df_champions, df_spells)
    df_queue = df[df["queueId"] == queue_id] if queue_id else df
    df_season = df_queue[df_queue["patch_major_minor"].str.startswith(season)]
    df_player = df_season[df_season["riotIdGameName"] == player]

    perf = df_player.groupby(["patch_major_minor", "championName"]).agg(
        victoires=("win", "sum"), nb_played=("win", "count"), kda_moyen=("kda", "mean"),
    ).reset_index().rename(columns={"championName": "champion", "patch_major_minor": "patch_majmin"})
    perf["winrate"] = ((perf["victoires"] / perf["nb_played"]) * 100).round(2)
    perf["kda_moyen"] = perf["kda_moyen"].round(2)
    all_patchs = sorted(perf["patch_majmin"].unique(), key=patch_to_tuple)

    resultats = []
    for _, ligne in changements.iterrows():
        champion, patch = ligne["name"], ligne["patch_majmin"]
        if patch not in all_patchs:
            continue
        idx = all_patchs.index(patch)
        if idx == 0:
            continue
        patch_avant = all_patchs[idx - 1]

        perf_apres = perf[(perf["patch_majmin"] == patch) & (perf["champion"] == champion)]
        perf_avant = perf[(perf["patch_majmin"] == patch_avant) & (perf["champion"] == champion)]
        if perf_apres.empty or perf_avant.empty:
            continue
        if perf_avant["nb_played"].iloc[0] < min_games or perf_apres["nb_played"].iloc[0] < min_games:
            continue

        resultats.append({
            "champion": champion, "patch": patch,
            "nb_buffs": ligne["nb_buffs"], "nb_nerfs": ligne["nb_nerfs"], "score": ligne["score"],
            "winrate_avant": perf_avant["winrate"].iloc[0], "winrate_apres": perf_apres["winrate"].iloc[0],
            "delta_winrate": round(perf_apres["winrate"].iloc[0] - perf_avant["winrate"].iloc[0], 2),
            "kda_avant": perf_avant["kda_moyen"].iloc[0], "kda_apres": perf_apres["kda_moyen"].iloc[0],
            "delta_kda": round(perf_apres["kda_moyen"].iloc[0] - perf_avant["kda_moyen"].iloc[0], 2),
        })
    return pd.DataFrame(resultats)


# ---------------------------------------------------------------------------
# Bans, runes, profil de combat, matchups
# ---------------------------------------------------------------------------

def classement_bans_champion(df, df_champions, rang=None, season="16", queue_id=420, top_n=15):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_rang = df_queue[df_queue["soloqueue_tier"] == rang] if rang else df_queue

    df_dedup = df_rang.drop_duplicates(subset=["matchId", "teamId"])[["bans"]].dropna()
    df_dedup = df_dedup[df_dedup["bans"] != ""]
    nb_phases = len(df_dedup)
    if nb_phases == 0:
        return pd.DataFrame(columns=["champion", "nb_bans", "ban_rate"])

    lignes = df_dedup.assign(ban_id=df_dedup["bans"].str.split(";")).explode("ban_id")
    lignes = lignes[lignes["ban_id"].notna() & (lignes["ban_id"] != "")]

    # Attention : dans champions_by_patch.csv, "id" est le slug (ex. "MissFortune"),
    # PAS l'id numerique -- c'est "key" qui contient l'id numerique (ex. 21),
    # le meme que celui utilise dans "bans"/"championId" des matchs joueurs.
    noms_champions = df_champions.drop_duplicates(subset="key", keep="last").copy()
    noms_champions["key"] = noms_champions["key"].astype(str).str.replace(r"\.0$", "", regex=True)
    noms_champions = noms_champions.set_index("key")["name"]

    compte = lignes.groupby("ban_id").size().reset_index(name="nb_bans")
    compte["ban_rate"] = (compte["nb_bans"] / nb_phases * 100).round(2)
    compte["champion"] = compte["ban_id"].map(noms_champions)
    compte = compte.dropna(subset=["champion"])
    compte = compte.sort_values("nb_bans", ascending=False).head(top_n)

    return compte[["champion", "nb_bans", "ban_rate"]]


def runes_favorites_joueur(df, player, role=None, champion=None, season="16", queue_id=420, top_n=15):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_role = df_queue[df_queue["position"] == role] if role else df_queue
    df_champ = df_role[df_role["championName"] == champion] if champion else df_role
    df_joueur = df_champ[df_champ["riotIdGameName"] == player].copy()
    df_joueur = df_joueur[df_joueur["perkPrimaryKeystoneName"].notna()]

    nb_games_total = len(df_joueur)
    if nb_games_total == 0:
        return pd.DataFrame(columns=["Rune", "Nombre de games", "% des games", "Winrate (%)"])

    df_runes = df_joueur.groupby("perkPrimaryKeystoneName").agg(
        victory=("win", "sum"),
        nb_played=("win", "count"),
    ).reset_index()

    df_runes["winrate"] = ((df_runes["victory"] / df_runes["nb_played"]) * 100).round(2)
    df_runes["pourcentage_games"] = ((df_runes["nb_played"] / nb_games_total) * 100).round(1)
    df_runes = df_runes.sort_values(by="nb_played", ascending=False).head(top_n)

    df_runes = df_runes.rename(columns={
        "perkPrimaryKeystoneName": "Rune", "nb_played": "Nombre de games",
        "pourcentage_games": "% des games", "winrate": "Winrate (%)",
    })
    return df_runes[["Rune", "Nombre de games", "% des games", "Winrate (%)"]]


def profil_combat_joueur(df, player, role=None, season="16", queue_id=420):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season

    df_player = df_queue[df_queue["riotIdGameName"] == player]
    if role:
        df_player = df_player[df_player["position"] == role]
    if df_player.empty:
        return pd.DataFrame()

    rang_df_joueur = df_player.dropna(subset=["soloqueue_tier"])
    if rang_df_joueur.empty:
        return pd.DataFrame()

    rang = rang_df_joueur.sort_values("gameStartTimestamp", ascending=False)["soloqueue_tier"].iloc[0]

    df_comparaison = df_queue[df_queue["soloqueue_tier"] == rang]
    df_comparaison = df_comparaison[df_comparaison["riotIdGameName"] != player]
    if role:
        df_comparaison = df_comparaison[df_comparaison["position"] == role]

    df_player = df_player.copy()
    df_comparaison = df_comparaison.copy()
    for frame in (df_player, df_comparaison):
        minutes = frame["gameDuration"] / 60
        frame["soin_bouclier_allies_min"] = (frame["totalHealsOnTeammates"] + frame["totalDamageShieldedOnTeammates"]) / minutes
        frame["degats_subis_min"] = frame["totalDamageTaken"] / minutes
        frame["degats_mitiges_min"] = frame["damageSelfMitigated"] / minutes

    colonnes_stats = {
        "Dégâts aux champions / min": "damagePerMinute",
        "Dégâts subis / min": "degats_subis_min",
        "Dégâts mitigés / min": "degats_mitiges_min",
        "Soin + bouclier alliés / min": "soin_bouclier_allies_min",
        "Participation aux kills (%)": "killParticipation",
        "Vision / min": "visionScorePerMinute",
    }

    lignes = []
    for nom_affiche, colonne in colonnes_stats.items():
        valeur_joueur = df_player[colonne].mean()
        valeur_moyenne = df_comparaison[colonne].mean()
        if colonne == "killParticipation":
            valeur_joueur *= 100
            valeur_moyenne *= 100
        lignes.append({
            "Statistique": nom_affiche,
            player: round(valeur_joueur, 2),
            f"Moyenne {rang}": round(valeur_moyenne, 2)
        })

    return pd.DataFrame(lignes)


def matchups_champion(df, champion, role, rang=None, season="16", queue_id=420, min_games=5, top_n=15):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_role = df_queue[df_queue["position"] == role]
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role

    colonnes = ["matchId", "teamId", "championName", "win"]
    d = df_rang[colonnes].dropna(subset=["matchId", "teamId", "championName"])

    merged = d.merge(d, on="matchId", suffixes=("", "_opp"))
    merged = merged[merged["teamId"] != merged["teamId_opp"]]

    matchups = merged[merged["championName"] == champion]
    if matchups.empty:
        return pd.DataFrame(columns=["champion", "nb_played", "winrate"])

    classement = matchups.groupby("championName_opp").agg(
        victoires=("win", "sum"),
        nb_played=("win", "count"),
    ).reset_index()
    classement["winrate"] = ((classement["victoires"] / classement["nb_played"]) * 100).round(2)
    classement = classement[classement["nb_played"] >= min_games]
    classement = classement.rename(columns={"championName_opp": "champion"})
    classement = classement.sort_values("winrate", ascending=False)

    if len(classement) > top_n:
        meilleurs = classement.head(top_n - top_n // 2)
        pires = classement.tail(top_n // 2)
        classement = pd.concat([meilleurs, pires]).drop_duplicates()
    classement = classement.sort_values("winrate", ascending=False)

    return classement[["champion", "nb_played", "winrate"]]