import streamlit as st

from models.joueur_live import charger_dataset_complet
from models.item import charger_donnees_items
from models.esport import annees_disponibles, charger_donnees_esport
from models.champion import charger_donnees_champions
from models.spell import charger_donnees_spells
from controllers.joueur import (
    get_recherche,
    get_stats_joueur,
    get_nombre_games,
    get_historique,
    get_stat_role,
    get_bilan_side,
    get_habitudes,
    get_habitudes_heatmap,
    get_multikills,
    get_objectifs,
    get_meilleurs_champions_bar,
    get_meilleurs_champions_table,
    get_builds,
    get_meilleurs_items,
    get_evolution_winrate,
    get_details_game,
    get_items_achetes_joueur,
    get_classement_pickrate_champion,
    get_classement_winrate_champion,
    get_impact_patch_pickrate,
    get_impact_patch_items,
    get_impact_patch_performance,
    get_classement_bans_champion,
    get_runes_joueur,
    get_combat,
    get_matchups_champion,
)
from controllers.esport import get_classement_buff_nerf_saison

ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}

QUEUES = {
    "Classée Solo/Duo": 420,
    "Classée Flex": 440,
    "ARAM": 450,
    "Normale Draft": 400,
    "Toutes les files": None,
}

# ---------------------------------------------------------------------------
# Page Streamlit
# ---------------------------------------------------------------------------

ICONES_CATEGORIE = {
    "Recherche": "🔎",
    "Profil": "🧑",
    "Mes champions": "⚔️",
    "Tier lists": "🏆",
    "Impact des patches": "📈",
}

OPTIONS_MENU = (
    [("Recherche", "recherche")]
    + [("Profil", f) for f in ["comparer_stats", "profil_detaille", "historique"]]
    + [("Mes champions", f) for f in ["meilleurs_champions", "items_runes"]]
    + [("Tier lists", f) for f in ["tier_lists_champions", "meilleurs_items"]]
    + [("Impact des patches", "impact_patch")]
)

LABELS_MENU = {
    ("Recherche", "recherche"): "Rechercher un pseudo",
    ("Profil", "comparer_stats"): "Comparer mes stats",
    ("Profil", "profil_detaille"): "Profil détaillé",
    ("Profil", "historique"): "Historique des games",
    ("Mes champions", "meilleurs_champions"): "Meilleurs champions",
    ("Mes champions", "items_runes"): "Items & runes",
    ("Tier lists", "tier_lists_champions"): "Tier lists champions",
    ("Tier lists", "meilleurs_items"): "Meilleurs items par rôle",
    ("Impact des patches", "impact_patch"): "Impact des changements de patch",
}


def _selectbox_saison(df, key):
    saisons = sorted(df["patch_major_minor"].dropna().str.split(".").str[0].unique(), reverse=True)
    return st.selectbox("Saison", options=saisons, index=0, key=key)


def _selectbox_queue(key):
    label = st.selectbox("File", options=list(QUEUES.keys()), index=0, key=key)
    return QUEUES[label]


@st.cache_data(show_spinner="Chargement de la liste des joueurs...")
def _liste_joueurs(df):
    return sorted(df["riotIdGameName"].dropna().unique())

def _selectbox_joueur(df, key, defaut=None):
    joueurs = _liste_joueurs(df)

    recherche = st.text_input("Rechercher un joueur", value=defaut or "", key=f"{key}_recherche")

    if recherche:
        correspondances = [j for j in joueurs if recherche.lower() in j.lower()][:20]
    else:
        correspondances = joueurs[:20]

    if not correspondances:
        st.warning("Aucun joueur trouvé.")
        return None

    index_defaut = correspondances.index(defaut) if defaut in correspondances else 0

    return st.selectbox("Joueur", options=correspondances, index=index_defaut, key=key)

def ligne_joueur_recherche(ligne, joueur):
    if ligne["Pseudo"] == joueur:
        return ["font-weight: bold"] * len(ligne)
    return [""] * len(ligne)

