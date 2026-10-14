import pandas as pd
import streamlit as st

from models.joueur import meilleurs_items_champion_role


TOP = [
    "Aatrox", "Akali", "Ambessa", "Camille", "Cho'Gath", "Darius", "Dr. Mundo", "Fiora", "Gangplank", "Garen", "Gnar", "Gragas", "Gwen", 
    "Heimerdinger", "Illaoi", "Irelia" ,"Jax", "Jayce", "K'Sante", "Kayle", "Kennen" ,"Kled", "Malphite" ,"Mordekaiser" ,"Nasus", "Olaf", 
    "Ornn", "Pantheon", "Renekton", "Riven", "Rumble", "Sett", "Shen", "Singed", "Sion", "Tahm Kench", "Teemo", "Trundle", "Tryndamere", 
    "Urgot", "Volibear", "Yasuo", "Yone", "Yorick", "Zaahen", "Maokai", "Poppy", "Wukong", "Vladimir", "Sylas", "Ryze", "Galio", "Udyr"
]
JGL = [
    "Amumu", "Bel'Veth", "Briar", "Cho'Gath", "Diana", "Ekko", "Elise", "Evelynn", "Fiddlesticks", "Graves", "Hecarim", "Ivern", "Jarvan IV", 
    "Karthus", "Kayn", "Kha'Zix", "Kindred", "Lee Sin", "Lillia", "Master Yi", "Naafiri", "Nidalee", "Nocturne", "Nunu & Willump", "Qiyana", 
    "Quinn", "Rammus", "Rek'Sai", "Rengar", "Sejuani", "Shaco", "Shyvana", "Skarner", "Sylas", "Talon", "Udyr", "Vi", "Viego", "Warwick", "Wukong", 
    "Xin Zhao", "Zac", "Zed", "Gragas", "Maokai", "Trundle", "Olaf", "Volibear", "Pantheon", "Poppy", "Taliyah","Rumble", "Zyra", "Camille", "Jax", "Brand"
]
MID = [
    "Ahri", "Akali", "Akshan", "Anivia", "Annie", "Aurelion Sol", "Aurora", "Azir", "Cassiopeia", "Diana", "Ekko", "Fizz", "Galio", "Hwei", "Irelia", 
    "Kassadin", "Katarina", "LeBlanc", "Lissandra", "Locke", "Lux", "Malzahar", "Mel", "Orianna", "Qiyana", "Ryze", "Sylas", "Syndra", "Taliyah", "Twisted Fate", 
    "Veigar", "Vex", "Viktor", "Vladimir", "Xerath", "Yasuo", "Yone", "Zed", "Zoe", "Corki", "Jayce", "Tristana", "Karma", "Neeko", "Lucian", "Ziggs", 
    "Swain", "Renekton", "Sett"
]
ADC = [
    "Aphelios", "Ashe", "Caitlyn", "Corki", "Draven", "Ezreal", "Jhin", "Jinx", "Kai'Sa", "Kalista", "Kog'Maw", "Lucian", "Miss Fortune", "Nilah", "Samira", 
    "Sivir", "Smolder", "Tristana", "Twitch", "Varus", "Vayne", "Viktor", "Xayah", "Yasuo", "Yunara", "Zeri", "Ziggs", "Senna", "Swain", "Syndra", "Cassiopeia",
    "Vladimir"
]
SUP = [
    "Alistar", "Bard", "Blitzcrank", "Brand", "Braum", "Camille", "Janna", "Karma", "Leona", "Lulu", "Lux", "Maokai", "Milio", "Morgana", "Nami", "Nautilus", 
    "Neeko", "Pantheon", "Poppy", "Pyke", "Rakan", "Rell", "Renata Glasc", "Senna", "Seraphine", "Sona", "Soraka", "Swain", "Tahm Kench", "Taric", "Thresh", 
    "Vel'Koz", "Xerath", "Yuumi", "Zilean", "Zyra", "Galio", "Shen", "Sett", "Ashe", "Annie", "Amumu", "Gragas", "Trundle", "Heimerdinger"
]

LISTE_ROLE = {"top": TOP, "jng": JGL, "mid": MID, "bot": ADC, "sup": SUP}

ITEM_SUP = ["Bloodsong", "Solstice Sleigh", "Celestial Opposition", "Zaz'Zak's Realmspike", "Dream Maker"]



def ban(df, champ_banni):
    ban = df[~df["champion"].isin(champ_banni)]
    return ban

def champ_pick(df, pick):
    ban = []
    for j in pick:
        ban.append(j)
    champ_restant = df[~df["champion"].isin(ban)]
    return champ_restant

