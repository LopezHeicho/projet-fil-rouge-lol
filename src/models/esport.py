import glob
import os
 
import pandas as pd
import streamlit as st
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
 
DOSSIER_ESPORT = r"C:\Users\lopez\Desktop\Projet Fil Rouge\clean_oe_matches\data\pro_matches_by_year"
 
 
# ---------------------------------------------------------------------------
# Chargement des donnees
# ---------------------------------------------------------------------------
 
def annees_disponibles():
    """Liste les annees dispo (un fichier parquet par annee), la plus recente
    en premier."""
    fichiers = glob.glob(os.path.join(DOSSIER_ESPORT, "*.parquet"))
    return sorted((os.path.splitext(os.path.basename(f))[0] for f in fichiers), reverse=True)
 
 
@st.cache_data
def charger_annee_esport(annee):
    return pd.read_parquet(os.path.join(DOSSIER_ESPORT, f"{annee}.parquet"))
 
 
def charger_donnees_esport(annees):
    """Concatene une ou plusieurs annees. Chaque annee individuelle est mise
    en cache separement (charger_annee_esport), donc appeler cette fonction
    avec des combinaisons differentes d'annees ne relit jamais deux fois le
    meme fichier depuis le disque."""
    return pd.concat([charger_annee_esport(a) for a in annees], ignore_index=True)
 
 
# ---------------------------------------------------------------------------
# Fonctions "joueur"
# ---------------------------------------------------------------------------
 
def stats_joueur(df, player_name_1, player_name_2=None):
    """Retourne (labels, values_1, values_2, nom_2)."""
    KDA = ((df[df["playername"] == player_name_1]["kills"].mean() + df[df["playername"] == player_name_1]["assists"].mean()) / df[df["playername"] == player_name_1]["deaths"].mean()).round(2)
    KP = (((df[df["playername"] == player_name_1]["kills"].mean() + df[df["playername"] == player_name_1]["assists"].mean()) / df[df["playername"] == player_name_1]["teamkills"].mean()) * 100).round(2)
    GM = df[df["playername"] == player_name_1]["earned gpm"].mean().round(2)
    DM = df[df["playername"] == player_name_1]["dpm"].mean().round(2)
    VSM = df[df["playername"] == player_name_1]["vspm"].mean().round(2)
    CSM = df[df["playername"] == player_name_1]["cspm"].mean().round(2)
    WPM = df[df["playername"] == player_name_1]["wpm"].mean().round(2)
 
    if player_name_2:
        KDA_2 = ((df[df["playername"] == player_name_2]["kills"].mean() + df[df["playername"] == player_name_2]["assists"].mean()) / df[df["playername"] == player_name_2]["deaths"].mean()).round(2)
        KP_2 = (((df[df["playername"] == player_name_2]["kills"].mean() + df[df["playername"] == player_name_2]["assists"].mean()) / df[df["playername"] == player_name_2]["teamkills"].mean()) * 100).round(2)
        GM_2 = df[df["playername"] == player_name_2]["earned gpm"].mean().round(2)
        DM_2 = df[df["playername"] == player_name_2]["dpm"].mean().round(2)
        VSM_2 = df[df["playername"] == player_name_2]["vspm"].mean().round(2)
        CSM_2 = df[df["playername"] == player_name_2]["cspm"].mean().round(2)
        WPM_2 = df[df["playername"] == player_name_2]["wpm"].mean().round(2)
 
        role_1 = df[df["playername"] == player_name_1]["position"].values[0]
        role_2 = df[df["playername"] == player_name_2]["position"].values[0]
 
        if role_1 != "sup" and role_2 != "sup":
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, CSM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, CSM_2]
        elif role_1 == role_2 == "sup":
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Wards / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, WPM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, WPM_2]
        else:
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2]
 
        nom_2 = player_name_2
    else:
        league = df[df["playername"] == player_name_1]["league"].values[0]
        league_df = df[df["league"] == league]
        role = league_df[league_df["playername"] == player_name_1]["position"].values[0]
 
        KDA_2 = ((league_df[league_df["position"] == role]["kills"].mean() + league_df[league_df["position"] == role]["assists"].mean()) / league_df[league_df["position"] == role]["deaths"].mean()).round(2)
        KP_2 = (((league_df[league_df["position"] == role]["kills"].mean() + league_df[league_df["position"] == role]["assists"].mean()) / league_df[league_df["position"] == role]["teamkills"].mean()) * 100).round(2)
        CSM_2 = league_df[league_df["position"] == role]["cspm"].mean().round(2)
        GM_2 = league_df[league_df["position"] == role]["earned gpm"].mean().round(2)
        DM_2 = league_df[league_df["position"] == role]["dpm"].mean().round(2)
        VSM_2 = league_df[league_df["position"] == role]["vspm"].mean().round(2)
        WPM_2 = league_df[league_df["position"] == role]["wpm"].mean().round(2)
 
        if role != "sup":
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, CSM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, CSM_2]
        else:
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Wards / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, WPM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, WPM_2]
 
        nom_2 = f"Moyenne {role} dans {league}"
 
    return labels, values_1, values_2, nom_2
 
 
