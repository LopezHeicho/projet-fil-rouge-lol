import streamlit as st 
import pandas as pd
import re
import difflib
from utils import patch_to_tuple, valeurs_numeriques

# ---------------------------------------------------------------------------
# Constantes utilisées lors du nettoyage
# ---------------------------------------------------------------------------

STATS_INVERSEES = {"Cout d'achat"}

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

@st.cache_data(show_spinner="Chargement des données items...")
def charger_donnees_items():
    df = pd.read_parquet("data/items_by_patch.parquet")
    df[["item_id", "maps", "required_ally"]] = df[["item_id", "maps", "required_ally"]].astype(str)
    df = df.replace(r"^game_item_\w+_\d+$", None, regex=True)

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

    colonnes_texte = ["plaintext", "description"]
    colonnes_a_remplir = [c for c in df.columns if c not in colonnes_texte]
    df[colonnes_a_remplir] = df[colonnes_a_remplir].fillna(0)

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
        "special_recipe", "in_store", "hide_from_all", "consumed", "consume_on_full", "stacks", "efficiency_gold",
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
                "item_id": ligne["item_id"],
                "name": ligne["name_avant"],
                "stat": stat,
                "avant": ligne[col_avant],
                "apres": ligne[col_apres],
                "type_changement" : type_changement
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

def budget_item_type(df, patch, type=None, budget_min=None, budget_max=None):
    """Retourne (avertissement, df_budget)."""
    df_patch = df[df["patch"] == patch]

    df_patch = df_patch[df_patch["purchasable"] == True]
    df_patch = df_patch[df_patch["maps"].str.contains("11", na=False)]

    if type:
        df_type = df_patch[df_patch["tags"].str.contains(type, case=False, na=False)]
    else:
        df_type = df_patch

    avertissement = None
    if type and df_type.empty:
        avertissement = f"Aucun item avec le tag '{type}' trouvé sur le patch {patch}."

    df_budget = df_type[
        (df_type["Cout d'achat"] >= budget_min) & (df_type["Cout d'achat"] <= budget_max)
    ]

    df_budget = df_budget.sort_values(ascending=True, by="Cout d'achat")
    df_budget = df_budget[["name", "tags", "Cout d'achat"]]

    return avertissement, df_budget

def _fusionner_doublons_item_id(df_sr):
    """Detecte les cas ou plusieurs item_id partagent le meme nom sur le
    meme patch avec des stats identiques (doublons Data Dragon, ex. Rod of
    Ages 6657/326657), et les fusionne vers un seul item_id canonique."""
    colonnes_stats = [c for c in df_sr.columns if c.startswith("stat_")]
    colonnes_comparaison = colonnes_stats + ["gold_base", "gold_total", "gold_sell", "plaintext"]
    colonnes_comparaison = [c for c in colonnes_comparaison if c in df_sr.columns]

    mapping_fusion = {}
    for (name, patch), lignes in df_sr.groupby(["name", "patch"]):
        ids = lignes["item_id"].unique()
        if len(ids) < 2:
            continue
        lignes_uniques = lignes[colonnes_comparaison].drop_duplicates()
        if len(lignes_uniques) == 1:
            id_canonique = sorted(ids, key=str)[0]
            for autre_id in ids:
                if autre_id != id_canonique:
                    mapping_fusion[autre_id] = id_canonique

    df_fusionne = df_sr.copy()
    df_fusionne["item_id"] = df_fusionne["item_id"].replace(mapping_fusion)
    return df_fusionne


def _texte_effet_seul(texte):
    """Retire le bloc de stats brutes (lignes "<nombre> <NomStat>") pour ne
    garder que le texte qui decrit vraiment le passif/actif, puis retire les
    chiffres restants."""
    if not isinstance(texte, str):
        return None
    lignes = texte.split("\n")
    lignes_effet = [l for l in lignes if not re.match(r"^\+?\d+(\.\d+)?%?\s+[A-Z]", l.strip())]
    texte_effet = " ".join(lignes_effet)
    texte_effet = re.sub(r"\d+(\.\d+)?%?", "", texte_effet)
    return re.sub(r"\s+", " ", texte_effet).strip()


