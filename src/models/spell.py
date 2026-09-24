import streamlit as st
import pandas as pd
from utils import patch_to_tuple

@st.cache_data
def charger_donnees_spells():
    df = pd.read_csv(r"C:\Users\lopez\Desktop\Projet Fil Rouge\lol_meta_dataset\data\champion_spells_by_patch.csv")
    df = df.drop(index=df[df["patch"].str.startswith("0.")].index)
    return df

def changement_spell_patch(df, patch_1, patch_2=None):
    all_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)

    if patch_2 is None:
        idx_patch_1 = all_patchs.index(patch_1)
        if idx_patch_1 == 0:
            return pd.DataFrame()
        patch_2 = all_patchs[idx_patch_1 - 1]

    df_patch_1 = df[df["patch"] == patch_1]
    df_patch_2 = df[df["patch"] == patch_2]

    df_patch_1 = df_patch_1.fillna(0)
    df_patch_2 = df_patch_2.fillna(0)

    if patch_to_tuple(patch_1) < patch_to_tuple(patch_2):
        df_avant, df_apres = df_patch_1, df_patch_2
    else:
        df_avant, df_apres = df_patch_2, df_patch_1

    df_fusion = pd.merge(df_avant, df_apres, on=["champion_id", "spell_key"], suffixes=("_avant", "_apres"))

    liste = []
    stats_a_comparer = [c for c in df_avant.columns if c != "patch"]
    for stat in stats_a_comparer:
        col_avant = stat + "_avant"
        col_apres = stat + "_apres"
        if col_avant not in df_fusion.columns or col_apres not in df_fusion.columns:
            continue

        ligne_changees = df_fusion[df_fusion[col_avant] != df_fusion[col_apres]]
        for _, ligne in ligne_changees.iterrows():
            liste.append({
                "champion_id": ligne["champion_id"],
                "spell": ligne["spell_key"],
                "stat": stat,
                "avant": ligne[col_avant],
                "apres": ligne[col_apres]
            })

    return pd.DataFrame(liste)