@st.cache_data(show_spinner="Calcul des confrontations entre champions...")
def table_confrontation(df):
    champ = df[~df["participantid"].isin([100, 200])].copy()

    blue = champ[champ["side"] == "Blue"][["gameid", "champion", "result"]]
    red = champ[champ["side"] == "Red"][["gameid", "champion", "result"]]

    all_game = pd.merge(blue, red, on="gameid", how="inner", suffixes=("_blue", "_red"))

    table = all_game.groupby(["champion_blue", "champion_red"]).agg(
        nb_games=("result_blue", "count"),
        victory=("result_blue", "sum")
    ).reset_index()

    table["winrate"] = ((table["victory"] / table["nb_games"]) * 100).round(2)

    return table

@st.cache_data(show_spinner="Calcul des synergies entre champions...")
def table_synergie(df):
    champ = df[~df["participantid"].isin([100, 200])].copy()

    blue = champ[champ["side"] == "Blue"][["gameid", "champion", "result"]]
    red = champ[champ["side"] == "Red"][["gameid", "champion", "result"]]

    all_game_blue = pd.merge(blue, blue, on="gameid", how="inner", suffixes=("_1", "_2"))

    all_game_red = pd.merge(red, red, on="gameid", how="inner", suffixes=("_1", "_2"))

    all_game = pd.concat([all_game_blue, all_game_red], axis=0)
    all_game = all_game[all_game["champion_1"] != all_game["champion_2"]]

    table = all_game.groupby(["champion_1", "champion_2"]).agg(
        nb_games=("result_1", "count"),
        victory=("result_1", "sum")
    ).reset_index()

    table["winrate"] = ((table["victory"] / table["nb_games"]) * 100).round(2)

    return table

def score_counter(df, table_confrontation, table_synergie, role, ban_allies, ban_adverses, nombre_champion, pick_allies=[], pick_adverses=[], min_games=5):
    ban1 = ban(df, ban_allies)
    ban2 = ban(ban1, ban_adverses)
    reste_champ = champ_pick(ban2, pick_allies)
    if pick_adverses != []:
        reste_champ_final = champ_pick(reste_champ, pick_adverses)
    else:
        reste_champ_final = reste_champ

    champion_candidat = reste_champ_final[(reste_champ_final["position"] == role) & (reste_champ_final["champion"].isin(LISTE_ROLE[role]))]["champion"].unique().tolist()

    liste = []

    for champion in champion_candidat:
        for adversaire in pick_adverses:
            ligne_1 = table_confrontation[(table_confrontation["champion_blue"] == champion) & (table_confrontation["champion_red"] == adversaire)]
            ligne_2 = table_confrontation[(table_confrontation["champion_blue"] == adversaire) & (table_confrontation["champion_red"] == champion)]

            if len(ligne_1) > 0:
                nb_1 = ligne_1["nb_games"].iloc[0]
                victoire_1 = ligne_1["victory"].iloc[0]
            else:
                nb_1 = 0
                victoire_1 = 0

            if len(ligne_2) > 0:
                nb_2 = ligne_2["nb_games"].iloc[0]
                victoire_2 = ligne_2["nb_games"].iloc[0] - ligne_2["victory"].iloc[0]
            else:
                nb_2 = 0
                victoire_2 = 0

            nb_games = nb_1 + nb_2
            victoires = victoire_1 + victoire_2
            if nb_games >= min_games:
                winrate = ((victoires / nb_games) * 100).round(2)
                score = {"champion" : champion, "nb_games" : nb_games, "victoires" : victoires, "winrate" : winrate}
                liste.append(score)

        for allies in pick_allies:
            ligne = table_synergie[(table_synergie["champion_1"] == champion) & (table_synergie["champion_2"] == allies)]

            if len(ligne) > 0:
                nb_games = ligne["nb_games"].iloc[0]
                victoires = ligne["victory"].iloc[0]
            else:
                nb_games = 0
                victoires = 0

            if nb_games >= min_games:
                winrate = ((victoires / nb_games) * 100).round(2)
                score = {"champion" : champion, "nb_games" : nb_games, "victoires" : victoires, "winrate" : winrate}
                liste.append(score)

    if len(liste) != 0:
        best_champ = pd.DataFrame(liste).groupby("champion").agg(
            nb_games=("nb_games", "sum"),
            victoires=("victoires", "sum")
        ).reset_index()

    else:
        reste_champ_final = reste_champ_final[(reste_champ_final["position"] == role) & (reste_champ_final["champion"].isin(LISTE_ROLE[role]))]
        best_champ = reste_champ_final.groupby("champion").agg(
            victoires=("result", "sum"),
            nb_games=("result", "count")
        ).reset_index()
    best_champ = best_champ[best_champ["nb_games"] >= min_games]
    best_champ["winrate"] = ((best_champ["victoires"] / best_champ["nb_games"]) * 100).round(2)

    C = 50   # winrate de référence (un champion "neutre" est supposé à 50/50)
    M = 50   # nombre de games de référence 

    best_champ["score_pondere"] = (
        (best_champ["nb_games"] / (best_champ["nb_games"] + M)) * best_champ["winrate"]
        + (M / (best_champ["nb_games"] + M)) * C
    )

    best_champ = best_champ.sort_values(ascending=False, by="score_pondere").head(nombre_champion)

    return best_champ


