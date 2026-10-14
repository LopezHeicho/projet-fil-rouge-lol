import pandas as pd
import plotly.graph_objects as go
 
from models.item import (
    evolution_item, 
    evolution_efficiency_item, 
    changement_item_patch, 
    comparaison_item, 
    budget_item_type, 
    classement_rework_item,
    detail_reworks_item, 
    classement_buff_nerf_item, 
    detail_buff_nerf_item
)
from models.champion import (
    stat_niveau, 
    comparaison_stats_champion, 
    evolution_champion, 
    difficulty_champion_type, 
    changement_champion_patch, 
    power_creep,
    classement_buff_nerf_champion,
    detail_buff_nerf_champion,
    composition_roster_par_patch,
    evolution_type_ressource
)
from models.spell import (
    changement_spell_patch,
    classement_buff_nerf_spell,
    detail_buff_nerf_spell,

)
from models.esport import winrate_champion_pro
 
 
# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------
 
def get_changement_item(df_items, patch_1, patch_2=None):
    return changement_item_patch(df_items, patch_1, patch_2)
 
 
def _figure_evolution_stat(df_item, df_stats, stat_a_tracer, nom_affiche, titre):
    fig = go.Figure(go.Scatter(
        mode="lines",
        x=df_item["patch"],
        y=df_stats[stat_a_tracer],
        line=dict(color="#2a78d6"),
        hovertemplate=f"<b>{nom_affiche}</b><br>patch : %{{x}}<br><br>{stat_a_tracer} : %{{y}}<br>"
    ))
    fig.update_layout(
        title=dict(text=f"{titre} {stat_a_tracer} pour {nom_affiche}", x=0.5, xanchor="center"),
        xaxis_title="Patch",
        yaxis_title=stat_a_tracer,
        xaxis=dict(type="category")
    )
    return fig
 
 
def get_evolution_item(df_items, item, item_id, stat):
    message_erreur, df_ambiguite, avertissements, nom_affiche, df_item, df_stats, stats_valides = evolution_item(
        df_items, item=item, item_id=item_id, stat=stat
    )
 
    if message_erreur:
        return {"erreur": message_erreur, "ambiguite": df_ambiguite, "avertissements": [], "figures": []}
 
    figures = [
        _figure_evolution_stat(df_item, df_stats, stat_a_tracer, nom_affiche, titre="Évolution de")
        for stat_a_tracer in stats_valides
    ]
    return {"erreur": None, "ambiguite": None, "avertissements": avertissements, "figures": figures}
 
 
def get_evolution_efficiency_item(df_items, item, item_id):
    message_erreur, df_ambiguite, avertissements, nom_affiche, df_item, df_stats, stats_valides = evolution_efficiency_item(
        df_items, item=item, item_id=item_id
    )
 
    if message_erreur:
        return {"erreur": message_erreur, "ambiguite": df_ambiguite, "avertissements": [], "figures": []}
 
    figures = [
        _figure_evolution_stat(df_item, df_stats, stat_a_tracer, nom_affiche, titre="Évolution de l'efficacité gold pour")
        for stat_a_tracer in stats_valides
    ]
    return {"erreur": None, "ambiguite": None, "avertissements": avertissements, "figures": figures}
 
 
def get_comparaison_item(df_items, patch_comparaison, item1, item_id1, item2=None, item_id2=None):
    (erreurs, ambiguites, avertissements_comp, noms_stats, valeurs_norm_1, valeurs_norm_2,
     valeurs_brutes_1, valeurs_brutes_2, nom1_affiche, nom2_affiche) = comparaison_item(
        df_items, patch_comparaison,
        item1=item1, item_id1=item_id1,
        item2=item2, item_id2=item_id2,
    )
 
    if erreurs:
        return {"erreurs": erreurs, "ambiguites": ambiguites, "avertissements": [], "fig": None}
 
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
 
    return {"erreurs": [], "ambiguites": ambiguites, "avertissements": avertissements_comp, "fig": fig_comp}


def get_budget_item(df_items, patch, type_budget, budget_min, budget_max):
    avertissement, df_budget = budget_item_type(df_items, patch, type_budget, budget_min, budget_max)
    return {"avertissement": avertissement, "df": df_budget}

def figure_classement_rework_item(classement):
    fig = go.Figure(go.Bar(
        x=classement["nb_reworks"], y=classement["name"], orientation="h",
        text=classement["nb_reworks"], textposition="outside",
        marker_color="#2a78d6",
        hovertemplate="<b>%{y}</b><br>Nombre de reworks : %{x}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Classement des items selon le nombre de reworks", x=0.5, xanchor="center"),
        xaxis_title="Nombre de reworks",
        yaxis_title="Items",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(classement) * 30)
    )
    return fig


def get_classement_rework_item(df_items, nb_items):
    classement = classement_rework_item(df_items)
    classement_affiche = classement.head(nb_items)
    fig = figure_classement_rework_item(classement_affiche)
    return classement_affiche, fig


