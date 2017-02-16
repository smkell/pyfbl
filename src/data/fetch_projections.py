# -*- coding: utf-8 -*-

""" Fetches projections from one or more sources.
"""
import os
import logging

from bs4 import BeautifulSoup
import click
from dotenv import find_dotenv, load_dotenv
from flags import Flags
import requests
import pandas as pd

class PositionElgibility(Flags):
    """ Bitwise enum for marking a player's egibility.abs
    """

    catcher = ()
    first_base = ()
    second_base = ()
    third_base = ()
    short_stop = ()
    outfield = ()
    left_field = ()
    center_field = ()
    right_field = ()
    designated_hitter = ()
    pitcher = ()
    starting_pitcher = ()
    relief_pitcher = ()

class Player(object):
    player_id = ''
    name = ''

    def __init__(self, player_id, name):
        self.player_id = player_id
        self.name = name
        self.runs = 0.0
        self.home_runs = 0.0
        self.runs_batted_in = 0.0
        self.stolen_bases = 0.0
        self.batting_avg = 0.0
        self.strikeouts = 0.0
        self.wins = 0.0
        self.saves = 0.0
        self.earned_run_avg = 0.0
        self.walks_hits_per_inning = 0.0
        self.position_elgibility = PositionElgibility.no_flags

    def __repr__(self):
        return "{0}".format(self.__dict__)

def parse_espn_player(table, position_code):
    position_codes = {'C': PositionElgibility.catcher,
                      '1B': PositionElgibility.first_base,
                      '2B': PositionElgibility.second_base,
                      '3B': PositionElgibility.third_base,
                      'SS': PositionElgibility.short_stop,
                      'OF': PositionElgibility.outfield,
                      'LF': PositionElgibility.left_field,
                      'CF': PositionElgibility.center_field,
                      'RF': PositionElgibility.right_field,
                      'DH': PositionElgibility.designated_hitter,
                      'P': PositionElgibility.pitcher,
                      'SP': PositionElgibility.starting_pitcher,
                      'RP': PositionElgibility.relief_pitcher}
    position_stats = {
        1: ['at_bats', 'runs', 'home_runs', 'runs_batted_in', 'batter_walks', 'batter_strikeouts', 'stolen_bases', 'batting_avg', 'on_base_percent', 'slugging_avg', 'on_base_plus_slugging'],
        2: ['games', 'games_started', 'innings_pitched', 'walks', 'strikeouts', 'wins', 'saves', 'holds', 'earned_run_avg', 'walks_hits_per_inning', 'strikeouts_per_9']
    }

    logger = logging.getLogger()
    name_row = table.select('tr')[0]
    name_cell = name_row.select('td > span.subheadPlayerNameLink > nobr > a')[0]

    stats_row = table.select('tr')[2]
    player_id = name_cell['playerid']
    player_name = name_cell.get_text()
    player = Player(player_id, player_name)

    position_cell = name_row.select('td > span.subheadPlayerNameLink')[0]
    position_cell_text = position_cell.get_text().replace(u"\u00A0", " ").split(" ")

    for comp in position_cell_text[3:]:
        comp = comp.replace(',', '')
        if comp in position_codes:
            player.position_elgibility = player.position_elgibility | position_codes[comp]

    stat_cells = stats_row.select('td.playertableStat')
    for stat_id in range(0, len(stat_cells)):
        stat_name = position_stats[position_code][stat_id]
        stat_text = stat_cells[stat_id].get_text()
        stat = stat_text.replace('--', '0')
        setattr(player, stat_name, float(stat))

    logger.debug('Processing player %s', player)
    return player

def fetch_espn_projections(season):
    logger = logging.getLogger(__name__)
    base_url = 'http://games.espn.com/flb/tools/projections'
    positions = {1: 13* 10 * 2, 2: 9*10*2 }

    players = []
    for position, count in positions.items():
        for start_index in range(0, count, 15):
            url = "{0}?display=alt&slotCategoryGroup={1}&startIndex={2}".format(base_url, position, start_index)
            logger.info('Fetching url %s', url)
            html_doc = requests.get(url).text
            soup = BeautifulSoup(html_doc, 'html.parser')
            player_tables = soup.select('table.tableBody')

            for row in player_tables:
                players.append(parse_espn_player(row, position))
    return players

@click.command()
@click.argument('year', type=click.INT)
@click.option('--espn/--no-espn', default=True)
def main(year, espn):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('fetching projections for %d season.', year)

    if espn:
        players = fetch_espn_projections(year)
        cols = [
            'player_id', 'name', 'position_elgibility',
            'at_bats', 'runs', 'home_runs', 'runs_batted_in', 'batter_walks', 'batter_strikeouts', 'stolen_bases', 'batting_avg', 'on_base_percent', 'slugging_avg', 'on_base_plus_slugging',
            'games', 'games_started', 'innings_pitched', 'walks', 'strikeouts', 'wins', 'saves', 'holds', 'earned_run_avg', 'walks_hits_per_inning', 'strikeouts_per_9'
        ]
        df = pd.DataFrame.from_records([p.__dict__ for p in players], columns=cols)
        df.loc[:,'position_elgibility'] = df['position_elgibility'].apply(lambda x: int(x))
        df.to_csv(os.path.join(project_dir, 'data/raw/projections-espn-{0}.csv'.format(year)), index=False)
        print(df.info())

    logger.info('Fetched projections for %d players', len(players))

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