def winrate_player_champion(df, player):
    df_player = df[df["playername"] == player]
    df_winrate = df_player.groupby("champion").agg(
        victory=("result", "sum"),
        nb_played=("result", "count")
    ).reset_index()
    df_winrate["winrate"] = ((df_winrate["victory"] / df_winrate["nb_played"]) * 100).round(2)
    df_winrate = df_winrate[df_winrate["nb_played"] >= 3]
    df_winrate = df_winrate.sort_values(ascending=False, by="nb_played")
    df_winrate = df_winrate.head(10)
    df_winrate = df_winrate.sort_values(ascending=False, by="winrate")
    return df_winrate
 
 
def evolution_joueur(df, player, stat="Winrate"):
    label = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Winrate"]
    if stat not in label:
        raise ValueError(f"'{stat}' n'est pas une stat valide. Choisis parmi : {label}")
 
    df_joueur = df[df["playername"] == player]
 
    evo = df_joueur.groupby("year").agg(
        kills_mean=("kills", "mean"),
        deaths_mean=("deaths", "mean"),
        assists_mean=("assists", "mean"),
        teamkills_mean=("teamkills", "mean"),
        gm=("earned gpm", "mean"),
        dm=("dpm", "mean"),
        vsm=("vspm", "mean"),
        csm=("cspm", "mean"),
        wpm=("wpm", "mean"),
        win=("result", "sum"),
        nb_played=("gameid", "count")
    ).reset_index()
 
    evo = evo[evo["nb_played"] >= 5]
 
    evo["KDA"] = (evo["kills_mean"] + evo["assists_mean"]) / evo["deaths_mean"]
    evo["Kill Participation"] = ((evo["kills_mean"] + evo["assists_mean"]) / evo["teamkills_mean"]) * 100
    evo["Winrate"] = (evo["win"] / evo["nb_played"]) * 100
    evo = evo.round(2)
 
    evo = evo.rename(columns={
        "gm": "Gold / Minute",
        "dm": "Damage / Minute",
        "vsm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "wpm": "Wards / Minute"
    })
 
    return evo
 
 
# ---------------------------------------------------------------------------
# Fonctions "equipe"
# ---------------------------------------------------------------------------
 
def bar_chart_winrate_team_data(df, league):
    df_teams = df[df["participantid"].isin([100, 200])]
    df_team = df_teams[df_teams["league"] == league]
 
    df_winrate = df_team.groupby("teamname").agg(
        victoire=("result", "sum"),
        nb_played=("result", "count")
    ).reset_index()
 
    df_winrate["winrate"] = (df_winrate["victoire"] / df_winrate["nb_played"]) * 100
    df_winrate = df_winrate.round(2)
    df_winrate = df_winrate[df_winrate["nb_played"] >= 5]
    df_winrate = df_winrate.sort_values(ascending=False, by="winrate")
 
    return df_winrate
 
 
def bar_chart_diff_data(df, league, valeur="golddiff", temps=10):
    df_teams = df[df["participantid"].isin([100, 200])]
    df_team = df_teams[df_teams["league"] == league]
    info = valeur + "at" + str(temps)
 
    df_diff = df_team.groupby("teamname").agg(
        diff=(info, "mean"),
        nb_played=("result", "count")
    ).reset_index()
    df_diff = df_diff[df_diff["nb_played"] >= 5]
    df_diff = df_diff.round(2)
    df_diff = df_diff.sort_values(ascending=False, by="diff")
 
    return df_diff
 
 
