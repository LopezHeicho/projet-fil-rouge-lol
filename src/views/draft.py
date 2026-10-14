import streamlit as st 
import pandas as pd

from models.draft import table_confrontation, table_synergie, modif_df
from models.joueur_live import charger_dataset_complet
from models.item import charger_donnees_items
from models.esport import charger_donnees_esport

from controllers.draft import get_score_counter, get_best_item_champion, get_best_runes_champion

ROLES = ["top", "jng", "mid", "bot", "sup"]
LABELS_ROLE = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "ADC", "sup": "Support"}



def load_view():
    st.set_page_config(page_title="Aide à la draft", layout="wide", initial_sidebar_state="expanded")
    st.title("Aide à la draft")

    df_pro = charger_donnees_esport([2025, 2026])
    df_joueur = charger_dataset_complet()
    df_items = charger_donnees_items()

    df_all = pd.concat([df_pro, modif_df(df_joueur)], axis=0)

    table_c = table_confrontation(df_all)
    table_s = table_synergie(df_all)



    col1, col2, col3 = st.columns([1, 4, 1])
    PLACEHOLDER = "-- Aucun --"

    all_champions = sorted(df_all["champion"].dropna().unique())

    # clés fixes pour les 10 slots de pick, définies une seule fois
    pick_allies_keys = [f"pick_ally_{i}" for i in range(5)]
    pick_adverses_keys = [f"pick_adv_{i}" for i in range(5)]
    toutes_les_cles_pick = pick_allies_keys + pick_adverses_keys

    with col1:
        ban_allies = st.multiselect("Ban alliés", all_champions, max_selections=5, key="ban_allies")

        for i, key in enumerate(pick_allies_keys):
            deja_pris = set(ban_allies) | set(st.session_state.get("ban_adverses", []))
            for autre_cle in toutes_les_cles_pick:
                if autre_cle != key:
                    valeur = st.session_state.get(autre_cle)
                    if valeur and valeur != PLACEHOLDER:
                        deja_pris.add(valeur)

            options = [PLACEHOLDER] + [c for c in all_champions if c not in deja_pris]
            st.selectbox(f"Pick allié {i + 1}", options, key=key)

    with col3:
        ban_adverses = st.multiselect("Ban adverses", all_champions, max_selections=5, key="ban_adverses")

        for i, key in enumerate(pick_adverses_keys):
            deja_pris = set(ban_allies) | set(ban_adverses)
            for autre_cle in toutes_les_cles_pick:
                if autre_cle != key:
                    valeur = st.session_state.get(autre_cle)
                    if valeur and valeur != PLACEHOLDER:
                        deja_pris.add(valeur)

            options = [PLACEHOLDER] + [c for c in all_champions if c not in deja_pris]
            st.selectbox(f"Pick adverse {i + 1}", options, key=key)

    pick_allies = [st.session_state[k] for k in pick_allies_keys if st.session_state.get(k) not in (None, PLACEHOLDER)]
    pick_adverses = [st.session_state[k] for k in pick_adverses_keys if st.session_state.get(k) not in (None, PLACEHOLDER)]

    with col2:
        role = st.selectbox("Ton rôle", options=ROLES, format_func=lambda r: LABELS_ROLE.get(r, r), key="role_draft")
        nombre_champion = st.slider("Nombre de champion", min_value=1, max_value=10, value=5, key="nombre_best_champion")

        if st.button("Voir les meilleurs champions"):
            best_champ, fig = get_score_counter(df_all, table_c, table_s, role, ban_allies, ban_adverses, nombre_champion, pick_allies, pick_adverses, min_games=5)
            st.session_state["resultat_best_champ"] = best_champ
            st.session_state["resultat_fig"] = fig

        if "resultat_best_champ" in st.session_state:
            st.plotly_chart(st.session_state["resultat_fig"], use_container_width=True)

            st.caption("💡 Clique sur un champion du tableau pour voir son build et ses runes recommandées.")
            selection = st.dataframe(
                st.session_state["resultat_best_champ"],
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            lignes_selectionnees = selection.selection.rows
            if lignes_selectionnees:
                index_ligne = lignes_selectionnees[0]
                champion_choisi = st.session_state["resultat_best_champ"].iloc[index_ligne]["champion"]

                st.subheader(f"Détails pour {champion_choisi}")

                best_item, first_item, boots = get_best_item_champion(df_joueur, df_items, champion_choisi, role)

                if first_item is None and boots is None and len(best_item) == 0:
                    st.warning("Échantillon de games ranked trop faible pour ce champion sur ce rôle : pas assez de données pour proposer un build.")
                else:
                    if first_item is not None:
                        st.write(f"Item de départ : {first_item['Item']}")
                    else:
                        st.info("Pas d'item de départ identifiable pour ce champion.")

                    if boots is not None:
                        st.write(f"Botte : {boots['Item']}")
                    else:
                        st.info("Pas de botte identifiable pour ce champion.")

                    st.dataframe(best_item, hide_index=True)

                runes = get_best_runes_champion(df_joueur, champion_choisi, role)
                if runes is None:
                    st.info("Pas assez de données pour recommander des runes pour ce champion.")
                else:
                    primary_key, pk0, pk1, pk2, pk3, sub_key, sk0, sk1, stat1, stat2, stat3 = runes
                    col_primaire, col_secondaire = st.columns(2)
                    with col_primaire:
                        st.write(f"**{primary_key}**")
                        st.write(pk0)
                        st.write(pk1)
                        st.write(pk2)
                        st.write(pk3)
                    with col_secondaire:
                        st.write(f"**{sub_key}**")
                        st.write(sk0)
                        st.write(sk1)
                    st.write(f"Shards : {stat1} / {stat2} / {stat3}")