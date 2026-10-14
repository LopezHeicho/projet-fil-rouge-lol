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
    details_game,
    stat_par_role,
    bilan_par_side_joueur,
    recap_multikills_joueur,
    profil_objectifs_joueur,
    habitudes_jeu_joueur,
    habitudes_jeu_joueur_heatmap,
    nombre_game_dispo,
    items_achetes_joueur,
    classement_pickrate_champion,
    classement_winrate_champion,
    impact_patch_pickrate_joueur,
    impact_patch_items_joueur,
    impact_patch_performance_joueur,
    classement_bans_champion,
    runes_favorites_joueur,
    profil_combat_joueur,
    matchups_champion,
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
        title=dict(text=f"Comparaison des statistiques de {nom1} et {nom2} sur la saison {season}", x=0.5, xanchor="center", font=dict(color="#F0E6D2")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#F0E6D2")),
        hovermode="closest",
    )
    return fig
 
 
def get_stats_joueur(df, player_name_1, player_name_2=None, position=None, season="16", queue_id=420,
                      df_esport=None, comparer_pro=False, pro_player=None, ligue_pro=None):
    resultat = calc_stats_joueur(
        df, player_name_1, player_name_2, position, season, queue_id,
        df_esport=df_esport, comparer_pro=comparer_pro, pro_player=pro_player, ligue_pro=ligue_pro,
    )
    if resultat is None:
        return {"fig": None, "erreur": "Rang non disponible : aucune game avec un rang solo/duo connu pour ce joueur."}

    labels, values_1, values_2, nom_2 = resultat
    fig = figure_stats_joueur(labels, values_1, values_2, player_name_1, nom_2, season)
    return {"fig": fig, "erreur": None}

def get_nombre_games(df, player, season="16", queue_id=420):
    return nombre_game_dispo(df, player, season=season, queue_id=queue_id)
 
 
def get_historique(df, player, nombre_game=5, season="16", queue_id=420):
    return historique_joueur(df, player, nombre_game=nombre_game, season=season, queue_id=queue_id)

