import streamlit as st
import pandas as pd
from utils import patch_to_tuple, valeurs_numeriques

STATS_INVERSEES = {"cooldown", "cost"}

@st.cache_data(show_spinner="Chargement des données sorts...")
def charger_donnees_spells():
    df = pd.read_parquet("data/champion_spells_by_patch.parquet")
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

    df_patch_1 = df_patch_1.fillna({c: 0 if pd.api.types.is_numeric_dtype(df_patch_1[c]) else "0" for c in df_patch_1.columns})
    df_patch_2 = df_patch_2.fillna({c: 0 if pd.api.types.is_numeric_dtype(df_patch_2[c]) else "0" for c in df_patch_2.columns})

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
            valeurs_avant = valeurs_numeriques(ligne[col_avant])
            valeurs_apres = valeurs_numeriques(ligne[col_apres])

            type_changement = None
            if valeurs_avant is not None and valeurs_apres is not None:
                moyenne_avant = sum(valeurs_avant) / len(valeurs_avant)
                moyenne_apres = sum(valeurs_apres) / len(valeurs_apres)
                if moyenne_apres != moyenne_avant:
                    if stat in STATS_INVERSEES:
                        type_changement = "buff" if moyenne_apres < moyenne_avant else "nerf"
                    else:
                        type_changement = "buff" if moyenne_apres > moyenne_avant else "nerf"

            liste.append({
                "champion_id": ligne["champion_id"],
                "spell": ligne["spell_key"],
                "stat": stat,
                "avant": ligne[col_avant],
                "apres": ligne[col_apres],
                "type_changement" : type_changement
            })

    return pd.DataFrame(liste)

@st.cache_data(show_spinner="Analyse des changements de sorts...")
def classement_buff_nerf_spell(df):

    all_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)
    resultats = []

    for patch in all_patchs:
        df_changement = changement_spell_patch(df, patch)
        df_changement["patch"] = patch
        resultats.append(df_changement)

    resultats = pd.concat(resultats, ignore_index=True).round(2)

    classement = resultats.groupby("champion_id").agg(
        nb_changements=("type_changement", "count"),
        nb_buffs=("type_changement", lambda x: (x == "buff").sum()),
        nb_nerfs=("type_changement", lambda x: (x == "nerf").sum())
    ).sort_values("nb_changements", ascending=False).reset_index()
    classement = classement.rename(columns={"champion_id":"name"})

    return classement, resultats

def detail_buff_nerf_spell(df, name):
    _, resultats = classement_buff_nerf_spell(df)
    return resultats[resultats["champion_id"] == name]

