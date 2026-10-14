import pandas as pd
import streamlit as st
 
from models.esport import annees_disponibles, charger_donnees_esport
from controllers.esport import (
    get_comparaison_joueurs,
    get_winrate_champion,
    get_winrate_team,
    get_winrate_side,
    get_duree_team,
    get_diff,
    get_comparaison_equipes,
    get_tableau_stats,
    get_head_to_head,
    get_details_game_pro,
    get_evolution_equipe,
    get_evolution_winrate_side,
    get_evolution_joueur,
    get_evolution_joueur,
    get_cluster_role,
    get_cluster_all_roles,
    get_correlation_pickrate,
    get_patchs_changements,
    get_classement_pickrate,
)

from models.champion import charger_donnees_champions
from models.spell import charger_donnees_spells
 
ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}
 
 
# ---------------------------------------------------------------------------
# Page Streamlit
# ---------------------------------------------------------------------------
 
# Réorganisation 2026-10-08 : les fonctions qui font la même analyse à
# l'échelle joueur vs équipe (comparer deux X, évolution dans le temps) sont
# regroupées en une seule entrée à onglets, sur le même principe que
# views/meta.py. Les 2 fonctions de clustering (un rôle / tous les rôles)
# sont fusionnées de la même façon. Les catégories Base/Cluster disparaissent
# au profit d'une liste à plat, groupée par icône (cf. légende sidebar).

ICONES_FONCTION = {
    "comparer": "🔀",
    "evolution": "🔀",
    "winrate_player_champion": "🧑",
    "cluster": "🧑",
    "tableau_stats": "🧑",
    "stats_ligue": "🛡️",
    "head_to_head_team": "🛡️",
    "classement_pickrate": "📈",
    "correlation_pickrate": "📈",
}

LABELS_MENU = {
    "comparer": "Comparer deux éléments",
    "evolution": "Évolution dans le temps",
    "winrate_player_champion": "Champions préférés d'un joueur",
    "cluster": "Profils de joueurs (clustering)",
    "tableau_stats": "Tableau des stats par rôle",
    "stats_ligue": "Stats des équipes d'une ligue",
    "head_to_head_team": "Face-à-face entre deux équipes",
    "classement_pickrate": "Tier list : champions les plus joués",
    "correlation_pickrate": "Impact des changements de patch sur le pickrate",
}