def _sont_similaires(texte_a, texte_b, seuil=0.75):
    """True si deux textes sont assez proches pour etre consideres comme
    'le meme kit' malgre de petites differences de formulation (ou des
    placeholders Data Dragon non resolus comme {{ Item_Mythic_Passive }}
    qui deviennent du texte reel selon la version)."""
    if not isinstance(texte_a, str) or not isinstance(texte_b, str):
        return texte_a == texte_b
    return difflib.SequenceMatcher(None, texte_a, texte_b).ratio() >= seuil


def _reworks_plaintext(df_item_id, patches_tries, seuil_trou=50):
    df_tri = df_item_id.copy()
    df_tri["_patch_key"] = df_tri["patch"].apply(patch_to_tuple)
    df_tri = df_tri.sort_values("_patch_key").drop_duplicates(subset="patch").reset_index(drop=True)

    index_patch = {p: i for i, p in enumerate(patches_tries)}
    indices_globaux = df_tri["patch"].map(index_patch)
    ecarts = indices_globaux.diff()

    trous = ecarts[ecarts > seuil_trou]
    if len(trous) > 0:
        derniere_position_trou = trous.index[-1]
        df_tri = df_tri.iloc[derniere_position_trou:].reset_index(drop=True)

    texte_kit = df_tri["plaintext"]
    if "description" in df_tri.columns:
        texte_kit = texte_kit.where(texte_kit.notna(), df_tri["description"].apply(_texte_effet_seul))

    texte_prec = texte_kit.shift()
    patch_prec = df_tri["patch"].shift()

    masque_changement = texte_prec.notna() & ~pd.Series(
        [_sont_similaires(a, b) for a, b in zip(texte_prec, texte_kit)],
        index=texte_kit.index,
    )

    df_evt = pd.DataFrame({
        "type": "Changement de kit",
        "patch_avant": patch_prec[masque_changement],
        "patch_apres": df_tri.loc[masque_changement, "patch"],
        "avant": texte_prec[masque_changement],
        "apres": texte_kit[masque_changement],
    })
    return df_evt.to_dict("records")


def _construire_lineages(df_sr):
    """Regroupe les item_id en 'lignees' : un item peut changer de nom au fil
    du temps sans changer d'item_id (ex. Luden's Echo -> Luden's Tempest ->
    Luden's Echo), et peut aussi changer d'item_id en gardant son nom (vrai
    nouvel identifiant Data Dragon). Deux item_id appartiennent a la meme
    lignee des qu'ils ont, a un moment ou un autre, porte le meme nom
    (composantes connexes du graphe nom <-> item_id).

    Retourne une liste de dicts {"ids": [...], "nom_affiche": str}, ou
    nom_affiche est le nom porte au patch le plus recent de la lignee."""
    noms_par_id = df_sr.groupby("item_id")["name"].apply(set).to_dict()
    ids_par_nom = df_sr.groupby("name")["item_id"].apply(set).to_dict()

    ids_non_visites = set(df_sr["item_id"].unique())
    lineages = []

    while ids_non_visites:
        depart = ids_non_visites.pop()
        a_explorer = [depart]
        ids_lineage = {depart}

        while a_explorer:
            id_courant = a_explorer.pop()
            for nom in noms_par_id.get(id_courant, set()):
                for autre_id in ids_par_nom.get(nom, set()):
                    if autre_id not in ids_lineage:
                        ids_lineage.add(autre_id)
                        ids_non_visites.discard(autre_id)
                        a_explorer.append(autre_id)

        lignes_lineage = df_sr[df_sr["item_id"].isin(ids_lineage)].copy()
        lignes_lineage["_patch_key"] = lignes_lineage["patch"].apply(patch_to_tuple)
        nom_affiche = lignes_lineage.sort_values("_patch_key")["name"].iloc[-1]

        lineages.append({"ids": sorted(ids_lineage, key=str), "nom_affiche": nom_affiche})

    return lineages


