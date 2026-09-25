import streamlit as st 
import pandas as pd
import re
from utils import patch_to_tuple

# ---------------------------------------------------------------------------
# Constantes utilisées lors du nettoyage
# ---------------------------------------------------------------------------

STATS_VALIDES = {
    "Tenacity", "Lethality", "Ability Haste", "Grievous Wounds", "Heal and Shield Power",
    "Omnivamp", "Spell Vamp", "Life Steal", "Cooldown Reduction", "Magic Penetration",
    "Armor Penetration", "Critical Strike Chance", "Critical Strike Damage",
    "Attack Speed", "Movement Speed", "Move Speed", "Attack Damage", "Ability Power",
    "Armor", "Magic Resist", "Health", "Mana", "Health Regen", "Mana Regen",
    "Base Health Regen", "Base Mana Regen", "Slow Resistance", "Attack Range",
}

MAPPING_STATS_EXISTANTES = {
    "Movement Speed": ["Movement Speeed (flat)", "Movement speed (%)"],
    "Move Speed": ["Movement Speeed (flat)", "Movement speed (%)"],
    "Mana Regen": ["Mana regen (flat)"],
    "Base Mana Regen": ["Mana regen (flat)"],
    "Health Regen": ["Hp regen (flat)"],
    "Base Health Regen": ["Hp regen (flat)"],
    "Health": ["HP (flat)"],
    "Critical Strike Chance": ["Crit (%)"],
    "Ability Power": ["AP (flat)"],
    "Mana": ["Mana (flat)"],
    "Armor": ["Armor (flat)"],
    "Magic Resist": ["Magic resist (flat)"],
    "Attack Damage": ["AD (flat)"],
    "Attack Speed": ["Atack speed (%)"],
    "Life Steal": ["Vol de vie (%)"],
}

DICO_VALEUR_GOLD = {
    "AD (flat)": 35,
    "AP (flat)": 20,
    "Armor (flat)": 20,
    "Magic resist (flat)": 20,
    "HP (flat)": 2.667,
    "Mana (flat)": 1,
    "Movement Speeed (flat)": 12,
    "Hp regen (flat)": 3,
    "Mana regen (flat)": 4,
    "Ability Haste (flat)": 50,
    "Lethality (flat)": 30,
    "Magic Penetration (flat)": 46.67,
    "Crit (%)": 40,
    "Atack speed (%)": 25,
    "Movement speed (%)": 65.11,
    "Vol de vie (%)": 53.55,
    "Tenacity (%)": 10.33,
    "Armor Penetration (%)": 41.67,
    "Magic Penetration (%)": 46.15,
    "Omnivamp (%)": 46,
    "Spell Vamp (%)": 27.5,
    "Cooldown Reduction (%)": 26.67,
    "Slow Resistance (%)": 10.33,
    "Critical Strike Damage (%)": 0,
    "Health (%)": 0,
    "Armor Penetration (flat)": 0,
    "Grievous Wounds (%)": 0,
    "Heal and Shield Power (%)": 0,
    "Base Health Regen (%)": 0,
    "Base Mana Regen (%)": 0,
}

# ---------------------------------------------------------------------------
# Extraction des stats depuis le texte de description
# ---------------------------------------------------------------------------

def extraire_stats_texte(description):
    if not isinstance(description, str):
        return []

    while True:
        nouvelle_version = re.sub(r"\([^()]*\)", "", description)
        if nouvelle_version == description:
            break
        description = nouvelle_version

    resultats = []

    pattern_plus = r"(?<!\d)(?<!below )(?<!above )(?<!under )(?<!over )(?<!lose )\+?(\d+(?:\.\d+)?)(%)?[ \t]+((?:[A-Z][a-zA-Z]*[ \t]*)+)(?![ \t]*reduction)"
    for val, pct, nom in re.findall(pattern_plus, description):
        resultats.append({"valeur": float(val), "pourcentage": bool(pct), "stat": nom.strip()})

    pattern_increases = r"Increases[ \t]+((?:[A-Z][a-zA-Z]*[ \t]*)+?)[ \t]+by[ \t]+(\d+(?:\.\d+)?)%"
    for nom, val in re.findall(pattern_increases, description):
        resultats.append({"valeur": float(val), "pourcentage": True, "stat": nom.strip()})

    pattern_tenacity = r"[Rr]educes the duration of .*? by (\d+(?:\.\d+)?)%"
    for val in re.findall(pattern_tenacity, description):
        resultats.append({"valeur": float(val), "pourcentage": True, "stat": "Tenacity"})

    pattern_heal_shield = r"Heals and Shields on you are increased by (\d+(?:\.\d+)?)%"
    for val in re.findall(pattern_heal_shield, description):
        resultats.append({"valeur": float(val), "pourcentage": True, "stat": "Heal and Shield Power"})

    for r in resultats:
        if r["stat"] == "Wounds":
            r["stat"] = "Grievous Wounds"

    pattern_grievous_ancien = r"Grievous Wounds reduces .*? by (\d+(?:\.\d+)?)%"
    for val in re.findall(pattern_grievous_ancien, description):
        resultats.append({"valeur": float(val), "pourcentage": True, "stat": "Grievous Wounds"})

    return resultats


