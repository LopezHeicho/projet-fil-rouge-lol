import pandas as pd
import plotly.graph_objects as go
 
from models.esport import (
    stats_joueur,
    winrate_player_champion,
    evolution_joueur,
    bar_chart_winrate_team_data,
    bar_chart_diff_data,
    bar_chart_team_data,
    tableau_stats,
    head_to_head_team,
    evolution_team,
    cluster_role,
    cluster_all_roles_standardise,
)
 
ARTICLES_EQUIPE = {
    "Taux first blood": "du", "Taux first dragon": "du", "Part dragon": "de la",
    "Taux first nashor": "du", "Part nashor": "de la", "Taux first tower": "du",
    "Part tower": "de la", "Taux first herald": "du", "Winrate": "du",
}
ARTICLES_JOUEUR = {
    "KDA": "du", "Kill Participation": "de la", "Gold / Minute": "des",
    "Damage / Minute": "des", "Vision / Minute": "des", "Creeps / Minute": "des",
    "Wards / Minute": "des", "Winrate": "du",
}
 
 
# ---------------------------------------------------------------------------
# Construction des figures (anciennement les _figure_xxx de la view)
# ---------------------------------------------------------------------------
 
def figure_stats_joueur(labels, values_1, values_2, nom1, nom2):
    values_1_normalized, values_2_normalized = [], []
    for v1, v2 in zip(values_1, values_2):
        axis_max = max(v1, v2)
        values_1_normalized.append(v1 / axis_max if axis_max != 0 else 0)
        values_2_normalized.append(v2 / axis_max if axis_max != 0 else 0)
 
    labels_closed = labels + labels[:1]
    values_1_normalized_closed = values_1_normalized + values_1_normalized[:1]
    values_2_normalized_closed = values_2_normalized + values_2_normalized[:1]
    values_1_closed = values_1 + values_1[:1]
    values_2_closed = values_2 + values_2[:1]
 
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_1_normalized_closed, theta=labels_closed, customdata=values_1_closed,
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        fill="toself", name=nom1,
        line=dict(color="#2a78d6"), fillcolor="rgba(42, 120, 214, 0.35)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=values_2_normalized_closed, theta=labels_closed, customdata=values_2_closed,
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        fill="toself", name=nom2,
        line=dict(color="#eb6834"), fillcolor="rgba(235, 104, 52, 0.35)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(showticklabels=False)),
        title=dict(text=f"Comparaison des statistiques de {nom1} et {nom2}", x=0.5, xanchor="center"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig
 
 
def figures_cluster(player_stats, labels, standardise=False):
    cluster_means = player_stats.groupby("cluster")[labels].mean().round(2)
    couleurs = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"]
    labels_closed = labels + labels[:1]
 
    if standardise:
        offset = abs(cluster_means.min().min()) + 0.5
        valeurs_affichees = cluster_means + offset
    else:
        valeurs_affichees = cluster_means / cluster_means.max()
 
    figures = []
    for cluster_id in cluster_means.index:
        valeurs_closed = valeurs_affichees.loc[cluster_id].tolist() + valeurs_affichees.loc[cluster_id].tolist()[:1]
        valeurs_brutes_closed = cluster_means.loc[cluster_id].tolist() + cluster_means.loc[cluster_id].tolist()[:1]
        nb_joueurs = (player_stats["cluster"] == cluster_id).sum()
 
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=valeurs_closed, theta=labels_closed, customdata=valeurs_brutes_closed,
            hovertemplate="%{theta}: %{customdata}<extra></extra>",
            fill="toself",
            line=dict(color=couleurs[cluster_id % len(couleurs)])
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(showticklabels=False)),
            title=dict(text=f"Cluster {cluster_id} ({nb_joueurs} joueurs)", x=0.5, xanchor="center"),
            showlegend=False,
        )
        figures.append(fig)
    return figures
 
 
