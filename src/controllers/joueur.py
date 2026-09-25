import pandas as pd
import plotly.graph_objects as go
 
from models.joueur import (
    calc_stats_joueur,
    calc_meilleurs_champions,
    best_champion_table,
    builds_frequents_champion,
    meilleurs_items_champion_role,
    calc_evolution_winrate,
    historique_joueur,
    stat_par_role,
    bilan_par_side_joueur,
    recap_multikills_joueur,
    profil_objectifs_joueur,
    habitudes_jeu_joueur,
)
from models.joueur_live import rechercher_et_recuperer, charger_dataset_complet, RechercheJoueurError
 
 
# ---------------------------------------------------------------------------
# Recherche (page d'accueil du module)
# ---------------------------------------------------------------------------
 
def get_recherche(game_name, tag_line, region="europe", count=20, queue=420, season="16"):
    """Lance la recherche live, puis prepare tout ce qu'affiche la premiere
    page (rang, winrate par role, 5 dernieres games). Ne leve jamais
    d'exception : les erreurs (Riot ID introuvable, cle API invalide...)
    reviennent dans la cle "erreur" du dict, a afficher avec st.error."""
    try:
        resultat = rechercher_et_recuperer(game_name, tag_line, region=region, count=count, queue=queue)
    except RechercheJoueurError as exc:
        return {"erreur": str(exc)}
 
    player = resultat["riot_id_game_name"]
    df = charger_dataset_complet()
 
    rang_row = resultat["rang"]
    rang_affiche = None
    if rang_row.get("soloqueue_tier"):
        rang_affiche = f"{rang_row['soloqueue_tier']} {rang_row.get('soloqueue_rank') or ''} — {rang_row.get('soloqueue_lp', 0)} LP".strip()
 
    return {
        "erreur": None,
        "player": player,
        "nb_matchs_recuperes": resultat["nb_matchs_recuperes"],
        "nb_lignes_nouvelles": resultat["nb_lignes_nouvelles"],
        "rang_affiche": rang_affiche,
        "rang_row": rang_row,
        "stat_role": stat_par_role(df, player, season=season, queue_id=queue),
        "historique": historique_joueur(df, player, nombre_game=5, season=season, queue_id=queue),
    }
 
 
# ---------------------------------------------------------------------------
# Onglets "Profil"
# ---------------------------------------------------------------------------
 
def figure_stats_joueur(labels, values_1, values_2, nom1, nom2, season):
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
        hovertemplate="%{theta}: %{customdata}<extra></extra>", hoveron="points",
        fill="toself", name=nom1,
        line=dict(color="#2a78d6"), fillcolor="rgba(42, 120, 214, 0.35)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=values_2_normalized_closed, theta=labels_closed, customdata=values_2_closed,
        hovertemplate="%{theta}: %{customdata}<extra></extra>", hoveron="points",
        fill="toself", name=nom2,
        line=dict(color="#eb6834"), fillcolor="rgba(235, 104, 52, 0.35)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(showticklabels=False)),
        title=dict(text=f"Comparaison des statistiques de {nom1} et {nom2} sur la saison {season}", x=0.5, xanchor="center"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig
 
 
def get_stats_joueur(df, player_name_1, player_name_2=None, position=None, season="16", queue_id=420):
    labels, values_1, values_2, nom_2 = calc_stats_joueur(df, player_name_1, player_name_2, position, season, queue_id)
    fig = figure_stats_joueur(labels, values_1, values_2, player_name_1, nom_2, season)
    return {"fig": fig}
 
 
def get_historique(df, player, nombre_game=5, season="16", queue_id=420):
    return historique_joueur(df, player, nombre_game=nombre_game, season=season, queue_id=queue_id)
 
 
def get_stat_role(df, player, season="16", queue_id=420):
    return stat_par_role(df, player, season=season, queue_id=queue_id)
 
 
def get_bilan_side(df, player, season="16", queue_id=420):
    return bilan_par_side_joueur(df, player, season=season, queue_id=queue_id)
 
 
def get_habitudes(df, player, season="16", queue_id=420):
    par_moment, par_jour = habitudes_jeu_joueur(df, player, season=season, queue_id=queue_id)
    return {"par_moment": par_moment, "par_jour": par_jour}
 
 
def get_multikills(df, player, season="16", queue_id=420):
    serie = recap_multikills_joueur(df, player, season=season, queue_id=queue_id)
    return serie.reset_index().rename(columns={"index": "Statistique", "Récap multikills": "Valeur"})
 
 
def get_objectifs(df, player, role=None, season="16", queue_id=420):
    return profil_objectifs_joueur(df, player, role=role, season=season, queue_id=queue_id)
 
 
# ---------------------------------------------------------------------------
# Onglets "Champions"
# ---------------------------------------------------------------------------
 
def figure_meilleurs_champions(df_winrate, player):
    fig = go.Figure(go.Bar(
        x=df_winrate["championName"], y=df_winrate["winrate"], customdata=df_winrate["nb_played"],
        marker=dict(color=df_winrate["winrate"], colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]),
        hovertemplate="<b>%{x}</b><br>Winrate : %{y}%<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Winrate des champions les plus joués par {player}", x=0.5, xanchor="center"),
        xaxis_title="Champion", yaxis_title="Winrate", yaxis=dict(range=[0, 100])
    )
    return fig
 
 
def get_meilleurs_champions_bar(df, player, nombre=10, season="16", queue_id=420):
    df_winrate = calc_meilleurs_champions(df, player, nombre=nombre, season=season, queue_id=queue_id)
    fig = figure_meilleurs_champions(df_winrate, player)
    return {"fig": fig}
 
 
def get_meilleurs_champions_table(df, player, nombre=10, season="16", queue_id=420):
    return best_champion_table(df, player, nombre=nombre, season=season, queue_id=queue_id)
 
 
def get_builds(df, df_items, player, champion, season="16", queue_id=420, min_games=2):
    return builds_frequents_champion(df, df_items, player, champion, season=season, queue_id=queue_id, min_games=min_games)
 
 
def get_meilleurs_items(df, df_items, champion, role, rang=None, season="16", queue_id=420, min_games=10):
    return meilleurs_items_champion_role(df, df_items, champion, role, rang=rang, season=season, queue_id=queue_id, min_games=min_games)
 
 
# ---------------------------------------------------------------------------
# Onglet "Évolution"
# ---------------------------------------------------------------------------
 
def figure_evolution_winrate(df_winrate, player):
    fig = go.Figure(go.Scatter(
        mode="lines",
        x=df_winrate["annee_semaine"], y=df_winrate["winrate"],
        line=dict(color="#2a78d6"),
        customdata=df_winrate["nb_played"],
        hovertemplate="<br>Winrate : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"Evolution du Winrate (%) de {player} par semaine", x=0.5, xanchor="center"),
        xaxis_title="Année - Semaine", yaxis_title="Winrate", xaxis=dict(dtick=1)
    )
    return fig
 
 
def get_evolution_winrate(df, player, season="16", queue_id=420):
    df_winrate = calc_evolution_winrate(df, player, season=season, queue_id=queue_id)
    fig = figure_evolution_winrate(df_winrate, player)
    return {"fig": fig}