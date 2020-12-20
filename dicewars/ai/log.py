from dicewars.client.game.board import Board
from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability

from typing import List, Optional

class Log:

    def __init__(self, logger, board, before: bool = False):
        self.board = board
        self.before = before
        self.helper = Helper()
        self.logger = logger


    def before_turn(self, player_name, nb_turns_this_game, largest_region, avg_dice):
        if self.before:
            self.log(player_name, nb_turns_this_game, largest_region, avg_dice)

    def after_turn(self, player_name, nb_turns_this_game, largest_region, avg_dice):
        if not self.before:
            self.log(player_name, nb_turns_this_game, largest_region, avg_dice)

    def log(self, player_name, nb_turns_this_game, largest_region, avg_dice):
        
        self.logger.warning("---------------------")
        self.logger.warning(f"{len(self.board.get_players_regions(player_name))}")  # Počet regionů:
        self.logger.warning(f"{largest_region}")  # Njevětší region:
        self.logger.warning(f"{self.board.get_player_dice(player_name)}")  # Počet kostek mých
        self.logger.warning(f"{avg_dice}")  # Prumer poctu kostek ostatnich:
        self.logger.warning(f"{self.board.nb_players_alive()}")  # Aktualni pocet protihracu
        self.logger.warning(f"{len(self.helper.borders_of_largest_region(self.board, player_name))}")  # delka hranic nejvetsiho regionu
        self.logger.warning(f"{len(self.board.get_player_border(player_name))}")  # celkova delka hranic
        self.logger.warning(f"{self.helper.avg_prob_of_holding_borders(self.board, player_name, False)}")  # prumerna pst udržení uzemi na vsech hranicich
        self.logger.warning(f"{self.helper.avg_prob_of_holding_borders(self.board, player_name, True)}")  # prumerna pst udržení uzemi na hranicich nejvetsiho regionu
        self.logger.warning(f"{self.helper.avg_nb_of_border_dice(self.board, player_name)}")  # prumerny pocet kostek na hranicich nejvetsiho regionu
        self.logger.warning(f"{nb_turns_this_game}")  # Pocet odehranych kol:
        self.logger.warning("---------------------")


class Helper:
    @staticmethod
    def player_largest_region(board: Board, player_name):
        """Get size of the largest region, including the areas within"""

        players_regions = board.get_players_regions(player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]

        largest_region = max_sized_regions[0]
        return largest_region


    @staticmethod
    def borders_of_largest_region(board: Board, player_name) -> List[int]:
        """Get borders IDs of largest region"""
        region = Helper.player_largest_region(board, player_name)
        return [areaID for areaID in region if board.is_at_border(board.get_area(areaID))]

    @staticmethod
    def avg_nb_of_border_dice(board: Board, player_name):
        """Get average number of dice on border of largest region"""
        border = Helper.borders_of_largest_region(board, player_name)

        if len(border) == 0:  # only for last round - all areas are mine
            return 8

        dice_sum = 0
        for areaID in border:
            dice_sum += board.get_area(areaID).get_dice()

        return dice_sum/len(border)

    @staticmethod
    def avg_prob_of_holding_borders(board: Board, player_name:int, largest_region_only=False):
        """Get average probability of holding border areas until next turn"""
        if(largest_region_only):
            border_ids = Helper.borders_of_largest_region(board, player_name)
            borders = [board.get_area(areaID) for areaID in border_ids]
        else:
            borders = board.get_player_border(player_name)

        if len(borders) == 0:  # only for last round - all areas are mine
            return 1

        probs = 0
        for area in borders:
            probs += can_hold(board, area.get_name(), area.get_dice(), player_name)



        return probs/len(borders)