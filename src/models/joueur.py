import pandas as pd
 
 
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
 
def calc_stats_joueur(df, player_name_1, player_name_2=None, position=None, season="16", queue_id=420):
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
 
    if player_name_2:
        KDA_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["kda"].mean().round(2)
        KP_2 = (df_filtre[df_filtre["riotIdGameName"] == player_name_2]["killParticipation"] * 100).mean().round(2)
        GM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["goldPerMinute"].mean().round(2)
        DM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["damagePerMinute"].mean().round(2)
        VSM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["visionScorePerMinute"].mean().round(2)
        CSM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["CSM"].mean().round(2)
        WPM_2 = df_filtre[df_filtre["riotIdGameName"] == player_name_2]["WPM"].mean().round(2)
        nom_2 = player_name_2
    else:
        rang = df_filtre[df_filtre["riotIdGameName"] == player_name_1].sort_values("gameStartTimestamp", ascending=False)["soloqueue_tier"].iloc[0]
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
 
 
def builds_frequents_champion(df, df_item, player, champion, season="16", queue_id=420, min_games=2):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_player = df_queue[df_queue["riotIdGameName"] == player]
    df_champ = df_player[df_player["championName"] == champion].copy()
 
    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    df_champ["build"] = df_champ[colonnes_items].apply(
        lambda row: frozenset(i for i in row if i != 0), axis=1
    )
 
    df_build = df_champ.groupby("build").agg(
        victory=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
 
    df_build["winrate"] = ((df_build["victory"] / df_build["nb_played"]) * 100).round(2)
    df_build = df_build[df_build["nb_played"] >= min_games]
    df_build = df_build.sort_values(by="nb_played", ascending=False)
 
    noms_items = df_item.drop_duplicates(subset="item_id").set_index("item_id")["name"]
    df_build["Build"] = df_build["build"].apply(
        lambda ids: ", ".join(sorted(noms_items.get(str(i), f"Item {i}") for i in ids))
    )
 
    df_build = df_build[["Build", "nb_played", "winrate"]]
    return df_build
 
 
def meilleurs_items_champion_role(df, df_items, champion, role, rang=None, season="16", queue_id=420, min_games=10):
    df_season = df[df["patch_major_minor"].str.startswith(season)]
    df_queue = df_season[df_season["queueId"] == queue_id] if queue_id else df_season
    df_champ = df_queue[df_queue["championName"] == champion]
    df_role = df_champ[df_champ["position"] == role]
    df_rang = df_role[df_role["soloqueue_tier"] == rang] if rang else df_role
 
    colonnes_items = ["item0", "item1", "item2", "item3", "item4", "item5"]
    df_rang = df_rang.copy()
    df_rang["build"] = df_rang[colonnes_items].apply(
        lambda row: frozenset(i for i in row if i != 0), axis=1
    )
    df_rang = df_rang[df_rang["gameDuration"] >= 900]
    df_rang = df_rang[df_rang["build"].apply(len) > 3]
 
    df_build = df_rang.groupby("build").agg(
        victory=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
 
    df_build["winrate"] = ((df_build["victory"] / df_build["nb_played"]) * 100).round(2)
    df_build = df_build[df_build["nb_played"] >= min_games]
    df_build = df_build.sort_values(by="winrate", ascending=False)
 
    noms_items = df_items.drop_duplicates(subset="item_id").set_index("item_id")["name"]
    df_build["Build"] = df_build["build"].apply(
        lambda ids: ", ".join(sorted(noms_items.get(str(i), f"Item {i}") for i in ids))
    )
 
    df_build = df_build[["Build", "nb_played", "winrate"]]
    return df_build
 
 
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
 
    tableau = df_player[["gameDate", "position", "championName", "win", "kda", "kills", "deaths", "assists", "totalMinionsKilled", "gameDurationMinute"]].head(nombre_game).copy()
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
        dm=("damagePerMinute", "mean")
    ).reset_index()
 
    df_role = df_role[df_role["nb_played"] >= 5]
 
    df_role["Winrate (%)"] = ((df_role["victory"] / df_role["nb_played"]) * 100).round(2)
    df_role = df_role.round(2)
 
    df_role = df_role.rename(columns={
        "position": "Role",
        "dm": "Damage / Minute",
        "kp": "Kill participation",
        "csm": "Creeps / Minute",
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
    df_side["winrate"] = ((df_side["victoires"] / df_side["nb_played"]) * 100).round(2)
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
 
    rang = df_player.sort_values("gameStartTimestamp", ascending=False)["soloqueue_tier"].iloc[0]
 
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
 
 
def _winrate_par_categorie(df_player, colonne, nom_colonne_affichee):
    table = df_player.groupby(colonne, observed=True).agg(
        victoires=("win", "sum"),
        nb_played=("win", "count")
    ).reset_index()
    table["winrate"] = ((table["victoires"] / table["nb_played"]) * 100).round(2)
    table = table.rename(columns={
        colonne: nom_colonne_affichee,
        "victoires": "Nombre victoire",
        "nb_played": "Nombre de game",
        "winrate": "Winrate"
    })
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
 
    par_moment = _winrate_par_categorie(df_player, "moment_journee", "Moment de la journée")
    par_jour = _winrate_par_categorie(df_player, "jour_semaine", "Jour de la semaine")
    par_jour["Jour de la semaine"] = pd.Categorical(par_jour["Jour de la semaine"], categories=list(jours.values()), ordered=True)
    par_jour = par_jour.sort_values("Jour de la semaine")
 
    return par_moment, par_jour
