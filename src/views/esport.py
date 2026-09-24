import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from models.esport import (
    annees_disponibles,
    charger_donnees_esport,
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

ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}

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
# Construction des figures
# ---------------------------------------------------------------------------

def _figure_stats_joueur(labels, values_1, values_2, nom1, nom2):
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


def _figures_cluster(player_stats, labels, standardise=False):
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


def _figure_winrate_team(df_winrate, league):
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


def _figure_diff(df_diff, valeur, temps):
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


def _figure_bar_team(label, values_1, values_2, team1, nom_2):
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


def _figure_winrate_champion(df_winrate, player):
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


def _figure_evolution_team(evo, team, stat):
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


def _figure_evolution_joueur(evo, player, stat):
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
# Page Streamlit
# ---------------------------------------------------------------------------

ICONES_CATEGORIE = {"Base": "📊", "Cluster": "🧬"}

OPTIONS_MENU = (
    [("Base", f) for f in [
        "stats_joueur", "winrate_player_champion", "evolution_joueur",
        "bar_chart_winrate_team", "bar_chart_diff", "bar_chart_team",
        "tableau_stats", "head_to_head_team", "evolution_team",
    ]]
    + [("Cluster", f) for f in ["cluster_role", "cluster_all_roles_standardise"]]
)

LABELS_MENU = {
    ("Base", "stats_joueur"): "Comparer deux joueurs",
    ("Base", "winrate_player_champion"): "Champions préférés d'un joueur",
    ("Base", "evolution_joueur"): "Évolution d'un joueur",
    ("Base", "bar_chart_winrate_team"): "Winrate des équipes d'une ligue",
    ("Base", "bar_chart_diff"): "Écarts moyens en début de game",
    ("Base", "bar_chart_team"): "Comparer deux équipes (objectifs)",
    ("Base", "tableau_stats"): "Tableau des stats par rôle",
    ("Base", "head_to_head_team"): "Face-à-face entre deux équipes",
    ("Base", "evolution_team"): "Évolution d'une équipe",
    ("Cluster", "cluster_role"): "Profils de joueurs par rôle",
    ("Cluster", "cluster_all_roles_standardise"): "Profils de joueurs tous rôles",
}


def _selectbox_annee(annees, key):
    """Selectbox Année avec une option 'Toutes les années' en plus des annees
    individuelles (la plus recente reste selectionnee par defaut). Retourne
    directement le DataFrame charge, deja concatene si besoin."""
    options = ["Toutes les années"] + annees
    choix = st.selectbox("Année", options=options, index=1, key=key)
    if choix == "Toutes les années":
        return charger_donnees_esport(annees)
    return charger_donnees_esport([choix])