def figure_winrate_team(df_winrate, league):
    fig = go.Figure(go.Bar(
        x=df_winrate["teamname"], y=df_winrate["winrate"], customdata=df_winrate["nb_played"],
        marker=dict(color=df_winrate["winrate"], colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]),
        hovertemplate="<b>%{x}</b><br>Winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Winrate des équipes de la ligue : {league}", x=0.5, xanchor="center"),
        xaxis_title="Equipe", yaxis_title="Winrate", yaxis=dict(range=[0, 100])
    )
    return fig
 
 
def figure_diff(df_diff, valeur, temps):
    fig = go.Figure(go.Bar(
        x=df_diff["teamname"], y=df_diff["diff"], customdata=df_diff["nb_played"],
        marker=dict(color=df_diff["diff"], colorscale=[[0, "#e34948"], [0.5, "#f0efec"], [1, "#2a78d6"]], line=dict(color="#898781", width=1)),
        hovertemplate=f"<b>%{{x}}</b><br>{valeur} at {temps} : %{{y}} golds<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"{valeur} au bout de {temps} minutes de game", x=0.5, xanchor="center"),
        xaxis_title="Equipe", yaxis_title="Diff"
    )
    return fig
 
 
def figure_bar_team(label, values_1, values_2, team1, nom_2):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=label, y=values_1, name=team1, marker_color="#2a78d6"))
    fig.add_trace(go.Bar(x=label, y=values_2, name=nom_2, marker_color="#eb6834"))
    fig.update_layout(
        barmode="group",
        title=dict(text=f"{team1} vs {nom_2}", x=0.5, xanchor="center"),
        yaxis_title="Pourcentage (%)", xaxis_title="Objectif",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig
 
 
def figure_winrate_champion(df_winrate, player):
    fig = go.Figure(go.Bar(
        x=df_winrate["champion"], y=df_winrate["winrate"], customdata=df_winrate["nb_played"],
        marker=dict(color=df_winrate["winrate"], colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]),
        hovertemplate="<b>%{x}</b><br>Winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Winrate des champions les plus joués par {player}", x=0.5, xanchor="center"),
        xaxis_title="Champion", yaxis_title="Winrate", yaxis=dict(range=[0, 100])
    )
    return fig
 
 
def figure_evolution_team(evo, team, stat):
    fig = go.Figure(go.Scatter(
        mode="lines", x=evo["year"], y=evo[stat], line=dict(color="#2a78d6"),
        customdata=evo["nb_played"],
        hovertemplate=f"{stat} : %{{y}}<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Évolution {ARTICLES_EQUIPE[stat]} {stat} de {team} au cours des années", x=0.5, xanchor="center"),
        xaxis_title="Année", xaxis=dict(dtick=1), yaxis_title=stat, yaxis=dict(range=[0, 100])
    )
    return fig
 
 
def figure_evolution_joueur(evo, player, stat):
    fig = go.Figure(go.Scatter(
        mode="lines", x=evo["year"], y=evo[stat], line=dict(color="#2a78d6"),
        customdata=evo["nb_played"],
        hovertemplate=f"{stat} : %{{y}}<br>Games jouées : %{{customdata}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Évolution {ARTICLES_JOUEUR[stat]} {stat} de {player} au cours des années", x=0.5, xanchor="center"),
        xaxis_title="Année", yaxis_title=stat, xaxis=dict(dtick=1)
    )
    return fig
 
 
# ---------------------------------------------------------------------------
# Orchestration : un get_xxx() par onglet de la view
# ---------------------------------------------------------------------------
 
