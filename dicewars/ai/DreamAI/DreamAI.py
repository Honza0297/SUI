import random
import logging
import sys

from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.client.game.board import Board
from dicewars.client.game.player import Player

class AI:
    def __init__(self, player_name, board, players_order):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')
        # Pred odevzdanim zmenit na stderr!!!
        out_hdlr = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(out_hdlr)
    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
        print("nejdelsi moje hranice:" + str(len(Helper.get_borders_of_largest_region(board, self.player_name)[0])))

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
    def get_player_largest_region(board: Board, player_name):
        """Get size of the largest region, including the areas within
        Attributes
        ----------
        largest_region : list of int
            Names of areas in the largest region
        Returns
        -------
            List
            Number of areas in the largest region
        """
        largest_region = []

        players_regions = board.get_players_regions(player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]

        largest_region = max_sized_regions[0]
        return largest_region


    @staticmethod
    def get_borders_of_largest_region(board: Board, player_name):
        region = Helper.get_player_largest_region(board, player_name)
        return [area for area in region if board.is_at_border(area)]



