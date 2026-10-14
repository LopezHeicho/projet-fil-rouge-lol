import streamlit as st

from src.router import redirect


def load_view():
    """Vue de la page d'accueil du projet"""

    st.title("Projet Fil Rouge — League of Legends Analytics")

    st.markdown(
        """
        Une application d'analyse de données autour de **League of Legends**, combinant
        données de joueurs classés (API Riot), données de la scène esportive
        professionnelle (Oracle's Elixir) et données officielles de jeu (Data Dragon)
        dans une seule interface.
        """
    )

    st.markdown("---")

    st.subheader("À propos de ce projet")
    st.info(
        "En reconversion professionnelle, j'ai choisi de construire ce projet autour de "
        "League of Legends : un jeu auquel je joue depuis plusieurs années et dont je "
        "suis également la scène compétitive avec beaucoup d'intérêt. Ce double regard, "
        "joueur et observateur de l'esport, m'a aidé à donner du sens aux données "
        "manipulées tout au long du projet. La partie la plus exigeante a été le "
        "traitement des items : les identifiants ne sont pas stables d'un patch à "
        "l'autre, certains objets changent de nom ou d'identifiant au fil des mises à "
        "jour, et plusieurs ID peuvent parfois désigner le même item réel (ou "
        "inversement, un même ID recouvrir des objets différents selon la période). "
        "Fiabiliser cette correspondance a demandé un vrai travail de nettoyage et de "
        "vérification des données, essentiel pour que les analyses de build restent "
        "justes."
    )

    st.markdown("---")

    st.subheader("Explorer l'application")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 🎮 Joueur lambda")
        st.caption("Historique de parties, stats agrégées, builds et runes favorites d'un joueur ranked.")
        if st.button("Explorer", key="home_joueur", use_container_width=True):
            redirect("joueur", reload=True)

    with col2:
        st.markdown("#### 🧠 Aide à la draft")
        st.caption("Recommandation de champions par rôle selon les bans/picks, combinant données pro et ranked.")
        if st.button("Explorer", key="home_draft", use_container_width=True):
            redirect("draft", reload=True)

    with col3:
        st.markdown("#### 🏆 Esport pro")
        st.caption("Stats équipes et joueurs professionnels (LEC, LCK, LCS, Worlds...).")
        if st.button("Explorer", key="home_esport", use_container_width=True):
            redirect("esport", reload=True)

    with col4:
        st.markdown("#### 📊 Méta")
        st.caption("Évolution et analyse des champions, items et sorts à travers les patchs.")
        if st.button("Explorer", key="home_meta", use_container_width=True):
            redirect("meta", reload=True)

    st.markdown("---")

    st.subheader("Sources de données")
    st.markdown(
        """
        - **Riot Developer API** (match-v5, league-v4) — historique de parties classées
        - **Data Dragon** — données officielles champions/items/sorts par patch
        - **Oracle's Elixir** — statistiques des matchs professionnels (ligues majeures)
        """
    )