def figure_bar_details_game(df, stat, couleurs, opacites=1):
    fig = go.Figure(go.Bar(
        x=df[stat],
        y=df["Champion"],
        orientation="h",
        marker=dict(color=couleurs, opacity=opacites),
        customdata=df[["kda", "CS"]],
        hovertemplate=f"<b>%{{y}}</b><br>{stat} : %{{x}}<br>KDA : %{{customdata[0]}}<br>CS : %{{customdata[1]}}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=stat, x=0.5, xanchor="center"),
        xaxis_title=stat,
        yaxis_title="Champions"
    )

    return fig

def figure_scatter_details_game(df, couleurs, opacites=1):
    fig = go.Figure(go.Scatter(
        mode="markers",
        x=df["Or gagné"],
        y=df["Dégats aux champions"],
        text=df["Champion"],
        textposition="top center",
        marker=dict(color=couleurs, opacity=opacites),
        customdata=df["Champion"],
        hovertemplate="<b>Champion : %{customdata}</b><br>Or gagné : %{x}<br><br>Dégats aux champions : %{y}<br><extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Or gagné vs Dégâts aux champions", x=0.5, xanchor="center"),
        xaxis_title="Or",
        yaxis_title="Dégats"
    )

    return fig



def get_details_game(df, df_items, match_id, joueur):
    blue_side, red_side = details_game(df, df_items, match_id)

    blue_side = blue_side.rename(columns={
        "riotIdGameName": "Pseudo",
        "championName": "Champion",
        "position": "Role",
        "goldEarned": "Or gagné",
        "totalDamageDealtToChampions": "Dégats aux champions", 
        "totalMinionsKilled": "CS",
        "teamDamagePercentage": "Pourcentage de dégats"
    })

    red_side = red_side.rename(columns={
        "riotIdGameName": "Pseudo",
        "championName": "Champion",
        "position": "Role",
        "goldEarned": "Or gagné",
        "totalDamageDealtToChampions": "Dégats aux champions", 
        "totalMinionsKilled": "CS",
        "teamDamagePercentage": "Pourcentage de dégats"
    })

    victoire = "Blue" if blue_side["win"].iloc[0] else "Red"
    duree_game = blue_side["gameDurationMinute"].iloc[0]
    colonne_detail = ["Pseudo", "Champion", "Role", "kills", "deaths", "assists", "Or gagné", "Dégats aux champions", "CS"]
    colonne_item = ["Pseudo", "item0", "item1", "item2", "item3" ,"item4", "item5", "item6"]

    df_scoreboard = pd.concat([blue_side, red_side])

    couleurs = df_scoreboard["side"].map({"Blue": "#2a78d6", "Red":"#c0392b"})
    opacites = df_scoreboard["Pseudo"].apply(lambda nom: 1.0 if nom == joueur else 0.4)

    fig1 = figure_bar_details_game(df_scoreboard, "Dégats aux champions", couleurs, opacites)
    fig2 = figure_bar_details_game(df_scoreboard, "Or gagné", couleurs, opacites)
    fig3 = figure_scatter_details_game(df_scoreboard, couleurs, opacites)
    fig4 = figure_bar_details_game(df_scoreboard, "killParticipation", couleurs, opacites)
    fig5 = figure_bar_details_game(df_scoreboard, "Pourcentage de dégats", couleurs, opacites)

    return blue_side[colonne_detail], red_side[colonne_detail], blue_side[colonne_item], red_side[colonne_item], fig1, fig2, fig3, fig4, fig5, victoire, duree_game

def figure_bar_stack_stat_role(df_role, player, season):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_role["Role"], y=df_role["victory"], name="Victoires", marker_color="#2a78d6",
        customdata=df_role["Nombre game"], hovertemplate="<b>%{x}</b><br>Victoires : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=df_role["Role"], y=df_role["Nombre game"] - df_role["victory"], name="Défaites", marker_color="#c0392b",
        customdata=df_role["Nombre game"], hovertemplate="<b>%{x}</b><br>Défaites : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Victoires/Défaites par rôle de {player}", x=0.5, xanchor="center"), barmode="stack",
        xaxis_title="Rôle", yaxis_title="Nombre de parties", yaxis=dict(range=[0, max(df_role["Nombre game"]) + 10])
    )
    return fig

def figure_scatter_stat_role(df_role, player, season):
    couleurs_role = {
        "top": "#2a78d6",
        "jng": "#eb6834",
        "mid": "#1baf7a",
        "bot": "#eda100",
        "sup": "#e87ba4",
    }
    fig = go.Figure(go.Scatter(
        mode="markers+text",textposition="top center",x=df_role["Gold / Minute"], y=df_role["Damage / Minute"], text=df_role["Role"],
        marker=dict(color=df_role["Role"].map(couleurs_role)), customdata=df_role[ "Nombre game"],
        hovertemplate="<b>%{text}</b><br>Gold / Minute : %{x}<br>Damage / Minute : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Gold / Minute vs Damage / Minute par rôle de {player}", x=0.5, xanchor="center"),
        xaxis_title="Gold / Minute", yaxis_title="Damage / Minute"
    )
    return fig

def get_stat_role(df, player, season="16", queue_id=420):
    df_role = stat_par_role(df, player, season=season, queue_id=queue_id)
    if df_role.empty:
        return df_role, None, None
    
    fig1 = figure_bar_stack_stat_role(df_role, player, season)

    fig2 = figure_scatter_stat_role(df_role, player, season)

    return df_role, fig1, fig2
 
