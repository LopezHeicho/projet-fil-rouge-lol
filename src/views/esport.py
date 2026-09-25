import pandas as pd
import streamlit as st
 
from models.esport import annees_disponibles, charger_donnees_esport
from controllers.esport import (
    get_comparaison_joueurs,
    get_winrate_champion,
    get_winrate_team,
    get_diff,
    get_comparaison_equipes,
    get_tableau_stats,
    get_head_to_head,
    get_evolution_equipe,
    get_evolution_joueur,
    get_cluster_role,
    get_cluster_all_roles,
)
 
ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}
 
 
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
 
            resultat = get_comparaison_joueurs(df, joueur1, joueur2)
            labels = resultat["labels"]
            nom_2 = resultat["nom_2"]
 
            if joueur2:
                st.caption(f"**{joueur1}** — {resultat['equipe1']} ({resultat['ligue1']})  vs  **{joueur2}** — {resultat['equipe2']} ({resultat['ligue2']})")
            else:
                st.caption(f"**{joueur1}** — {resultat['equipe1']} ({resultat['ligue1']})  vs  {nom_2}")
 
            if joueur2:
                col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
                with col_m1:
                    st.metric(f"KDA {joueur1}", resultat["values_1"][labels.index("KDA")])
                with col_m2:
                    st.metric(f"Winrate {joueur1}", f"{resultat['winrate_1']}%")
                with col_m3:
                    st.metric(f"Games {joueur1}", resultat["nb_games_1"])
                with col_m4:
                    st.metric(f"KDA {joueur2}", resultat["values_2"][labels.index("KDA")])
                with col_m5:
                    st.metric(f"Winrate {joueur2}", f"{resultat['winrate_2']}%")
                with col_m6:
                    st.metric(f"Games {joueur2}", resultat["nb_games_2"])
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric(f"KDA {joueur1}", resultat["values_1"][labels.index("KDA")])
                with col_m2:
                    st.metric(f"Winrate {joueur1}", f"{resultat['winrate_1']}%")
                with col_m3:
                    st.metric(f"Games {joueur1}", resultat["nb_games_1"])
 
            st.plotly_chart(resultat["fig"], use_container_width=True)
            st.dataframe(resultat["df_comparaison"], use_container_width=True, hide_index=True)
 
            if joueur2:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.caption(f"Champions les plus joués par {joueur1}")
                    st.dataframe(resultat["champions_j1"], use_container_width=True, hide_index=True)
                with col_c2:
                    st.caption(f"Champions les plus joués par {joueur2}")
                    st.dataframe(resultat["champions_j2"], use_container_width=True, hide_index=True)
            else:
                st.caption(f"Champions les plus joués par {joueur1}")
                st.dataframe(resultat["champions_j1"], use_container_width=True, hide_index=True)
 
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
 
            resultat = get_winrate_champion(df, joueur)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
        elif fonction_active == "bar_chart_winrate_team":
            st.subheader("Winrate des équipes d'une ligue")
 
            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="winrate_team_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                index_defaut = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut, key="winrate_team_ligue")
 
            resultat = get_winrate_team(df, ligue)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
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
 
            resultat = get_diff(df, ligue, valeur, temps)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
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
 
            resultat = get_comparaison_equipes(df, team1, team2)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
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
 
            player_stats = get_tableau_stats(df, role, ligue, tri)
            st.dataframe(player_stats, use_container_width=True)
 
        elif fonction_active == "cluster_role":
            st.subheader("Profils de joueurs par rôle")
 
            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="cluster_role_annee")
            with col2:
                role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="cluster_role_role")
 
            resultat = get_cluster_role(df, role)
            st.caption(f"{resultat['nb_clusters']} clusters détectés parmi {resultat['nb_joueurs']} joueurs.")
            for fig in resultat["figures"]:
                st.plotly_chart(fig, use_container_width=True)
 
        elif fonction_active == "cluster_all_roles_standardise":
            st.subheader("Profils de joueurs tous rôles confondus")
 
            df = _selectbox_annee(annees, key="cluster_all_annee")
 
            resultat = get_cluster_all_roles(df)
            st.caption(f"{resultat['nb_clusters']} clusters détectés parmi {resultat['nb_joueurs']} joueurs (tous rôles).")
            for fig in resultat["figures"]:
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
 
            resultat = get_head_to_head(df_all, team1, team2)
            if resultat is None:
                st.info(f"{team1} et {team2} ne se sont jamais affrontées.")
            else:
                st.markdown(f"**{resultat['nb_played']} games jouées** entre {team1} et {team2}")
                st.markdown(f"### {team1} **{resultat['win1']} victoires** — **{resultat['win2']} victoires** {team2}")
                st.markdown(f"### {team1} **{resultat['winrate1']}%** — **{resultat['winrate2']}%** {team2}")
                st.dataframe(resultat["df_recap_games"], use_container_width=True, hide_index=True)
 
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
 
            resultat = get_evolution_equipe(df_all, team, stat)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
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
 
            resultat = get_evolution_joueur(df_all, joueur, stat)
            st.plotly_chart(resultat["fig"], use_container_width=True)
            