def load_view():
    st.set_page_config(page_title="Analyse Joueur", layout="wide", initial_sidebar_state="expanded")
    st.title("Ton profil League of Legends")

    with st.sidebar:
        st.caption("🔎 Recherche · 🧑 Profil · ⚔️ Mes champions · 🏆 Tier lists · 📈 Impact des patches")
        categorie_active, fonction_active = st.radio(
            "Fonction",
            options=OPTIONS_MENU,
            format_func=lambda o: f"{ICONES_CATEGORIE[o[0]]} {LABELS_MENU[o]}",
            key="radio_menu_joueur",
            label_visibility="collapsed",
        )

    # ------------------------------------------------------------------
    # Onglet Recherche : pas besoin du dataset charge avant d'avoir cherche
    # ------------------------------------------------------------------
    if fonction_active == "recherche":
        st.subheader("Rechercher un joueur")
        st.caption("Entre ton Riot ID (Pseudo#TAG) pour récupérer tes dernières games et ton rang actuel.")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            pseudo = st.text_input("Pseudo", key="recherche_pseudo")
        with col2:
            tag = st.text_input("TAG (sans le #)", key="recherche_tag")
        with col3:
            region = st.selectbox("Région", options=["europe", "americas", "asia", "sea"], key="recherche_region")
        with col4:
            nb_games = st.slider("Nombre de games", min_value=10, max_value=50, value=30, key="recherche_count")

        if st.button("Rechercher", type="primary", key="recherche_bouton"):
            if not pseudo or not tag:
                st.warning("Renseigne un pseudo ET un tag.")
            else:
                with st.spinner("Récupération de tes dernières games auprès de l'API Riot..."):
                    resultat = get_recherche(pseudo, tag, region=region, count=nb_games)
                if resultat["erreur"]:
                    st.error(resultat["erreur"])
                else:
                    st.session_state["joueur_pseudo_actif"] = resultat["player"]
                    st.success(
                        f"{resultat['nb_matchs_recuperes']} game(s) récupérée(s) pour {pseudo}#{tag}."
                    )
                    st.caption(
                        f"{resultat['nb_lignes_nouvelles']} nouvelle(s) ligne(s) ajoutée(s) à l'historique."
                    )
                    if resultat["rang_affiche"]:
                        st.metric("Rang actuel :", resultat["rang_affiche"])
                    else:
                        st.caption("Rang non disponible (compte non classé sur cette file, ou non résolu).")

        pseudo_actif = st.session_state.get("joueur_pseudo_actif")
        if pseudo_actif:
            df = charger_dataset_complet()
            # Recalcule l'affichage a chaque fois (pas seulement juste apres
            # une recherche) pour que revenir sur cet onglet plus tard
            # affiche toujours les stats a jour du joueur actif.
            st.divider()
            st.subheader(f"Profil de {pseudo_actif}")
            st.dataframe(get_stat_role(df, pseudo_actif)[0], use_container_width=True, hide_index=True)
            st.write("5 dernières games")
            st.dataframe(get_historique(df, pseudo_actif, nombre_game=5), use_container_width=True, hide_index=True)
        return

    # ------------------------------------------------------------------
    # Tous les autres onglets : le dataset complet doit deja exister
    # ------------------------------------------------------------------
    df = charger_dataset_complet()
    mon_pseudo = "LopezHeichõ"
    pseudo_actif = st.session_state.get("joueur_pseudo_actif") or mon_pseudo

    if categorie_active == "Profil":

        if fonction_active == "comparer_stats":
            st.subheader("Comparer mes stats")

            onglet_radar, onglet_objectifs, onglet_combat = st.tabs(
                ["Radar", "Objectifs", "Profil de combat"]
            )

            with onglet_radar:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    saison = _selectbox_saison(df, key="stats_saison")
                with col2:
                    queue = _selectbox_queue(key="stats_queue")
                with col3:
                    joueur1 = _selectbox_joueur(df, key="stats_joueur_1", defaut=pseudo_actif)
                with col4:
                    mode_comp = st.radio("Comparer à", options=["Moyenne de mon rang", "Un autre joueur", "Un joueur pro"], index=0, horizontal=True, key="stats_mode")

                joueur2 = None
                role = None
                df_esport = None
                comparer_pro = False
                pro_player = None
                ligue_pro = None

                if mode_comp == "Un autre joueur":
                    autres = [j for j in sorted(df["riotIdGameName"].dropna().unique()) if j != joueur1]
                    joueur2 = st.selectbox("Joueur 2", options=autres, key="stats_joueur_2")
                elif mode_comp == "Un joueur pro":
                    comparer_pro = True
                    col5, col6, col7 = st.columns(3)
                    with col5:
                        role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="stats_pro_role")
                    with col6:
                        annees = annees_disponibles()
                        annee = st.selectbox("Année (pro)", options=annees, index=0, key="stats_pro_annee")
                        df_esport = charger_donnees_esport([annee])
                    with col7:
                        ligues_role = sorted(df_esport[df_esport["position"] == role]["league"].dropna().unique())
                        options_ligue = ["Toutes les ligues"] + ligues_role
                        ligue_choisie = st.selectbox("Ligue pro (optionnel)", options=options_ligue, key="stats_pro_ligue")
                        ligue_pro = None if ligue_choisie == "Toutes les ligues" else ligue_choisie

                    pros_df = df_esport[df_esport["position"] == role]
                    if ligue_pro:
                        pros_df = pros_df[pros_df["league"] == ligue_pro]
                    pros_dispo = sorted(pros_df["playername"].dropna().unique())
                    options_pro = ["Moyenne des pros de ce rôle"] + pros_dispo
                    pro_choisi = st.selectbox("Joueur pro (optionnel)", options=options_pro, key="stats_pro_joueur")
                    pro_player = None if pro_choisi == "Moyenne des pros de ce rôle" else pro_choisi
                else:
                    role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="stats_role")

                resultat = get_stats_joueur(
                    df, joueur1, joueur2, position=role, season=saison, queue_id=queue,
                    df_esport=df_esport, comparer_pro=comparer_pro, pro_player=pro_player, ligue_pro=ligue_pro,
                )
                if resultat.get("erreur"):
                    st.warning(resultat["erreur"])
                else:
                    st.plotly_chart(resultat["fig"], use_container_width=True)

            with onglet_objectifs:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    saison = _selectbox_saison(df, key="obj_saison")
                with col2:
                    queue = _selectbox_queue(key="obj_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="obj_joueur", defaut=pseudo_actif)
                with col4:
                    role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="obj_role")

                table, fig = get_objectifs(df, joueur, role=role, season=saison, queue_id=queue)
                if table.empty:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(table, use_container_width=True, hide_index=True)

            with onglet_combat:
                st.caption("Dégâts/soins/vision par minute et participation aux kills, comparés à la moyenne de ton rang.")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    saison = _selectbox_saison(df, key="combat_saison")
                with col2:
                    queue = _selectbox_queue(key="combat_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="combat_joueur", defaut=pseudo_actif)
                with col4:
                    role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="combat_role")

                table, fig = get_combat(df, joueur, role=role, season=saison, queue_id=queue)
                if table.empty:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(table, use_container_width=True, hide_index=True)

        elif fonction_active == "profil_detaille":
            st.subheader("Profil détaillé")

            onglet_role, onglet_side, onglet_habitudes, onglet_multi, onglet_evo, onglet_matchups = st.tabs(
                ["Stats par rôle", "Bilan Bleu / Rouge", "Quand je joue le mieux", "Récap multikills", "Évolution du winrate", "Matchups"]
            )

            with onglet_role:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="role_saison")
                with col2:
                    queue = _selectbox_queue(key="role_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="role_joueur", defaut=pseudo_actif)

                df_role, fig1, fig2 = get_stat_role(df, joueur, season=saison, queue_id=queue)
                if df_role.empty:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    col4, col5 = st.columns([3,2])
                    with col4:
                        st.plotly_chart(fig1, use_container_width=True)
                    with col5:
                        st.plotly_chart(fig2, use_container_width=True)
                    st.dataframe(df_role, use_container_width=True, hide_index=True)

            with onglet_side:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="side_saison")
                with col2:
                    queue = _selectbox_queue(key="side_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="side_joueur", defaut=pseudo_actif)

                df_side, fig_side = get_bilan_side(df, joueur, season=saison, queue_id=queue)
                if df_side.empty:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
                    with col_centre:
                        st.plotly_chart(fig_side, use_container_width=True)
                    st.dataframe(df_side, use_container_width=True, hide_index=True)

            with onglet_habitudes:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="habitudes_saison")
                with col2:
                    queue = _selectbox_queue(key="habitudes_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="habitudes_joueur", defaut=pseudo_actif)

                resultat = get_habitudes(df, joueur, season=saison, queue_id=queue)
                grille = get_habitudes_heatmap(df, joueur, season=saison, queue_id=queue)

                colgauche, colcentre, coldroite = st.columns([2, 3, 2])
                with colcentre:
                    st.plotly_chart(grille, use_container_width=True)

                st.subheader("Détail par jour et par moment")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("Par moment de la journée")
                    st.dataframe(resultat["par_moment"], use_container_width=True, hide_index=True)
                with col_b:
                    st.caption("Par jour de la semaine")
                    st.dataframe(resultat["par_jour"], use_container_width=True, hide_index=True)

            with onglet_multi:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="multi_saison")
                with col2:
                    queue = _selectbox_queue(key="multi_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="multi_joueur", defaut=pseudo_actif)

                serie,table,  fig = get_multikills(df, joueur, season=saison, queue_id=queue)
                if serie.empty:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.plotly_chart(fig, use_container_width=True)
                    with col_b:
                        with st.container(border=True):
                            st.metric("Plus longue série de multikills", serie.loc["Plus longue killing spree"])
                        with st.container(border=True):
                            st.metric("plus gros multikill obtenu", serie.loc["Plus gros multikill"])
                        with st.container(border=True):
                            st.metric("Nombre de multikills", serie.loc["Pentakills"] + serie.loc["Quadrakills"] + serie.loc["Triplekills"] + serie.loc["Doublekills"])

                    st.dataframe(table, use_container_width=True, hide_index=True)

            with onglet_evo:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="evo_saison")
                with col2:
                    queue = _selectbox_queue(key="evo_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="evo_joueur", defaut=pseudo_actif)

                resultat = get_evolution_winrate(df, joueur, season=saison, queue_id=queue)
                st.plotly_chart(resultat["fig"], use_container_width=True)

            with onglet_matchups:
                st.caption("Winrate d'un champion face à chaque champion adverse rencontré dans la même lane. Calculé sur toute la population, mais limité aux champions du joueur choisi.")

                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="matchup_saison")
                with col2:
                    queue = _selectbox_queue(key="matchup_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="matchup_joueur", defaut=pseudo_actif)

                df_joueur_season_mu = df[df["patch_major_minor"].str.startswith(saison)]
                df_joueur_season_mu = df_joueur_season_mu[df_joueur_season_mu["queueId"] == queue] if queue else df_joueur_season_mu
                df_joueur_mu = df_joueur_season_mu[df_joueur_season_mu["riotIdGameName"] == joueur]
                counts_champ_role_mu = df_joueur_mu.groupby(["championName", "position"]).size()
                champions_joues_mu = sorted(counts_champ_role_mu.index.get_level_values("championName").unique())

                if not champions_joues_mu:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    champion_defaut_mu, role_defaut_mu = counts_champ_role_mu.idxmax()

                    col4, col5 = st.columns(2)
                    with col4:
                        index_champ_mu = champions_joues_mu.index(champion_defaut_mu)
                        champion = st.selectbox("Champion", options=champions_joues_mu, index=index_champ_mu, key="matchup_champion")
                    with col5:
                        index_role_mu = ROLES.index(role_defaut_mu) if role_defaut_mu in ROLES else 0
                        role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], index=index_role_mu, key="matchup_role")

                    col6, col7, col8 = st.columns(3)
                    with col6:
                        rangs = sorted(df["soloqueue_tier"].dropna().unique())
                        rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="matchup_rang")
                        rang = None if rang_choice == "Tous les rangs" else rang_choice
                    with col7:
                        min_games = st.slider("Nombre de games minimum", 2, 20, 5, key="matchup_min_games")
                    with col8:
                        top_n = st.slider("Nombre de matchups à afficher", 4, 30, 14, key="matchup_topn")

                    resultat = get_matchups_champion(df, champion, role, rang=rang, season=saison, queue_id=queue, min_games=min_games, top_n=top_n)
                    if resultat["table"].empty:
                        st.info("Pas assez de matchups pour ce champion/rôle sur cette sélection (toute la population).")
                    else:
                        st.plotly_chart(resultat["fig"], use_container_width=True)
                        st.dataframe(resultat["table"], use_container_width=True, hide_index=True)

        elif fonction_active == "historique":
            st.subheader("Historique des games")

            df_items = charger_donnees_items()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                saison = _selectbox_saison(df, key="hist_saison")
            with col2:
                queue = _selectbox_queue(key="hist_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="hist_joueur", defaut=pseudo_actif)
            with col4:
                game_dispo = get_nombre_games(df, joueur, season=saison, queue_id=queue)
                nombre = st.slider("Nombre de games", min_value=5, max_value=game_dispo, value=10, key="hist_nombre")

            df_historique = get_historique(df, joueur, nombre_game=nombre, season=saison, queue_id=queue)

            st.caption("💡 Clique sur une ligne pour voir le détail de la game (picks et builds des deux équipes).")
            selection = st.dataframe(
                df_historique,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_order=["Date et heure", "Role", "Champion", "Resultat", "KDA", "Kills", "Deaths", "Assists", "Creep", "Durée de la game"])

            if selection.selection.rows:
                index_ligne = selection.selection.rows[0]
                ligne = df_historique.iloc[index_ligne]
                match_id = ligne["matchId"]

                try:
                    detail_blue, detail_red, item_blue, item_red, fig1, fig2, fig3, fig4, fig5, victoire, duree_game = get_details_game(df, df_items, match_id, joueur)
                except ValueError as erreur:
                    st.error(str(erreur))
                else:
                    onglet_detail, onglet_item, onglet_graph = st.tabs(["Détails", "Items", "Graphiques"])
                    with onglet_detail:
                        st.subheader(f"🏆 Victoire : {victoire}")
                        st.write(f"⏳ Durée de la game : {duree_game}")

                        st.subheader("Blue side")
                        styler_blue = detail_blue.style.apply(lambda ligne:ligne_joueur_recherche(ligne, joueur), axis=1)
                        st.dataframe(styler_blue, use_container_width=True, hide_index=True)

                        st.subheader("Red side")
                        styler_red = detail_red.style.apply(lambda ligne: ligne_joueur_recherche(ligne, joueur), axis=1)
                        st.dataframe(styler_red, use_container_width=True, hide_index=True)

                    with onglet_item:
                        st.subheader(f"🏆 Victoire : {victoire}")
                        st.write(f"⏳ Durée de la game : {duree_game}")

                        st.subheader("Blue side")
                        styler_blue = item_blue.style.apply(lambda ligne:ligne_joueur_recherche(ligne, joueur), axis=1)
                        st.dataframe(styler_blue, use_container_width=True, hide_index=True)

                        st.subheader("Red side")
                        styler_red = item_red.style.apply(lambda ligne: ligne_joueur_recherche(ligne, joueur), axis=1)
                        st.dataframe(styler_red, use_container_width=True, hide_index=True)

                    with onglet_graph:
                        st.subheader(f"🏆 Victoire : {victoire}")
                        st.write(f"⏳ Durée de la game : {duree_game}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(fig1, use_container_width=True)  # Dégâts aux champions
                        with col2:
                            st.plotly_chart(fig2, use_container_width=True)  # Or gagné
                        col3, col4 = st.columns(2)
                        with col3:
                            st.plotly_chart(fig5, use_container_width=True)  # Pourcentage de dégâts
                        with col4:
                            st.plotly_chart(fig4, use_container_width=True)  # Kill participation
                        col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
                        with col_centre:
                            st.plotly_chart(fig3, use_container_width=True)  # Scatter, en pleine largeur en dessous

    elif categorie_active == "Mes champions":
        df_items = charger_donnees_items()

        if fonction_active == "meilleurs_champions":
            st.subheader("Meilleurs champions")

            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="champ_bar_saison")
            with col2:
                queue = _selectbox_queue(key="champ_bar_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="champ_bar_joueur", defaut=pseudo_actif)

            resultat = get_meilleurs_champions_bar(df, joueur, season=saison, queue_id=queue)
            st.plotly_chart(resultat["fig"], use_container_width=True)
            st.dataframe(get_meilleurs_champions_table(df, joueur, season=saison, queue_id=queue), use_container_width=True, hide_index=True)

        elif fonction_active == "items_runes":
            st.subheader("Items & runes")

            onglet_builds, onglet_runes, onglet_achats = st.tabs(
                ["Builds fréquents", "Runes favorites", "Efficacité des achats"]
            )

            with onglet_builds:
                st.caption("Les builds complets varient beaucoup d'une game à l'autre : on regarde la fréquence de chaque item individuellement plutôt que la combinaison exacte des 6 items.")

                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="builds_saison")
                with col2:
                    queue = _selectbox_queue(key="builds_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="builds_joueur", defaut=pseudo_actif)

                df_joueur_season = df[df["patch_major_minor"].str.startswith(saison)]
                df_joueur_season = df_joueur_season[df_joueur_season["queueId"] == queue] if queue else df_joueur_season
                counts_champ_joueur = df_joueur_season[df_joueur_season["riotIdGameName"] == joueur]["championName"].dropna().value_counts()
                champions_joues = sorted(counts_champ_joueur.index.tolist())
                if not champions_joues:
                    st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
                else:
                    index_champ_defaut = champions_joues.index(counts_champ_joueur.idxmax())
                    champion = st.selectbox("Champion", options=champions_joues, index=index_champ_defaut, key="builds_champion")
                    min_games = st.slider("Nombre de games minimum", 1, 10, 2, key="builds_min_games")
                    resultat_builds = get_builds(df, df_items, joueur, champion, season=saison, queue_id=queue, min_games=min_games)
                    if resultat_builds["table"].empty:
                        st.info("Pas assez de games avec ce champion pour ce seuil.")
                    else:
                        st.plotly_chart(resultat_builds["fig"], use_container_width=True)
                        st.dataframe(resultat_builds["table"], use_container_width=True, hide_index=True)

            with onglet_runes:
                st.caption("Rune clé (keystone) la plus prise par ce joueur, et son winrate associé.")

                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="runes_saison")
                with col2:
                    queue = _selectbox_queue(key="runes_queue")
                with col3:
                    joueur = _selectbox_joueur(df, key="runes_joueur", defaut=pseudo_actif)

                col4, col5, col6 = st.columns(3)
                with col4:
                    role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="runes_role")
                with col5:
                    champions_joueur = sorted(df[df["riotIdGameName"] == joueur]["championName"].dropna().unique())
                    champion = st.selectbox("Champion (optionnel)", options=[None] + champions_joueur, format_func=lambda c: "Tous" if c is None else c, key="runes_champion")
                with col6:
                    top_n = st.slider("Nombre de runes à afficher", 3, 15, 10, key="runes_topn")

                resultat_runes = get_runes_joueur(df, joueur, role=role, champion=champion, season=saison, queue_id=queue, top_n=top_n)
                
                if resultat_runes["table"].empty:
                    st.info(f"Aucune rune trouvée pour {joueur} sur cette sélection.")
                else:
                    st.plotly_chart(resultat_runes["fig"], use_container_width=True)
                    st.dataframe(resultat_runes["table"], use_container_width=True, hide_index=True)

            with onglet_achats:
                st.caption("Items les plus achetés (item0 à item5, hors trinket) par le joueur recherché, avec leur efficacité gold théorique.")

                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="subopt_saison")
                with col2:
                    queue = _selectbox_queue(key="subopt_queue")
                with col3:
                    role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="subopt_role")

                joueur = _selectbox_joueur(df, key="subopt_joueur", defaut=pseudo_actif)
                top_n = st.slider("Nombre d'items à afficher", 5, 30, 15, key="subopt_joueur_topn")

                resultat_joueur = get_items_achetes_joueur(df, df_items, joueur, role=role, season=saison, queue_id=queue, top_n=top_n)
                if resultat_joueur["table"].empty:
                    st.info(f"Aucun achat trouvé pour {joueur} sur cette sélection.")
                else:
                    st.plotly_chart(resultat_joueur["fig"], use_container_width=True)
                    st.dataframe(resultat_joueur["table"], use_container_width=True, hide_index=True)

    elif categorie_active == "Tier lists":

        if fonction_active == "tier_lists_champions":
            st.subheader("Tier lists champions")
            st.caption("Ne dépend pas d'un pseudo précis : calculé sur tous les joueurs du dataset.")

            onglet_pickrate, onglet_winrate, onglet_bans = st.tabs(
                ["Plus joués", "Meilleur winrate", "Plus bannis"]
            )

            with onglet_pickrate:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="classpick_saison")
                with col2:
                    queue = _selectbox_queue(key="classpick_queue")
                with col3:
                    options_role = ["Tous les rôles"] + ROLES
                    role_choisi = st.selectbox("Rôle", options=options_role, format_func=lambda r: LABELS_ROLE.get(r, r), key="classpick_role")
                role = None if role_choisi == "Tous les rôles" else role_choisi

                col4, col5 = st.columns(2)
                with col4:
                    rangs = sorted(df["soloqueue_tier"].dropna().unique())
                    rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="classpick_rang")
                    rang = None if rang_choice == "Tous les rangs" else rang_choice
                with col5:
                    top_n = st.slider("Nombre de champions", 5, 30, 15, key="classpick_topn")

                resultat = get_classement_pickrate_champion(df, role=role, rang=rang, season=saison, queue_id=queue, top_n=top_n)
                if resultat["table"].empty:
                    st.info("Aucune donnée pour cette sélection.")
                else:
                    st.plotly_chart(resultat["fig"], use_container_width=True)
                    st.dataframe(resultat["table"], use_container_width=True, hide_index=True)

            with onglet_winrate:
                col1, col2, col3 = st.columns(3)
                with col1:
                    saison = _selectbox_saison(df, key="classwin_saison")
                with col2:
                    queue = _selectbox_queue(key="classwin_queue")
                with col3:
                    options_role = ["Tous les rôles"] + ROLES
                    role_choisi = st.selectbox("Rôle", options=options_role, format_func=lambda r: LABELS_ROLE.get(r, r), key="classwin_role")
                role = None if role_choisi == "Tous les rôles" else role_choisi

                col4, col5, col6 = st.columns(3)
                with col4:
                    rangs = sorted(df["soloqueue_tier"].dropna().unique())
                    rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="classwin_rang")
                    rang = None if rang_choice == "Tous les rangs" else rang_choice
                with col5:
                    min_games = st.slider("Nombre de games minimum", 5, 50, 20, key="classwin_min_games")
                with col6:
                    top_n = st.slider("Nombre de champions", 5, 30, 15, key="classwin_topn")

                resultat = get_classement_winrate_champion(df, role=role, rang=rang, season=saison, queue_id=queue, min_games=min_games, top_n=top_n)
                if resultat["table"].empty:
                    st.info("Aucune donnée pour cette sélection (essaie de baisser le nombre de games minimum).")
                else:
                    st.plotly_chart(resultat["fig"], use_container_width=True)
                    st.dataframe(resultat["table"], use_container_width=True, hide_index=True)

            with onglet_bans:
                st.caption("Les bans sont au niveau équipe (pas de rôle associé) : calculé sur toutes les phases de ban de la sélection.")

                col1, col2 = st.columns(2)
                with col1:
                    saison = _selectbox_saison(df, key="classban_saison")
                with col2:
                    queue = _selectbox_queue(key="classban_queue")

                col3, col4 = st.columns(2)
                with col3:
                    rangs = sorted(df["soloqueue_tier"].dropna().unique())
                    rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="classban_rang")
                    rang = None if rang_choice == "Tous les rangs" else rang_choice
                with col4:
                    top_n = st.slider("Nombre de champions", 5, 30, 15, key="classban_topn")

                df_champions_ban = charger_donnees_champions()
                resultat = get_classement_bans_champion(df, df_champions_ban, rang=rang, season=saison, queue_id=queue, top_n=top_n)
                if resultat["table"].empty:
                    st.info("Aucune donnée de ban pour cette sélection.")
                else:
                    st.plotly_chart(resultat["fig"], use_container_width=True)
                    st.dataframe(resultat["table"], use_container_width=True, hide_index=True)

        elif fonction_active == "meilleurs_items":
            st.subheader("Meilleurs items par rôle (toute la population)")
            st.caption("Ne dépend pas d'un pseudo précis : regarde tous les joueurs du dataset pour un champion/rôle donné.")

            df_items = charger_donnees_items()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                saison = _selectbox_saison(df, key="items_saison")
            with col2:
                queue = _selectbox_queue(key="items_queue")

            df_pop_season = df[df["patch_major_minor"].str.startswith(saison)]
            df_pop_season = df_pop_season[df_pop_season["queueId"] == queue] if queue else df_pop_season
            counts_champ_role = df_pop_season.groupby(["championName", "position"]).size()
            champion_defaut, role_defaut = counts_champ_role.idxmax() if not counts_champ_role.empty else (None, None)

            champions_dispo = sorted(df["championName"].dropna().unique())
            with col3:
                index_champ = champions_dispo.index(champion_defaut) if champion_defaut in champions_dispo else 0
                champion = st.selectbox("Champion", options=champions_dispo, index=index_champ, key="items_champion")
            with col4:
                index_role = ROLES.index(role_defaut) if role_defaut in ROLES else 0
                role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], index=index_role, key="items_role")

            col5, col6 = st.columns(2)
            with col5:
                rangs = sorted(df["soloqueue_tier"].dropna().unique())
                rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="items_rang")
                rang = None if rang_choice == "Tous les rangs" else rang_choice
            with col6:
                min_games = st.slider("Nombre de games minimum par item", 3, 30, 10, key="items_min_games")

            resultat_items_role = get_meilleurs_items(df, df_items, champion, role, rang=rang, season=saison, queue_id=queue, min_games=min_games)
            if resultat_items_role["table"].empty:
                st.info("Pas assez de games pour ce champion/rôle sur cette sélection.")
            else:
                st.plotly_chart(resultat_items_role["fig"], use_container_width=True)
                st.dataframe(resultat_items_role["table"], use_container_width=True, hide_index=True)

    elif categorie_active == "Impact des patches":

        if fonction_active == "impact_patch":
            st.subheader("Impact des changements de patch")
            st.caption("Est-ce que les buffs/nerfs de champions, sorts et items changent la façon dont ce joueur joue ?")

            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="impact_saison")
            with col2:
                queue = _selectbox_queue(key="impact_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="impact_joueur", defaut=pseudo_actif)

            df_champions = charger_donnees_champions()
            df_spells = charger_donnees_spells()
            df_items = charger_donnees_items()

            onglet_pick, onglet_items, onglet_perf, onglet_saison = st.tabs(
                ["Pick/drop de champion", "Items achetés", "Performance (winrate/KDA)", "Champions les plus modifiés cette saison"]
            )

            with onglet_pick:
                resultat_pick = get_impact_patch_pickrate(df, df_champions, df_spells, joueur, season=saison, queue_id=queue)
                if resultat_pick["table"].empty:
                    st.info("Pas de champion touché par un changement de patch sur cette sélection.")
                else:
                    st.plotly_chart(resultat_pick["fig"], use_container_width=True)
                    st.dataframe(resultat_pick["table"], use_container_width=True, hide_index=True)

            with onglet_items:
                resultat_items = get_impact_patch_items(df, df_items, joueur, season=saison, queue_id=queue)
                if resultat_items["table"].empty:
                    st.info("Pas d'item touché par un changement de patch sur cette sélection.")
                else:
                    st.plotly_chart(resultat_items["fig"], use_container_width=True)
                    st.dataframe(resultat_items["table"], use_container_width=True, hide_index=True)

            with onglet_perf:
                min_games = st.slider("Nombre de games minimum (avant ET après)", 1, 10, 3, key="impact_perf_min_games")
                resultat_perf = get_impact_patch_performance(df, df_champions, df_spells, joueur, season=saison, queue_id=queue, min_games=min_games)
                if resultat_perf["table"].empty:
                    st.info("Pas assez de games avant/après un changement de patch pour ce seuil.")
                else:
                    st.plotly_chart(resultat_perf["fig"], use_container_width=True)
                    st.dataframe(resultat_perf["table"], use_container_width=True, hide_index=True)

            with onglet_saison:
                st.caption("Cumul des buffs/nerfs de stats de base + sorts sur tous les patchs de la saison sélectionnée (pas besoin d'un joueur précis, utilise la saison choisie ci-dessus).")
                top_n = st.slider("Nombre de champions", 5, 30, 15, key="buffnerf_topn")

                resultat_bn = get_classement_buff_nerf_saison(df_champions, df_spells, season=saison, top_n=top_n)
                if resultat_bn["table"].empty:
                    st.info("Aucun changement détecté pour cette saison.")
                else:
                    st.plotly_chart(resultat_bn["fig"], use_container_width=True)
                    st.dataframe(resultat_bn["table"], use_container_width=True, hide_index=True)