def taux_first(df_filtre, colonne):
    return ((df_filtre[colonne].sum() / df_filtre[colonne].count()) * 100).round(2)
 
 
def part_objectif(df_filtre, colonne, colonne_opp):
    return ((df_filtre[colonne].mean() / (df_filtre[colonne].mean() + df_filtre[colonne_opp].mean())) * 100).round(2)
 
 
def bar_chart_team_data(df, team1, team2=None):
    """Retourne (label, values_1, values_2, nom_2)."""
    df_team = df[df["participantid"].isin([100, 200])]
    df1 = df_team[df_team["teamname"] == team1]
    label = ["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor", "Part nashor", "Taux first tower", "Part tower", "Taux first herald"]
 
    values_1 = [
        taux_first(df1, "firstblood"),
        taux_first(df1, "firstdragon"),
        part_objectif(df1, "dragons", "opp_dragons"),
        taux_first(df1, "firstbaron"),
        part_objectif(df1, "barons", "opp_barons"),
        taux_first(df1, "firsttower"),
        part_objectif(df1, "towers", "opp_towers"),
        taux_first(df1, "firstherald"),
    ]
 
    if team2:
        df2 = df_team[df_team["teamname"] == team2]
        values_2 = [
            taux_first(df2, "firstblood"),
            taux_first(df2, "firstdragon"),
            part_objectif(df2, "dragons", "opp_dragons"),
            taux_first(df2, "firstbaron"),
            part_objectif(df2, "barons", "opp_barons"),
            taux_first(df2, "firsttower"),
            part_objectif(df2, "towers", "opp_towers"),
            taux_first(df2, "firstherald"),
        ]
        nom_2 = team2
    else:
        league = df1["league"].values[0]
        df_league = df_team[df_team["league"] == league]
        df_league = df_league[~(df_league["teamname"] == team1)]
        values_2 = [
            taux_first(df_league, "firstblood"),
            taux_first(df_league, "firstdragon"),
            part_objectif(df_league, "dragons", "opp_dragons"),
            taux_first(df_league, "firstbaron"),
            part_objectif(df_league, "barons", "opp_barons"),
            taux_first(df_league, "firsttower"),
            part_objectif(df_league, "towers", "opp_towers"),
            taux_first(df_league, "firstherald"),
        ]
        nom_2 = f"Moyenne {league}"
 
    return label, values_1, values_2, nom_2
 
 