def stat_deja_presente(row, nom_stat, mapping):
    colonnes = mapping.get(nom_stat)
    if not colonnes:
        return False
    for col in colonnes:
        if col in row.index and pd.notna(row[col]) and row[col] != 0:
            return True
    return False

# ---------------------------------------------------------------------------
# Chargement + nettoyage (mis en cache)
# ---------------------------------------------------------------------------

@st.cache_data
def charger_donnees_items():
    df = pd.read_csv(
        "data/items_by_patch.csv",
        dtype={"item_id": str, "maps": str, "required_ally": str}
    )

    # Certains item_id (ex: 3632) apparaissent sur des patchs où l'item n'existe
    # plus, avec toutes les colonnes à 0 au lieu de NaN (name=0, tags=0, etc.).
    # On les enlève : un vrai item a toujours un nom sous forme de texte.
    df = df[df["name"].apply(lambda x: isinstance(x, str))]

    # On garde seulement les items jouables sur la faille de l'invocateur
    df = df[df["maps"].str.contains(r"(?:^|;)11(?:;|$)", na=False)]

    # Nettoyage des tags d'icônes du type "%i:ornnIcon%" présents dans certains noms
    df["name"] = df["name"].str.replace(r"%i:\w+%\s*", "", regex=True)

    df = df.rename(columns={
        "gold_total": "Cout d'achat",
        "stat_FlatMovementSpeedMod": "Movement Speeed (flat)",
        "stat_FlatMPRegenMod": "Mana regen (flat)",
        "stat_FlatHPRegenMod": "Hp regen (flat)",
        "stat_FlatHPPoolMod": "HP (flat)",
        "stat_FlatCritChanceMod": "Crit (%)",
        "stat_FlatMagicDamageMod": "AP (flat)",
        "stat_FlatMPPoolMod": "Mana (flat)",
        "stat_FlatArmorMod": "Armor (flat)",
        "stat_FlatSpellBlockMod": "Magic resist (flat)",
        "stat_FlatPhysicalDamageMod": "AD (flat)",
        "stat_PercentAttackSpeedMod": "Atack speed (%)",
        "stat_PercentMovementSpeedMod": "Movement speed (%)",
        "stat_PercentLifeStealMod": "Vol de vie (%)"
    })

    df["Crit (%)"] = df["Crit (%)"] * 100
    df["Atack speed (%)"] = df["Atack speed (%)"] * 100
    df["Movement speed (%)"] = df["Movement speed (%)"] * 100
    df["Vol de vie (%)"] = df["Vol de vie (%)"] * 100

    df = df[df["consumed"] != True]

    df["stat_extraite"] = df["description"].apply(extraire_stats_texte)

    df["stat_extraite"] = df.apply(
        lambda row: [
            s for s in row["stat_extraite"]
            if s["stat"] in STATS_VALIDES and not stat_deja_presente(row, s["stat"], MAPPING_STATS_EXISTANTES)
        ],
        axis=1
    )

    combinaisons_trouvees = set()
    for liste in df["stat_extraite"]:
        for stat in liste:
            combinaisons_trouvees.add((stat["stat"], stat["pourcentage"]))

    for nom_stat, est_pourcentage in combinaisons_trouvees:
        nom_colonne = f"extrait_{nom_stat}" + (" (%)" if est_pourcentage else "")
        df[nom_colonne] = df["stat_extraite"].apply(
            lambda liste, nom=nom_stat, pct=est_pourcentage: next(
                (s["valeur"] for s in liste if s["stat"] == nom and s["pourcentage"] == pct),
                None
            )
        )

    df = df.drop(columns="stat_extraite")

    fusions = {
        "extrait_Health": "HP (flat)",
        "extrait_Armor": "Armor (flat)",
        "extrait_Mana": "Mana (flat)",
        "extrait_Attack Damage": "AD (flat)",
        "extrait_Ability Power": "AP (flat)",
        "extrait_Magic Resist": "Magic resist (flat)",
        "extrait_Movement Speed": "Movement Speeed (flat)",
        "extrait_Move Speed": "Movement Speeed (flat)",
        "extrait_Movement Speed (%)": "Movement speed (%)",
        "extrait_Move Speed (%)": "Movement speed (%)",
        "extrait_Attack Speed (%)": "Atack speed (%)",
        "extrait_Life Steal (%)": "Vol de vie (%)",
        "extrait_Critical Strike Chance (%)": "Crit (%)",
        "extrait_Health Regen": "Hp regen (flat)",
        "extrait_Mana Regen": "Mana regen (flat)",
    }

    for col_extrait, col_cible in fusions.items():
        if col_extrait in df.columns:
            df[col_cible] = df[col_cible].fillna(df[col_extrait])
            df = df.drop(columns=[col_extrait])

    colonnes_restantes = [c for c in df.columns if c.startswith("extrait_")]
    df = df.rename(columns={
        c: (
            c.replace("extrait_", "")
            if "(%)" in c
            else c.replace("extrait_", "") + " (flat)"
        )
        for c in colonnes_restantes
    })
    df = df.rename(columns={c: c.replace("extrait_", "") for c in colonnes_restantes})

    df = df.fillna(0)

    df["efficiency_gold"] = 0
    for colonne, valeur in DICO_VALEUR_GOLD.items():
        if colonne in df.columns:
            df["efficiency_gold"] += df[colonne] * valeur
    df["efficiency_gold"] = ((df["efficiency_gold"] / df["Cout d'achat"]) * 100).round(2)

    return df