def get_detail_reworks_item(df_items, name):
    return detail_reworks_item(df_items, name)

def figure_classement_buff_nerf_item(classement):
    fig = go.Figure(go.Bar(
        x=classement["nb_changements"], y=classement["name"], orientation="h",
        text=classement["nb_changements"], textposition="outside",
        marker_color="#2a78d6",
        hovertemplate="<b>%{y}</b><br>Nombre de changements : %{x}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Classement des items selon le nombre de changements", x=0.5, xanchor="center"),
        xaxis_title="Nombre de changements",
        yaxis_title="Items",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(classement) * 30)
    )
    return fig

def get_classement_buff_nerf_item(df_items, nb_items):
    classement, _ =  classement_buff_nerf_item(df_items)
    classement_affiche = classement.head(nb_items)
    fig = figure_classement_buff_nerf_item(classement_affiche)
    return classement_affiche, fig,

def get_detail_buff_nerf_item(df_items, item_id):
    resultat = detail_buff_nerf_item(df_items, item_id)
    return resultat
    

# ---------------------------------------------------------------------------
# Champion
# ---------------------------------------------------------------------------
 
def get_changement_champion(df_champions, patch_1, patch_2=None):
    return changement_champion_patch(df_champions, patch_1, patch_2)
 
 
def get_stats_disponibles_champion(df_champions, champion):
    """Construit la liste des stats traçables pour un champion donné (sa
    ressource - mana/energie/etc - varie d'un champion a l'autre)."""
    ressource = df_champions[df_champions["name"] == champion]["partype"].values[0]
    return ["HP", "Regen HP", ressource, "Regen " + ressource, "Armor", "Magic Resist",
            "Crit", "Ad", "As", "Ms", "range"]
 
 
def get_evolution_champion(df_champions, champion, stat):
    df_champion_evo = evolution_champion(df_champions, champion, stat)
 
    fig_evo = go.Figure(go.Scatter(
        mode="lines",
        x=df_champion_evo["patch"],
        y=df_champion_evo[stat],
        line=dict(color="#2a78d6"),
        hovertemplate=f"<b>{champion}</b><br>patch : %{{x}}<br><br>{stat} : %{{y}}<br>"
    ))
    fig_evo.update_layout(
        title=dict(text=f"Évolution de la stat {stat} au cours des patchs", x=0.5, xanchor="center"),
        xaxis_title="Patch",
        yaxis_title=stat,
        xaxis=dict(type="category")
    )
    return {"fig": fig_evo}

 
def get_comparaison_champion(df_champions, patch, champion1, champion2, niveau):
    avertissement_comp, labels, diffs, couleurs, valeurs1, valeurs2, nom1, nom2 = comparaison_stats_champion(
        df_champions, patch, niveau, champion1, champion2
    )
 
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
 
    return {"avertissement": avertissement_comp, "fig": fig_comp}
 
 
def get_stat_niveau(df_champions, patch, niveau, champion):
    resultat = stat_niveau(df_champions, patch, niveau, champion)
    return pd.DataFrame(resultat.items(), columns=["Statistique", "Valeur"])


def get_confrontation_champion_winrate(df_champions, df_esport, patch, niveau, champion, role=None, league=None):
    stats_table = get_stat_niveau(df_champions, patch, niveau, champion)
    patch_majmin = ".".join(patch.split(".")[:2])
    winrate_pro = winrate_champion_pro(df_esport, champion, role=role, league=league, patch_majmin=patch_majmin)
    return {"stats": stats_table, "winrate_pro": winrate_pro}


def get_difficulty_champion(df_champions, patch, type_diff, max_diff):
    avertissement, df_diff = difficulty_champion_type(df_champions, patch, type_diff, max_diff)
    return {"avertissement": avertissement, "df": df_diff}

def figure_power_creep(table_all_champ, table_cohort_fixe, stat):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        mode="lines",
        x=table_all_champ["patch"],
        y=table_all_champ["stat_niveau_18"],
        name="Roster complet",
        line=dict(color="#2a78d6"),
        hovertemplate=f"<b>Roster complet</b><br>patch : %{{x}}<br><br>{stat} : %{{y}}<br>"
    ))
    fig.add_trace(go.Scatter(
        mode="lines",
        x=table_cohort_fixe["patch"],
        y=table_cohort_fixe["stat_niveau_18"],
        name="Cohorte fixe",
        line=dict(color="#d6782a"),
        hovertemplate=f"<b>Cohorte fixe</b><br>patch : %{{x}}<br><br>{stat} : %{{y}}<br>"
    ))
    fig.update_layout(
        title=dict(text=f"Évolution du power creep pour la stat {stat}", x=0.5, xanchor="center"),
        xaxis_title="Patch",
        yaxis_title=stat,
        xaxis=dict(type="category")
    )
    return fig


def get_power_creep(df_champions, stat):
    table_all_champ = power_creep(df_champions, stat)
    table_cohort_fixe = power_creep(df_champions, stat, cohort_fixe=True)

    fig = figure_power_creep(table_all_champ, table_cohort_fixe, stat)

    return fig