def figure_bilan_side(df_side, player, season):
    couleurs_victoire = df_side["side"].map({"Bleu": "#2a78d6", "Rouge":"#c0392b"})
    couleurs_defaite = df_side["side"].map({"Bleu": "#cde2fb", "Rouge":"#f5d4d1"})
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_side["side"], y=df_side["victoires"], name="Victoires", marker_color=couleurs_victoire,
        customdata=df_side["Nombre game"], hovertemplate="<b>%{x}</b><br>Victoires : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=df_side["side"], y=df_side["Nombre game"] - df_side["victoires"], name="Défaites", marker_color=couleurs_defaite,
        customdata=df_side["Nombre game"], hovertemplate="<b>%{x}</b><br>Défaites : %{y}<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Victoires/Défaites par côté de {player}", x=0.5, xanchor="center"), barmode="stack",
        xaxis_title="Côté", yaxis_title="Nombre de parties", yaxis=dict(range=[0, max(df_side["Nombre game"]) + 10]), showlegend=False
    )
    return fig

def get_bilan_side(df, player, season="16", queue_id=420):
    df_side = bilan_par_side_joueur(df, player, season=season, queue_id=queue_id)
    if df_side.empty:
        return df_side, None
    
    fig= figure_bilan_side(df_side, player, season)

    return df_side, fig
 
def get_habitudes(df, player, season="16", queue_id=420):
    par_moment, par_jour = habitudes_jeu_joueur(df, player, season=season, queue_id=queue_id)
    return {"par_moment": par_moment, "par_jour": par_jour}

def figure_heatmap_habitudes(grille, grille_nb, player):
    texte = grille.map(lambda v: "" if pd.isna(v) else f"{v:.0f}%")
    nb_affiche = grille_nb.map(lambda v: "0" if pd.isna(v) else f"{int(v)}")

    fig = go.Figure(go.Heatmap(
        z=grille.values,
        x=grille.columns,
        y=grille.index,
        customdata=nb_affiche.values,
        colorscale="RdYlGn",
        zmin=0, zmax=100,
        text=texte.values,
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate="%{y} - %{x}<br>Winrate : %{text}<br>Games jouées : %{customdata}<extra></extra>"
    ))
    fig.update_layout(title=dict(text=f"Winrate par jour et moment de la journée de {player}", x=0.5, xanchor="center"))
    return fig

def get_habitudes_heatmap(df, player, season="16", queue_id=420):
    grille, grille_nb = habitudes_jeu_joueur_heatmap(df, player, season=season, queue_id=queue_id)
    fig = figure_heatmap_habitudes(grille, grille_nb, player)
    return fig