def get_patch_gaps(df, item_id, seuil=5):
    tous_les_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)
    patchs_item = sorted(df[df["item_id"] == item_id]["patch"].unique(), key=patch_to_tuple)

    if len(patchs_item) < 2:
        return []

    trous = []
    for i in range(len(patchs_item) - 1):
        p_avant, p_apres = patchs_item[i], patchs_item[i + 1]
        idx_avant = tous_les_patchs.index(p_avant)
        idx_apres = tous_les_patchs.index(p_apres)
        nb_manquants = idx_apres - idx_avant - 1

        if nb_manquants >= seuil:
            trous.append((p_avant, p_apres, nb_manquants))

    return trous

def resoudre_item_id(df, item=None, item_id=None):
    """Retourne (id_, message_erreur, df_ambiguite)."""
    if item_id is not None:
        if item_id not in df["item_id"].unique():
            return None, f"Aucun item avec item_id={item_id}.", None
        return item_id, None, None

    matches = df[df["name"] == item]
    ids_possibles = matches["item_id"].unique()

    if len(ids_possibles) == 0:
        return None, f"Aucun item trouvé avec le nom '{item}'.", None

    if len(ids_possibles) > 1:
        matches_triees = matches.copy()
        matches_triees["_patch_key"] = matches_triees["patch"].apply(patch_to_tuple)
        matches_triees = matches_triees.sort_values("_patch_key")
        apercu = (
            matches_triees.groupby("item_id")
            .agg(tags=("tags", "first"), patch_min=("patch", "first"), patch_max=("patch", "last"))
            .reset_index()
        )
        return None, f"'{item}' correspond à plusieurs item_id différents, précise lequel :", apercu

    return ids_possibles[0], None, None

def stats_disponibles_item(df, item=None, item_id=None):
    """Retourne la liste des stats réellement disponibles (non nulles) pour cet item."""
    id_, message_erreur, df_ambiguite = resoudre_item_id(df, item, item_id)
    if id_ is None:
        return []

    df_item = df[df["item_id"] == id_]

    colonnes_a_exclure = [
        "item_id", "name", "patch", "plaintext", "tags", "description", "colloq",
        "gold_base", "gold_sell", "purchasable", "depth", "from", "into", "maps",
        "image_full", "required_champion", "required_ally", "special_recipe",
        "in_store", "hide_from_all", "consumed", "consume_on_full", "stacks",
        "efficiency_gold"
    ]

    df_stats = df_item.drop(columns=[c for c in colonnes_a_exclure if c in df_item.columns])
    colonnes_non_nulles = (df_stats == 0).all()
    df_stats = df_stats.loc[:, ~colonnes_non_nulles]

    return df_stats.columns.tolist()


