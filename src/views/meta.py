import streamlit as st
import pandas as pd
 
from models.item import charger_donnees_items, stats_disponibles_item
from models.champion import charger_donnees_champions
from models.spell import charger_donnees_spells
from utils import patch_to_tuple
from controllers.meta import (
    get_changement_item,
    get_evolution_item,
    get_evolution_efficiency_item,
    get_comparaison_item,
    get_changement_champion,
    get_stats_disponibles_champion,
    get_evolution_champion,
    get_comparaison_champion,
    get_stat_niveau,
    get_difficulty_champion,
    get_changement_spell,
)
 
 
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
 
ICONES_CATEGORIE = {"Item": "🗡️", "Champion": "⚔️", "Spell": "✨"}
 
LABELS_MENU = {
    ("Item", "changement_item_patch"): "Changements entre deux patchs",
    ("Item", "evolution_item"): "Évolution d'un item",
    ("Item", "evolution_efficiency_item"): "Efficacité gold d'un item",
    ("Item", "comparaison_item"): "Comparer deux items",
    ("Champion", "changement_champion_patch"): "Changements entre deux patchs",
    ("Champion", "evolution_champion"): "Évolution d'un champion",
    ("Champion", "comparaison_stats_champion"): "Comparer deux champions",
    ("Champion", "stat_niveau"): "Stats à un niveau donné",
    ("Champion", "difficulty_champion_type"): "Champions par difficulté / type",
    ("Spell", "changement_spell_patch"): "Changements des sorts entre deux patchs",
}
 
OPTIONS_MENU = (
    [("Item", f) for f in ["changement_item_patch", "evolution_item", "evolution_efficiency_item", "comparaison_item"]]
    + [("Champion", f) for f in ["changement_champion_patch", "evolution_champion", "comparaison_stats_champion", "stat_niveau", "difficulty_champion_type"]]
    + [("Spell", f) for f in ["changement_spell_patch"]]
)
 
def load_view():
    st.set_page_config(page_title="Analyse Item, Champion & Spell", layout="wide")
    st.title("Analyse des items, des champion et des spells")
 
    df_champions = charger_donnees_champions()
    df_spells = charger_donnees_spells()
    df_items = charger_donnees_items()
 
    patches_item = sorted(df_items["patch"].unique(), key=patch_to_tuple, reverse=True)
    patches_champions = sorted(df_champions["patch"].unique(), key=patch_to_tuple, reverse=True)
    champions = sorted(df_champions["name"].dropna().unique())
    patches_spells = sorted(df_spells["patch"].unique(), key=patch_to_tuple, reverse=True)
 
    with st.sidebar:
        st.caption("🗡️ Item · ⚔️ Champion · ✨ Spell")
        categorie_active, fonction_active = st.radio(
            "Fonction",
            options=OPTIONS_MENU,
            format_func=lambda o: f"{ICONES_CATEGORIE[o[0]]} {LABELS_MENU[o]}",
            key="radio_menu",
            label_visibility="collapsed",
        )
 
    if categorie_active == "Item":
 
        if fonction_active == "changement_item_patch":
            st.subheader("Changements entre deux patchs")
 
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
                st.dataframe(tableau_changements, use_container_width=True)
 
        elif fonction_active == "evolution_item":
            st.subheader("Évolution d'un item au fil des patchs")
 
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
 
        elif fonction_active == "evolution_efficiency_item":
            st.subheader("Évolution de l'efficacité gold d'un item")
 
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
 
        elif fonction_active == "comparaison_item":
            st.subheader("Comparaison entre deux items")
 
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
 
    elif categorie_active == "Champion":
 
        if fonction_active == "changement_champion_patch":
            st.subheader("Changements entre deux patchs")
 
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
                st.dataframe(tableau_changements_champ, use_container_width=True)
 
        elif fonction_active == "evolution_champion":
            st.subheader("Évolution d'un champion au fil des patchs")
 
            champion_evo = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="evo_champion")
            stats_evo = get_stats_disponibles_champion(df_champions, champion_evo)
            # NOTE : clé volontairement renommée en "evo_stat_champion" (au lieu de
            # "evo_stat") pour ne plus entrer en collision avec le selectbox de
            # l'onglet Item > Évolution d'un item, qui utilise aussi "evo_stat".
            # Dans le fichier d'origine les deux onglets partageaient la même clé,
            # ce qui pouvait faire "fuiter" la sélection de stat de l'un vers
            # l'autre via st.session_state.
            stat_evo = st.selectbox("Statistique", options=stats_evo, index=stats_evo.index("HP"), key="evo_stat_champion")
 
            resultat = get_evolution_champion(df_champions, champion_evo, stat_evo)
            st.plotly_chart(resultat["fig"], use_container_width=True)
 
        elif fonction_active == "comparaison_stats_champion":
            st.subheader("Comparaison de deux champions")
 
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
 
        elif fonction_active == "stat_niveau":
            st.subheader("Stats d'un champion à un niveau donné")
 
            col1, col2, col3 = st.columns(3)
            with col1:
                patch_niveau = st.selectbox("Patch", options=patches_champions, index=0, key="niveau_patch")
            with col2:
                champion_niveau = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="niveau_champion")
            with col3:
                niveau = st.slider("Niveau", min_value=1, max_value=18, value=18, key="niveau_valeur")
 
            df_resultat = get_stat_niveau(df_champions, patch_niveau, niveau, champion_niveau)
            st.dataframe(df_resultat, use_container_width=True, hide_index=True)
 
        elif fonction_active == "difficulty_champion_type":
            st.subheader("Champions par difficulté et par type")
 
            types = ["Assassin", "Mage", "Ranged", "Melee", "Stealth", "Tank", "Pusher", "Recommended",
                    "Carry", "Fighter", "Jungler", "Support", "Marksman"]
 
            col1, col2, col3 = st.columns(3)
            with col1:
                patch_diff = st.selectbox("Patch", options=patches_champions, index=0, key="diff_patch")
            with col2:
                type_choice = st.selectbox("Type", options=["Tous les types"] + types, key="diff_type")
                type_diff = None if type_choice == "Tous les types" else type_choice
            with col3:
                filtrer_diff = st.checkbox("Filtrer par difficulté max", key="diff_filtrer")
                max_diff = st.slider("Difficulté max", 0, 10, 10, key="diff_max") if filtrer_diff else None
 
            resultat = get_difficulty_champion(df_champions, patch_diff, type_diff, max_diff)
            if resultat["avertissement"]:
                st.warning(resultat["avertissement"])
            st.dataframe(resultat["df"], use_container_width=True, hide_index=True)
 
    elif categorie_active == "Spell":
 
        if fonction_active == "changement_spell_patch":
            st.subheader("Changements des sorts entre deux patchs")
 
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
                st.dataframe(tableau_spells, use_container_width=True)