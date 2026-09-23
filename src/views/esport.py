import streamlit as st
import plotly.graph_objects as go
import pandas as pd
 
 
@st.cache_data
def charger_donnees():
    return pd.read_csv(r"C:\Users\lopez\Desktop\Projet Fil Rouge\clean_oe_matches\data\pro_matches_all_years.csv")
 
 
def spider_chart_stats_joueur(df, player_name_1, player_name_2=None, year=None):
 
    if year:
        df = df[df["year"] == year]
 
    # Calculons les statistiques du joueur 1 spécifié.
 
    KDA = ((df[df["playername"] == player_name_1]["kills"].mean() + df[df["playername"] == player_name_1]["assists"].mean()) / df[df["playername"] == player_name_1]["deaths"].mean()).round(2)
    KP = (((df[df["playername"] == player_name_1]["kills"].mean() + df[df["playername"] == player_name_1]["assists"].mean()) / df[df["playername"] == player_name_1]["teamkills"].mean()) * 100).round(2)
    GM = df[df["playername"] == player_name_1]["earned gpm"].mean().round(2)
    DM = df[df["playername"] == player_name_1]["dpm"].mean().round(2)
    VSM = df[df["playername"] == player_name_1]["vspm"].mean().round(2)
    CSM = df[df["playername"] == player_name_1]["cspm"].mean().round(2)
    WPM = df[df["playername"] == player_name_1]["wpm"].mean().round(2)
 
    if player_name_2:
 
        # Calculons les statistiques du joueur 2 spécifié.
 
        KDA_2 = ((df[df["playername"] == player_name_2]["kills"].mean() + df[df["playername"] == player_name_2]["assists"].mean()) / df[df["playername"] == player_name_2]["deaths"].mean()).round(2)
        KP_2 = (((df[df["playername"] == player_name_2]["kills"].mean() + df[df["playername"] == player_name_2]["assists"].mean()) / df[df["playername"] == player_name_2]["teamkills"].mean()) * 100).round(2)
        GM_2 = df[df["playername"] == player_name_2]["earned gpm"].mean().round(2)
        DM_2 = df[df["playername"] == player_name_2]["dpm"].mean().round(2)
        VSM_2 = df[df["playername"] == player_name_2]["vspm"].mean().round(2)
        CSM_2 = df[df["playername"] == player_name_2]["cspm"].mean().round(2)
        WPM_2 = df[df["playername"] == player_name_2]["wpm"].mean().round(2)
 
        if df[df["playername"] == player_name_1]["position"].values[0] != "sup" and df[df["playername"] == player_name_2]["position"].values[0] != "sup":
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Creeps / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, CSM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, CSM_2]
        elif df[df["playername"] == player_name_1]["position"].values[0] == df[df["playername"] == player_name_2]["position"].values[0] == "sup":
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute", "Wards / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM, WPM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2, WPM_2]
        else:
            labels = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute"]
            values_1 = [KDA, KP, GM, DM, VSM]
            values_2 = [KDA_2, KP_2, GM_2, DM_2, VSM_2]
    else:
        # Filtrons le DataFrame pour ne conserver que les données de la ligue spécifiée.
 
        league = df[df["playername"] == player_name_1]["league"].values[0]
        league_df = df[df["league"] == league]
        role = league_df[league_df["playername"] == player_name_1]["position"].values[0]
 
        # Calculons les statistiques moyennes de ce rôle dans la ligue spécifiée.
 
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
 
    # Normalisation des valeurs pour que le graphique soit plus lisible.
 
    values_1_normalized = []
    values_2_normalized = []
 
    for v1, v2 in zip(values_1, values_2):
        axis_max = max(v1, v2)
        values_1_normalized.append(v1 / axis_max if axis_max != 0 else 0)
        values_2_normalized.append(v2 / axis_max if axis_max != 0 else 0)
 
    labels = labels + labels[:1]
    values_1_normalized = values_1_normalized + values_1_normalized[:1]
    values_2_normalized = values_2_normalized + values_2_normalized[:1]
    values_1 = values_1 + values_1[:1]
    values_2 = values_2 + values_2[:1]
 
    # Création du graphique radar avec Plotly
 
    fig = go.Figure()
 
    fig.add_trace(go.Scatterpolar(
        r=values_1_normalized, theta=labels, customdata=values_1,
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        fill='toself', name=player_name_1,
        line=dict(color="#2a78d6"),           # bleu
        fillcolor="rgba(42, 120, 214, 0.35)"  # même bleu, semi-transparent
    ))
    fig.add_trace(go.Scatterpolar(
        r=values_2_normalized, theta=labels, customdata=values_2,
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        fill='toself',
        name=player_name_2 if player_name_2 else f'Moyenne {role} dans {league}',
        line=dict(color="#eb6834"),           # orange
        fillcolor="rgba(235, 104, 52, 0.35)"  # même orange, semi-transparent
    ))
 
    fig.update_layout(
        polar=dict(radialaxis=dict(showticklabels=False)),
        title=dict(text=f"Comparaison des statistiques de {player_name_1} et {player_name_2 if player_name_2 else f'Moyenne {role} dans {league}'}", x=0.5, xanchor='center'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5)
    )
 
    return fig
 
 
