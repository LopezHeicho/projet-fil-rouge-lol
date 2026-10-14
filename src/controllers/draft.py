import pandas as pd
import plotly.graph_objects as go

from models.draft import score_counter, best_item_champion, best_runes_champion


def figure_score_counter(best_champ):
    fig = go.Figure(go.Bar(
        x=best_champ["winrate"], 
        y=best_champ["champion"], 
        orientation="h", 
        customdata=best_champ["nb_games"],
        hovertemplate="<b>%{y}</b><br>Winrate : %{x}<br>Games jouées : %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Meilleur champions", x=0.5 ,xanchor="center"),
        xaxis_title="Winrate",
        yaxis_title="Champion",
        yaxis=dict(autorange="reversed")
    )

    return fig


def get_score_counter(df_pro, table_confrontation, table_synergie, role, ban_allies, ban_adverses, nombre_champion, pick_allies=[], pick_adverses=[], min_games=5):
    best_champ = score_counter(df_pro, table_confrontation, table_synergie, role, ban_allies, ban_adverses, nombre_champion, pick_allies, pick_adverses, min_games)
    fig = figure_score_counter(best_champ)

    return best_champ, fig

def get_best_item_champion(df_joueur, df_items, champion, role):
    best_item ,first_item, boots = best_item_champion(df_joueur, df_items, champion, role)

    return best_item, first_item, boots

def get_best_runes_champion(df_joueur, champion, role, min_games=5):
    resultat = best_runes_champion(df_joueur, champion, role, min_games)
    if resultat == None:
        return None

    primary_key, pk0, pk1, pk2, pk3, sub_key, sk0, sk1, stat1, stat2, stat3 = resultat

    return primary_key, pk0, pk1, pk2, pk3, sub_key, sk0, sk1, stat1, stat2, stat3