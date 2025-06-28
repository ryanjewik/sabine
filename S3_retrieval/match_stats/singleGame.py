import json
import os
from collections import defaultdict
from datetime import datetime

def process_game_file(game_file_path, league, year):
    with open(game_file_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)  # this loads the array


    key_counts = defaultdict(int)
    elimCount = 0
    defuseCount = 0
    detonateCount = 0
    spikePlantedCount = 0
    platformGameId = game_data[0]['platformGameId']
    gameStartTime = None
    roundNumber = 1
    eventList = []
    teamOneRoundCount = 0
    teamTwoRoundCount = 0




    #maps the platformGameId to the mapping_data
    with open (f"../{league}/esports-data/mapping_data.json", "r", encoding="utf-8") as f:
        mapping_data = json.load(f)
    platform_gameid_lookup = {entry["platformGameId"]: entry for entry in mapping_data}
    mapping = platform_gameid_lookup.get(platformGameId)


    # Players lookup
    with open (f"../{league}/esports-data/players.json", "r", encoding="utf-8") as f:
        players_data = json.load(f)
    player_lookup = {entry["id"]: entry for entry in players_data}
    player_name_dict = {}
    if mapping and 'participantMapping' in mapping:
        participant_ids = list(mapping['participantMapping'].values())
        participant_keys = list(mapping['participantMapping'].keys())
        for k in participant_keys:
            player_id = mapping['participantMapping'][k]
            player = player_lookup.get(player_id)
            player_name_dict[int(k)] = player['handle'] if player else None
    else:
        print('No participantMapping found in mapping')


    # Maps the team to the one in mapping_data. We can replace the team values with the team names now using team_name_dict
    with open (f"../{league}/esports-data/teams.json", "r", encoding="utf-8") as f:
        teams_data = json.load(f)
    team_lookup = {entry["id"]: entry for entry in teams_data}
    team_name_dict = {}
    if mapping and 'teamMapping' in mapping:
        team_ids = list(mapping['teamMapping'].values())
        team_keys = list(mapping['teamMapping'].keys())
        if len(team_ids) >= 2:
            first_team = team_lookup.get(team_ids[0])
            second_team = team_lookup.get(team_ids[1])
            # Build dictionary: keys from teamMapping, values are team names
            team_name_dict = {
                int(team_keys[0]): first_team['name'] if first_team else None,
                int(team_keys[1]): second_team['name'] if second_team else None
            }
        else:
            print('Not enough teams in teamMapping')
    else:
        print('No teamMapping found in mapping')



    # we now have the tournament names, and date range
    with open (f"../{league}/esports-data/tournaments.json", "r", encoding="utf-8") as f:
        tournaments_data = json.load(f)
    tournament_lookup = {entry["id"]: entry for entry in tournaments_data}
    if mapping and 'tournamentId' in mapping:
        tournament_id = mapping['tournamentId']
        tournament = tournament_lookup.get(tournament_id)
        if tournament:
            tournament_name = tournament.get('name')
            tournament_name = tournament_name.replace('_', ' ')
        else:
            print('No tournament found for tournamentId', tournament_id)
    else:
        print('No tournamentId in mapping or mapping not found')



    #function for roundDecided
    def count_round_decided(item):
        nonlocal elimCount, defuseCount, detonateCount, spikePlantedCount, roundNumber, teamOneRoundCount, teamTwoRoundCount
        cause = item['result']['spikeModeResult']['cause']
        if cause == "ELIMINATION":
            elimCount += 1
        elif cause == "SPIKE_DEFUSE":
            defuseCount += 1
            spikePlantedCount += 1
        elif cause == "DETONATE":
            detonateCount += 1
            spikePlantedCount += 1
        roundNumber += 1
        eventList.append(f"Round {roundNumber - 1} ended with {cause.lower()}. The winning team is {team_name_dict[item['result']['winningTeam']['value']] }.")
        if item['result']['winningTeam']['value'] == list(team_name_dict.keys())[0]:
            teamOneRoundCount += 1
        elif item['result']['winningTeam']['value'] == list(team_name_dict.keys())[1]:
            teamTwoRoundCount += 1
        eventList.append(f"The current score is {team_name_dict[list(team_name_dict.keys())[0]]} {teamOneRoundCount} - {teamTwoRoundCount} {team_name_dict[list(team_name_dict.keys())[1]]}.")


    #fixes the "walltime" format
    def fix_walltime(timestamp: str) -> str:
        # Ensure the year has 4 digits
        if timestamp.startswith("0") or timestamp.startswith("00"):
            timestamp = "2" + timestamp  # Assumes it's supposed to be 2022, etc.

        # Remove milliseconds and keep only the datetime part
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If parsing fails, just return the original timestamp
            return timestamp




    # Initialize player stats dictionary
    player_stats = {}
    for k, player_name in player_name_dict.items():
        # Determine team for this player (first 5 are team 1, next 5 are team 2)
        if k <= 5:
            team = team_name_dict[list(team_name_dict.keys())[1]]
        else:
            team = team_name_dict[list(team_name_dict.keys())[0]]
        player_stats[player_name] = {
            'team': team,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'KDA': 0.0,
            'first_kills': 0,
            'first_deaths': 0
        }

    # Track first kill and first death per round
    current_round = 1
    first_kill_in_round = set()
    first_death_in_round = set()
    round_first_kill_found = False
    round_first_death_found = False




    #loop through the game_data
    for x in game_data:
        for y in x:
            key_counts[y] += 1
            if y == "roundDecided":
                count_round_decided(x['roundDecided'])
                # Reset for next round
                current_round += 1
                round_first_kill_found = False
                round_first_death_found = False
                gameEndTime = fix_walltime(x['metadata']['wallTime'])
            elif y == "playerDied":
                playerAssist = []
                deceased_num = x[y]['deceasedId']['value']
                killer_num = x[y]['killerId']['value'] if 'killerId' in x[y] else None
                deceased_name = player_name_dict[deceased_num]
                # First death in round
                if not round_first_death_found:
                    player_stats[deceased_name]['first_deaths'] += 1
                    round_first_death_found = True
                player_stats[deceased_name]['deaths'] += 1
                # First kill in round
                if killer_num is not None:
                    killer_name = player_name_dict[killer_num]
                    if not round_first_kill_found:
                        player_stats[killer_name]['first_kills'] += 1
                        round_first_kill_found = True
                    player_stats[killer_name]['kills'] += 1
                # Update assists
                if x[y]['assistants']:
                    for assistants in x[y]['assistants']:
                        assistant_num = assistants['assistantId']['value']
                        assistant_name = player_name_dict[assistant_num]
                        player_stats[assistant_name]['assists'] += 1
                eventList.append(f"{killer_name if killer_num is not None else 'Unknown'} killed {deceased_name} {'with assist from ' + ', '.join(playerAssist) if playerAssist else ''} in round {roundNumber}")
            elif y == "platformGameId":
                if platformGameId is None:
                    platformGameId = x['platformGameId']
            elif y == "gameDecided": #team mapping here
                if 'winningTeam' in x[y]:
                    if 'value' in x[y]['winningTeam']:
                        winningTeamValue = x[y]['winningTeam']['value']
                        gameEndTime = x['metadata']['wallTime']
                        gameEndTime = fix_walltime(gameEndTime)
                        eventList.append(f"Game ended with winning team: {team_name_dict[winningTeamValue]} at {gameEndTime}")
                    else:
                        print(f"Warning: 'winningTeam' exists but has no 'value': {x[y]['winningTeam']}")
                        eventList.append(f"GameDecided event has 'winningTeam' but no 'value': {x[y]['winningTeam']}")
                else:
                    eventList.append("GameDecided event missing 'winningTeam' key.")
                    print(f"Warning: 'winningTeam' key missing in gameDecided event for file {game_file_path}")
                print(x[y])
            elif y == 'roundStarted':
                if gameStartTime is None:
                    gameStartTime = x['metadata']['wallTime']
                    gameStartTime = fix_walltime(gameStartTime)
                    eventList.append(f"Game started at {gameStartTime}")
                   
                   
       
        
                

    # After processing all events, check if 'roundDecided' exists in key_counts
    if 'roundDecided' not in key_counts:
        print("No game stats exist: 'roundDecided' not found in game data. Summary will not be created.")
        return

    # Determine winning team if not set
    if 'winningTeamValue' not in locals():
        # Compare teamOneRoundCount and teamTwoRoundCount
        if teamOneRoundCount > teamTwoRoundCount:
            winningTeamValue = list(team_name_dict.keys())[0]
        elif teamTwoRoundCount > teamOneRoundCount:
            winningTeamValue = list(team_name_dict.keys())[1]
        else:
            winningTeamValue = None  # Tie or unknown
        print(f"winningTeamValue was not set by events, determined by score: {winningTeamValue}")

    winningTeam = team_name_dict[winningTeamValue] if winningTeamValue is not None else 'Unknown'
    basic_stats = []
    #our data
    basic_stats.append(f"platformGameId: {platformGameId}")
    basic_stats.append(f"Team 1: {team_name_dict[list(team_name_dict.keys())[0]]}")
    basic_stats.append(f"Team 2: {team_name_dict[list(team_name_dict.keys())[1]]}")
    basic_stats.append(f"Winning Team: {winningTeam}")
    basic_stats.append(f"Score: {team_name_dict[list(team_name_dict.keys())[0]]} {teamOneRoundCount} - {teamTwoRoundCount} {team_name_dict[list(team_name_dict.keys())[1]]}")
    basic_stats.append(f"Tournament Name: {tournament_name}")
    basic_stats.append(f"Game Start Time: {gameStartTime}")
    basic_stats.append(f"Game End Time: {gameEndTime}")
    basic_stats.append(f"Rounds ended by ELIMINATION count: {elimCount}")
    basic_stats.append(f"Rounds ended by DEFUSE count: {defuseCount}")
    basic_stats.append(f"Rounds ended by DETONATE count: {detonateCount}")
    basic_stats.append(f"SPIKE PLANTED count: {spikePlantedCount}")
    # Print participating players
    basic_stats.append("Participating Players:")
    for k in sorted(player_name_dict.keys()):
        basic_stats.append(f"Player {k}: {player_name_dict[k]}")
        


    # Calculate KDA for each player
    for player_name, stats in player_stats.items():
        deaths = stats['deaths'] if stats['deaths'] > 0 else 1  # avoid division by zero
        stats['KDA'] = round((stats['kills'] + stats['assists']) / deaths, 2)

    # Print player stats
    prettyPlayerStats = []
    for player_name, stats in player_stats.items():
        prettyPlayerStats.append(f"{player_name}: Team={stats['team']}, Kills={stats['kills']}, Deaths={stats['deaths']}, Assists={stats['assists']}, KDA={stats['KDA']}, First Kills={stats['first_kills']}, First Deaths={stats['first_deaths']}")

    # Remove 'val:' prefix from platformGameId for filename
    clean_platformGameId = platformGameId.replace('val:', '') if platformGameId.startswith('val:') else platformGameId

    # Ensure match_summaries directory exists
    summaries_dir = "match_summaries"
    os.makedirs(summaries_dir, exist_ok=True)

    # Write summary to file in match_summaries directory, but skip if it already exists
    summary_filename = os.path.join(summaries_dir, f"{clean_platformGameId}_match_summary.txt")
    if os.path.exists(summary_filename):
        print(f"Summary already exists for {clean_platformGameId}, skipping.")
        return
    with open(summary_filename, "w", encoding="utf-8") as f:
        for line in basic_stats:
            f.write(line + "\n")
        f.write("\n--- Events ---\n")
        for event in eventList:
            f.write(event + "\n")
        f.write("\n--- Player Stats ---\n")
        for line in prettyPlayerStats:
            f.write(line + "\n")
    print(f"Summary written to {summary_filename}")


if __name__ == "__main__":
    # Example usage: python singleGame.py F:/VCT-data/vct-international/2024/your_game_file.json vct-international 2024
    import sys
    if len(sys.argv) != 4:
        print("Usage: python singleGame.py <game_file_path> <league> <year>")
        sys.exit(1)
    game_file_path = sys.argv[1]
    league = sys.argv[2]
    year = int(sys.argv[3])
    print(f"Processing {game_file_path}")
    process_game_file(game_file_path, league, year)