def figure_classement_buff_nerf_champion(classement):
    fig = go.Figure(go.Bar(
        x=classement["nb_changements"], y=classement["name"], orientation="h",
        text=classement["nb_changements"], textposition="outside",
        marker_color="#2a78d6",
        hovertemplate="<b>%{y}</b><br>Nombre de changements : %{x}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Classement des champions selon le nombre de changements", x=0.5, xanchor="center"),
        xaxis_title="Nombre de changements",
        yaxis_title="Champions",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(classement) * 30)
    )
    return fig

def get_classement_buff_nerf_champion(df_champion, nb_champion):
    classement, _ =  classement_buff_nerf_champion(df_champion)
    classement_affiche = classement.head(nb_champion)
    fig = figure_classement_buff_nerf_champion(classement_affiche)
    return classement_affiche, fig,

def get_detail_buff_nerf_champion(df_champion, name):
    resultat = detail_buff_nerf_champion(df_champion, name)
    return resultat

COULEURS_CLASSE = {
    "Fighter": "#2a78d6",
    "Mage": "#4a3aa7",
    "Tank": "#1baf7a",
    "Assassin": "#eda100",
    "Support": "#e87ba4",
    "Marksman": "#008300",
}

def figure_composition_roster(composition, proportions=False, classes=None):
    donnees = composition
    if proportions:
        donnees = donnees.div(donnees.sum(axis=1), axis=0) * 100
    if classes:
        donnees = donnees[classes]

    fig = go.Figure()
    for classe in COULEURS_CLASSE:
        if classe not in donnees.columns:
            continue
        fig.add_trace(go.Scatter(
            x=donnees.index, y=donnees[classe],
            mode="lines", stackgroup="composition", name=classe,
            line=dict(color=COULEURS_CLASSE[classe], width=0.5),
        ))

    fig.update_layout(
        title=dict(text="Évolution de la composition du roster par rôle", x=0.5, xanchor="center"),
        xaxis_title="Patch",
        yaxis_title="Proportion (%)" if proportions else "Nombre de champions",
        xaxis=dict(nticks=20),
        hovermode="x unified",
    )
    return fig

def get_composition_roster(df_champions, proportions=False, classes=None):
    composition = composition_roster_par_patch(df_champions)
    fig = figure_composition_roster(composition, proportions, classes)
    return composition, fig

COULEURS_RESSOURCE = {
    "Mana": "#2a78d6",
    "Energy": "#eb6834",
    "Ressource alternative": "#1baf7a",
    "Aucune ressource": "#4a3aa7",
}

def figure_evolution_type_ressource(evolution, proportions=False, categories=None):
    donnees = evolution
    if proportions:
        donnees = donnees.div(donnees.sum(axis=1), axis=0) * 100
    if categories:
        donnees = donnees[categories]

    fig = go.Figure()
    for categorie in COULEURS_RESSOURCE:
        if categorie not in donnees.columns:
            continue
        fig.add_trace(go.Scatter(
            x=donnees.index, y=donnees[categorie],
            mode="lines", stackgroup="ressource", name=categorie,
            line=dict(color=COULEURS_RESSOURCE[categorie], width=0.5),
        ))

    fig.update_layout(
        title=dict(text="Évolution du type de ressource des champions", x=0.5, xanchor="center"),
        xaxis_title="Patch",
        yaxis_title="Proportion (%)" if proportions else "Nombre de champions",
        xaxis=dict(nticks=20),
        hovermode="x unified",
    )
    return fig

def get_evolution_type_ressource(df_champions, proportions=False, categories=None):
    evolution = evolution_type_ressource(df_champions)
    fig = figure_evolution_type_ressource(evolution, proportions, categories)
    return evolution, fig

# ---------------------------------------------------------------------------
# Spell
# ---------------------------------------------------------------------------
 
def get_changement_spell(df_spells, patch_1, patch_2=None):
    return changement_spell_patch(df_spells, patch_1, patch_2)

def figure_classement_buff_nerf_spell(classement):
    fig = go.Figure(go.Bar(
        x=classement["nb_changements"], y=classement["name"], orientation="h",
        text=classement["nb_changements"], textposition="outside",
        marker_color="#2a78d6",
        hovertemplate="<b>%{y}</b><br>Nombre de changements : %{x}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Classement des champions selon le nombre de changements", x=0.5, xanchor="center"),
        xaxis_title="Nombre de changements",
        yaxis_title="Champions",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(classement) * 30)
    )
    return fig

def get_classement_buff_nerf_spell(df_spell, nb_champion):
    classement, _ =  classement_buff_nerf_spell(df_spell)
    classement_affiche = classement.head(nb_champion)
    fig = figure_classement_buff_nerf_spell(classement_affiche)
    return classement_affiche, fig,

def get_detail_buff_nerf_spell(df_spell, name):
    resultat = detail_buff_nerf_spell(df_spell, name)
    return resultat

