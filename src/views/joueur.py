import streamlit as st
 
from models.joueur_live import charger_dataset_complet
from models.item import charger_donnees_items
from controllers.joueur import (
    get_recherche,
    get_stats_joueur,
    get_nombre_games,
    get_historique,
    get_stat_role,
    get_bilan_side,
    get_habitudes,
    get_multikills,
    get_objectifs,
    get_meilleurs_champions_bar,
    get_meilleurs_champions_table,
    get_builds,
    get_meilleurs_items,
    get_evolution_winrate,
)
 
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
 
ICONES_CATEGORIE = {"Recherche": "🔎", "Profil": "🧑", "Champions": "⚔️", "Évolution": "📈"}
 
OPTIONS_MENU = (
    [("Recherche", "recherche")]
    + [("Profil", f) for f in [
        "stats_joueur", "historique", "stat_role", "bilan_side", "habitudes", "multikills", "objectifs",
    ]]
    + [("Champions", f) for f in [
        "meilleurs_champions_bar", "meilleurs_champions_table", "builds", "meilleurs_items",
    ]]
    + [("Évolution", "evolution_winrate")]
)
 
LABELS_MENU = {
    ("Recherche", "recherche"): "Rechercher un pseudo",
    ("Profil", "stats_joueur"): "Comparer mes stats (radar)",
    ("Profil", "historique"): "Historique des games",
    ("Profil", "stat_role"): "Stats par rôle",
    ("Profil", "bilan_side"): "Bilan Bleu / Rouge",
    ("Profil", "habitudes"): "Quand je joue le mieux",
    ("Profil", "multikills"): "Récap multikills",
    ("Profil", "objectifs"): "Profil objectifs",
    ("Champions", "meilleurs_champions_bar"): "Meilleurs champions (graphique)",
    ("Champions", "meilleurs_champions_table"): "Meilleurs champions (tableau)",
    ("Champions", "builds"): "Builds fréquents",
    ("Champions", "meilleurs_items"): "Meilleurs items par rôle",
    ("Évolution", "evolution_winrate"): "Évolution du winrate",
}
 
 
def _selectbox_saison(df, key):
    saisons = sorted(df["patch_major_minor"].dropna().str.split(".").str[0].unique(), reverse=True)
    return st.selectbox("Saison", options=saisons, index=0, key=key)
 
 
def _selectbox_queue(key):
    label = st.selectbox("File", options=list(QUEUES.keys()), index=0, key=key)
    return QUEUES[label]
 
 
def _selectbox_joueur(df, key, defaut=None):
    joueurs = sorted(df["riotIdGameName"].dropna().unique())
    index_defaut = joueurs.index(defaut) if defaut in joueurs else 0
    return st.selectbox("Joueur", options=joueurs, index=index_defaut, key=key)
 
 
