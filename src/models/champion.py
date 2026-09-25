import streamlit as st
import numpy as np
import pandas as pd 
from utils import patch_to_tuple

@st.cache_data
def charger_donnees_champions():
    df = pd.read_csv("data/champions_by_patch.csv")

    df = df.drop(index=df[df["patch"].str.startswith("0.")].index)

    corrections = {"Figher": "Fighter", "Suppport": "Support"}
    df["tags"] = df["tags"].str.split(r"[;,]", regex=True).apply(
        lambda tags: ";".join(corrections.get(tag.strip().capitalize(), tag.strip().capitalize()) for tag in tags)
    )

    df["stat_attackspeed"] = df["stat_attackspeed"].fillna(0.625 * (1 + df["stat_attackspeedoffset"])).round(3)

    return df

def stat_niveau(df, patch, niveau, champion):
    df_patch = df[df["patch"] == patch]
    df_champion = df_patch[df_patch["name"] == champion]

    hp_base = df_champion["stat_hp"].values[0]
    hp_perlevel = df_champion["stat_hpperlevel"].values[0]
    hp = hp_base + hp_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    mana_base = df_champion["stat_mp"].values[0]
    mana_perlevel = df_champion["stat_mpperlevel"].values[0]
    mana = mana_base + mana_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    armor_base = df_champion["stat_armor"].values[0]
    armor_perlevel = df_champion["stat_armorperlevel"].values[0]
    armor = armor_base + armor_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    magic_resist_base = df_champion["stat_spellblock"].values[0]
    magic_resist_perlevel = df_champion["stat_spellblockperlevel"].values[0]
    magic_resist = magic_resist_base + magic_resist_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    regen_hp_base = df_champion["stat_hpregen"].values[0]
    regen_hp_perlevel = df_champion["stat_hpregenperlevel"].values[0]
    regen_hp = regen_hp_base + regen_hp_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    regen_mana_base = df_champion["stat_mpregen"].values[0]
    regen_mana_perlevel = df_champion["stat_mpregenperlevel"].values[0]
    regen_mana = regen_mana_base + regen_mana_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    crit_base = df_champion["stat_crit"].values[0]
    crit_perlevel = df_champion["stat_critperlevel"].values[0]
    crit = crit_base + crit_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    ad_base = df_champion["stat_attackdamage"].values[0]
    ad_perlevel = df_champion["stat_attackdamageperlevel"].values[0]
    ad = ad_base + ad_perlevel * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1))

    if df_champion["stat_attackspeedoffset"].isna().values[0]:
        as_base = df_champion["stat_attackspeed"].values[0]
    else:
        as_base = 0.625 / (1 + df_champion["stat_attackspeedoffset"].values[0])

    bonus_as_pourcent = df_champion["stat_attackspeedperlevel"].values[0] * (niveau - 1) * (0.7025 + 0.0175 * (niveau - 1)) / 100
    as_final = as_base * (1 + bonus_as_pourcent)

    ms = df_champion["stat_movespeed"].values[0]
    range_ = df_champion["stat_attackrange"].values[0]
    resource_type = df_champion["partype"].values[0]

    resultat = {
        "HP": round(float(hp), 2),
        "Regen HP": round(float(regen_hp), 2),
    }

    if not pd.isna(resource_type):
        resultat[resource_type] = round(float(mana), 2)
        resultat[f"Regen {resource_type}"] = round(float(regen_mana), 2)

    resultat.update({
        "Armor": round(float(armor), 2),
        "Magic Resist": round(float(magic_resist), 2),
        "Crit": round(float(crit), 2),
        "Ad": round(float(ad), 2),
        "As": round(float(as_final), 3),
        "Ms": round(float(ms), 2),
        "range": round(float(range_), 2)
    })

    return resultat

def comparaison_stats_champion(df, patch, niveau, champion1, champion2=None):
    """Retourne (avertissement, labels, diffs, couleurs, valeurs1, valeurs2, nom1, nom2)."""
    df_patch = df[df["patch"] == patch]

    stat1 = stat_niveau(df, patch, niveau, champion1)
    avertissement = None
    nom1 = champion1

    if champion2:
        stat2 = stat_niveau(df, patch, niveau, champion2)
        nom2 = champion2

        ressource1 = df_patch[df_patch["name"] == champion1]["partype"].values[0]
        ressource2 = df_patch[df_patch["name"] == champion2]["partype"].values[0]

        if ressource1 != ressource2:
            stat1.pop(ressource1, None)
            stat1.pop(f"Regen {ressource1}", None)
            stat2.pop(ressource2, None)
            stat2.pop(f"Regen {ressource2}", None)
    else:
        ressource = df_patch[df_patch["name"] == champion1]["partype"].values[0]

        champions = df_patch["name"].unique()
        liste = [stat_niveau(df, patch, niveau, champion) for champion in champions]
        df_moyenne = pd.DataFrame(liste)
        stat2 = df_moyenne.mean(numeric_only=True).to_dict()
        nom2 = "Moyenne des champions"

        if not pd.isna(ressource):
            avertissement = (
                f"Attention : on ne compare la {ressource} de {champion1} qu'avec la moyenne des "
                f"champions ayant aussi la {ressource}."
            )

    stats_communes = [stat for stat in stat1 if stat in stat2]

    labels = []
    diffs = []
    for stat in stats_communes:
        valeur1 = stat1[stat]
        valeur2 = stat2[stat]
        if valeur2 == 0:
            continue
        diffs.append((valeur1 - valeur2) / valeur2 * 100)
        labels.append(stat)

    couleurs = ["#2ecc71" if d >= 0 else "#e74c3c" for d in diffs]

    valeurs1 = [stat1[stat] for stat in labels]
    valeurs2 = [stat2[stat] for stat in labels]

    return avertissement, labels, diffs, couleurs, valeurs1, valeurs2, nom1, nom2

