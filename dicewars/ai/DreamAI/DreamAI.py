import random
import logging
import sys

from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.client.game.board import Board
from dicewars.client.game.player import Player
from typing import List, Optional

class AI:
    def __init__(self, player_name, board, players_order):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')
        # Pred odevzdanim zmenit na stderr!!!
        out_hdlr = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(out_hdlr)
        print(player_name)

    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """

        print(Helper.avg_prob_of_holding_borders(board, self.player_name))
        print(Helper.avg_prob_of_holding_borders(board, self.player_name, True))

        attacks = list(possible_attacks(board, self.player_name))
        while attacks:
            source, target = attacks.pop()
            #if source.get_dice() > target.get_dice():
            if attack_succcess_probability(source.get_dice(), target.get_dice()) > 0.5: 
                return BattleCommand(source.get_name(), target.get_name())
        else:
            self.logger.debug("No more possible turns.")
            return EndTurnCommand()



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

        probs = 0
        for area in borders:
            probs += can_hold(board, area.get_name(), area.get_dice(), player_name)

        return probs/len(borders)