def load_view():
    st.set_page_config(page_title="Analyse Joueur", layout="wide")
    st.title("Ton profil League of Legends")
 
    with st.sidebar:
        st.caption("🔎 Recherche · 🧑 Profil · ⚔️ Champions · 📈 Évolution")
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
            nb_games = st.slider("Nombre de games", min_value=10, max_value=100, value=50, key="recherche_count")
 
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
                        f"{resultat['nb_matchs_recuperes']} game(s) récupérée(s) "
                        f"({resultat['nb_lignes_nouvelles']} nouvelle(s) ligne(s) ajoutée(s) au dataset)."
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
            st.dataframe(get_stat_role(df, pseudo_actif), use_container_width=True, hide_index=True)
            st.caption("5 dernières games")
            st.dataframe(get_historique(df, pseudo_actif, nombre_game=5), use_container_width=True, hide_index=True)
        return
 
    # ------------------------------------------------------------------
    # Tous les autres onglets : le dataset complet doit deja exister
    # ------------------------------------------------------------------
    df = charger_dataset_complet()
    pseudo_actif = st.session_state.get("joueur_pseudo_actif")
 
    if categorie_active == "Profil":
 
        if fonction_active == "stats_joueur":
            st.subheader("Comparer mes stats (radar)")
 
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                saison = _selectbox_saison(df, key="stats_saison")
            with col2:
                queue = _selectbox_queue(key="stats_queue")
            with col3:
                joueur1 = _selectbox_joueur(df, key="stats_joueur_1", defaut=pseudo_actif)
            with col4:
                mode_comp = st.radio("Comparer à", options=["Moyenne de mon rang", "Un autre joueur"], index=0, horizontal=True, key="stats_mode")
 
            joueur2 = None
            role = None
            if mode_comp == "Un autre joueur":
                autres = [j for j in sorted(df["riotIdGameName"].dropna().unique()) if j != joueur1]
                joueur2 = st.selectbox("Joueur 2", options=autres, key="stats_joueur_2")
            else:
                role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="stats_role")
 
            resultat = get_stats_joueur(df, joueur1, joueur2, position=role, season=saison, queue_id=queue)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
        elif fonction_active == "historique":
            st.subheader("Historique des games")
 
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
 
            st.dataframe(get_historique(df, joueur, nombre_game=nombre, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
        elif fonction_active == "stat_role":
            st.subheader("Stats par rôle")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="role_saison")
            with col2:
                queue = _selectbox_queue(key="role_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="role_joueur", defaut=pseudo_actif)
 
            st.dataframe(get_stat_role(df, joueur, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
        elif fonction_active == "bilan_side":
            st.subheader("Bilan Bleu / Rouge")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="side_saison")
            with col2:
                queue = _selectbox_queue(key="side_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="side_joueur", defaut=pseudo_actif)
 
            st.dataframe(get_bilan_side(df, joueur, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
        elif fonction_active == "habitudes":
            st.subheader("Quand je joue le mieux")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="habitudes_saison")
            with col2:
                queue = _selectbox_queue(key="habitudes_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="habitudes_joueur", defaut=pseudo_actif)
 
            resultat = get_habitudes(df, joueur, season=saison, queue_id=queue)
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("Par moment de la journée")
                st.dataframe(resultat["par_moment"], use_container_width=True, hide_index=True)
            with col_b:
                st.caption("Par jour de la semaine")
                st.dataframe(resultat["par_jour"], use_container_width=True, hide_index=True)
 
        elif fonction_active == "multikills":
            st.subheader("Récap multikills")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="multi_saison")
            with col2:
                queue = _selectbox_queue(key="multi_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="multi_joueur", defaut=pseudo_actif)
 
            st.dataframe(get_multikills(df, joueur, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
        elif fonction_active == "objectifs":
            st.subheader("Profil objectifs")
 
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                saison = _selectbox_saison(df, key="obj_saison")
            with col2:
                queue = _selectbox_queue(key="obj_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="obj_joueur", defaut=pseudo_actif)
            with col4:
                role = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="obj_role")
 
            st.dataframe(get_objectifs(df, joueur, role=role, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
    elif categorie_active == "Champions":
        df_items = charger_donnees_items()
 
        if fonction_active == "meilleurs_champions_bar":
            st.subheader("Meilleurs champions (graphique)")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="champ_bar_saison")
            with col2:
                queue = _selectbox_queue(key="champ_bar_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="champ_bar_joueur", defaut=pseudo_actif)
 
            resultat = get_meilleurs_champions_bar(df, joueur, season=saison, queue_id=queue)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
        elif fonction_active == "meilleurs_champions_table":
            st.subheader("Meilleurs champions (tableau détaillé)")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="champ_table_saison")
            with col2:
                queue = _selectbox_queue(key="champ_table_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="champ_table_joueur", defaut=pseudo_actif)
 
            st.dataframe(get_meilleurs_champions_table(df, joueur, season=saison, queue_id=queue), use_container_width=True, hide_index=True)
 
        elif fonction_active == "builds":
            st.subheader("Builds fréquents")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="builds_saison")
            with col2:
                queue = _selectbox_queue(key="builds_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="builds_joueur", defaut=pseudo_actif)
 
            champions_joues = sorted(df[df["riotIdGameName"] == joueur]["championName"].dropna().unique())
            if not champions_joues:
                st.info("Ce joueur n'a aucune game enregistrée sur cette saison/file.")
            else:
                champion = st.selectbox("Champion", options=champions_joues, key="builds_champion")
                min_games = st.slider("Nombre de games minimum par build", 1, 10, 2, key="builds_min_games")
                st.dataframe(get_builds(df, df_items, joueur, champion, season=saison, queue_id=queue, min_games=min_games), use_container_width=True, hide_index=True)
 
        elif fonction_active == "meilleurs_items":
            st.subheader("Meilleurs items par rôle (toute la population)")
            st.caption("Ne dépend pas d'un pseudo précis : regarde tous les joueurs du dataset pour un champion/rôle donné.")
 
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                saison = _selectbox_saison(df, key="items_saison")
            with col2:
                queue = _selectbox_queue(key="items_queue")
            with col3:
                champion = st.selectbox("Champion", options=sorted(df["championName"].dropna().unique()), key="items_champion")
            with col4:
                role = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="items_role")
 
            col5, col6 = st.columns(2)
            with col5:
                rangs = sorted(df["soloqueue_tier"].dropna().unique())
                rang_choice = st.selectbox("Rang (optionnel)", options=["Tous les rangs"] + rangs, key="items_rang")
                rang = None if rang_choice == "Tous les rangs" else rang_choice
            with col6:
                min_games = st.slider("Nombre de games minimum par build", 3, 30, 10, key="items_min_games")
 
            st.dataframe(
                get_meilleurs_items(df, df_items, champion, role, rang=rang, season=saison, queue_id=queue, min_games=min_games),
                use_container_width=True, hide_index=True,
            )
 
    elif categorie_active == "Évolution":
 
        if fonction_active == "evolution_winrate":
            st.subheader("Évolution du winrate")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                saison = _selectbox_saison(df, key="evo_saison")
            with col2:
                queue = _selectbox_queue(key="evo_queue")
            with col3:
                joueur = _selectbox_joueur(df, key="evo_joueur", defaut=pseudo_actif)
 
            resultat = get_evolution_winrate(df, joueur, season=saison, queue_id=queue)
            st.plotly_chart(resultat["fig"], use_container_width=True)