def evolution_champion(df, champion, stat="HP"):
    df_champion = df[df["name"] == champion].copy()
    ressource = df_champion["partype"].values[0]
    stats = ["HP", "Regen HP", ressource, "Regen " + ressource, "Armor", "Magic Resist", "Crit", "Ad", "As", "Ms", "range"]

    if stat not in stats:
        raise ValueError(f"'{stat}' n'est pas une stat valide. Choisis parmi : {stats}")

    df_champion = df_champion.rename(columns={
        "stat_hp": "HP",
        "stat_mp": ressource,
        "stat_movespeed": "Ms",
        "stat_armor": "Armor",
        "stat_spellblock": "Magic Resist",
        "stat_attackrange": "range",
        "stat_hpregen": "Regen HP",
        "stat_mpregen": "Regen " + ressource,
        "stat_crit": "Crit",
        "stat_attackdamage": "Ad"
    })

    df_champion["As"] = np.where(
        df_champion["stat_attackspeedoffset"].isna(),
        df_champion["stat_attackspeed"],
        0.625 / (1 + df_champion["stat_attackspeedoffset"])
    )

    df_champion = df_champion[["patch"] + stats]

    return df_champion


def difficulty_champion_type(df, patch, type=None, max_difficulty=None):
    """Retourne (avertissement, df_diff)."""
    types = ["Assassin", "Mage", "Ranged", "Melee", "Stealth", "Tank", "Pusher", "Recommended",
             "Carry", "Fighter", "Jungler", "Support", "Marksman"]

    if type is not None and type not in types:
        raise ValueError(f"'{type}' n'est pas un type de champion valide. Choisis parmi : {types}")

    df_patch = df[df["patch"] == patch]

    if type:
        df_type = df_patch[df_patch["tags"].str.contains(type)]
    else:
        df_type = df_patch

    avertissement = None
    if max_difficulty == 0:
        avertissement = "Aucun champion n'a une difficulté égale à 0, choisis une difficulté entre 1 et 10."

    if max_difficulty:
        df_diff = df_type[df_type["difficulty"] <= max_difficulty]
    else:
        df_diff = df_type

    df_diff = df_diff[df_diff["difficulty"] != 0]
    df_diff = df_diff.sort_values(ascending=True, by="difficulty")
    df_diff = df_diff[["name", "difficulty", "attack", "defense", "magic"]]

    return avertissement, df_diff

def changement_champion_patch(df, patch_1, patch_2=None):
    all_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)

    if patch_2 is None:
        idx_patch_1 = all_patchs.index(patch_1)
        if idx_patch_1 == 0:
            return pd.DataFrame()
        patch_2 = all_patchs[idx_patch_1 - 1]

    df_patch_1 = df[df["patch"] == patch_1]
    df_patch_2 = df[df["patch"] == patch_2]

    colonne_a_exclure = ["id", "patch", "title", "tags", "attack", "defense", "magic", "difficulty",
                          "is_variant", "stat_attackspeedoffset"]
    df_patch_1 = df_patch_1.drop(columns=colonne_a_exclure)
    df_patch_2 = df_patch_2.drop(columns=colonne_a_exclure)

    df_patch_1 = df_patch_1.fillna(0)
    df_patch_2 = df_patch_2.fillna(0)

    if patch_to_tuple(patch_1) < patch_to_tuple(patch_2):
        df_avant, df_apres = df_patch_1, df_patch_2
    else:
        df_avant, df_apres = df_patch_2, df_patch_1

    df_fusion = pd.merge(df_avant, df_apres, on="key", suffixes=("_avant", "_apres"))

    liste = []
    stats_a_comparer = [c for c in df_avant.columns if c != "key"]
    for stat in stats_a_comparer:
        col_avant = stat + "_avant"
        col_apres = stat + "_apres"
        if col_avant not in df_fusion.columns or col_apres not in df_fusion.columns:
            continue

        lignes_changees = df_fusion[df_fusion[col_avant] != df_fusion[col_apres]]
        for _, ligne in lignes_changees.iterrows():
            liste.append({
                "champion_id": ligne["key"],
                "name": ligne["name_avant"],
                "stat": stat,
                "avant": ligne[col_avant],
                "apres": ligne[col_apres]
            })

    return pd.DataFrame(liste)