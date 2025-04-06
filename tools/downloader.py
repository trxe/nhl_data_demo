import nhl_api
import database
import argparse
import time
import logging
import datetime as dt
import json
import requests
import traceback
from logger import Logger
from pathlib import Path

APP_NAME = "nhlgamedata"
RETRY_THRESHOLD = 100

def parse_date(val: str, default_mm_dd) -> tuple[str, dt.date, bool]:
    def strptime(dstr: str):
        return dt.datetime.strptime(dstr, "%Y-%m-%d")
    if len(val) > 4:
        return val, strptime(val), False
    filled_date = f"{val}-{default_mm_dd}"
    return filled_date, strptime(filled_date), True

def fmt_date(val: dt.date, fmt: str = '%Y-%m-%d') -> str:
    return val.strftime(fmt)

def tui():
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("-pre", help="include preseason", action="store_true")
    parser.add_argument("-post", help="include postseason", action="store_true")
    parser.add_argument("-noreg", help="exclude regular season", default=False, action="store_false")
    parser.add_argument("-out", help="output directory", default="./data_json")
    _args = parser.parse_args()
    print(APP_NAME)
    args = { 'gametype_filter': [ ] }
    if _args.pre:
        args['gametype_filter'].append(1)
    if _args.post:
        args['gametype_filter'].append(3)
    if not _args.noreg:
        args['gametype_filter'].append(2)
    args['outdir'] = _args.out

    args['from_date'] = input("from year OR date (YYYY-MM-DD) [default: 2024]: ", ) or "2024"
    args['to_date'] = input("from year OR date (YYYY-MM-DD) [default: 2025]: ", ) or "2025"

    args['team_filter'] = input('filter by teams (abbrevs separated by ",") [default: all]: ').split(',')
    if args['team_filter'] == ['']:
        args['team_filter'] = []
    return args

def get_games(schedule: dict, upto: dt.datetime, team_filter: set[str], gametype_filter: set[int]):
    def get_game_if(day: dict, game: dict):
        return ( 
            parse_date(day.get('date'), '01-01')[1] < upto and 
            game.get('gameType') in gametype_filter and (
                not team_filter or
                game.get('awayTeam').get('abbrev') in team_filter or
                game.get('homeTeam').get('abbrev') in team_filter
            )
        )
    _, end_week, _ = parse_date(schedule.get('nextStartDate'), '01-01')
    return [ 
        game
        for day in schedule.get('gameWeek')
        for game in day.get('games')
        if get_game_if(day, game)
    ] , fmt_date(min(upto, end_week))

def main(gametype_filter: list[int], from_date: str, to_date: str, team_filter: list[str], outdir: str):
    RETRY = 0
    team_filter_comb = '' if not team_filter else f"_{'_'.join(team_filter)}"
    type_filter_comb = f"_{'t'.join([str(s) for s in gametype_filter])}"
    gametype_filter = set(gametype_filter)
    team_filter = set(team_filter)
    start_str, start, start_whole_year = parse_date(from_date, '12-01')
    end_str, end, end_whole_year = parse_date(to_date, '07-01')
    pre, _, _, _ = nhl_api.get_season_windows(start_str)
    _, _, _, postend = nhl_api.get_season_windows(end_str)
    if start_whole_year:
        start_str, start = pre, parse_date(pre, 'invalid')[1]
    if end_whole_year:
        end_str, end = postend, parse_date(postend, 'invalid')[1]
    logging.info(f"From {start_str} to {end_str}")
    while start < end and RETRY < RETRY_THRESHOLD:
        playbyplays = []
        rosters = []
        shifts = []
        games = []
        date = fmt_date(start)
        RETRY += 1
        try:
            sched = nhl_api.get_schedule(date)
            games, enddate = get_games(sched, end, team_filter, gametype_filter)
            Logger.info(f"DATE {date}")
        
            game_ids = [g.get('id') for g in games]
            for idx, gid in enumerate(game_ids):
                Logger.info(f"Requesting for game details {gid} [{idx}/{len(game_ids)}]")
                pbp = nhl_api.get_play_by_play(gid)
                Logger.info(f"Requesting for game shifts {gid} [{idx}/{len(game_ids)}]")
                shiftcharts = nhl_api.get_shiftcharts(gid)
                plays = [
                    {**p, 'gameId': gid}
                    for p in pbp.get('plays')
                ]
                playbyplays.extend(plays)
                ros = [
                    {**p, 'gameId': gid}
                    for p in pbp.get('rosterSpots')
                ]
                rosters.extend(ros)
                shifts.extend(shiftcharts.get('data'))

            start += dt.timedelta(days=7)
        except Exception as e:
            Logger.error(f"{e}\n{traceback.format_exc()}")
        finally:
            Logger.info("saving results")
            def write_to(datatype: str, data: any):
                if data:
                    with open(Path(outdir, f"{datatype}_{date}_{enddate}{type_filter_comb}{team_filter_comb}.json"), '+w') as file:
                        json.dump(data, file)
                else:
                    Logger.info(f"no data in {datatype}")

            write_to('rosters', rosters)
            write_to('games', games)
            write_to('playbyplays', playbyplays)
            write_to('shifts', shifts)
    

if __name__ == '__main__':
    args = tui()
    poutdir = Path(args['outdir'])
    outlog = Path(poutdir, f"{fmt_date(dt.datetime.now(), "%Y%m%d_%H%M%S")}.log")
    with open(outlog, '+w') as file:
        Logger.init(outstream=file)
        print(args)
        main(**args)