def tableau_stats(df, role, league=None, sort_by="Winrate"):
    stats = ["Winrate", "KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
             "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Gold diff at 15",
             "XP diff at 15", "Nombre game"]
 
    if sort_by not in stats:
        raise ValueError(f"'{sort_by}' n'est pas une stat valide. Choisis parmi : {stats}")
 
    if league:
        df_league = df[df["league"] == league]
        df_role = df_league[df_league["position"] == role]
    else:
        df_role = df[df["position"] == role]
 
    player_stats = df_role.groupby("playername").agg(
        kills_mean=("kills", "mean"),
        assists_mean=("assists", "mean"),
        deaths_mean=("deaths", "mean"),
        teamkills_mean=("teamkills", "mean"),
        gm=("earned gpm", "mean"),
        dm=("dpm", "mean"),
        vsm=("vspm", "mean"),
        csm=("cspm", "mean"),
        wpm=("wpm", "mean"),
        nb_victory=("result", "sum"),
        nb_played=("result", "count"),
        golddiffat15=("golddiffat15", "mean"),
        xpdiffat15=("xpdiffat15", "mean")
    ).reset_index()
 
    player_stats["KDA"] = (player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["deaths_mean"]
    player_stats["Kill Participation"] = ((player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["teamkills_mean"]) * 100
    player_stats["Winrate"] = (player_stats["nb_victory"] / player_stats["nb_played"]) * 100
 
    player_stats = player_stats.round(2)
    player_stats = player_stats[player_stats["nb_played"] >= 5]
    player_stats = player_stats.drop(columns=["kills_mean", "assists_mean", "deaths_mean", "teamkills_mean", "nb_victory"])
 
    player_stats = player_stats.rename(columns={
        "gm": "Gold / Minute",
        "dm": "Damage / Minute",
        "vsm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "wpm": "Wards / Minute",
        "golddiffat15": "Gold diff at 15",
        "xpdiffat15": "XP diff at 15",
        "nb_played": "Nombre game"
    })
 
    col = player_stats.pop(sort_by)
    player_stats.insert(1, sort_by, col)
    player_stats = player_stats.sort_values(ascending=False, by=sort_by)
    player_stats = player_stats.reset_index(drop=True)
 
    return player_stats
 
 
def head_to_head_team(df, team1, team2):
    """Retourne (win1, win2, winrate1, winrate2, df_recap_games) ou None si les
    deux equipes ne se sont jamais affrontees."""
    df1 = df[(df["teamname"] == team1) & (df["participantid"].isin([100, 200]))]
    df2 = df[(df["teamname"] == team2) & (df["participantid"].isin([100, 200]))]
 
    df_games = df1[df1["gameid"].isin(df2["gameid"])]
 
    if len(df_games) == 0:
        return None
 
    nb_played = df_games["result"].count()
    win1 = df_games["result"].sum()
    win2 = nb_played - win1
    winrate1 = ((win1 / nb_played) * 100).round(2)
    winrate2 = 100 - winrate1
 
    df_recap_games = df_games[["year", "league", "result", "gamelength"]].copy()
    df_recap_games["result"] = df_recap_games["result"].replace({0: team2, 1: team1})
    df_recap_games["minute"] = (df_recap_games["gamelength"] // 60).astype(str) + "m"
    df_recap_games["seconde"] = (df_recap_games["gamelength"] % 60).astype(str) + "s"
    df_recap_games["gamelength"] = df_recap_games["minute"] + df_recap_games["seconde"]
    df_recap_games = df_recap_games.drop(columns=["minute", "seconde"])
    df_recap_games = df_recap_games.rename(columns={"year": "Année", "league": "Ligue", "result": "Vainqueur", "gamelength": "Durée de la game"})
    df_recap_games = df_recap_games.reset_index(drop=True)
 
    return win1, win2, winrate1, winrate2, df_recap_games
 
 
def evolution_team(df, team, stat="Winrate"):
    label = ["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor", "Part nashor", "Taux first tower", "Part tower", "Taux first herald", "Winrate"]
    if stat not in label:
        raise ValueError(f"'{stat}' n'est pas une stat valide. Choisis parmi : {label}")
 
    df_team = df[(df["teamname"] == team) & (df["participantid"].isin([100, 200]))]
 
    evo = df_team.groupby("year").agg(
        win=("result", "sum"),
        nb_played=("result", "count"),
        firstblood=("firstblood", "mean"),
        firstdragon=("firstdragon", "mean"),
        dragons=("dragons", "mean"),
        opp_dragons=("opp_dragons", "mean"),
        firstbaron=("firstbaron", "mean"),
        barons=("barons", "mean"),
        opp_barons=("opp_barons", "mean"),
        firsttower=("firsttower", "mean"),
        towers=("towers", "mean"),
        opp_towers=("opp_towers", "mean"),
        firstherald=("firstherald", "mean")
    ).reset_index()
 
    evo["Taux first blood"] = (evo["firstblood"] * 100).round(2)
    evo["Taux first dragon"] = (evo["firstdragon"] * 100).round(2)
    evo["Part dragon"] = ((evo["dragons"] / (evo["dragons"] + evo["opp_dragons"])) * 100).round(2)
    evo["Taux first nashor"] = (evo["firstbaron"] * 100).round(2)
    evo["Part nashor"] = ((evo["barons"] / (evo["barons"] + evo["opp_barons"])) * 100).round(2)
    evo["Taux first tower"] = (evo["firsttower"] * 100).round(2)
    evo["Part tower"] = ((evo["towers"] / (evo["towers"] + evo["opp_towers"])) * 100).round(2)
    evo["Taux first herald"] = (evo["firstherald"] * 100).round(2)
    evo["Winrate"] = ((evo["win"] / evo["nb_played"]) * 100).round(2)
 
    return evo
 
 
# ---------------------------------------------------------------------------
# Fonctions "cluster"
# ---------------------------------------------------------------------------
 
def find_best_k(features_scaled, k_range=range(2, 8)):
    best_k = None
    best_score = -1
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features_scaled)
        score = silhouette_score(features_scaled, labels)
        if score > best_score:
            best_score = score
            best_k = k
    return best_k
 
 
def cluster_role(df, role):
    """Retourne (player_stats, labels) -- player_stats contient une colonne
    'cluster', labels la liste des stats utilisees pour le clustering."""
    role_df = df[df["position"] == role]
 
    player_stats = role_df.groupby("playername").agg(
        kills_mean=("kills", "mean"),
        assists_mean=("assists", "mean"),
        deaths_mean=("deaths", "mean"),
        teamkills_mean=("teamkills", "mean"),
        gm=("earned gpm", "mean"),
        dm=("dpm", "mean"),
        vsm=("vspm", "mean"),
        csm=("cspm", "mean"),
        wpm=("wpm", "mean")
    ).reset_index()
    player_stats["KDA"] = (player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["deaths_mean"]
    player_stats["Kill Participation"] = ((player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["teamkills_mean"]) * 100
    player_stats = player_stats.round(2)
 
    games_count = role_df.groupby("playername").size()
    player_stats = player_stats[player_stats["playername"].isin(games_count[games_count >= 5].index)]
    player_stats = player_stats.dropna()
 
    player_stats = player_stats.rename(columns={
        "gm": "Gold / Minute",
        "dm": "Damage / Minute",
        "vsm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "wpm": "Wards / Minute"
    })
    player_stats = player_stats.drop(columns=["kills_mean", "assists_mean", "deaths_mean", "teamkills_mean"])
 
    if role != "sup":
        labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute"]
    else:
        labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Wards / Minute"]
 
    features_scaled = StandardScaler().fit_transform(player_stats[labels])
    best_k = find_best_k(features_scaled)
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    player_stats["cluster"] = kmeans.fit_predict(features_scaled)
 
    return player_stats, labels
 
 
def cluster_all_roles_standardise(df):
    """Retourne (all_players, labels) -- chaque role est standardise
    separement avant d'etre regroupe, pour ne pas biaiser le clustering vers
    les roles qui ont naturellement des stats plus hautes (ex: un mid fait
    plus de degats qu'un support)."""
    roles = ["top", "jng", "mid", "bot", "sup"]
    labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute", "Wards / Minute"]
 
    all_players = []
 
    for role in roles:
        role_df = df[df["position"] == role]
 
        player_stats = role_df.groupby("playername").agg(
            kills_mean=("kills", "mean"),
            assists_mean=("assists", "mean"),
            deaths_mean=("deaths", "mean"),
            teamkills_mean=("teamkills", "mean"),
            gm=("earned gpm", "mean"),
            dm=("dpm", "mean"),
            vsm=("vspm", "mean"),
            csm=("cspm", "mean"),
            wpm=("wpm", "mean")
        ).reset_index()
 
        player_stats["KDA"] = (player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["deaths_mean"]
        player_stats["Kill Participation"] = ((player_stats["kills_mean"] + player_stats["assists_mean"]) / player_stats["teamkills_mean"]) * 100
        player_stats = player_stats.round(2)
 
        games_count = role_df.groupby("playername").size()
        player_stats = player_stats[player_stats["playername"].isin(games_count[games_count >= 5].index)]
        player_stats = player_stats.dropna()
 
        player_stats = player_stats.rename(columns={
            "gm": "Gold / Minute", "dm": "Damage / Minute", "vsm": "Vision / Minute",
            "csm": "Creeps / Minute", "wpm": "Wards / Minute"
        })
 
        features_scaled = StandardScaler().fit_transform(player_stats[labels])
        role_scaled_df = pd.DataFrame(features_scaled, columns=labels)
        role_scaled_df["playername"] = player_stats["playername"].values
        role_scaled_df["position"] = role
 
        all_players.append(role_scaled_df)
 
    all_players = pd.concat(all_players, ignore_index=True)
 
    features_scaled_all = all_players[labels].values
    best_k = find_best_k(features_scaled_all)
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    all_players["cluster"] = kmeans.fit_predict(features_scaled_all)
 
    return all_players, labels