def load_view():
    st.set_page_config(page_title="Analyse Esport", layout="wide")
    st.title("Analyse des matchs pro (Oracle's Elixir)")

    annees = annees_disponibles()

    with st.sidebar:
        st.caption("📊 Base · 🧬 Cluster")
        categorie_active, fonction_active = st.radio(
            "Fonction",
            options=OPTIONS_MENU,
            format_func=lambda o: f"{ICONES_CATEGORIE[o[0]]} {LABELS_MENU[o]}",
            key="radio_menu_esport",
            label_visibility="collapsed",
        )

    # -------------------- fonctions sur une seule annee --------------------
    if fonction_active in (
        "stats_joueur", "winrate_player_champion", "bar_chart_winrate_team",
        "bar_chart_diff", "bar_chart_team", "tableau_stats",
        "cluster_role", "cluster_all_roles_standardise",
    ):
        if fonction_active == "stats_joueur":
            st.subheader("Comparer deux joueurs")

            col1, col2, col3 = st.columns(3)
            with col1:
                df = _selectbox_annee(annees, key="stats_joueur_annee")
            joueurs = sorted(df["playername"].dropna().unique())

            with col2:
                index_defaut_j1 = joueurs.index("Faker") if "Faker" in joueurs else 0
                joueur1 = st.selectbox("Joueur 1", options=joueurs, index=index_defaut_j1, key="stats_joueur_1")
            with col3:
                mode_comp = st.radio("Comparer à", options=["Moyenne de son rôle", "Un autre joueur"], index=1, horizontal=True, key="stats_joueur_mode")

            joueur2 = None
            if mode_comp == "Un autre joueur":
                autres_joueurs = [j for j in joueurs if j != joueur1]
                index_defaut_j2 = autres_joueurs.index("Chovy") if "Chovy" in autres_joueurs else 0
                joueur2 = st.selectbox("Joueur 2", options=autres_joueurs, index=index_defaut_j2, key="stats_joueur_2")

            labels, values_1, values_2, nom_2 = stats_joueur(df, joueur1, joueur2)

            equipe1 = df[df["playername"] == joueur1]["teamname"].values[0]
            ligue1 = df[df["playername"] == joueur1]["league"].values[0]
            if joueur2:
                equipe2 = df[df["playername"] == joueur2]["teamname"].values[0]
                ligue2 = df[df["playername"] == joueur2]["league"].values[0]
                st.caption(f"**{joueur1}** — {equipe1} ({ligue1})  vs  **{joueur2}** — {equipe2} ({ligue2})")
            else:
                st.caption(f"**{joueur1}** — {equipe1} ({ligue1})  vs  {nom_2}")

            nb_games_1 = df[df["playername"] == joueur1].shape[0]
            winrate_1 = (df[df["playername"] == joueur1]["result"].mean() * 100).round(2)

            if joueur2:
                nb_games_2 = df[df["playername"] == joueur2].shape[0]
                winrate_2 = (df[df["playername"] == joueur2]["result"].mean() * 100).round(2)

                col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
                with col_m1:
                    st.metric(f"KDA {joueur1}", values_1[labels.index("KDA")])
                with col_m2:
                    st.metric(f"Winrate {joueur1}", f"{winrate_1}%")
                with col_m3:
                    st.metric(f"Games {joueur1}", nb_games_1)
                with col_m4:
                    st.metric(f"KDA {joueur2}", values_2[labels.index("KDA")])
                with col_m5:
                    st.metric(f"Winrate {joueur2}", f"{winrate_2}%")
                with col_m6:
                    st.metric(f"Games {joueur2}", nb_games_2)
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric(f"KDA {joueur1}", values_1[labels.index("KDA")])
                with col_m2:
                    st.metric(f"Winrate {joueur1}", f"{winrate_1}%")
                with col_m3:
                    st.metric(f"Games {joueur1}", nb_games_1)

            fig = _figure_stats_joueur(labels, values_1, values_2, joueur1, nom_2)
            st.plotly_chart(fig, use_container_width=True)

            df_comparaison = pd.DataFrame({
                "Statistique": labels,
                joueur1: values_1,
                nom_2: values_2,
            })
            st.dataframe(df_comparaison, use_container_width=True, hide_index=True)

            if joueur2:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.caption(f"Champions les plus joués par {joueur1}")
                    st.dataframe(winrate_player_champion(df, joueur1)[["champion", "winrate", "nb_played"]], use_container_width=True, hide_index=True)
                with col_c2:
                    st.caption(f"Champions les plus joués par {joueur2}")
                    st.dataframe(winrate_player_champion(df, joueur2)[["champion", "winrate", "nb_played"]], use_container_width=True, hide_index=True)
            else:
                st.caption(f"Champions les plus joués par {joueur1}")
                st.dataframe(winrate_player_champion(df, joueur1)[["champion", "winrate", "nb_played"]], use_container_width=True, hide_index=True)

        elif fonction_active == "winrate_player_champion":
            st.subheader("Champions préférés d'un joueur")

            col1, col2, col3 = st.columns(3)
            with col1:
                df = _selectbox_annee(annees, key="winrate_champ_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                index_defaut_ligue = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut_ligue, key="winrate_champ_ligue")

            joueurs = sorted(df[df["league"] == ligue]["playername"].dropna().unique())
            with col3:
                index_defaut = joueurs.index("Faker") if "Faker" in joueurs else 0
                joueur = st.selectbox("Joueur", options=joueurs, index=index_defaut, key="winrate_champ_joueur")

            df_winrate = winrate_player_champion(df, joueur)
            fig = _figure_winrate_champion(df_winrate, joueur)
            st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "bar_chart_winrate_team":
            st.subheader("Winrate des équipes d'une ligue")

            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="winrate_team_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                index_defaut = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut, key="winrate_team_ligue")

            df_winrate = bar_chart_winrate_team_data(df, ligue)
            fig = _figure_winrate_team(df_winrate, ligue)
            st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "bar_chart_diff":
            st.subheader("Écarts moyens en début de game")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                df = _selectbox_annee(annees, key="diff_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                index_defaut = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut, key="diff_ligue")
            with col3:
                valeur = st.selectbox("Statistique", options=["golddiff", "xpdiff", "csdiff"], key="diff_valeur")
            with col4:
                temps = st.selectbox("Minute", options=[10, 15, 20, 25], key="diff_temps")

            df_diff = bar_chart_diff_data(df, ligue, valeur, temps)
            fig = _figure_diff(df_diff, valeur, temps)
            st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "bar_chart_team":
            st.subheader("Comparer deux équipes (objectifs)")

            col1, col2, col3 = st.columns(3)
            with col1:
                df = _selectbox_annee(annees, key="bar_team_annee")
            equipes = sorted(df["teamname"].dropna().unique())
            with col2:
                index_defaut_t1 = equipes.index("T1") if "T1" in equipes else 0
                team1 = st.selectbox("Équipe 1", options=equipes, index=index_defaut_t1, key="bar_team_1")
            with col3:
                mode_comp = st.radio("Comparer à", options=["Moyenne de sa ligue", "Une autre équipe"], index=1, horizontal=True, key="bar_team_mode")

            team2 = None
            if mode_comp == "Une autre équipe":
                autres_equipes = [e for e in equipes if e != team1]
                index_defaut_t2 = autres_equipes.index("Gen.G") if "Gen.G" in autres_equipes else 0
                team2 = st.selectbox("Équipe 2", options=autres_equipes, index=index_defaut_t2, key="bar_team_2")

            label, values_1, values_2, nom_2 = bar_chart_team_data(df, team1, team2)
            fig = _figure_bar_team(label, values_1, values_2, team1, nom_2)
            st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "tableau_stats":
            st.subheader("Tableau des stats par rôle")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                df = _selectbox_annee(annees, key="tableau_annee")
            with col2:
                role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="tableau_role")
            ligues = sorted(df["league"].dropna().unique())
            with col3:
                index_defaut_ligue = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut_ligue, key="tableau_ligue")
            with col4:
                tri = st.selectbox(
                    "Trier par",
                    options=["Winrate", "KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
                             "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Gold diff at 15",
                             "XP diff at 15", "Nombre game"],
                    key="tableau_tri",
                )

            player_stats = tableau_stats(df, role, ligue, tri)
            st.dataframe(player_stats, use_container_width=True)

        elif fonction_active == "cluster_role":
            st.subheader("Profils de joueurs par rôle")

            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="cluster_role_annee")
            with col2:
                role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="cluster_role_role")

            player_stats, labels = cluster_role(df, role)
            st.caption(f"{player_stats['cluster'].nunique()} clusters détectés parmi {len(player_stats)} joueurs.")
            for fig in _figures_cluster(player_stats, labels, standardise=False):
                st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "cluster_all_roles_standardise":
            st.subheader("Profils de joueurs tous rôles confondus")

            df = _selectbox_annee(annees, key="cluster_all_annee")

            all_players, labels = cluster_all_roles_standardise(df)
            st.caption(f"{all_players['cluster'].nunique()} clusters détectés parmi {len(all_players)} joueurs (tous rôles).")
            for fig in _figures_cluster(all_players, labels, standardise=True):
                st.plotly_chart(fig, use_container_width=True)

    # ----------------------- fonctions sur toutes les annees ---------------
    else:
        df_all = charger_donnees_esport(annees)

        if fonction_active == "head_to_head_team":
            st.subheader("Face-à-face entre deux équipes")

            equipes = sorted(df_all["teamname"].dropna().unique())
            col1, col2 = st.columns(2)
            with col1:
                index_defaut_t1 = equipes.index("T1") if "T1" in equipes else 0
                team1 = st.selectbox("Équipe 1", options=equipes, index=index_defaut_t1, key="h2h_team1")
            with col2:
                autres_equipes = [e for e in equipes if e != team1]
                index_defaut_t2 = autres_equipes.index("Gen.G") if "Gen.G" in autres_equipes else 0
                team2 = st.selectbox("Équipe 2", options=autres_equipes, index=index_defaut_t2, key="h2h_team2")

            resultat = head_to_head_team(df_all, team1, team2)
            if resultat is None:
                st.info(f"{team1} et {team2} ne se sont jamais affrontées.")
            else:
                win1, win2, winrate1, winrate2, df_recap_games = resultat
                nb_played = win1 + win2
                st.markdown(f"**{nb_played} games jouées** entre {team1} et {team2}")
                st.markdown(f"### {team1} **{win1} victoires** — **{win2} victoires** {team2}")
                st.markdown(f"### {team1} **{winrate1}%** — **{winrate2}%** {team2}")
                st.dataframe(df_recap_games, use_container_width=True, hide_index=True)

        elif fonction_active == "evolution_team":
            st.subheader("Évolution d'une équipe au fil des années")

            ligues = sorted(df_all["league"].dropna().unique())
            col1, col2, col3 = st.columns(3)
            with col1:
                index_defaut_ligue = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut_ligue, key="evo_team_ligue")

            equipes = sorted(df_all[df_all["league"] == ligue]["teamname"].dropna().unique())
            with col2:
                index_defaut = equipes.index("T1") if "T1" in equipes else 0
                team = st.selectbox("Équipe", options=equipes, index=index_defaut, key="evo_team_nom")
            with col3:
                stat = st.selectbox(
                    "Statistique",
                    options=["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor",
                             "Part nashor", "Taux first tower", "Part tower", "Taux first herald", "Winrate"],
                    key="evo_team_stat",
                )

            evo = evolution_team(df_all, team, stat)
            fig = _figure_evolution_team(evo, team, stat)
            st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "evolution_joueur":
            st.subheader("Évolution d'un joueur au fil des années")

            ligues = sorted(df_all["league"].dropna().unique())
            col1, col2, col3 = st.columns(3)
            with col1:
                index_defaut_ligue = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut_ligue, key="evo_joueur_ligue")

            joueurs = sorted(df_all[df_all["league"] == ligue]["playername"].dropna().unique())
            with col2:
                index_defaut = joueurs.index("Faker") if "Faker" in joueurs else 0
                joueur = st.selectbox("Joueur", options=joueurs, index=index_defaut, key="evo_joueur_nom")
            with col3:
                stat = st.selectbox(
                    "Statistique",
                    options=["KDA", "Kill Participation", "Gold / Minute", "Damage / Minute",
                             "Vision / Minute", "Creeps / Minute", "Wards / Minute", "Winrate"],
                    key="evo_joueur_stat",
                )

            evo = evolution_joueur(df_all, joueur, stat)
            fig = _figure_evolution_joueur(evo, joueur, stat)
            st.plotly_chart(fig, use_container_width=True)
            