def figure_multikills(serie, player):
    serie = serie.loc[["Pentakills", "Quadrakills", "Triplekills", "Doublekills"]]
    fig = go.Figure(go.Bar(
        x=serie.index.map({"Pentakills": "Penta", "Quadrakills": "Quadra", "Triplekills": "Triple", "Doublekills": "Double"}),
        y=serie.values,
        text=serie.values,
        textposition="outside",
        marker=dict(color=serie.values, colorscale=[[0, "#cde2fb"], [1, "#0d366b"]]),
        hovertemplate="<b>%{x}</b><br>Nombre : %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"Récapitulatif des multikills de {player}", x=0.5, xanchor="center"),
        xaxis_title="Type de multikill", yaxis_title="Nombre",
        yaxis=dict(range=[0, max(serie.values) * 1.15])
    )
    return fig

def get_multikills(df, player, season="16", queue_id=420):
    serie = recap_multikills_joueur(df, player, season=season, queue_id=queue_id)
    table = serie.reset_index().rename(columns={"index": "Statistique", "Récap multikills": "Valeur"})
    if serie.empty:
        return serie,table, None
    
    fig = figure_multikills(serie, player)

    return serie, table, fig
    
def figure_objectifs(table, player, colonne_moyenne):
    table = table.copy()
    table["ecart_pct"] = ((table[player] - table[colonne_moyenne]) / table[colonne_moyenne] * 100).round(1)

    fig = go.Figure(go.Bar(
        x=table["ecart_pct"],
        y=table["Statistique"],
        orientation="h",
        marker=dict(
            color=table["ecart_pct"],
            colorscale=[[0, "#c0392b"], [0.5, "#f2f2f2"], [1, "#2a5d9f"]],
            cmid=0
        ),
        text=table["ecart_pct"].map(lambda v: f"{v:+.1f}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Écart : %{x:+.1f}%<extra></extra>"
    ))
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(
        title=dict(text=f"Écart à la moyenne de rang de {player}", x=0.5, xanchor="center"),
        xaxis_title="Écart par rapport à la moyenne (%)",
        yaxis_title="",
        showlegend=False
    )
    return fig
 
def get_objectifs(df, player, role=None, season="16", queue_id=420):
    table = profil_objectifs_joueur(df, player, role=role, season=season, queue_id=queue_id)
    if table.empty:
        return table, None

    colonne_moyenne = [c for c in table.columns if c.startswith("Moyenne")][0]
    fig = figure_objectifs(table, player, colonne_moyenne)
    return table, fig
 
 
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
 
 
COULEURS_WINRATE = {"Faible (<45%)": "#e34948", "Moyen (45-55%)": "#898781", "Fort (>55%)": "#2a78d6"}

def _categorie_winrate(valeur):
    if valeur < 45:
        return "Faible (<45%)"
    elif valeur <= 55:
        return "Moyen (45-55%)"
    return "Fort (>55%)"


def figure_builds(df_build):
    df = df_build.copy()
    df["categorie"] = df["Winrate (%)"].apply(_categorie_winrate)
    df = df.sort_values("Nombre de games")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Nombre de games"], y=df["Item"], orientation="h",
        marker=dict(color=[COULEURS_WINRATE[c] for c in df["categorie"]]),
        customdata=df[["Winrate (%)", "% des games"]],
        hovertemplate="<b>%{y}</b><br>%{x} games (%{customdata[1]}%% des games)<br>Winrate : %{customdata[0]}%%<extra></extra>",
        showlegend=False,
    ))
    for categorie, couleur in COULEURS_WINRATE.items():
        fig.add_trace(go.Bar(x=[None], y=[None], marker=dict(color=couleur), name=categorie, showlegend=True))

    fig.update_layout(
        xaxis_title="Nombre de games", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["Item"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_builds(df, df_items, player, champion, season="16", queue_id=420, min_games=2):
    table = builds_frequents_champion(df, df_items, player, champion, season=season, queue_id=queue_id, min_games=min_games)
    fig = figure_builds(table) if not table.empty else None
    return {"fig": fig, "table": table}
 
 
def get_meilleurs_items(df, df_items, champion, role, rang=None, season="16", queue_id=420, min_games=10):
    table = meilleurs_items_champion_role(df, df_items, champion, role, rang=rang, season=season, queue_id=queue_id, min_games=min_games)
    fig = figure_builds(table) if not table.empty else None
    return {"fig": fig, "table": table}


def figure_classement_pickrate_champion(df_classement):
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


def get_classement_pickrate_champion(df, role=None, rang=None, season="16", queue_id=420, top_n=15):
    df_classement = classement_pickrate_champion(df, role=role, rang=rang, season=season, queue_id=queue_id, top_n=top_n)
    fig = figure_classement_pickrate_champion(df_classement) if not df_classement.empty else None
    return {"fig": fig, "table": df_classement}


def figure_classement_winrate_champion(df_classement):
    df = df_classement.sort_values("winrate")
    fig = go.Figure(go.Bar(
        x=df["winrate"], y=df["champion"], orientation="h",
        marker=dict(color=df["winrate"], colorscale=[[0, "#eb6834"], [0.5, "#f2f2f2"], [1, "#2a78d6"]], cmid=50),
        customdata=df[["nb_played"]],
        hovertemplate="<b>%{y}</b><br>Winrate : %{x}%% (%{customdata[0]} games)<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Winrate (%)", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["champion"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_classement_winrate_champion(df, role=None, rang=None, season="16", queue_id=420, min_games=20, top_n=15):
    df_classement = classement_winrate_champion(df, role=role, rang=rang, season=season, queue_id=queue_id, min_games=min_games, top_n=top_n)
    fig = figure_classement_winrate_champion(df_classement) if not df_classement.empty else None
    return {"fig": fig, "table": df_classement}

COULEURS_EFFICACITE = {"Sous-optimal (<80%)": "#e34948", "Correct (80-100%)": "#898781", "Efficace (≥100%)": "#2a78d6"}

def _categorie_efficacite(valeur):
    if valeur < 80:
        return "Sous-optimal (<80%)"
    elif valeur < 100:
        return "Correct (80-100%)"
    return "Efficace (≥100%)"


def figure_items_achetes_joueur(df_classement):
    df = df_classement.copy()
    df["categorie"] = df["efficacite_moyenne"].apply(_categorie_efficacite)
    df = df.sort_values("nb_achats")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["nb_achats"], y=df["name"], orientation="h",
        marker=dict(color=[COULEURS_EFFICACITE[c] for c in df["categorie"]]),
        customdata=df[["efficacite_moyenne"]],
        hovertemplate="<b>%{y}</b><br>%{x} achats<br>Efficacité moyenne : %{customdata[0]}%%<extra></extra>",
        showlegend=False,
    ))
    for categorie, couleur in COULEURS_EFFICACITE.items():
        fig.add_trace(go.Bar(x=[None], y=[None], marker=dict(color=couleur), name=categorie, showlegend=True))

    fig.update_layout(
        xaxis_title="Nombre d'achats", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["name"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_items_achetes_joueur(df, df_items, joueur, role=None, season="16", queue_id=420, top_n=15):
    df_classement = items_achetes_joueur(df, df_items, joueur, role=role, season=season, queue_id=queue_id, top_n=top_n)
    fig = figure_items_achetes_joueur(df_classement)
    return {"fig": fig, "table": df_classement}
 
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


# ---------------------------------------------------------------------------
# Impact des changements de patch sur le jeu d'un joueur
# ---------------------------------------------------------------------------

def figure_impact_patch(df, colonne_delta, colonne_avant, colonne_apres, label_col, titre, xaxis_title):
    df = df.copy()
    df = df.sort_values(colonne_delta)
    df["label"] = df[label_col] + " (" + df["patch"] + ")"

    fig = go.Figure(go.Bar(
        x=df[colonne_delta], y=df["label"], orientation="h",
        marker=dict(
            color=df[colonne_delta],
            colorscale=[[0, "#e34948"], [0.5, "#f2f2f2"], [1, "#2a78d6"]],
            cmid=0,
        ),
        customdata=df[[colonne_avant, colonne_apres, "nb_buffs", "nb_nerfs"]],
        hovertemplate="<b>%{y}</b><br>Avant : %{customdata[0]}<br>Après : %{customdata[1]}<br>Buffs : %{customdata[2]} / Nerfs : %{customdata[3]}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(
        title=dict(text=titre, x=0.5, xanchor="center"),
        xaxis_title=xaxis_title, yaxis_title=None,
        height=max(300, 28 * len(df)),
    )
    return fig


def get_impact_patch_pickrate(df, df_champions, df_spells, player, season="16", queue_id=420):
    table = impact_patch_pickrate_joueur(df, df_champions, df_spells, player, season=season, queue_id=queue_id)
    fig = None
    if not table.empty:
        fig = figure_impact_patch(
            table, "delta_pickrate", "pickrate_avant", "pickrate_apres", "champion",
            f"Pickrate de {player} avant/après changement de patch", "Δ pickrate (points)",
        )
    return {"fig": fig, "table": table}


def get_impact_patch_items(df, df_items, player, season="16", queue_id=420):
    table = impact_patch_items_joueur(df, df_items, player, season=season, queue_id=queue_id)
    fig = None
    if not table.empty:
        fig = figure_impact_patch(
            table, "delta_frequence", "frequence_avant", "frequence_apres", "item",
            f"Fréquence d'achat de {player} avant/après changement de patch", "Δ fréquence d'achat (points)",
        )
    return {"fig": fig, "table": table}


def get_impact_patch_performance(df, df_champions, df_spells, player, season="16", queue_id=420, min_games=3):
    table = impact_patch_performance_joueur(df, df_champions, df_spells, player, season=season, queue_id=queue_id, min_games=min_games)
    fig = None
    if not table.empty:
        fig = figure_impact_patch(
            table, "delta_winrate", "winrate_avant", "winrate_apres", "champion",
            f"Winrate de {player} avant/après changement de patch", "Δ winrate (points)",
        )
    return {"fig": fig, "table": table}


# ---------------------------------------------------------------------------
# Bans, runes, profil de combat, matchups
# ---------------------------------------------------------------------------

def figure_classement_bans_champion(df_classement):
    df = df_classement.sort_values("ban_rate")
    fig = go.Figure(go.Bar(
        x=df["ban_rate"], y=df["champion"], orientation="h",
        marker=dict(color="#c0392b"),
        customdata=df[["nb_bans"]],
        hovertemplate="<b>%{y}</b><br>Banni dans %{x}%% des phases de ban (%{customdata[0]} bans)<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Taux de ban (%)", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["champion"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_classement_bans_champion(df, df_champions, rang=None, season="16", queue_id=420, top_n=15):
    table = classement_bans_champion(df, df_champions, rang=rang, season=season, queue_id=queue_id, top_n=top_n)
    fig = figure_classement_bans_champion(table) if not table.empty else None
    return {"fig": fig, "table": table}


def figure_runes_joueur(df_runes):
    df = df_runes.copy()
    df["categorie"] = df["Winrate (%)"].apply(_categorie_winrate)
    df = df.sort_values("Nombre de games")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Nombre de games"], y=df["Rune"], orientation="h",
        marker=dict(color=[COULEURS_WINRATE[c] for c in df["categorie"]]),
        customdata=df[["Winrate (%)", "% des games"]],
        hovertemplate="<b>%{y}</b><br>%{x} games (%{customdata[1]}%% des games)<br>Winrate : %{customdata[0]}%%<extra></extra>",
        showlegend=False,
    ))
    for categorie, couleur in COULEURS_WINRATE.items():
        fig.add_trace(go.Bar(x=[None], y=[None], marker=dict(color=couleur), name=categorie, showlegend=True))

    fig.update_layout(
        xaxis_title="Nombre de games", yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=df["Rune"].tolist(), tickmode="linear", dtick=1),
        height=max(300, 32 * len(df)),
    )
    return fig


def get_runes_joueur(df, player, role=None, champion=None, season="16", queue_id=420, top_n=15):
    table = runes_favorites_joueur(df, player, role=role, champion=champion, season=season, queue_id=queue_id, top_n=top_n)
    fig = figure_runes_joueur(table) if not table.empty else None
    return {"fig": fig, "table": table}

def get_combat(df, player, role=None, season="16", queue_id=420):
    table = profil_combat_joueur(df, player, role=role, season=season, queue_id=queue_id)
    if table.empty:
        return table, None
    colonne_moyenne = [c for c in table.columns if c.startswith("Moyenne")][0]
    fig = figure_objectifs(table, player, colonne_moyenne)
    return table, fig


def get_matchups_champion(df, champion, role, rang=None, season="16", queue_id=420, min_games=5, top_n=15):
    table = matchups_champion(df, champion, role, rang=rang, season=season, queue_id=queue_id, min_games=min_games, top_n=top_n)
    fig = figure_classement_winrate_champion(table) if not table.empty else None
    return {"fig": fig, "table": table}