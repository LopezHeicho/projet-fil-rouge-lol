import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from models.item import evolution_item, evolution_efficiency_item, changement_item_patch, comparaison_item, charger_donnees_items, stats_disponibles_item
from models.champion import stat_niveau, comparaison_stats_champion, evolution_champion, difficulty_champion_type, changement_champion_patch, charger_donnees_champions
from models.spell import charger_donnees_spells, changement_spell_patch
from utils import patch_to_tuple

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
            
            tableau_changements = changement_item_patch(df_items, patch_1, patch_2)
            
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
            
            message_erreur, df_ambiguite, avertissements, nom_affiche, df_item, df_stats, stats_valides = evolution_item(
                df_items, item=nom_evo, item_id=id_evo, stat=stat_choice
            )
                
            if message_erreur:
                st.error(message_erreur)
                if df_ambiguite is not None:
                    st.dataframe(df_ambiguite, use_container_width=True)
            else:
                for texte in avertissements:
                    st.warning(texte)
                for stat_a_tracer in stats_valides:
                    fig = go.Figure(go.Scatter(
                        mode="lines",
                        x=df_item["patch"],
                        y=df_stats[stat_a_tracer],
                        line=dict(color="#2a78d6"),
                        hovertemplate=f"<b>{nom_affiche}</b><br>patch : %{{x}}<br><br>{stat_a_tracer} : %{{y}}<br>"
                    ))
                    fig.update_layout(
                        title=dict(text=f"Évolution de {stat_a_tracer} pour {nom_affiche}", x=0.5, xanchor="center"),
                        xaxis_title="Patch",
                        yaxis_title=stat_a_tracer,
                        xaxis=dict(type="category")
                    )
                    st.plotly_chart(fig, use_container_width=True)

        elif fonction_active == "evolution_efficiency_item":
            st.subheader("Évolution de l'efficacité gold d'un item")

            nom_evo_eff, id_evo_eff = choisir_item(df_items, key_prefix="evo_eff", default="Doran's Blade")

            message_erreur, df_ambiguite, avertissements, nom_affiche, df_item, df_stats, stats_valides = evolution_efficiency_item(
                df_items, item=nom_evo_eff, item_id=id_evo_eff
            )

            if message_erreur:
                st.error(message_erreur)
                if df_ambiguite is not None:
                    st.dataframe(df_ambiguite, use_container_width=True)
            else:
                for texte in avertissements:
                    st.warning(texte)
                for stat_a_tracer in stats_valides:
                    fig = go.Figure(go.Scatter(
                        mode="lines",
                        x=df_item["patch"],
                        y=df_stats[stat_a_tracer],
                        line=dict(color="#2a78d6"),
                        hovertemplate=f"<b>{nom_affiche}</b><br>patch : %{{x}}<br><br>{stat_a_tracer} : %{{y}}<br>"
                    ))
                    fig.update_layout(
                        title=dict(text=f"Évolution de l'efficacité gold pour {nom_affiche}", x=0.5, xanchor="center"),
                        xaxis_title="Patch",
                        yaxis_title=stat_a_tracer,
                        xaxis=dict(type="category")
                    )
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

            (erreurs, ambiguites, avertissements_comp, noms_stats, valeurs_norm_1, valeurs_norm_2,
             valeurs_brutes_1, valeurs_brutes_2, nom1_affiche, nom2_affiche) = comparaison_item(
                df_items, patch_comparaison,
                item1=nom_item1, item_id1=id_item1,
                item2=nom_item2, item_id2=id_item2,
            )

            if erreurs:
                for erreur in erreurs:
                    st.error(erreur)
                if ambiguites["item1"] is not None:
                    st.dataframe(ambiguites["item1"], use_container_width=True)
                if ambiguites["item2"] is not None:
                    st.dataframe(ambiguites["item2"], use_container_width=True)
            else:
                for texte in avertissements_comp:
                    st.warning(texte)

                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(
                    name=nom1_affiche,
                    x=noms_stats,
                    y=valeurs_norm_1,
                    customdata=valeurs_brutes_1,
                    hovertemplate="<b>%{x}</b><br>" + f"{nom1_affiche}" + " : %{customdata}<extra></extra>",
                ))
                fig_comp.add_trace(go.Bar(
                    name=nom2_affiche,
                    x=noms_stats,
                    y=valeurs_norm_2,
                    customdata=valeurs_brutes_2,
                    hovertemplate="<b>%{x}</b><br>" + f"{nom2_affiche}" + " : %{customdata}<extra></extra>",
                ))
                fig_comp.update_layout(
                    barmode="group",
                    title=dict(text=f"{nom1_affiche} par rapport à {nom2_affiche}", x=0.5, xanchor="center"),
                    yaxis_title="Valeur normalisée (% du max)",
                    xaxis_title="Stats",
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            
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
            
            tableau_changements_champ = changement_champion_patch(df_champions, patch_1_champ, patch_2_champ)
            if tableau_changements_champ.empty:
                st.info("Aucun changement détecté entre ces deux patchs (ou patch_1 est le tout premier patch disponible).")
            else:
                st.dataframe(tableau_changements_champ, use_container_width=True)

        elif fonction_active == "evolution_champion":
            st.subheader("Évolution d'un champion au fil des patchs")

            champion_evo = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="evo_champion")
            ressource_evo = df_champions[df_champions["name"] == champion_evo]["partype"].values[0]
            stats_evo = ["HP", "Regen HP", ressource_evo, "Regen " + ressource_evo, "Armor", "Magic Resist",
                        "Crit", "Ad", "As", "Ms", "range"]
            stat_evo = st.selectbox("Statistique", options=stats_evo, index=stats_evo.index("HP"), key="evo_stat")

            df_champion_evo = evolution_champion(df_champions, champion_evo, stat_evo)

            fig_evo = go.Figure(go.Scatter(
                mode="lines",
                x=df_champion_evo["patch"],
                y=df_champion_evo[stat_evo],
                line=dict(color="#2a78d6"),
                hovertemplate=f"<b>{champion_evo}</b><br>patch : %{{x}}<br><br>{stat_evo} : %{{y}}<br>"
            ))
            fig_evo.update_layout(
                title=dict(text=f"Évolution de la stat {stat_evo} au cours des patchs", x=0.5, xanchor="center"),
                xaxis_title="Patch",
                yaxis_title=stat_evo,
                xaxis=dict(type="category")
            )
            st.plotly_chart(fig_evo, use_container_width=True)

        elif fonction_active == "comparaison_stats_champion":
            st.subheader("Comparaison de deux champions")

            col1, col2, col3 = st.columns(3)
            with col1:
                patch_comp = st.selectbox("Patch", options=patches_champions, index=0, key="comp_patch")
            with col2:
                champion1 = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="comp_champion1")
            with col3:
                niveau_comp = st.slider("Niveau", min_value=1, max_value=18, value=18, key="comp_niveau")

            mode_comp = st.radio(
                "Comparer à",
                options=["Moyenne des champions", "Un autre champion"],
                index=1,
                horizontal=True,
                key="comp_mode",
            )

            champion2 = None
            if mode_comp == "Un autre champion":
                autres_champions = [c for c in champions if c != champion1]
                index_defaut_champion2 = autres_champions.index("Lucian") if "Lucian" in autres_champions else 0
                champion2 = st.selectbox("Champion à comparer", options=autres_champions, index=index_defaut_champion2, key="comp_champion2")

            avertissement_comp, labels, diffs, couleurs, valeurs1, valeurs2, nom1, nom2 = comparaison_stats_champion(
                df_champions, patch_comp, niveau_comp, champion1, champion2
            )
            if avertissement_comp:
                st.warning(avertissement_comp)

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=labels,
                y=diffs,
                marker_color=couleurs,
                text=[f"{d:+.1f}%" for d in diffs],
                textposition="outside",
                customdata=list(zip(valeurs1, valeurs2)),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + f"{nom1}" + ": %{customdata[0]:.2f}<br>"
                    + f"{nom2}" + ": %{customdata[1]:.2f}<br>"
                    "Différence : %{y:+.1f}%<extra></extra>"
                )
            ))
            fig_comp.update_layout(
                title=dict(text=f"{nom1} par rapport à {nom2} (%)", x=0.5, xanchor="center"),
                yaxis_title="Différence (%)",
                xaxis_title="Stats",
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        elif fonction_active == "stat_niveau":
            st.subheader("Stats d'un champion à un niveau donné")

            col1, col2, col3 = st.columns(3)
            with col1:
                patch_niveau = st.selectbox("Patch", options=patches_champions, index=0, key="niveau_patch")
            with col2:
                champion_niveau = st.selectbox("Champion", options=champions, index=champions.index("Kai'Sa"), key="niveau_champion")
            with col3:
                niveau = st.slider("Niveau", min_value=1, max_value=18, value=18, key="niveau_valeur")

            resultat = stat_niveau(df_champions, patch_niveau, niveau, champion_niveau)
            st.dataframe(
                pd.DataFrame(resultat.items(), columns=["Statistique", "Valeur"]),
                use_container_width=True,
                hide_index=True,
            )

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

            avertissement_diff, df_diff = difficulty_champion_type(df_champions, patch_diff, type_diff, max_diff)
            if avertissement_diff:
                st.warning(avertissement_diff)
            st.dataframe(df_diff, use_container_width=True, hide_index=True)

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

            tableau_spells = changement_spell_patch(df_spells, patch_1_spell, patch_2_spell)
            if tableau_spells.empty:
                st.info("Aucun changement détecté entre ces deux patchs (ou patch_1 est le tout premier patch disponible).")
            else:
                st.dataframe(tableau_spells, use_container_width=True)