def tableau_stats(df, role, league=None, year=None, sort_by="Winrate"):
 
    stats = ["Winrate", "KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
             "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Gold diff at 15",
             "XP diff at 15", "Nombre game"]
 
    if sort_by not in stats:
        raise ValueError(f"'{sort_by}' n'est pas une stat valide. Choisis parmi : {stats}")
 
    if year:
        df = df[df["year"] == year]
 
    # Création du tableau selon le role et la ligue si il y en a une.
    if league:
        df_league = df[df["league"] == league]
        df_role = df_league[df_league["position"] == role]
    else:
        df_role = df[df["position"] == role]
 
    # Calcul des stats moyennes
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
 
    # Suppression des joueurs avec trop peu de games
    player_stats = player_stats[player_stats["nb_played"] >= 5]
 
    # renomage des colonnes necessaire et suppresion des colonnes inutiles
    player_stats = player_stats.drop(columns=["kills_mean", "assists_mean", "deaths_mean", "teamkills_mean", "nb_victory"])
 
    player_stats.rename(columns={
        "gm": "Gold / Minute",
        "dm": "Damage / Minute",
        "vsm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "wpm": "Wards / Minute",
        "golddiffat15": "Gold diff at 15",
        "xpdiffat15": "XP diff at 15",
        "nb_played": "Nombre game"
    }, inplace=True)
 
    col = player_stats.pop(sort_by)
    player_stats.insert(1, sort_by, col)
    player_stats = player_stats.sort_values(ascending=False, by=sort_by)
    player_stats = player_stats.reset_index(drop=True)
 
    return player_stats
 
 
