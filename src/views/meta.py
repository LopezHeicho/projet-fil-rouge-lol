import streamlit as st
import pandas as pd

from models.item import charger_donnees_items, stats_disponibles_item
from models.champion import charger_donnees_champions
from models.spell import charger_donnees_spells
from models.esport import annees_disponibles, charger_donnees_esport
from utils import patch_to_tuple, patch_oe_vers_majmin
from controllers.esport import get_confrontation_stats_winrate
from controllers.meta import (
    get_changement_item,
    get_classement_buff_nerf_item,
    classement_buff_nerf_champion,
    get_detail_buff_nerf_item,
    get_evolution_item,
    get_evolution_efficiency_item,
    get_comparaison_item,
    get_budget_item,
    get_classement_rework_item,
    get_detail_reworks_item,
    classement_rework_item,
    get_changement_champion,
    classement_buff_nerf_item,
    get_stats_disponibles_champion,
    get_evolution_champion,
    get_comparaison_champion,
    get_stat_niveau,
    get_difficulty_champion,
    get_classement_buff_nerf_champion,
    get_detail_buff_nerf_champion,
    get_power_creep,
    get_composition_roster,
    COULEURS_CLASSE,
    get_evolution_type_ressource,
    COULEURS_RESSOURCE,
    get_changement_spell,
    get_classement_buff_nerf_spell,
    classement_buff_nerf_spell,
    get_detail_buff_nerf_spell,
    get_confrontation_champion_winrate,
)


def couleur_changement(ligne):
    fond = {"buff": "color: #1a7f37; font-weight: 600", "nerf": "color: #c0392b; font-weight: 600"}.get(ligne["type_changement"], "")
    return [fond if col in ("avant", "apres") else "" for col in ligne.index]


def choisir_item(df, key_prefix, label="Item", patch=None, default=None):
    """Si `patch` est précisé, ne propose que les items qui existent sur ce patch."""
    df_options = df if patch is None else df[df["patch"] == patch]

    noms = sorted(df_options["name"].dropna().unique())
    index_defaut = noms.index(default) if default in noms else 0
    nom = st.selectbox(label, options=noms, index=index_defaut, key=f"{key_prefix}_nom")

    ids_possibles = df_options[df_options["name"] == nom]["item_id"].unique()
    item_id = None
    if len(ids_possibles) > 1:
        matches = df_options[df_options["name"] == nom].copy()
        matches["_patch_key"] = matches["patch"].apply(patch_to_tuple)
        matches = matches.sort_values("_patch_key")
        apercu = (
            matches.groupby("item_id")
            .agg(tags=("tags", "first"), patch_min=("patch", "first"), patch_max=("patch", "last"))
            .reset_index()
        )
        st.caption(f"Plusieurs versions de '{nom}' existent, précise laquelle :")
        st.dataframe(apercu, use_container_width=True)
        item_id = st.selectbox("item_id à utiliser", options=apercu["item_id"].tolist(), key=f"{key_prefix}_id")

    return nom, item_id

# ---------------------------------------------------------------------------
# Page Streamlit
# ---------------------------------------------------------------------------
#
# Organisation par FONCTION (pas par type de donnée) : chaque entrée de la
# sidebar correspond à un type d'analyse, et quand cette analyse existe pour
# plusieurs types de données (item/champion/spell), elle est proposée sous
# forme d'onglets à l'intérieur d'une même entrée plutôt que d'être dupliquée
# en plusieurs lignes de sidebar. Les entrées qui n'existent que pour un seul
# type (ex. budget_item_type, qui n'a pas d'équivalent champion/spell)
# restent des entrées simples, sans onglet.

ICONES_FONCTION = {
    "changements_patch": "🔀",
    "classement_buff_nerf": "🔀",
    "evolution": "🔀",
    "comparaison": "🔀",
    "filtrer_type": "🔀",
    "rework_item": "🗡️",
    "stats_vs_winrate_pro": "⚔️",
    "tendances_design": "⚔️",
}

ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}

LABELS_MENU = {
    "changements_patch": "Changements entre deux patchs",
    "classement_buff_nerf": "Classement selon les buffs/nerfs",
    "evolution": "Évolution au fil des patchs",
    "comparaison": "Comparer deux éléments",
    "filtrer_type": "Filtrer par type",
    "rework_item": "Classement des items reworkés",
    "stats_vs_winrate_pro": "Stats de base vs winrate pro",
    "tendances_design": "Tendances de design des champions",
}