@st.cache_data(show_spinner="Analyse des reworks d'items...")
def classement_rework_item(df):
    """Classement des items (par lignee, cf _construire_lineages) selon le
    nombre total de reworks : changements d'item_id (hors doublons Data
    Dragon et hors objets simultanement differents type Enchantment) +
    changements de kit (plaintext, ou description en repli) a item_id
    constant."""
    df_sr = df[df["maps"].str.contains("11", na=False)]
    df_sr = df_sr[df_sr["purchasable"] != False]
    df_sr = _fusionner_doublons_item_id(df_sr)

    simultane = df_sr.groupby(["name", "patch"])["item_id"].nunique()
    noms_simultanes = set(simultane[simultane > 1].index.get_level_values("name"))

    lineages = _construire_lineages(df_sr)
    patches_tries = sorted(df_sr["patch"].unique(), key=patch_to_tuple)

    resultats = []
    for lineage in lineages:
        ids = lineage["ids"]
        lignes_lineage = df_sr[df_sr["item_id"].isin(ids)]

        if noms_simultanes & set(lignes_lineage["name"].unique()):
            continue

        nb_changements_id = len(ids) - 1

        nb_changements_kit = 0
        for item_id in ids:
            historique_id = df_sr[df_sr["item_id"] == item_id]
            nb_changements_kit += len(_reworks_plaintext(historique_id, patches_tries))

        total = nb_changements_id + nb_changements_kit
        if total > 0:
            resultats.append({
                "name": lineage["nom_affiche"],
                "nb_changements_id": nb_changements_id,
                "nb_changements_kit": nb_changements_kit,
                "nb_reworks": total,
            })

    classement = pd.DataFrame(resultats).sort_values("nb_reworks", ascending=False).reset_index(drop=True)
    return classement


@st.cache_data(show_spinner="Détail des changements de l'item...")
def detail_reworks_item(df, name):
    """Detail chronologique de tous les reworks (changements d'item_id et
    changements de kit) pour la lignee complete de l'item portant ce nom a
    un moment ou un autre de son histoire."""
    df_sr = df[df["maps"].str.contains("11", na=False)]
    df_sr = _fusionner_doublons_item_id(df_sr)

    lineages = _construire_lineages(df_sr)
    patches_tries = sorted(df_sr["patch"].unique(), key=patch_to_tuple)
    lineage = next(
        (l for l in lineages if name in df_sr[df_sr["item_id"].isin(l["ids"])]["name"].unique()),
        None
    )
    if lineage is None:
        return pd.DataFrame()

    ids = lineage["ids"]
    lignes_lineage = df_sr[df_sr["item_id"].isin(ids)].copy()
    lignes_lineage["_patch_key"] = lignes_lineage["patch"].apply(patch_to_tuple)

    ids_tries = sorted(
        ids,
        key=lambda i: lignes_lineage[lignes_lineage["item_id"] == i]["_patch_key"].min()
    )

    evenements = []
    for id_avant, id_apres in zip(ids_tries, ids_tries[1:]):
        historique_avant = lignes_lineage[lignes_lineage["item_id"] == id_avant].sort_values("_patch_key")
        historique_apres = lignes_lineage[lignes_lineage["item_id"] == id_apres].sort_values("_patch_key")
        evenements.append({
            "type": "Nouvel identifiant",
            "patch_avant": historique_avant["patch"].iloc[-1],
            "patch_apres": historique_apres["patch"].iloc[0],
            "avant": f"item_id {id_avant}",
            "apres": f"item_id {id_apres}",
        })

    for item_id in ids:
        historique_id = df_sr[df_sr["item_id"] == item_id]
        evenements.extend(_reworks_plaintext(historique_id, patches_tries))

    df_evenements = pd.DataFrame(evenements)
    if not df_evenements.empty:
        df_evenements["_tri"] = df_evenements["patch_apres"].apply(patch_to_tuple)
        df_evenements = df_evenements.sort_values("_tri").drop(columns="_tri").reset_index(drop=True)

    return df_evenements
@st.cache_data(show_spinner="Analyse des changements d'items...")
def classement_buff_nerf_item(df):

    all_patchs = sorted(df["patch"].unique(), key=patch_to_tuple)
    resultats = []

    for patch in all_patchs:
        df_changement = changement_item_patch(df, patch)
        df_changement["patch"] = patch
        resultats.append(df_changement)

    resultats = pd.concat(resultats, ignore_index=True).round(2)

    classement = resultats.groupby("item_id").agg(
        name=("name", "first"),
        nb_changements=("type_changement", "count"),
        nb_buffs=("type_changement", lambda x: (x == "buff").sum()),
        nb_nerfs=("type_changement", lambda x: (x == "nerf").sum())
    ).sort_values("nb_changements", ascending=False).reset_index()

    return classement, resultats

def detail_buff_nerf_item(df, item_id):
    _, resultats = classement_buff_nerf_item(df)
    return resultats[resultats["item_id"] == item_id]