BOOTS = [
    "Boots", "Ghostcrawlers", "Berserker's Greaves", "Gluttonous Greaves",
    "Boots of Swiftness", "Symbiotic Soles", "Synchronized Souls",
    "Sorcerer's Shoes", "Plated Steelcaps", "Mercury's Treads",
    "Mobility Boots", "Ionian Boots of Lucidity", "Immortal Path",
    "Swiftmarch", "Crimson Lucidity", "Gunmetal Greaves",
    "Chainlaced Crushers", "Armored Advance", "Spellslinger's Shoes",
    "Forever Forward",
]

def best_item_champion(df_joueur, df_items, champion, role):
    best_build = meilleurs_items_champion_role(df_joueur, df_items, champion, role)

    if role == "jng":
        first_item = None
    elif role == "sup":
        first_item_filtre = best_build[best_build["Item"].isin(ITEM_SUP)]
        first_item = first_item_filtre.iloc[0] if len(first_item_filtre) > 0 else None
    else:
        first_item_filtre = best_build[best_build["Item"].str.contains("Doran")]
        first_item = first_item_filtre.iloc[0] if len(first_item_filtre) > 0 else None

    boots_filtre = best_build[best_build["Item"].isin(BOOTS)]
    boots = boots_filtre.iloc[0] if len(boots_filtre) > 0 else None

    best_item = best_build[~(
        (best_build["Item"].str.contains("Doran"))
        | (best_build["Item"].isin(ITEM_SUP))
        | (best_build["Item"].isin(BOOTS))
    )].head(4)

    return best_item, first_item, boots


def best_runes_colonnes(df, colonne, min_games=5):
    runes = df.groupby(colonne).agg(victory=("win", "sum"), nb_games=("win", "count")).reset_index()
    runes = runes[runes["nb_games"] >= min_games]

    if len(runes) == 0:
        return None
    
    runes = runes.sort_values(ascending=False, by="nb_games")
    
    return runes.head(1)[colonne].iloc[0]

def best_runes_champion(df_joueur, champion, role, min_games=5):
    df_role = df_joueur[df_joueur["position"] == role]
    df_champion = df_role[df_role["championName"] == champion]

    primary_key = best_runes_colonnes(df_champion, "perkPrimaryStyleName", min_games)
    if primary_key == None:
        return None
    
    df_primary_key = df_champion[df_champion["perkPrimaryStyleName"] == primary_key].copy()
    df_primary_key["perkPrimarySelectionsNames"] = df_primary_key["perkPrimarySelectionsNames"].str.split(";")

    df_primary_key["pk0"] = df_primary_key["perkPrimarySelectionsNames"].str[0]
    df_primary_key["pk1"] = df_primary_key["perkPrimarySelectionsNames"].str[1]
    df_primary_key["pk2"] = df_primary_key["perkPrimarySelectionsNames"].str[2]
    df_primary_key["pk3"] = df_primary_key["perkPrimarySelectionsNames"].str[3]

    pk0 = best_runes_colonnes(df_primary_key, "pk0", min_games)
    pk1 = best_runes_colonnes(df_primary_key, "pk1", min_games)
    pk2 = best_runes_colonnes(df_primary_key, "pk2", min_games)
    pk3 = best_runes_colonnes(df_primary_key, "pk3", min_games)

    sub_key = best_runes_colonnes(df_champion[df_champion["perkSubStyleName"] != primary_key], "perkSubStyleName", min_games)

    if sub_key == None:
        return None
    
    df_sub_key = df_champion[df_champion["perkSubStyleName"] == sub_key].copy()
    df_sub_key["perkSubSelectionsNames"] = df_sub_key["perkSubSelectionsNames"].str.split(";")

    df_sub_key["sk0"] = df_sub_key["perkSubSelectionsNames"].str[0]
    df_sub_key["sk1"] = df_sub_key["perkSubSelectionsNames"].str[1]

    sk0 = best_runes_colonnes(df_sub_key, "sk0", min_games)
    sk1 = best_runes_colonnes(df_sub_key, "sk1", min_games)

    stat1 = best_runes_colonnes(df_champion, "perkStatOffenseName", min_games)
    stat2 = best_runes_colonnes(df_champion, "perkStatFlexName", min_games)
    stat3 = best_runes_colonnes(df_champion, "perkStatDefenseName", min_games)

    return primary_key, pk0, pk1, pk2, pk3, sub_key, sk0, sk1, stat1, stat2, stat3

def modif_df(df_joueur):
    df_ranked = df_joueur[df_joueur["queueId"] == 420]
    new_df = df_ranked[["matchId", "championName", "side", "win", "position"]].copy()
    new_df = new_df.rename(columns={
        "matchId": "gameid",
        "championName": "champion",
        "win": "result",
    })

    return new_df