OPTIONS_MENU = [
    "comparer",
    "evolution",
    "winrate_player_champion",
    "cluster",
    "tableau_stats",
    "stats_ligue",
    "head_to_head_team",
    "classement_pickrate",
    "correlation_pickrate",
]
 
 
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
    st.set_page_config(page_title="Analyse Esport", layout="wide", initial_sidebar_state="expanded")
    st.title("Analyse des matchs pro (Oracle's Elixir)")
 
    annees = annees_disponibles()
 
    with st.sidebar:
        st.caption("🔀 Joueur + Équipe · 🧑 Joueur · 🛡️ Équipe · 📈 Meta / patch")
        fonction_active = st.radio(
            "Fonction",
            options=OPTIONS_MENU,
            format_func=lambda o: f"{ICONES_FONCTION[o]} {LABELS_MENU[o]}",
            key="radio_menu_esport",
            label_visibility="collapsed",
        )

    # -------------------- fonctions sur une seule annee --------------------
    if fonction_active in (
        "comparer", "winrate_player_champion", "stats_ligue",
        "tableau_stats", "cluster", "classement_pickrate"
    ):
        if fonction_active == "comparer":
            st.subheader("Comparer deux éléments")

            onglet_joueur, onglet_equipe = st.tabs(["Joueur", "Équipe"])

            with onglet_joueur:
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

            with onglet_equipe:
                col1, col2, col3 = st.columns(3)
                with col1:
                    df = _selectbox_annee(annees, key="bar_team_annee")
                equipes = sorted(df["teamname"].dropna().unique())
                with col2:
                    index_defaut_t1 = equipes.index("T1") if "T1" in equipes else 0
                    team1 = st.selectbox("Équipe 1", options=equipes, index=index_defaut_t1, key="bar_team_1")
                with col3:
                    mode_comp_equipe = st.radio("Comparer à", options=["Moyenne de sa ligue", "Une autre équipe"], index=1, horizontal=True, key="bar_team_mode")

                team2 = None
                if mode_comp_equipe == "Une autre équipe":
                    autres_equipes = [e for e in equipes if e != team1]
                    index_defaut_t2 = autres_equipes.index("Gen.G") if "Gen.G" in autres_equipes else 0
                    team2 = st.selectbox("Équipe 2", options=autres_equipes, index=index_defaut_t2, key="bar_team_2")

                resultat = get_comparaison_equipes(df, team1, team2)
                st.plotly_chart(resultat["fig"], use_container_width=True)

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
            st.dataframe(resultat["table"], use_container_width=True, hide_index=True)

        elif fonction_active == "stats_ligue":
            st.subheader("Stats des équipes d'une ligue")

            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="winrate_team_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                index_defaut = ligues.index("LCK") if "LCK" in ligues else 0
                ligue = st.selectbox("Ligue", options=ligues, index=index_defaut, key="winrate_team_ligue")

            onglet_winrate, onglet_side, onglet_duree, onglet_diff = st.tabs(
                ["Winrate", "Winrate par side", "Durée de game", "Écarts en début de game"]
            )

            with onglet_winrate:
                resultat = get_winrate_team(df, ligue)
                st.plotly_chart(resultat["fig"], use_container_width=True)

            with onglet_side:
                resultat_side = get_winrate_side(df, ligue)
                st.plotly_chart(resultat_side["fig"], use_container_width=True)

            with onglet_duree:
                resultat_duree = get_duree_team(df, ligue)
                st.plotly_chart(resultat_duree["fig"], use_container_width=True)

            with onglet_diff:
                col3, col4 = st.columns(2)
                with col3:
                    valeur = st.selectbox("Statistique", options=["golddiff", "xpdiff", "csdiff"], key="diff_valeur")
                with col4:
                    temps = st.selectbox("Minute", options=[10, 15, 20, 25], key="diff_temps")

                resultat_diff = get_diff(df, ligue, valeur, temps)
                st.plotly_chart(resultat_diff["fig"], use_container_width=True)

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
 
            player_stats, fig = get_tableau_stats(df, role, ligue, tri)
            st.plotly_chart(fig)
            st.dataframe(player_stats, use_container_width=True)
 
        elif fonction_active == "cluster":
            st.subheader("Profils de joueurs (clustering)")
            st.info(
                "Chaque joueur est regroupé automatiquement avec ceux qui ont un profil de jeu "
                "statistiquement proche (vision, dégâts, creeps, etc.), sans catégorie définie à "
                "l'avance : c'est du *clustering* (algorithme K-Means). Chaque graphique ci-dessous "
                "représente donc le profil **moyen** d'un groupe de joueurs, pas un joueur en "
                "particulier — l'idée est de faire ressortir des styles de jeu qui se distinguent "
                "naturellement dans les données (par exemple un groupe plus porté sur la vision, "
                "un autre plus porté sur les dégâts)."
            )

            onglet_role, onglet_tous = st.tabs(["Un rôle", "Tous les rôles"])

            with onglet_role:
                col1, col2 = st.columns(2)
                with col1:
                    df = _selectbox_annee(annees, key="cluster_role_annee")
                with col2:
                    role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="cluster_role_role")

                resultat = get_cluster_role(df, role)
                st.caption(f"{resultat['nb_clusters']} clusters détectés parmi {resultat['nb_joueurs']} joueurs.")
                for fig in resultat["figures"]:
                    st.plotly_chart(fig, use_container_width=True)

            with onglet_tous:
                df = _selectbox_annee(annees, key="cluster_all_annee")

                resultat = get_cluster_all_roles(df)
                st.caption(f"{resultat['nb_clusters']} clusters détectés parmi {resultat['nb_joueurs']} joueurs (tous rôles).")
                for fig in resultat["figures"]:
                    st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "classement_pickrate":
            st.subheader("Tier list : champions les plus joués")

            col1, col2 = st.columns(2)
            with col1:
                df = _selectbox_annee(annees, key="classement_pick_annee")
            ligues = sorted(df["league"].dropna().unique())
            with col2:
                options_ligue = ["Toutes les ligues"] + ligues
                index_defaut_ligue = (ligues.index("LCK") + 1) if "LCK" in ligues else 0
                ligue_choisie = st.selectbox("Ligue", options=options_ligue, index=index_defaut_ligue, key="classement_pick_ligue")
            ligue = None if ligue_choisie == "Toutes les ligues" else ligue_choisie

            col3, col4 = st.columns(2)
            with col3:
                options_role = ["Tous les rôles"] + ROLES
                role_choisi = st.selectbox("Rôle", options=options_role, format_func=lambda r: LABELS_ROLE.get(r, r), key="classement_pick_role")
            role = None if role_choisi == "Tous les rôles" else role_choisi
            with col4:
                top_n = st.slider("Nombre de champions", min_value=5, max_value=30, value=10, key="classement_pick_topn")

            resultat = get_classement_pickrate(df, ligue, role, top_n)
            st.plotly_chart(resultat["fig"], use_container_width=True)
            st.dataframe(resultat["table"], use_container_width=True, hide_index=True)
 
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

                st.caption("💡 Clique sur une ligne pour voir le détail de la game (picks blue side / red side).")
                selection = st.dataframe(
                    resultat["df_recap_games"],
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    column_order=["Année", "Ligue", "Vainqueur", "Durée de la game"])

                if selection.selection.rows:
                    index_ligne = selection.selection.rows[0]
                    ligne = resultat["df_recap_games"].iloc[index_ligne]
                    gameid = ligne["gameid"]

                    detail = get_details_game_pro(df_all, gameid)

                    onglet_detail, onglet_graph = st.tabs(["Détails", "Graphiques"])

                    with onglet_detail:
                        st.subheader(f"🏆 Victoire : {detail['victoire']}")
                        st.write(f"⏳ Durée de la game : {detail['duree_game']}")

                        st.subheader(f"Blue side ({detail['equipe_bleue']})")
                        st.dataframe(detail["blue_side"], use_container_width=True, hide_index=True)

                        st.subheader(f"Red side ({detail['equipe_rouge']})")
                        st.dataframe(detail["red_side"], use_container_width=True, hide_index=True)

                    with onglet_graph:
                        st.subheader(f"🏆 Victoire : {detail['victoire']}")
                        st.write(f"⏳ Durée de la game : {detail['duree_game']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(detail["fig1"], use_container_width=True)  # Degats aux champions
                        with col2:
                            st.plotly_chart(detail["fig2"], use_container_width=True)  # Or gagne
                        col3, col4 = st.columns(2)
                        with col3:
                            st.plotly_chart(detail["fig5"], use_container_width=True)  # Pourcentage de degats
                        with col4:
                            st.plotly_chart(detail["fig4"], use_container_width=True)  # Kill participation
                        col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
                        with col_centre:
                            st.plotly_chart(detail["fig3"], use_container_width=True)  # Scatter
 
        elif fonction_active == "evolution":
            st.subheader("Évolution dans le temps")

            onglet_joueur, onglet_equipe = st.tabs(["Joueur", "Équipe"])

            with onglet_joueur:
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

            with onglet_equipe:
                ligues = sorted(df_all["league"].dropna().unique())
                col1, col2 = st.columns(2)
                with col1:
                    index_defaut_ligue = ligues.index("LCK") if "LCK" in ligues else 0
                    ligue = st.selectbox("Ligue", options=ligues, index=index_defaut_ligue, key="evo_team_ligue")

                equipes = sorted(df_all[df_all["league"] == ligue]["teamname"].dropna().unique())
                with col2:
                    index_defaut = equipes.index("T1") if "T1" in equipes else 0
                    team = st.selectbox("Équipe", options=equipes, index=index_defaut, key="evo_team_nom")

                onglet_stats, onglet_side, onglet_duree = st.tabs(["Statistiques", "Blue vs Red Side", "Durée de game"])

                with onglet_stats:
                    stat_team = st.selectbox(
                        "Statistique",
                        options=["Taux first blood", "Taux first dragon", "Part dragon", "Taux first nashor",
                                "Part nashor", "Taux first tower", "Part tower", "Taux first herald", "Winrate"],
                        key="evo_team_stat",
                    )
                    resultat = get_evolution_equipe(df_all, team, stat_team)
                    st.plotly_chart(resultat["fig"], use_container_width=True)

                with onglet_side:
                    resultat_side = get_evolution_winrate_side(df_all, team)
                    st.plotly_chart(resultat_side["fig"], use_container_width=True)

                with onglet_duree:
                    resultat_duree = get_evolution_equipe(df_all, team, "Durée de game")
                    st.plotly_chart(resultat_duree["fig"], use_container_width=True)

        elif fonction_active == "correlation_pickrate":
            st.subheader("Impact des changements de patch sur le pickrate")

            ligues = sorted(df_all["league"].dropna().unique())
            col1, col2 = st.columns(2)
            with col1:
                options_ligue = ["Toutes les ligues"] + ligues
                index_defaut_ligue = (ligues.index("LCK") + 1) if "LCK" in ligues else 0
                ligue_choisie = st.selectbox("Ligue", options=options_ligue, index=index_defaut_ligue, key="correl_pick_ligue")
            ligue = None if ligue_choisie == "Toutes les ligues" else ligue_choisie
            with col2:
                options_role = ["Tous les rôles"] + ROLES
                role_choisi = st.selectbox("Rôle", options=options_role, format_func=lambda r: LABELS_ROLE.get(r, r), key="correl_pick_role")
            role = None if role_choisi == "Tous les rôles" else role_choisi

            df_champions = charger_donnees_champions()
            df_spells = charger_donnees_spells()

            patchs_disponibles = get_patchs_changements(df_all, df_champions, df_spells, ligue, role)

            if not patchs_disponibles:
                st.info("Aucun changement de champion détecté sur les patches couverts par cette ligue.")
            else:
                patch_choisi = st.selectbox("Patch", options=list(reversed(patchs_disponibles)), key="correl_pick_patch")
                resultat = get_correlation_pickrate(df_all, df_champions, df_spells, ligue, patch_choisi, role)
                st.plotly_chart(resultat["fig"], use_container_width=True)
                st.dataframe(resultat["table"], use_container_width=True, hide_index=True)