import pandas as pd
import plotly.graph_objects as go
 
from models.esport import (
    stats_joueur,
    winrate_player_champion,
    evolution_joueur,
    bar_chart_winrate_team_data,
    bar_chart_diff_data,
    bar_chart_team_data,
    bar_chart_duree_team_data,
    tableau_stats,
    head_to_head_team,
    details_game_pro,
    evolution_team,
    evolution_winrate_side,
    bar_chart_winrate_side_data,
    cluster_role,
    cluster_all_roles_standardise,
    correlation_pickrate_changements,
    classement_pickrate_champion_role,
    confrontation_stats_winrate_pro,
    classement_buff_nerf_saison,
)

from utils import patch_to_tuple
 
ARTICLES_EQUIPE = {
    "Taux first blood": "du", "Taux first dragon": "du", "Part dragon": "de la",
    "Taux first nashor": "du", "Part nashor": "de la", "Taux first tower": "du",
    "Part tower": "de la", "Taux first herald": "du", "Winrate": "du",
    "Durée de game": "de la",
}
ARTICLES_JOUEUR = {
    "KDA": "du", "Kill Participation": "de la", "Gold / Minute": "des",
    "Damage / Minute": "des", "Vision / Minute": "des", "Creeps / Minute": "des",
    "Wards / Minute": "des", "Winrate": "du",
}
 
 
# ---------------------------------------------------------------------------
# Construction des figures 
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
        hovertemplate=f"<b>{nom1}</b><br>%{{theta}}: %{{customdata}}<extra></extra>",
        mode="lines+markers", marker=dict(size=7), hoveron="points",
        fill="toself", name=nom1,
        line=dict(color="#2a78d6"), fillcolor="rgba(42, 120, 214, 0.35)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=values_2_normalized_closed, theta=labels_closed, customdata=values_2_closed,
        hovertemplate=f"<b>{nom2}</b><br>%{{theta}}: %{{customdata}}<extra></extra>",
        mode="lines+markers", marker=dict(size=7), hoveron="points",
        fill="toself", name=nom2,
        line=dict(color="#eb6834"), fillcolor="rgba(235, 104, 52, 0.35)"
    ))
    fig.update_layout(
        height=520,
        margin=dict(t=90, b=110, l=70, r=70),
        paper_bgcolor="#101B2D",
        plot_bgcolor="#101B2D",
        font=dict(color="#F0E6D2"),
        polar=dict(
            bgcolor="#1E2328",
            radialaxis=dict(showticklabels=False, gridcolor="#785A28", linecolor="#785A28"),
            angularaxis=dict(gridcolor="#785A28", linecolor="#785A28", color="#F0E6D2"),
        ),
        title=dict(text=f"Comparaison des statistiques de {nom1} et {nom2}", x=0.5, xanchor="center", font=dict(color="#F0E6D2")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#F0E6D2")),
        hovermode="closest",
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
 
        couleur_cluster = couleurs[cluster_id % len(couleurs)]
        r, g, b = int(couleur_cluster[1:3], 16), int(couleur_cluster[3:5], 16), int(couleur_cluster[5:7], 16)
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=valeurs_closed, theta=labels_closed, customdata=valeurs_brutes_closed,
            hovertemplate=f"<b>Cluster {cluster_id}</b><br>%{{theta}}: %{{customdata}}<extra></extra>",
            mode="lines+markers", marker=dict(size=7), hoveron="points",
            fill="toself",
            line=dict(color=couleur_cluster), fillcolor=f"rgba({r}, {g}, {b}, 0.35)"
        ))
        fig.update_layout(
            height=420,
            margin=dict(t=70, b=50, l=60, r=60),
            paper_bgcolor="#101B2D",
            plot_bgcolor="#101B2D",
            font=dict(color="#F0E6D2"),
            polar=dict(
                bgcolor="#1E2328",
                radialaxis=dict(showticklabels=False, gridcolor="#785A28", linecolor="#785A28"),
                angularaxis=dict(gridcolor="#785A28", linecolor="#785A28", color="#F0E6D2"),
            ),
            title=dict(text=f"Cluster {cluster_id} ({nb_joueurs} joueurs)", x=0.5, xanchor="center", font=dict(color="#F0E6D2")),
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
 
 
def figure_comparaison_diverging(label, values_1, values_2, team1, team2):
    ecarts = [v1 - v2 for v1, v2 in zip(values_1, values_2)]

    fig = go.Figure(go.Bar(
        x=ecarts,
        y=label,
        orientation="h",
        marker=dict(
            color=ecarts,
            colorscale=[[0, "#eb6834"], [0.5, "#f2f2f2"], [1, "#2a78d6"]],
            cmid=0
        ),
        text=[f"{e:+.1f} pts" for e in ecarts],
        textposition="outside",
        customdata=list(zip(values_1, values_2)),
        hovertemplate=f"<b>%{{y}}</b><br>{team1} : %{{customdata[0]:.2f}}<br>{team2} : %{{customdata[1]:.2f}}<br>Écart : %{{x:+.1f}} pts<extra></extra>"
    ))
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(
        title=dict(text=f"{team1} vs {team2} — écart par objectif", x=0.5, xanchor="center"),
        xaxis_title=f"Écart ({team1} − {team2}, en points de %)",
        yaxis_title="",
        showlegend=False
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
        xaxis_title="Année", xaxis=dict(dtick=1), 
        yaxis_title=stat, yaxis=dict(range=[0, 100]) if stat != "Durée de game" else {}
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

def figure_tableau_stat(df, stat):
    est_diff = "diff" in stat.lower()

    if est_diff:
        marker = dict(
            color=df[stat],
            colorscale=[[0, "#c0392b"], [0.5, "#e8e8e8"], [1, "#0d366b"]],
            cmid=0,
            showscale=False,
        )
    else:
        marker = dict(
            color=df[stat],
            colorscale=[[0, "#cde2fb"], [1, "#0d366b"]],
            showscale=False,
        )

    fig = go.Figure(go.Bar(
        x=df["playername"],
        y=df[stat],
        marker=marker,
        hovertemplate=f"<b>%{{x}}</b><br>{stat} : %{{y}}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"{stat} par joueur", x=0.5, xanchor="center"),
        xaxis_title="Joueur",
        yaxis_title=stat
    )

    if est_diff:
        fig.add_hline(y=0, line_color="rgba(0,0,0,0.3)", line_width=1)

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
    table = df_winrate[["champion", "nb_played", "winrate"]].reset_index(drop=True)
    return {"fig": fig, "table": table}
 
 
def get_winrate_team(df, ligue):
    df_winrate = bar_chart_winrate_team_data(df, ligue)
    fig = figure_winrate_team(df_winrate, ligue)
    return {"fig": fig}


def figure_winrate_side(df_winrate, league):
    df_blue = df_winrate[df_winrate["side"] == "Blue"]
    df_red = df_winrate[df_winrate["side"] == "Red"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_blue["teamname"], y=df_blue["winrate"], name="Blue Side",
        marker_color="#2a78d6", customdata=df_blue["nb_played"],
        hovertemplate="<b>%{x}</b><br>Blue Side winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=df_red["teamname"], y=df_red["winrate"], name="Red Side",
        marker_color="#e34948", customdata=df_red["nb_played"],
        hovertemplate="<b>%{x}</b><br>Red Side winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Winrate par side des équipes de la ligue : {league}", x=0.5, xanchor="center"),
        xaxis_title="Equipe", yaxis_title="Winrate", yaxis=dict(range=[0, 100]),
        barmode="group",
    )
    return fig


def get_winrate_side(df, ligue):
    df_winrate = bar_chart_winrate_side_data(df, ligue)
    fig = figure_winrate_side(df_winrate, ligue)
    return {"fig": fig}

def figure_duree_team(df_duree, league):
    fig = go.Figure(go.Bar(
        x=df_duree["teamname"], y=df_duree["duree_moyenne"], customdata=df_duree["nb_played"],
        marker=dict(color=df_duree["duree_moyenne"], colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]),
        hovertemplate="<b>%{x}</b><br>Durée moyenne : %{y} min<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Durée moyenne des games — {league}", x=0.5, xanchor="center"),
        xaxis_title="Equipe", yaxis_title="Durée (minutes)"
    )
    return fig


def get_duree_team(df, ligue):
    df_duree = bar_chart_duree_team_data(df, ligue)
    fig = figure_duree_team(df_duree, ligue)
    return {"fig": fig}
 
 
def get_diff(df, ligue, valeur, temps):
    df_diff = bar_chart_diff_data(df, ligue, valeur, temps)
    fig = figure_diff(df_diff, valeur, temps)
    return {"fig": fig}
 
 
def get_comparaison_equipes(df, team1, team2=None):
    label, values_1, values_2, nom_2 = bar_chart_team_data(df, team1, team2)
    fig = figure_comparaison_diverging(label, values_1, values_2, team1, nom_2)
    return {"fig": fig}
 
 
def get_tableau_stats(df, role, ligue, tri):
    resultat = tableau_stats(df, role, ligue, tri)
    fig = figure_tableau_stat(resultat, tri)

    return resultat, fig
 
 
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
 
 
def figure_bar_details_game_pro(df, stat, label_axe, couleurs):
    fig = go.Figure(go.Bar(
        x=df[stat],
        y=df["champion"],
        orientation="h",
        marker=dict(color=couleurs),
        customdata=df[["kills", "deaths", "assists", "CS"]],
        hovertemplate=f"<b>%{{y}}</b><br>{label_axe} : %{{x}}<br>KDA : %{{customdata[0]}}/%{{customdata[1]}}/%{{customdata[2]}}<br>CS : %{{customdata[3]}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=label_axe, x=0.5, xanchor="center"),
        xaxis_title=label_axe,
        yaxis_title="Champions"
    )
    return fig


def figure_scatter_details_game_pro(df, couleurs):
    fig = go.Figure(go.Scatter(
        mode="markers",
        x=df["Or gagne"],
        y=df["Degats aux champions"],
        text=df["champion"],
        textposition="top center",
        marker=dict(color=couleurs),
        customdata=df["champion"],
        hovertemplate="<b>Champion : %{customdata}</b><br>Or gagn\u00e9 : %{x}<br><br>D\u00e9g\u00e2ts aux champions : %{y}<br><extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Or gagn\u00e9 vs D\u00e9g\u00e2ts aux champions", x=0.5, xanchor="center"),
        xaxis_title="Or",
        yaxis_title="D\u00e9g\u00e2ts"
    )
    return fig


def get_details_game_pro(df, gameid):
    blue_side, red_side = details_game_pro(df, gameid)

    for cote in (blue_side, red_side):
        cote["Kill Participation"] = ((cote["kills"] + cote["assists"]) / cote["teamkills"] * 100).round(2)
        cote["Pourcentage de degats"] = (cote["damageshare"] * 100).round(2)

    renommage = {
        "playername": "Joueur",
        "position": "Role",
        "earnedgold": "Or gagne",
        "damagetochampions": "Degats aux champions",
        "total cs": "CS",
    }
    blue_side = blue_side.rename(columns=renommage)
    red_side = red_side.rename(columns=renommage)

    equipe_bleue = blue_side["teamname"].iloc[0]
    equipe_rouge = red_side["teamname"].iloc[0]
    victoire = equipe_bleue if blue_side["result"].iloc[0] else equipe_rouge

    duree = blue_side["gamelength"].iloc[0]
    duree_game = f"{int(duree // 60)}m{int(duree % 60)}s"

    colonne_detail = ["Joueur", "champion", "Role", "kills", "deaths", "assists", "Or gagne", "Degats aux champions", "CS"]

    df_scoreboard = pd.concat([blue_side, red_side])
    couleurs = df_scoreboard["side"].map({"Blue": "#2a78d6", "Red": "#c0392b"})

    fig1 = figure_bar_details_game_pro(df_scoreboard, "Degats aux champions", "Degats aux champions", couleurs)
    fig2 = figure_bar_details_game_pro(df_scoreboard, "Or gagne", "Or gagne", couleurs)
    fig3 = figure_scatter_details_game_pro(df_scoreboard, couleurs)
    fig4 = figure_bar_details_game_pro(df_scoreboard, "Kill Participation", "Kill Participation", couleurs)
    fig5 = figure_bar_details_game_pro(df_scoreboard, "Pourcentage de degats", "Pourcentage de degats", couleurs)

    return {
        "equipe_bleue": equipe_bleue,
        "equipe_rouge": equipe_rouge,
        "victoire": victoire,
        "duree_game": duree_game,
        "blue_side": blue_side[colonne_detail],
        "red_side": red_side[colonne_detail],
        "fig1": fig1, "fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5,
    }


def get_evolution_equipe(df_all, team, stat):
    evo = evolution_team(df_all, team, stat)
    fig = figure_evolution_team(evo, team, stat)
    return {"fig": fig}

def figure_evolution_winrate_side(evo, team):
    df_blue = evo[evo["side"] == "Blue"]
    df_red = evo[evo["side"] == "Red"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_blue["year"], y=df_blue["winrate"], mode="lines+markers", name="Blue Side",
        line=dict(color="#2a78d6"), customdata=df_blue["nb_played"],
        hovertemplate="<b>%{x}</b><br>Blue Side winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_red["year"], y=df_red["winrate"], mode="lines+markers", name="Red Side",
        line=dict(color="#e34948"), customdata=df_red["nb_played"],
        hovertemplate="<b>%{x}</b><br>Red Side winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Évolution du winrate Blue/Red Side — {team}", x=0.5, xanchor="center"),
        xaxis_title="Année", yaxis_title="Winrate", yaxis=dict(range=[0, 100]),
        xaxis=dict(dtick=1, tickformat="d"),
    )
    return fig


def get_evolution_winrate_side(df, team):
    evo = evolution_winrate_side(df, team)
    fig = figure_evolution_winrate_side(evo, team)
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

COULEURS_SCORE = {"Buff net": "#2a78d6", "Nerf net": "#e34948", "Neutre": "#898781"}

def get_patchs_changements(df_matchs, df_champions, df_spells, league, role=None):
    df_correlation = correlation_pickrate_changements(df_matchs, df_champions, df_spells, league, role)
    return sorted(df_correlation["patch"].unique(), key=patch_to_tuple)


def figure_correlation_pickrate(df_patch):
    df = df_patch.copy()
    df["categorie"] = df["score"].apply(lambda s: "Buff net" if s > 0 else ("Nerf net" if s < 0 else "Neutre"))
    df = df.sort_values("delta_pickrate")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["delta_pickrate"], y=df["champion"], orientation="h",
        marker=dict(color=[COULEURS_SCORE[c] for c in df["categorie"]]),
        customdata=df[["score", "pickrate_avant", "pickrate_apres"]],
        hovertemplate=(
            "<b>%{y}</b><br>Score buff/nerf : %{customdata[0]}<br>"
            "Pickrate : %{customdata[1]}%% → %{customdata[2]}%% (Δ%{x:+.2f} pt)<extra></extra>"
        ),
        showlegend=False,
    ))
    for categorie, couleur in COULEURS_SCORE.items():
        fig.add_trace(go.Bar(x=[None], y=[None], marker=dict(color=couleur), name=categorie, showlegend=True))

    fig.update_layout(
        xaxis_title="Delta pickrate (points de %)", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["champion"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_correlation_pickrate(df_matchs, df_champions, df_spells, league, patch, role=None):
    df_correlation = correlation_pickrate_changements(df_matchs, df_champions, df_spells, league, role)
    df_patch = df_correlation[df_correlation["patch"] == patch].sort_values("delta_pickrate", key=abs, ascending=False)
    fig = figure_correlation_pickrate(df_patch)
    return {"fig": fig, "table": df_patch}

def figure_classement_pickrate(df_classement):
    df = df_classement.sort_values("pickrate")
    fig = go.Figure(go.Bar(
        x=df["pickrate"], y=df["champion"], orientation="h",
        marker=dict(color="#2a78d6"),
        customdata=df[["nb_picks"]],
        hovertemplate="<b>%{y}</b><br>Pickrate : %{x}%% (%{customdata[0]} picks)<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Pickrate (%)", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["champion"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_classement_pickrate(df, league=None, role=None, top_n=10):
    df_classement = classement_pickrate_champion_role(df, league, role, top_n)
    fig = figure_classement_pickrate(df_classement)
    return {"fig": fig, "table": df_classement}


def figure_confrontation_stats_winrate(df):
    fig = go.Figure(go.Scatter(
        x=df["indice_stats"], y=df["winrate"],
        mode="markers+text",
        text=df["name"], textposition="top center",
        marker=dict(
            size=df["nb_played"], sizemode="area",
            sizeref=2. * df["nb_played"].max() / (40. ** 2), sizemin=4,
            color=df["winrate"], colorscale=[[0, "#eb6834"], [0.5, "#f2f2f2"], [1, "#2a78d6"]], cmid=50,
            showscale=True, colorbar=dict(title="Winrate"),
        ),
        customdata=df[["nb_played"]],
        hovertemplate="<b>%{text}</b><br>Indice stats (z-score) : %{x:.2f}<br>Winrate pro : %{y:.1f}%<br>Games : %{customdata[0]}<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="gray")
    fig.add_vline(x=0, line_dash="dot", line_color="gray")
    fig.update_layout(
        title=dict(text="Stats de base vs winrate réel en pro", x=0.5, xanchor="center"),
        xaxis_title="Indice de stats brutes (z-score moyen HP / Armor / Magic Resist / AD, niveau 18)",
        yaxis_title="Winrate pro (%)",
    )
    return fig


def get_confrontation_stats_winrate(df_champions, df_esport, patch, role=None, league=None, min_games=5):
    df = confrontation_stats_winrate_pro(df_champions, df_esport, patch, role=role, league=league, min_games=min_games)
    fig = figure_confrontation_stats_winrate(df) if not df.empty else None
    return {"fig": fig, "table": df}


def figure_classement_buff_nerf_saison(df_classement):
    df = df_classement.sort_values("score")
    fig = go.Figure(go.Bar(
        x=df["score"], y=df["name"], orientation="h",
        marker=dict(color=df["score"], colorscale=[[0, "#e34948"], [0.5, "#f2f2f2"], [1, "#2a78d6"]], cmid=0),
        customdata=df[["nb_buffs", "nb_nerfs", "nb_patchs_touches"]],
        hovertemplate="<b>%{y}</b><br>Buffs : %{customdata[0]} / Nerfs : %{customdata[1]} (sur %{customdata[2]} patchs)<br>Score net : %{x}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(
        xaxis_title="Score net (buffs - nerfs)", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["name"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 28 * len(df)),
    )
    return fig


def get_classement_buff_nerf_saison(df_champions, df_spells, season="16", top_n=15):
    table = classement_buff_nerf_saison(df_champions, df_spells, season=season, top_n=top_n)
    fig = figure_classement_buff_nerf_saison(table) if not table.empty else None
    return {"fig": fig, "table": table}