def get_comparaison_joueurs(df, joueur1, joueur2=None):
    labels, values_1, values_2, nom_2 = stats_joueur(df, joueur1, joueur2)
 
    equipe1 = df[df["playername"] == joueur1]["teamname"].values[0]
    ligue1 = df[df["playername"] == joueur1]["league"].values[0]
    nb_games_1 = df[df["playername"] == joueur1].shape[0]
    winrate_1 = (df[df["playername"] == joueur1]["result"].mean() * 100).round(2)
 
    equipe2, ligue2, nb_games_2, winrate_2 = None, None, None, None
    if joueur2:
        equipe2 = df[df["playername"] == joueur2]["teamname"].values[0]
        ligue2 = df[df["playername"] == joueur2]["league"].values[0]
        nb_games_2 = df[df["playername"] == joueur2].shape[0]
        winrate_2 = (df[df["playername"] == joueur2]["result"].mean() * 100).round(2)
 
    fig = figure_stats_joueur(labels, values_1, values_2, joueur1, nom_2)
 
    df_comparaison = pd.DataFrame({
        "Statistique": labels,
        joueur1: values_1,
        nom_2: values_2,
    })
 
    champions_j1 = winrate_player_champion(df, joueur1)[["champion", "winrate", "nb_played"]]
    champions_j2 = winrate_player_champion(df, joueur2)[["champion", "winrate", "nb_played"]] if joueur2 else None
 
    return {
        "labels": labels,
        "values_1": values_1,
        "values_2": values_2,
        "nom_2": nom_2,
        "equipe1": equipe1, "ligue1": ligue1,
        "equipe2": equipe2, "ligue2": ligue2,
        "nb_games_1": nb_games_1, "winrate_1": winrate_1,
        "nb_games_2": nb_games_2, "winrate_2": winrate_2,
        "fig": fig,
        "df_comparaison": df_comparaison,
        "champions_j1": champions_j1,
        "champions_j2": champions_j2,
    }
 
 
def get_winrate_champion(df, joueur):
    df_winrate = winrate_player_champion(df, joueur)
    fig = figure_winrate_champion(df_winrate, joueur)
    return {"fig": fig}
 
 
def get_winrate_team(df, ligue):
    df_winrate = bar_chart_winrate_team_data(df, ligue)
    fig = figure_winrate_team(df_winrate, ligue)
    return {"fig": fig}
 
 
def get_diff(df, ligue, valeur, temps):
    df_diff = bar_chart_diff_data(df, ligue, valeur, temps)
    fig = figure_diff(df_diff, valeur, temps)
    return {"fig": fig}
 
 
def get_comparaison_equipes(df, team1, team2=None):
    label, values_1, values_2, nom_2 = bar_chart_team_data(df, team1, team2)
    fig = figure_bar_team(label, values_1, values_2, team1, nom_2)
    return {"fig": fig}
 
 
def get_tableau_stats(df, role, ligue, tri):
    return tableau_stats(df, role, ligue, tri)
 
 
def get_head_to_head(df_all, team1, team2):
    resultat = head_to_head_team(df_all, team1, team2)
    if resultat is None:
        return None
    win1, win2, winrate1, winrate2, df_recap_games = resultat
    return {
        "win1": win1, "win2": win2,
        "winrate1": winrate1, "winrate2": winrate2,
        "nb_played": win1 + win2,
        "df_recap_games": df_recap_games,
    }
 
 
def get_evolution_equipe(df_all, team, stat):
    evo = evolution_team(df_all, team, stat)
    fig = figure_evolution_team(evo, team, stat)
    return {"fig": fig}
 
 
def get_evolution_joueur(df_all, joueur, stat):
    evo = evolution_joueur(df_all, joueur, stat)
    fig = figure_evolution_joueur(evo, joueur, stat)
    return {"fig": fig}
 
 
def get_cluster_role(df, role):
    player_stats, labels = cluster_role(df, role)
    figures = figures_cluster(player_stats, labels, standardise=False)
    return {
        "player_stats": player_stats,
        "labels": labels,
        "figures": figures,
        "nb_clusters": player_stats["cluster"].nunique(),
        "nb_joueurs": len(player_stats),
    }
 
 
def get_cluster_all_roles(df):
    all_players, labels = cluster_all_roles_standardise(df)
    figures = figures_cluster(all_players, labels, standardise=True)
    return {
        "all_players": all_players,
        "labels": labels,
        "figures": figures,
        "nb_clusters": all_players["cluster"].nunique(),
        "nb_joueurs": len(all_players),
    }
