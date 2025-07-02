import requests
from bs4 import BeautifulSoup
import os

retrieved = True
os.makedirs("player_profiles", exist_ok=True)

if not retrieved:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64 X64)"
    }
    response = requests.get('https://www.vlr.gg/stats/?event_group_id=74&region=all&min_rounds=10&min_rating=1550&agent=all&map_id=all&timespan=90d', headers = headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    #print(soup.prettify())
    with open("vlr_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)
else:
    with open("vlr_page.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')


#region dictionary
country_regions = {
    # CHINA region
    "CN": "CHINA",
    "HK": "CHINA",
    "TW": "CHINA",

    # APAC region (expanded with SEA)
    "JP": "APAC",
    "KR": "APAC",
    "IN": "APAC",
    "SG": "APAC",
    "TH": "APAC",
    "VN": "APAC",
    "PH": "APAC",
    "MY": "APAC",
    "ID": "APAC",
    "AU": "APAC",
    "NZ": "APAC",
    "PK": "APAC",
    "BD": "APAC",
    "KH": "APAC",  # Cambodia
    "LA": "APAC",  # Laos
    "MM": "APAC",  # Myanmar
    "BN": "APAC",  # Brunei
    "TL": "APAC",  # Timor-Leste
    "LK": "APAC",  # Sri Lanka
    "NP": "APAC",  # Nepal
    "AF": "APAC",  # Afghanistan
    "MN": "APAC",  # Mongolia
    "UZ": "APAC",  # Uzbekistan
    "TJ": "APAC",  # Tajikistan
    "TM": "APAC",  # Turkmenistan
    "KG": "APAC",  # Kyrgyzstan

    # AMERICAS region
    "US": "AMERICAS",
    "CA": "AMERICAS",
    "BR": "AMERICAS",
    "MX": "AMERICAS",
    "AR": "AMERICAS",
    "CL": "AMERICAS",
    "CO": "AMERICAS",
    "PE": "AMERICAS",
    "UY": "AMERICAS",
    "VE": "AMERICAS",

    # EMEA region
    "GB": "EMEA",
    "FR": "EMEA",
    "DE": "EMEA",
    "ES": "EMEA",
    "IT": "EMEA",
    "NL": "EMEA",
    "SE": "EMEA",
    "PL": "EMEA",
    "FI": "EMEA",
    "NO": "EMEA",
    "DK": "EMEA",
    "BE": "EMEA",
    "PT": "EMEA",
    "GR": "EMEA",
    "IE": "EMEA",
    "HU": "EMEA",
    "CZ": "EMEA",
    "RO": "EMEA",
    "SK": "EMEA",
    "BG": "EMEA",
    "HR": "EMEA",
    "SI": "EMEA",
    "RS": "EMEA",
    "ME": "EMEA",  # Montenegro
    "MK": "EMEA",  # North Macedonia
    "AL": "EMEA",  # Albania
    "BA": "EMEA",  # Bosnia and Herzegovina
    "XK": "EMEA",  # Kosovo
    "LT": "EMEA",  # Lithuania
    "LV": "EMEA",  # Latvia
    "EE": "EMEA",  # Estonia
    "IS": "EMEA",  # Iceland
    "CH": "EMEA",  # Switzerland
    "LI": "EMEA",  # Liechtenstein
    "LU": "EMEA",  # Luxembourg
    "TR": "EMEA",
    "RU": "EMEA",
    "UA": "EMEA",
    "BY": "EMEA",
    "KZ": "EMEA",
    "GE": "EMEA",
    "AM": "EMEA",
    "AZ": "EMEA",
    "IL": "EMEA",
    "EG": "EMEA",
    "DZ": "EMEA",
    "MA": "EMEA",
    "TN": "EMEA",
    "LY": "EMEA",
    "SD": "EMEA",
    "ET": "EMEA",
    "KE": "EMEA",
    "NG": "EMEA",
    "GH": "EMEA",
    "CI": "EMEA",  # Côte d'Ivoire
    "ZA": "EMEA",
    "UG": "EMEA",
    "TZ": "EMEA",
    "AO": "EMEA",
    "MZ": "EMEA",
    "ZW": "EMEA",
    "ZM": "EMEA",
    "SN": "EMEA",  # Senegal
    "SA": "EMEA",
    "AE": "EMEA",
    "QA": "EMEA",
    "KW": "EMEA",
    "BH": "EMEA",
    "OM": "EMEA",
    "YE": "EMEA",
    "IQ": "EMEA",
    "IR": "EMEA",
    "SY": "EMEA",
    "JO": "EMEA",
    "LB": "EMEA",
    "PS": "EMEA",
    "EN": "EMEA",  # England
    "UN": "EMEA"
}





table = '<table class = "wf-table mod-stats mod-scroll" style> ==$0'

playerTable = soup.find('table', class_='wf-table mod-stats mod-scroll')
if playerTable:
    # Iterate through rows
    # Loop through all rows
    for row in playerTable.find_all('tr'):
        #create dictionary for player stats
        keys = ['PLAYER', 'COUNTRY CODE', 'REGION', 'AGENTS', 'ROUNDS', 'RATING 2.0', 'ACS', 'K/D', 'KAST', 'ADR', 'FPR', 'APR', 'FKPR', 'FDPR', 'HS%', 'CL%', 'Kills', 'Deaths', 'Assists', 'First Kills', 'First Deaths']
        player_dict = {key: None for key in keys}

        #get player name, country code, and region
        player_td = row.find('td', class_='mod-player mod-a')
        player_tag = player_td.find('a') if player_td else None
        flag = player_tag.find('i') if player_tag else None
        code = flag['class'][1].split('-')[-1].upper() if flag and 'class' in flag.attrs else None
        player_dict['COUNTRY CODE'] = code
        player_dict['REGION'] = country_regions.get(code, 'INTL')
        player_dict['PLAYER'] = player_tag['href'].rsplit('/', 1)[-1] if player_tag and 'href' in player_tag.attrs else None

        #get player agents
        agent_td = row.find('td', class_='mod-agents')
        player_dict['AGENTS'] = ', '.join(
            img['src'].split('agents/')[1].replace('.png', '').upper()
            for img in agent_td.find_all('img')
        ) if agent_td else None



        # This code assumes you're inside the for loop already:
        # for row in playerTable.find_all('tr'):

        # ROUNDS
        rounds_td = row.find("td", class_="mod-rnd")
        player_dict["ROUNDS"] = rounds_td.text.strip() if rounds_td else None

        # ACS (grab separately since it's the only one with mod-acs)
        acs_td = row.find("td", class_="mod-acs")
        acs = acs_td.find("span").text.strip() if acs_td and acs_td.find("span") else None
        player_dict["ACS"] = acs

        # Grab all non-ACS mod-color-sq tds (in correct order)
        color_tds = row.find_all("td", class_="mod-color-sq")
        stat_cells = [td for td in color_tds if 'mod-acs' not in td.get('class', [])]

        # Expected order:
        color_stat_keys = [
            "RATING 2.0", "K/D", "KAST", "ADR", "FPR", "APR",
            "FKPR", "FDPR", "HS%", "CL%"
        ]

        for key, td in zip(color_stat_keys, stat_cells):
            span = td.find("span")
            player_dict[key] = span.text.strip() if span else None

        # Get plain stat columns from the end
        last_5_stats = ["Kills", "Deaths", "Assists", "First Kills", "First Deaths"]
        all_tds = row.find_all("td")
        last_tds = all_tds[-5:]

        for key, td in zip(last_5_stats, last_tds):
            player_dict[key] = td.text.strip()

        # Compose a natural language summary for RAG/embedding
        player = player_dict['PLAYER']
        region = player_dict['REGION']
        country = player_dict['COUNTRY CODE']
        agents = player_dict['AGENTS'] if player_dict['AGENTS'] else "various agents"
        rounds = player_dict['ROUNDS']
        rating = player_dict['RATING 2.0']
        acs = player_dict['ACS']
        kd = player_dict['K/D']
        kills = player_dict['Kills']
        deaths = player_dict['Deaths']
        kast = player_dict['KAST']
        adr = player_dict['ADR']
        fpr = player_dict['FPR']
        apr = player_dict['APR']
        fkpr = player_dict['FKPR']
        fdpr = player_dict['FDPR']
        hs = player_dict['HS%']
        cl = player_dict['CL%']
        first_kills = player_dict['First Kills']
        first_deaths = player_dict['First Deaths']
        assists = player_dict['Assists']
        
        summary_text = "This is a collection of VCT {region} players and their statistics. They are ordered by RATING 2.0, which would typically indicate a player's ability (the higher the better). However this is not the only thing to take into consideration, players that show more consistency over an abundant amount of rounds would be desirable.\n\n"

        summary_text += f"Player Profile: {player}\n\n"
        summary_text += f"{player} is a player from the {region} region ({country}). They primarily play agents like {agents}. Across {rounds} rounds, their performance metrics include:\n\n"
        summary_text += f"- Rating 2.0: {rating}\n"
        summary_text += f"- Average Combat Score (ACS): {acs}\n"
        summary_text += f"- Kill/Death ratio: {kd} ({kills} kills, {deaths} deaths)\n"
        summary_text += f"- KAST (Kill, Assist, Survive, Trade): {kast}\n"
        summary_text += f"- Average Damage per Round (ADR): {adr}\n"
        summary_text += f"- First Kill Participation Rate (FKPR): {fkpr}\n"
        summary_text += f"- First Death Participation Rate (FDPR): {fdpr}\n"
        summary_text += f"- Headshot percentage: {hs}\n"
        summary_text += f"- Assist rate (APR): {apr}\n"
        summary_text += f"- Clutch success rate: {cl}\n"
        summary_text += f"- First kills: {first_kills}\n"
        summary_text += f"- First deaths: {first_deaths}\n"
        summary_text += f"- Assists: {assists}\n\n"



        # Collect player summaries by region
        if 'region_summaries' not in globals():
            region_summaries = {'APAC': [], 'AMERICAS': [], 'EMEA': [], 'CHINA': [], 'INTL': []}
        region_key = region if region in region_summaries else 'INTL'
        region_summaries[region_key].append(summary_text)

# After the playerTable loop, write region summaries to multiple files per region (split into 3 parts)
if 'region_summaries' in globals():
    for region, summaries in region_summaries.items():
        if summaries:
            chunk_size = (len(summaries) + 2) // 3  # Split into 3 nearly equal parts
            for i in range(3):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < 2 else len(summaries)
                chunk = summaries[start:end]
                if not chunk:
                    continue
                part_label = ["FIRST PART", "SECOND PART", "THIRD PART"][i]
                filename = os.path.join("player_profiles", f"{region}_player_profiles_part{i+1}.txt")
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(f"=== {region} PLAYER PROFILES: {part_label} ===\n\n")
                    file.write("\n".join(chunk))
                print(f"Saved {region} player profiles part {i+1} to {filename}")