OPTIONS_MENU = [
    # Groupé par icône (cf. légende en haut de la sidebar) : d'abord les
    # fonctions communes à plusieurs types (🔀 Item + Champion [+ Spell]),
    # puis les fonctions Item seul (🗡️), puis Champion seul (⚔️).
    "changements_patch",
    "classement_buff_nerf",
    "evolution",
    "comparaison",
    "filtrer_type",
    "rework_item",
    "stats_vs_winrate_pro",
    "tendances_design",
]

def load_view():
    st.set_page_config(page_title="Analyse Item, Champion & Spell", layout="wide", initial_sidebar_state="expanded")
    st.title("Analyse des items, des champion et des spells")

    df_champions = charger_donnees_champions()
    df_spells = charger_donnees_spells()
    df_items = charger_donnees_items()

    patches_item = sorted(df_items["patch"].unique(), key=patch_to_tuple, reverse=True)
    patches_champions = sorted(df_champions["patch"].unique(), key=patch_to_tuple, reverse=True)
    champions = sorted(df_champions["name"].dropna().unique())
    patches_spells = sorted(df_spells["patch"].unique(), key=patch_to_tuple, reverse=True)

    with st.sidebar:
        st.caption("🔀 Item + Champion (+ Spell) · 🗡️ Item seul · ⚔️ Champion seul")
        fonction_active = st.radio(
            "Fonction",
            options=OPTIONS_MENU,
            format_func=lambda o: f"{ICONES_FONCTION[o]} {LABELS_MENU[o]}",
            key="radio_menu",
            label_visibility="collapsed",
        )

    if fonction_active == "changements_patch":
        st.subheader("Changements entre deux patchs")

        onglet_item, onglet_champion, onglet_spell = st.tabs(["Item", "Champion", "Spell"])

        with onglet_item:
            col1, col2 = st.columns(2)
            with col1:
                patch_1 = st.selectbox("Patch", options=patches_item, index=0, key="changement_patch_1")
            with col2:
                mode_patch_2 = st.radio(
                    "Comparer à",
                    options=["Patch précédent", "Choisir un patch"],
                    index=0,
                    horizontal=True,
                    key="changement_mode",
                )

            patch_2 = None
            if mode_patch_2 == "Choisir un patch":
                autres_patches = [p for p in patches_item if p != patch_1]
                patch_2 = st.selectbox("Patch de comparaison", options=autres_patches, key="changement_patch_2")

            tableau_changements = get_changement_item(df_items, patch_1, patch_2)

            if tableau_changements.empty:
                st.info("Aucun changement détecté entre ces deux patchs (ou patch_1 est le tout premier patch disponible).")
            else:
                styler = tableau_changements.style.apply(couleur_changement, axis=1)
                styler = styler.hide(axis="columns", subset=["type_changement"])
                st.dataframe(styler, use_container_width=True)

        with onglet_champion:
            col1, col2 = st.columns(2)
            with col1:
                patch_1_champ = st.selectbox("Patch", options=patches_champions, index=0, key="changement_champ_patch_1")
            with col2:
                mode_patch_2_champ = st.radio(
                    "Comparer à",
                    options=["Patch précédent", "Choisir un patch"],
                    index=0,
                    horizontal=True,
                    key="changement_champ_mode",
                )

            patch_2_champ = None
            if mode_patch_2_champ == "Choisir un patch":
                autres_patches_champ = [p for p in patches_champions if p != patch_1_champ]
                patch_2_champ = st.selectbox("Patch de comparaison", options=autres_patches_champ, key="changement_champ_patch_2")

            tableau_changements_champ = get_changement_champion(df_champions, patch_1_champ, patch_2_champ)
            if tableau_changements_champ.empty:
                st.info("Aucun changement détecté entre ces deux patchs (ou patch_1 est le tout premier patch disponible).")
            else:
                styler = tableau_changements_champ.style.apply(couleur_changement, axis=1)
                styler = styler.hide(axis="columns", subset=["type_changement"])
                st.dataframe(styler, use_container_width=True)

        with onglet_spell:
            col1, col2 = st.columns(2)
            with col1:
                patch_1_spell = st.selectbox("Patch", options=patches_spells, index=0, key="spell_patch_1")
            with col2:
                mode_patch_2_spell = st.radio(
                    "Comparer à",
                    options=["Patch précédent", "Choisir un patch"],
                    index=0,
                    horizontal=True,
                    key="spell_mode",
                )

            patch_2_spell = None
            if mode_patch_2_spell == "Choisir un patch":
                autres_patches_spell = [p for p in patches_spells if p != patch_1_spell]
                patch_2_spell = st.selectbox("Patch de comparaison", options=autres_patches_spell, key="spell_patch_2")

            tableau_spells = get_changement_spell(df_spells, patch_1_spell, patch_2_spell)
            if tableau_spells.empty:
                st.info("Aucun changement détecté entre ces deux patchs (ou patch_1 est le tout premier patch disponible).")
            else:
                styler = tableau_spells.style.apply(couleur_changement, axis=1)
                styler = styler.hide(axis="columns", subset=["type_changement"])
                st.dataframe(styler, use_container_width=True)

    elif fonction_active == "classement_buff_nerf":
        st.subheader("Classement selon les buffs/nerfs")

        onglet_item, onglet_champion, onglet_spell = st.tabs(["Item", "Champion", "Spell"])

        with onglet_item:
            classement_complet, _ = classement_buff_nerf_item(df_items)

            nb_items = st.slider("Nombre d'items à afficher", min_value=5, max_value=len(classement_complet), value=10, step=1, key="classement_buff_nerf_nb_items")

            classement, fig = get_classement_buff_nerf_item(df_items, nb_items)
            if classement.empty:
                st.info("Aucun item buffé/nerfé trouvé dans les données.")
            else:
                with st.container(height=500):
                    st.plotly_chart(fig, use_container_width=True)

                st.caption("💡 Clique sur une ligne pour voir le détail des changements de cet item.")
                selection = st.dataframe(
                    classement,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                if selection.selection.rows:
                    item_id = classement.iloc[selection.selection.rows[0]]["item_id"]
                    name = classement.iloc[selection.selection.rows[0]]["name"]

                    st.subheader(f"Détail des buffs/nerfs de l'item {name}")

                    tableau_changements = get_detail_buff_nerf_item(df_items, item_id)
                    styler = tableau_changements.style.apply(couleur_changement, axis=1)
                    styler = styler.hide(axis="columns", subset=["type_changement"])
                    st.dataframe(styler, use_container_width=True)

        with onglet_champion:
            classement_complet, _ = classement_buff_nerf_champion(df_champions)

            nb_champions = st.slider("Nombre de champions à afficher", min_value=5, max_value=len(classement_complet), value=10, step=1, key="classement_buff_nerf_nb_champions")

            classement, fig = get_classement_buff_nerf_champion(df_champions, nb_champions)
            if classement.empty:
                st.info("Aucun champion buffé/nerfé trouvé dans les données.")
            else:
                with st.container(height=500):
                    st.plotly_chart(fig, use_container_width=True)

                st.caption("💡 Clique sur une ligne pour voir le détail des changements de ce champion.")
                selection = st.dataframe(
                    classement,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                if selection.selection.rows:
                    name = classement.iloc[selection.selection.rows[0]]["name"]

                    st.subheader(f"Détail des buffs/nerfs du champion {name}")

                    tableau_changements = get_detail_buff_nerf_champion(df_champions, name)
                    styler = tableau_changements.style.apply(couleur_changement, axis=1)
                    styler = styler.hide(axis="columns", subset=["type_changement"])
                    st.dataframe(styler, use_container_width=True)

        with onglet_spell:
            classement_complet, _ = classement_buff_nerf_spell(df_spells)

            nb_spells = st.slider("Nombre de champions à afficher", min_value=5, max_value=len(classement_complet), value=10, step=1, key="classement_buff_nerf_nb_spell")

            classement, fig = get_classement_buff_nerf_spell(df_spells, nb_spells)
            if classement.empty:
                st.info("Aucun sorts buffé/nerfé trouvé dans les données.")
            else:
                with st.container(height=500):
                    st.plotly_chart(fig, use_container_width=True)

                st.caption("💡 Clique sur une ligne pour voir le détail des changements de ce sort.")
                selection = st.dataframe(
                    classement,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                if selection.selection.rows:
                    name = classement.iloc[selection.selection.rows[0]]["name"]

                    st.subheader(f"Détail des buffs/nerfs du champion {name}")

                    tableau_changements = get_detail_buff_nerf_spell(df_spells, name)
                    styler = tableau_changements.style.apply(couleur_changement, axis=1)
                    styler = styler.hide(axis="columns", subset=["type_changement"])
                    st.dataframe(styler, use_container_width=True)

    elif fonction_active == "evolution":
        st.subheader("Évolution au fil des patchs")

        onglet_item, onglet_efficacite, onglet_champion = st.tabs(["Item", "Efficacité gold", "Champion"])

        with onglet_item:
            nom_evo, id_evo = choisir_item(df_items, key_prefix="evo", default="Doran's Blade")

            stats_disponibles = stats_disponibles_item(df_items, item=nom_evo, item_id=id_evo)
            if st.session_state.get("evo_stat") not in stats_disponibles:
                st.session_state.pop("evo_stat", None)
            index_defaut_stat = stats_disponibles.index("Cout d'achat") if "Cout d'achat" in stats_disponibles else 0
            stat_choice = st.selectbox(
                "Statistique à tracer",
                options=stats_disponibles,
                index=index_defaut_stat,
                key="evo_stat",
            )

            resultat = get_evolution_item(df_items, nom_evo, id_evo, stat_choice)

            if resultat["erreur"]:
                st.error(resultat["erreur"])
                if resultat["ambiguite"] is not None:
                    st.dataframe(resultat["ambiguite"], use_container_width=True)
            else:
                for texte in resultat["avertissements"]:
                    st.warning(texte)
                for fig in resultat["figures"]:
                    st.plotly_chart(fig, use_container_width=True)

        with onglet_efficacite:
            nom_evo_eff, id_evo_eff = choisir_item(df_items, key_prefix="evo_eff", default="Doran's Blade")

            resultat = get_evolution_efficiency_item(df_items, nom_evo_eff, id_evo_eff)

            if resultat["erreur"]:
                st.error(resultat["erreur"])
                if resultat["ambiguite"] is not None:
                    st.dataframe(resultat["ambiguite"], use_container_width=True)
            else:
                for texte in resultat["avertissements"]:
                    st.warning(texte)
                for fig in resultat["figures"]:
                    st.plotly_chart(fig, use_container_width=True)

        with onglet_champion:
            champion_evo = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="evo_champion")
            stats_evo = get_stats_disponibles_champion(df_champions, champion_evo)
            # NOTE : clé volontairement renommée en "evo_stat_champion" (au lieu de
            # "evo_stat") pour ne plus entrer en collision avec le selectbox de
            # l'onglet Item > Évolution d'un item, qui utilise aussi "evo_stat".
            stat_evo = st.selectbox("Statistique", options=stats_evo, index=stats_evo.index("HP"), key="evo_stat_champion")

            resultat = get_evolution_champion(df_champions, champion_evo, stat_evo)
            st.plotly_chart(resultat["fig"], use_container_width=True)

    elif fonction_active == "comparaison":
        st.subheader("Comparer deux éléments")

        onglet_item, onglet_champion = st.tabs(["Item", "Champion"])

        with onglet_item:
            patch_comparaison = st.selectbox("Patch", options=patches_item, index=0, key="comp_patch")

            col1, col2 = st.columns(2)
            with col1:
                nom_item1, id_item1 = choisir_item(df_items, key_prefix="comp_item1", label="Item 1", patch=patch_comparaison, default="Doran's Blade")
            with col2:
                mode_comparaison_item = st.radio(
                    "Comparer à",
                    options=["Moyenne du patch", "Un autre item"],
                    index=1,
                    horizontal=True,
                    key="comp_mode",
                )

            nom_item2, id_item2 = None, None
            if mode_comparaison_item == "Un autre item":
                nom_item2, id_item2 = choisir_item(df_items, key_prefix="comp_item2", label="Item 2", patch=patch_comparaison, default="Doran's Shield")

            resultat = get_comparaison_item(
                df_items, patch_comparaison,
                item1=nom_item1, item_id1=id_item1,
                item2=nom_item2, item_id2=id_item2,
            )

            if resultat["erreurs"]:
                for erreur in resultat["erreurs"]:
                    st.error(erreur)
                if resultat["ambiguites"]["item1"] is not None:
                    st.dataframe(resultat["ambiguites"]["item1"], use_container_width=True)
                if resultat["ambiguites"]["item2"] is not None:
                    st.dataframe(resultat["ambiguites"]["item2"], use_container_width=True)
            else:
                for texte in resultat["avertissements"]:
                    st.warning(texte)
                st.plotly_chart(resultat["fig"], use_container_width=True)

        with onglet_champion:
            col1, col2, col3 = st.columns(3)
            with col1:
                # NOTE : clé renommée "comp_patch_champion" (au lieu de "comp_patch")
                # pour la même raison que ci-dessus : "comp_patch" est déjà utilisée
                # par l'onglet Item > Comparer deux items.
                patch_comp = st.selectbox("Patch", options=patches_champions, index=0, key="comp_patch_champion")
            with col2:
                champion1 = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="comp_champion1")
            with col3:
                niveau_comp = st.slider("Niveau", min_value=1, max_value=18, value=18, key="comp_niveau")

            # NOTE : clé renommée "comp_mode_champion" (au lieu de "comp_mode"),
            # même raison : collision avec l'onglet Item > Comparer deux items.
            mode_comp = st.radio(
                "Comparer à",
                options=["Moyenne des champions", "Un autre champion"],
                index=1,
                horizontal=True,
                key="comp_mode_champion",
            )

            champion2 = None
            if mode_comp == "Un autre champion":
                autres_champions = [c for c in champions if c != champion1]
                index_defaut_champion2 = autres_champions.index("Lucian") if "Lucian" in autres_champions else 0
                champion2 = st.selectbox("Champion à comparer", options=autres_champions, index=index_defaut_champion2, key="comp_champion2")

            resultat = get_comparaison_champion(df_champions, patch_comp, champion1, champion2, niveau_comp)
            if resultat["avertissement"]:
                st.warning(resultat["avertissement"])
            st.plotly_chart(resultat["fig"], use_container_width=True)

    elif fonction_active == "stats_vs_winrate_pro":
        st.subheader("Stats de base vs winrate réel en pro")

        # Patch par defaut "intelligent" : les patchs champion (Data Dragon)
        # les plus recents peuvent etre plus recents que les patchs reellement
        # joues en pro sur l'annee par defaut (lag naturel, fin de saison...).
        # Sans ca, le patch le plus recent (index 0) peut n'avoir AUCUNE game
        # pro sur l'annee par defaut, et "Pas assez de games pro" s'affiche
        # meme pour un champion tres joue (ex. Jarvan IV, ~1880 games en 2026,
        # mais 0 sur le tout dernier patch champion si celui-ci n'a pas encore
        # ete joue en pro). On choisit donc le patch champion le plus recent
        # qui a reellement des games pro sur l'annee par defaut.
        annees_pro_defaut = annees_disponibles()
        df_esport_defaut = charger_donnees_esport([annees_pro_defaut[0]])
        patches_pro_defaut = set(
            df_esport_defaut[df_esport_defaut["position"] != "team"]["patch"].dropna().apply(patch_oe_vers_majmin)
        )
        patch_defaut = next(
            (p for p in patches_champions if ".".join(p.split(".")[:2]) in patches_pro_defaut),
            patches_champions[0],
        )
        index_patch_defaut = patches_champions.index(patch_defaut)

        onglet_un, onglet_tous = st.tabs(["Un champion", "Tous les champions"])

        with onglet_un:
            col1, col2, col3 = st.columns(3)
            with col1:
                patch_niveau = st.selectbox("Patch", options=patches_champions, index=index_patch_defaut, key="niveau_patch")
            with col2:
                champion_niveau = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="niveau_champion")
            with col3:
                niveau = st.slider("Niveau", min_value=1, max_value=18, value=18, key="niveau_valeur")

            df_resultat = get_stat_niveau(df_champions, patch_niveau, niveau, champion_niveau)
            st.dataframe(df_resultat, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Confronter à son vrai winrate en pro")

            col4, col5, col6 = st.columns(3)
            with col4:
                annees_pro = annees_disponibles()
                annee_pro = st.selectbox("Année (pro)", options=annees_pro, index=0, key="niveau_annee_pro")
                df_esport_niveau = charger_donnees_esport([annee_pro])
            with col5:
                role_pro = st.selectbox("Rôle (optionnel)", options=[None] + ROLES, format_func=lambda r: "Tous" if r is None else LABELS_ROLE[r], key="niveau_role_pro")
            with col6:
                base_ligue = df_esport_niveau[df_esport_niveau["position"] == role_pro] if role_pro else df_esport_niveau
                ligues_role = sorted(base_ligue["league"].dropna().unique())
                options_ligue = ["Toutes les ligues"] + ligues_role
                ligue_choisie = st.selectbox("Ligue pro (optionnel)", options=options_ligue, key="niveau_ligue_pro")
                ligue_pro = None if ligue_choisie == "Toutes les ligues" else ligue_choisie

            resultat_winrate = get_confrontation_champion_winrate(
                df_champions, df_esport_niveau, patch_niveau, niveau, champion_niveau, role=role_pro, league=ligue_pro,
            )
            if resultat_winrate["winrate_pro"] is None:
                st.info(f"Pas assez de games pro pour {champion_niveau} sur cette sélection.")
            else:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(f"Winrate pro réel de {champion_niveau}", f"{resultat_winrate['winrate_pro']['winrate']}%")
                with col_m2:
                    st.metric("Games pro prises en compte", resultat_winrate["winrate_pro"]["nb_played"])

        with onglet_tous:
            col1, col2, col3 = st.columns(3)
            with col1:
                patch_confront = st.selectbox("Patch", options=patches_champions, index=index_patch_defaut, key="confront_patch")
            with col2:
                annees_pro = annees_disponibles()
                annee_confront = st.selectbox("Année (pro)", options=annees_pro, index=0, key="confront_annee_pro")
                df_esport_confront = charger_donnees_esport([annee_confront])
            with col3:
                role_confront = st.selectbox("Rôle", options=ROLES, format_func=lambda r: LABELS_ROLE[r], key="confront_role")

            ligues_role = sorted(df_esport_confront[df_esport_confront["position"] == role_confront]["league"].dropna().unique())
            options_ligue = ["Toutes les ligues"] + ligues_role
            ligue_choisie = st.selectbox("Ligue pro (optionnel)", options=options_ligue, key="confront_ligue")
            ligue_confront = None if ligue_choisie == "Toutes les ligues" else ligue_choisie

            min_games_confront = st.slider("Nombre de games pro minimum par champion", 3, 30, 5, key="confront_min_games")

            resultat_confront = get_confrontation_stats_winrate(
                df_champions, df_esport_confront, patch_confront, role=role_confront, league=ligue_confront, min_games=min_games_confront,
            )
            if resultat_confront["table"].empty:
                st.info("Aucun champion ne correspond à cette sélection (essaie de baisser le nombre de games minimum).")
            else:
                st.plotly_chart(resultat_confront["fig"], use_container_width=True)
                st.dataframe(resultat_confront["table"], use_container_width=True, hide_index=True)

    elif fonction_active == "filtrer_type":
        st.subheader("Filtrer par type")

        onglet_item, onglet_champion = st.tabs(["Item (prix)", "Champion (difficulté)"])

        with onglet_item:
            types_item = ["Active", "Armor", "ArmorPenetration", "AttackSpeed", "Aura", "AbilityHaste",
                        "Boots", "Bilgewater", "Consumable", "CooldownReduction", "CriticalStrike",
                        "Damage", "GoldPer", "Health", "HealthRegen", "Jungle", "Lane", "LifeSteal",
                        "MagicPenetration", "MagicResist", "Mana", "ManaRegen", "Movement",
                        "NonbootsMovement", "OnHit", "Slow", "SpellBlock", "SpellDamage", "SpellVamp",
                        "Stealth", "Tenacity", "Trinket", "Vision"]

            col1, col2, col3 = st.columns(3)
            with col1:
                patch_budget = st.selectbox("Patch", options=patches_item, index=0, key="budget_patch")
            with col2:
                type_choice_budget = st.selectbox("Type", options=["Tous les types"] + types_item, key="budget_type")
                type_budget = None if type_choice_budget == "Tous les types" else type_choice_budget
            with col3:
                budget_min, budget_max = st.slider(
                    "Budget (or)",
                    min_value=0,
                    max_value=4000,
                    value=(2000, 3000),
                    step=100,
                    key="budget_max"
                )

            resultat = get_budget_item(df_items, patch_budget, type_budget, budget_min, budget_max)
            if resultat["avertissement"]:
                st.warning(resultat["avertissement"])
            st.dataframe(resultat["df"], use_container_width=True, hide_index=True)

        with onglet_champion:
            types = ["Assassin", "Mage", "Ranged", "Melee", "Stealth", "Tank", "Pusher", "Recommended",
                    "Carry", "Fighter", "Support", "Marksman"]

            col1, col2, col3 = st.columns(3)
            with col1:
                patch_diff = st.selectbox("Patch", options=patches_champions, index=0, key="diff_patch")
            with col2:
                type_choice = st.selectbox("Type", options=["Tous les types"] + types, key="diff_type")
                type_diff = None if type_choice == "Tous les types" else type_choice
            with col3:
                max_diff = st.slider("Difficulté max", 0, 10, 5, key="diff_max")

            resultat = get_difficulty_champion(df_champions, patch_diff, type_diff, max_diff)
            if resultat["avertissement"]:
                st.warning(resultat["avertissement"])
            st.dataframe(resultat["df"], use_container_width=True, hide_index=True)

    elif fonction_active == "rework_item":
        st.subheader("Classement des items reworkés")

        classement_complet = classement_rework_item(df_items)

        nb_items = st.slider("Nombre d'items à afficher", min_value=5, max_value=len(classement_complet), value=10, step=1, key="classement_rework_nb_items")

        classement, fig = get_classement_rework_item(df_items, nb_items)
        if classement.empty:
            st.info("Aucun item reworké trouvé dans les données.")
        else:
            with st.container(height=500):
                st.plotly_chart(fig, use_container_width=True)

            st.caption("💡 Clique sur une ligne pour voir le détail des reworks de cet item.")
            selection = st.dataframe(
                classement, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row"
            )

            lignes_selectionnees = selection["selection"]["rows"]
            if lignes_selectionnees:
                item_choisi = classement.iloc[lignes_selectionnees[0]]["name"]
                st.subheader(f"Détail des reworks de {item_choisi}")
                detail = get_detail_reworks_item(df_items, item_choisi)
                if detail.empty:
                    st.info("Aucun détail disponible.")
                else:
                    st.dataframe(detail, use_container_width=True, hide_index=True)

    elif fonction_active == "tendances_design":
        st.subheader("Tendances de design des champions")

        onglet_power_creep, onglet_composition, onglet_ressource = st.tabs([
            "Power creep", "Composition du roster", "Type de ressource"
        ])

        with onglet_power_creep:
            stat = ["HP", "Regen HP", "Mana", "Regen Mana", "Armor", "Magic Resist", "Ad", "As"]
            stat_power_creep = st.selectbox("Statistique", options=stat, index=0, key="power_creep_stat")

            fig = get_power_creep(df_champions, stat_power_creep)
            st.plotly_chart(fig, use_container_width=True)

        with onglet_composition:
            proportions_composition = st.toggle("Afficher en proportions (%)", value=False, key="composition_roster_proportions")
            classes_selection = st.multiselect(
                "Classes à afficher",
                options=list(COULEURS_CLASSE.keys()),
                default=list(COULEURS_CLASSE.keys()),
                key="composition_roster_classes"
            )

            if not classes_selection:
                st.info("Sélectionne au moins une classe.")
            else:
                composition, fig = get_composition_roster(df_champions, proportions_composition, classes_selection)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Voir le tableau"):
                    st.dataframe(composition, use_container_width=True)

        with onglet_ressource:
            proportions_ressource = st.toggle("Afficher en proportions (%)", value=False, key="evolution_ressource_proportions")
            categories_selection = st.multiselect(
                "Catégories à afficher",
                options=list(COULEURS_RESSOURCE.keys()),
                default=list(COULEURS_RESSOURCE.keys()),
                key="evolution_ressource_categories"
            )

            if not categories_selection:
                st.info("Sélectionne au moins une catégorie.")
            else:
                evolution, fig = get_evolution_type_ressource(df_champions, proportions_ressource, categories_selection)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Voir le tableau"):
                    st.dataframe(evolution, use_container_width=True)