def bar_chart_winrate_team(df, league, year=None):
 
    if year:
        df = df[df["year"] == year]
 
    df_teams = df[df["participantid"].isin([100, 200])]
    df_team = df_teams[df_teams["league"] == league]
 
    df_winrate = df_team.groupby("teamname").agg(
        victoire=("result", "sum"),
        nb_played=("result", "count")
    ).reset_index()
 
    df_winrate["winrate"] = (df_winrate["victoire"] / df_winrate["nb_played"]) * 100
    df_winrate = df_winrate.round(2)
 
    # Filtre sur le nombre de games (à ajuster si tu avais choisi un autre seuil)
    df_winrate = df_winrate[df_winrate["nb_played"] >= 5]
 
    df_winrate = df_winrate.sort_values(ascending=False, by="winrate")
 
    fig = go.Figure(go.Bar(
        x=df_winrate["teamname"],
        y=df_winrate["winrate"],
        customdata=df_winrate["nb_played"],
        marker=dict(
            color=df_winrate["winrate"],
            colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]
        ),
        hovertemplate="<b>%{x}</b><br>Winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
 
    fig.update_layout(
        title=dict(text=f"Winrate des équipes de la ligue : {league}", x=0.5, xanchor="center"),
        xaxis_title="Equipe",
        yaxis_title="Winrate",
        yaxis=dict(range=[0, 100])
    )
 
    return fig
 
 
def bar_chart_diff(df, league, valeur="golddiff", temps=10, year=None):
    diff = ["golddiff", "xpdiff", "csdiff"]
 
    if year:
        df = df[df["year"] == year]
 
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
 
    fig = go.Figure(go.Bar(
        x=df_diff["teamname"],
        y=df_diff["diff"],
        customdata=df_diff["nb_played"],
        marker=dict(
            color=df_diff["diff"],
            colorscale=[[0, "#e34948"], [0.5, "#f0efec"], [1, "#2a78d6"]],
            line=dict(color="#898781", width=1)
        ),
        hovertemplate=f"<b>%{{x}}</b><br>{valeur} at {temps} : %{{y}} golds<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
 
    fig.update_layout(
        title=dict(text=f"{valeur} au bout de {temps} minutes de game", x=0.5, xanchor="center"),
        xaxis_title="Equipe",
        yaxis_title="Diff"
    )
 
    return fig
 
 
def taux_first(df_filtre, colonne):
    return ((df_filtre[colonne].sum() / df_filtre[colonne].count()) * 100).round(2)
 
 
def part_objectif(df_filtre, colonne, colonne_opp):
    return ((df_filtre[colonne].mean() / (df_filtre[colonne].mean() + df_filtre[colonne_opp].mean())) * 100).round(2)
 
 
def bar_chart_team(df, team1, team2=None, year=None):
    if year:
        df = df[df["year"] == year]
 
    df_team = df[df["participantid"].isin([100, 200])]
    df1 = df_team[df_team["teamname"] == team1]
    label = ["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor", "Part nashor", "Taux first tower", "Part tower", "Taux first herald"]
 
    tfb = taux_first(df1, "firstblood")
    tfd = taux_first(df1, "firstdragon")
    pdr = part_objectif(df1, "dragons", "opp_dragons")
    tfn = taux_first(df1, "firstbaron")
    pna = part_objectif(df1, "barons", "opp_barons")
    tft = taux_first(df1, "firsttower")
    pto = part_objectif(df1, "towers", "opp_towers")
    tfh = taux_first(df1, "firstherald")
 
    values_1 = [tfb, tfd, pdr, tfn, pna, tft, pto, tfh]
 
    if team2:
        df2 = df_team[df_team["teamname"] == team2]
 
        tfb2 = taux_first(df2, "firstblood")
        tfd2 = taux_first(df2, "firstdragon")
        pdr2 = part_objectif(df2, "dragons", "opp_dragons")
        tfn2 = taux_first(df2, "firstbaron")
        pna2 = part_objectif(df2, "barons", "opp_barons")
        tft2 = taux_first(df2, "firsttower")
        pto2 = part_objectif(df2, "towers", "opp_towers")
        tfh2 = taux_first(df2, "firstherald")
 
        nom_2 = team2
    else:
        league = df1["league"].values[0]
        df_league = df_team[df_team["league"] == league]
        df_league = df_league[~(df_league["teamname"] == team1)]
 
        tfb2 = taux_first(df_league, "firstblood")
        tfd2 = taux_first(df_league, "firstdragon")
        pdr2 = part_objectif(df_league, "dragons", "opp_dragons")
        tfn2 = taux_first(df_league, "firstbaron")
        pna2 = part_objectif(df_league, "barons", "opp_barons")
        tft2 = taux_first(df_league, "firsttower")
        pto2 = part_objectif(df_league, "towers", "opp_towers")
        tfh2 = taux_first(df_league, "firstherald")
 
        nom_2 = f"Moyenne {league}"
 
    values_2 = [tfb2, tfd2, pdr2, tfn2, pna2, tft2, pto2, tfh2]
 
    fig = go.Figure()
    fig.add_trace(go.Bar(x=label, y=values_1, name=team1, marker_color="#2a78d6"))
    fig.add_trace(go.Bar(x=label, y=values_2, name=nom_2, marker_color="#eb6834"))
 
    fig.update_layout(
        barmode="group",
        title=dict(text=f"{team1} vs {nom_2}", x=0.5, xanchor="center"),
        yaxis_title="Pourcentage (%)",
        xaxis_title="Objectif",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
 
    return fig
 
 
def winrate_player_champion(df, player, year=None):
    if year:
        df = df[df["year"] == year]
 
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
 
    fig = go.Figure(go.Bar(
        x=df_winrate["champion"],
        y=df_winrate["winrate"],
        customdata=df_winrate["nb_played"],
        marker=dict(
            color=df_winrate["winrate"],
            colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]
        ),
        hovertemplate="<b>%{x}</b><br>Winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
 
    fig.update_layout(
        title=dict(text=f"Winrate des champions les plus joués par {player}", x=0.5, xanchor="center"),
        xaxis_title="Champion",
        yaxis_title="Winrate",
        yaxis=dict(range=[0, 100])
    )
 
    return fig
 
 
def head_to_head_team(df, team1, team2):
    """Historique des confrontations directes entre deux équipes.
 
    Retourne (resume, df_recap_games). resume est None si les deux équipes
    ne se sont jamais affrontées (pas d'appel à print/display : c'est à
    load_view d'afficher le résultat avec les composants Streamlit).
    """
    df1 = df[(df["teamname"] == team1) & (df["participantid"].isin([100, 200]))]
    df2 = df[(df["teamname"] == team2) & (df["participantid"].isin([100, 200]))]
 
    df_games = df1[df1["gameid"].isin(df2["gameid"])]
 
    if len(df_games) == 0:
        return None, None
 
    nb_played = df_games["result"].count()
    win1 = df_games["result"].sum()
    win2 = nb_played - win1
    winrate1 = ((win1 / nb_played) * 100).round(2)
    winrate2 = 100 - winrate1
 
    resume = {
        "team1": team1,
        "team2": team2,
        "win1": win1,
        "win2": win2,
        "winrate1": winrate1,
        "winrate2": winrate2,
    }
 
    df_recap_games = df_games[["year", "league", "result", "gamelength"]].copy()
    df_recap_games["result"] = df_recap_games["result"].replace({0: team2, 1: team1})
    df_recap_games["minute"] = (df_recap_games["gamelength"] // 60).astype(str) + "m"
    df_recap_games["seconde"] = (df_recap_games["gamelength"] % 60).astype(str) + "s"
    df_recap_games["gamelength"] = df_recap_games["minute"] + df_recap_games["seconde"]
    df_recap_games = df_recap_games.drop(columns=["minute", "seconde"])
    df_recap_games = df_recap_games.rename(columns={
        "year": "Année", "league": "Ligue", "result": "Vainqueur", "gamelength": "Durée de la game"
    })
    df_recap_games = df_recap_games.reset_index(drop=True)
 
    return resume, df_recap_games
 
 
def evolution_team(df, team, stat="Winrate"):
    label = ["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor", "Part nashor",
              "Taux first tower", "Part tower", "Taux first herald", "Winrate"]
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
 
    fig = go.Figure(go.Scatter(
        mode="lines+markers",
        x=evo["year"],
        y=evo[stat],
        line=dict(color="#2a78d6"),
        customdata=evo["nb_played"],
        hovertemplate=f"<b>{stat}</b> : %{{y}}<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
 
    articles = {
        "Taux first blood": "du",
        "Taux first dragon": "du",
        "Part dragon": "de la",
        "Taux first nashor": "du",
        "Part nashor": "de la",
        "Taux first tower": "du",
        "Part tower": "de la",
        "Taux first herald": "du",
        "Winrate": "du"
    }
 
    fig.update_layout(
        title=dict(text=f"Évolution {articles[stat]} {stat} de {team} au cours des années", x=0.5, xanchor="center"),
        xaxis_title="Année",
        xaxis=dict(dtick=1),
        yaxis_title=stat,
        yaxis=dict(range=[0, 100])
    )
    return fig
 
 
def evolution_joueur(df, player, stat="Winrate"):
    label = ["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute", "Vision / Minute",
              "Creeps / Minute", "Wards / Minute", "Winrate"]
    df_joueur = df[df["playername"] == player]
 
    if stat not in label:
        raise ValueError(f"'{stat}' n'est pas une stat valide. Choisis parmi : {label}")
 
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
 
    evo.rename(columns={
        "gm": "Gold / Minute",
        "dm": "Damage / Minute",
        "vsm": "Vision / Minute",
        "csm": "Creeps / Minute",
        "wpm": "Wards / Minute"
    }, inplace=True)
 
    fig = go.Figure(go.Scatter(
        mode="lines+markers",
        x=evo["year"],
        y=evo[stat],
        line=dict(color="#2a78d6"),
        customdata=evo["nb_played"],
        hovertemplate=f"<b>{stat}</b> : %{{y}}<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
 
    articles = {
        "KDA": "du",
        "Kill Participation": "de la",
        "Gold / Minute": "des",
        "Damage / Minute": "des",
        "Vision / Minute": "des",
        "Creeps / Minute": "des",
        "Wards / Minute": "des",
        "Winrate": "du"
    }
 
    fig.update_layout(
        title=dict(text=f"Évolution {articles[stat]} {stat} de {player} au cours des années", x=0.5, xanchor="center"),
        xaxis_title="Année",
        yaxis_title=stat,
        xaxis=dict(dtick=1)
    )
 
    return fig
 
 
def load_view():
    """Vue d'analyse — regroupe toutes les visualisations du projet."""
 
    st.set_page_config(page_title="Analyse", layout="wide")
 
    st.title("Analyse — visualisations et exploration")
 
    df = charger_donnees()
 
    # Listes réutilisées par plusieurs sections
    joueurs = sorted(df["playername"].dropna().unique())
    equipes = sorted(df[df["participantid"].isin([100, 200])]["teamname"].dropna().unique())
    leagues = sorted(df["league"].dropna().unique())
    roles = sorted(df["position"].dropna().unique())
    years = sorted(df["year"].dropna().unique())
 
    # --- Spider chart : comparaison de statistiques joueur ---
 
    st.subheader("Comparaison des statistiques d'un joueur (radar chart)")
 
    col1, col2, col3 = st.columns(3)
 
    with col1:
        player_name_1 = st.selectbox("Joueur", options=joueurs, key="spider_player_1")
 
    with col2:
        mode_comparaison = st.radio(
            "Comparer à",
            options=["Moyenne du poste dans la ligue", "Un autre joueur"],
            horizontal=True,
            key="spider_mode",
        )
 
    with col3:
        year_choice_spider = st.selectbox("Année", options=["Toutes les années"] + years, key="spider_year")
        year_spider = None if year_choice_spider == "Toutes les années" else year_choice_spider
 
    player_name_2 = None
    if mode_comparaison == "Un autre joueur":
        autres_joueurs = [j for j in joueurs if j != player_name_1]
        player_name_2 = st.selectbox("Joueur à comparer", options=autres_joueurs, key="spider_player_2")
 
    fig_spider = spider_chart_stats_joueur(df, player_name_1, player_name_2, year_spider)
    st.plotly_chart(fig_spider, use_container_width=True)
 
    st.divider()
 
    # --- Tableau des statistiques par rôle ---
 
    st.subheader("Tableau des statistiques par rôle")
 
    stats_options = ["Winrate", "KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
                      "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Gold diff at 15",
                      "XP diff at 15", "Nombre game"]
 
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        role = st.selectbox("Rôle", options=roles, key="tableau_role")
 
    with col2:
        league_choice = st.selectbox("Ligue", options=["Toutes les ligues"] + leagues, key="tableau_league")
        league_tableau = None if league_choice == "Toutes les ligues" else league_choice
 
    with col3:
        sort_by = st.selectbox("Trier par", options=stats_options, key="tableau_sort_by")
 
    with col4:
        year_choice_tableau = st.selectbox("Année", options=["Toutes les années"] + years, key="tableau_year")
        year_tableau = None if year_choice_tableau == "Toutes les années" else year_choice_tableau
 
    tableau = tableau_stats(df, role, league_tableau, year_tableau, sort_by)
    st.dataframe(tableau, use_container_width=True)
 
    st.caption("Seuls les joueurs ayant disputé au moins 5 games sont affichés.")
 
    st.divider()
 
    # --- Winrate des équipes par ligue ---
 
    st.subheader("Winrate des équipes par ligue")
 
    col1, col2 = st.columns(2)
 
    with col1:
        league_bar = st.selectbox("Ligue", options=leagues, key="bar_league")
 
    with col2:
        year_choice_bar = st.selectbox("Année", options=["Toutes les années"] + years, key="bar_year")
        year_bar = None if year_choice_bar == "Toutes les années" else year_choice_bar
 
    fig_bar = bar_chart_winrate_team(df, league_bar, year_bar)
    st.plotly_chart(fig_bar, use_container_width=True)
 
    st.caption("Seules les équipes ayant disputé au moins 5 games sont affichées.")
 
    st.divider()
 
    # --- Différentiels d'équipe (gold / xp / cs) ---
 
    st.subheader("Différentiels d'équipe par ligue")
 
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        league_diff = st.selectbox("Ligue", options=leagues, key="diff_league")
 
    with col2:
        valeur_diff = st.selectbox("Statistique", options=["golddiff", "xpdiff", "csdiff"], key="diff_valeur")
 
    with col3:
        temps_diff = st.selectbox("Minute de jeu", options=[10, 15, 20, 25], index=1, key="diff_temps")
 
    with col4:
        year_choice_diff = st.selectbox("Année", options=["Toutes les années"] + years, key="diff_year")
        year_diff = None if year_choice_diff == "Toutes les années" else year_choice_diff
 
    fig_diff = bar_chart_diff(df, league_diff, valeur_diff, temps_diff, year_diff)
    st.plotly_chart(fig_diff, use_container_width=True)
 
    st.caption("Seules les équipes ayant disputé au moins 5 games sont affichées.")
 
    st.divider()
 
    # --- Comparaison des objectifs entre équipes ---
 
    st.subheader("Comparaison des objectifs entre équipes")
 
    col1, col2, col3 = st.columns(3)
 
    with col1:
        team1 = st.selectbox("Équipe", options=equipes, key="team_1")
 
    with col2:
        mode_team = st.radio(
            "Comparer à",
            options=["Moyenne de la ligue", "Une autre équipe"],
            horizontal=True,
            key="team_mode",
        )
 
    with col3:
        year_choice_team = st.selectbox("Année", options=["Toutes les années"] + years, key="team_year")
        year_team = None if year_choice_team == "Toutes les années" else year_choice_team
 
    team2 = None
    if mode_team == "Une autre équipe":
        autres_equipes = [e for e in equipes if e != team1]
        team2 = st.selectbox("Équipe à comparer", options=autres_equipes, key="team_2")
 
    fig_team = bar_chart_team(df, team1, team2, year_team)
    st.plotly_chart(fig_team, use_container_width=True)
 
    st.divider()
 
    # --- Winrate par champion pour un joueur ---
 
    st.subheader("Winrate par champion")
 
    col1, col2 = st.columns(2)
 
    with col1:
        player_champion = st.selectbox("Joueur", options=joueurs, key="champion_player")
 
    with col2:
        year_choice_champion = st.selectbox("Année", options=["Toutes les années"] + years, key="champion_year")
        year_champion = None if year_choice_champion == "Toutes les années" else year_choice_champion
 
    fig_champion = winrate_player_champion(df, player_champion, year_champion)
    st.plotly_chart(fig_champion, use_container_width=True)
 
    st.caption("Top 10 des champions les plus joués (au moins 3 games) par ce joueur.")
 
    st.divider()
 
    # --- Face à face entre deux équipes ---
 
    st.subheader("Face à face entre deux équipes")
 
    col1, col2 = st.columns(2)
 
    with col1:
        team1_h2h = st.selectbox("Équipe 1", options=equipes, key="h2h_team_1")
 
    with col2:
        autres_equipes_h2h = [e for e in equipes if e != team1_h2h]
        team2_h2h = st.selectbox("Équipe 2", options=autres_equipes_h2h, key="h2h_team_2")
 
    resume_h2h, df_h2h = head_to_head_team(df, team1_h2h, team2_h2h)
 
    if resume_h2h is None:
        st.info(f"{team1_h2h} et {team2_h2h} ne se sont jamais affrontées.")
    else:
        st.markdown(
            f"#### {resume_h2h['team1']} **{resume_h2h['win1']}** — **{resume_h2h['win2']}** {resume_h2h['team2']} "
            f"({resume_h2h['winrate1']}% — {resume_h2h['winrate2']}%)"
        )
        st.dataframe(df_h2h, use_container_width=True)
 
    st.divider()
 
    # --- Évolution d'une équipe au fil des années ---
 
    st.subheader("Évolution d'une équipe au fil des années")
 
    stats_evolution_team = ["Winrate", "Taux first blood", "Taux first dragon", "Part dragon",
                             "Taux first nashor", "Part nashor", "Taux first tower", "Part tower",
                             "Taux first herald"]
 
    col1, col2 = st.columns(2)
 
    with col1:
        team_evolution = st.selectbox("Équipe", options=equipes, key="evo_team")
 
    with col2:
        stat_evolution_team = st.selectbox("Statistique", options=stats_evolution_team, key="evo_team_stat")
 
    fig_evo_team = evolution_team(df, team_evolution, stat_evolution_team)
    st.plotly_chart(fig_evo_team, use_container_width=True)
 
    st.divider()
 
    # --- Évolution d'un joueur au fil des années ---
 
    st.subheader("Évolution d'un joueur au fil des années")
 
    stats_evolution_joueur = ["Winrate", "KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
                               "Vision / Minute", "Creeps / Minute", "Wards / Minute"]
 
    col1, col2 = st.columns(2)
 
    with col1:
        player_evolution = st.selectbox("Joueur", options=joueurs, key="evo_player")
 
    with col2:
        stat_evolution_joueur = st.selectbox("Statistique", options=stats_evolution_joueur, key="evo_player_stat")
 
    fig_evo_joueur = evolution_joueur(df, player_evolution, stat_evolution_joueur)
    st.plotly_chart(fig_evo_joueur, use_container_width=True)
 
    st.caption("Seules les années avec au moins 5 games jouées par le joueur sont affichées.")