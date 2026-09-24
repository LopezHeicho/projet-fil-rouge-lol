import pandas as pd
import plotly.graph_objects as go
 
from models.item import evolution_item, evolution_efficiency_item, changement_item_patch, comparaison_item
from models.champion import stat_niveau, comparaison_stats_champion, evolution_champion, difficulty_champion_type, changement_champion_patch
from models.spell import changement_spell_patch
 
 
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
 
 
def get_difficulty_champion(df_champions, patch, type_diff, max_diff):
    avertissement, df_diff = difficulty_champion_type(df_champions, patch, type_diff, max_diff)
    return {"avertissement": avertissement, "df": df_diff}
 
 
# ---------------------------------------------------------------------------
# Spell
# ---------------------------------------------------------------------------
 
def get_changement_spell(df_spells, patch_1, patch_2=None):
    return changement_spell_patch(df_spells, patch_1, patch_2)