def evolution_item(df, item=None, item_id=None, stat=None, seuil_trou=5):
    """Retourne (message_erreur, df_ambiguite, avertissements, nom_affiche, df_item, df_stats, stats_valides)."""
    id_, message_erreur, df_ambiguite = resoudre_item_id(df, item, item_id)
    if id_ is None:
        return message_erreur, df_ambiguite, [], None, None, None, []

    nom_affiche = item if item is not None else df[df["item_id"] == id_]["name"].iloc[-1]

    avertissements = []
    trous = get_patch_gaps(df, id_, seuil=seuil_trou)
    for p_avant, p_apres, nb in trous:
        nom_avant = df[(df["item_id"] == id_) & (df["patch"] == p_avant)]["name"].values[0]
        tags_avant = df[(df["item_id"] == id_) & (df["patch"] == p_avant)]["tags"].values[0]
        nom_apres = df[(df["item_id"] == id_) & (df["patch"] == p_apres)]["name"].values[0]
        tags_apres = df[(df["item_id"] == id_) & (df["patch"] == p_apres)]["tags"].values[0]
        avertissements.append(
            f"Trou de {nb} patchs entre {p_avant} et {p_apres} pour item_id={id_}. "
            f"Avant : '{nom_avant}' (tags: {tags_avant}) — Après : '{nom_apres}' (tags: {tags_apres}). "
            "Vérifie que c'est bien le même item avant de faire confiance au graphique."
        )

    df_item = df[df["item_id"] == id_].copy()
    df_item["_patch_key"] = df_item["patch"].apply(patch_to_tuple)
    df_item = df_item.sort_values("_patch_key").drop(columns="_patch_key")

    colonnes_a_exclure = [
        "item_id", "name", "patch", "plaintext", "tags", "description", "colloq",
        "gold_base", "gold_sell", "purchasable", "depth", "from", "into", "maps",
        "image_full", "required_champion", "required_ally", "special_recipe",
        "in_store", "hide_from_all", "consumed", "consume_on_full", "stacks"
    ]
    if stat is None:
        colonnes_a_exclure.append("efficiency_gold")

    df_stats = df_item.drop(columns=[c for c in colonnes_a_exclure if c in df_item.columns])

    colonnes_non_nulles = (df_stats == 0).all()
    df_stats = df_stats.loc[:, ~colonnes_non_nulles]

    stats_a_tracer = [stat] if stat is not None else df_stats.columns.tolist()

    stats_valides = []
    for s in stats_a_tracer:
        if s not in df_stats.columns:
            avertissements.append(f"Stat '{s}' introuvable ou vide pour cet item.")
            continue
        stats_valides.append(s)

    return None, None, avertissements, nom_affiche, df_item, df_stats, stats_valides

def evolution_efficiency_item(df, item=None, item_id=None, seuil_trou=5):
    return evolution_item(df, item=item, item_id=item_id, stat="efficiency_gold", seuil_trou=seuil_trou)

def changement_item_patch(df, patch_1, patch_2=None):
    all_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)

    if patch_2 is None:
        idx_patch_1 = all_patchs.index(patch_1)
        if idx_patch_1 == 0:
            return pd.DataFrame()
        patch_2 = all_patchs[idx_patch_1 - 1]

    df_patch_1 = df[df["patch"] == patch_1]
    df_patch_2 = df[df["patch"] == patch_2]

    colonnes_a_exclure = [
        "patch", "plaintext", "tags", "description", "colloq", "gold_base", "gold_sell", "purchasable",
        "depth", "from", "into", "maps", "image_full", "required_champion", "required_ally",
        "special_recipe", "in_store", "hide_from_all", "consumed", "consume_on_full", "stacks",
    ]
    df_patch_1 = df_patch_1.drop(columns=colonnes_a_exclure)
    df_patch_2 = df_patch_2.drop(columns=colonnes_a_exclure)

    df_patch_1 = df_patch_1.fillna(0)
    df_patch_2 = df_patch_2.fillna(0)

    if patch_to_tuple(patch_1) < patch_to_tuple(patch_2):
        df_avant, df_apres = df_patch_1, df_patch_2
    else:
        df_avant, df_apres = df_patch_2, df_patch_1

    df_fusion = pd.merge(df_avant, df_apres, on="item_id", suffixes=("_avant", "_apres"))

    liste = []
    stats_a_comparer = [c for c in df_avant.columns if c != "item_id"]
    for stat in stats_a_comparer:
        col_avant = stat + "_avant"
        col_apres = stat + "_apres"
        if col_avant not in df_fusion.columns or col_apres not in df_fusion.columns:
            continue
        ligne_changees = df_fusion[df_fusion[col_avant] != df_fusion[col_apres]]
        for _, ligne in ligne_changees.iterrows():
            liste.append({
                "item_id": ligne["item_id"],
                "name": ligne["name_avant"],
                "stat": stat,
                "avant": ligne[col_avant],
                "apres": ligne[col_apres]
            })

    return pd.DataFrame(liste)

def comparaison_item(df, patch, item1=None, item_id1=None, item2=None, item_id2=None, seuil_trou=5):
    """Retourne (erreurs, ambiguites, avertissements, noms_stats, valeurs_norm_1, valeurs_norm_2, valeurs_brutes_1, valeurs_brutes_2, nom_item1, nom_item2)."""
    erreurs = []
    ambiguites = {"item1": None, "item2": None}

    id_1, message_1, ambiguite_1 = resoudre_item_id(df, item1, item_id1)
    if id_1 is None:
        erreurs.append(message_1)
        ambiguites["item1"] = ambiguite_1

    item2_demande = item_id2 is not None or item2 is not None
    id_2 = None
    if item2_demande:
        id_2, message_2, ambiguite_2 = resoudre_item_id(df, item2, item_id2)
        if id_2 is None:
            erreurs.append(message_2)
            ambiguites["item2"] = ambiguite_2

    if id_1 is None or (item2_demande and id_2 is None):
        return erreurs, ambiguites, [], [], [], [], [], [], None, None

    avertissements = []
    for id_courant in [id_1, id_2]:
        if id_courant is None:
            continue
        trous = get_patch_gaps(df, id_courant, seuil=seuil_trou)
        for p_avant, p_apres, nb in trous:
            nom_avant = df[(df["item_id"] == id_courant) & (df["patch"] == p_avant)]["name"].values[0]
            tags_avant = df[(df["item_id"] == id_courant) & (df["patch"] == p_avant)]["tags"].values[0]
            nom_apres = df[(df["item_id"] == id_courant) & (df["patch"] == p_apres)]["name"].values[0]
            tags_apres = df[(df["item_id"] == id_courant) & (df["patch"] == p_apres)]["tags"].values[0]
            avertissements.append(
                f"Trou de {nb} patchs entre {p_avant} et {p_apres} pour item_id={id_courant}. "
                f"Avant : '{nom_avant}' (tags: {tags_avant}) — Après : '{nom_apres}' (tags: {tags_apres})."
            )

    colonnes_a_exclure = [
        "name", "patch", "plaintext", "tags", "description", "colloq",
        "gold_base", "gold_sell", "purchasable", "depth", "from", "into", "maps",
        "image_full", "required_champion", "required_ally", "special_recipe",
        "in_store", "hide_from_all", "consumed", "consume_on_full", "stacks"
    ]

    df_patch = df[df["patch"] == patch]
    df_item1 = df_patch[df_patch["item_id"] == id_1]

    if id_2 is None:
        valeur1 = df_item1["efficiency_gold"].values[0]
        valeur2 = df_patch["efficiency_gold"].mean().round(2)
        valeurs_comparees = {"efficiency_gold": (valeur1, valeur2)}
    else:
        df_item2 = df_patch[df_patch["item_id"] == id_2]

        df_item1_stats = df_item1.drop(columns=[c for c in colonnes_a_exclure + ["item_id"] if c in df_item1.columns])
        df_item2_stats = df_item2.drop(columns=[c for c in colonnes_a_exclure + ["item_id"] if c in df_item2.columns])

        toutes_les_stats = set(df_item1_stats.columns) | set(df_item2_stats.columns)

        valeurs_comparees = {}
        for stat in toutes_les_stats:
            valeur1 = df_item1_stats[stat].values[0] if stat in df_item1_stats.columns else 0
            valeur2 = df_item2_stats[stat].values[0] if stat in df_item2_stats.columns else 0
            valeur1 = 0 if pd.isna(valeur1) else valeur1
            valeur2 = 0 if pd.isna(valeur2) else valeur2
            valeurs_comparees[stat] = (valeur1, valeur2)

    noms_stats, valeurs_norm_1, valeurs_norm_2 = [], [], []
    valeurs_brutes_1, valeurs_brutes_2 = [], []

    for stat, (v1, v2) in valeurs_comparees.items():
        if v1 == 0 and v2 == 0:
            continue
        max_val = max(v1, v2)
        norm1 = (v1 / max_val * 100) if max_val != 0 else 0
        norm2 = (v2 / max_val * 100) if max_val != 0 else 0
        noms_stats.append(stat)
        valeurs_norm_1.append(norm1)
        valeurs_norm_2.append(norm2)
        valeurs_brutes_1.append(v1)
        valeurs_brutes_2.append(v2)

    nom_item1 = item1 or f"item_id={id_1}"
    nom_item2 = item2 if item2 is not None else "moyenne du patch"

    return erreurs, ambiguites, avertissements, noms_stats, valeurs_norm_1, valeurs_norm_2, valeurs_brutes_1, valeurs_brutes_2, nom_item1, nom_item2