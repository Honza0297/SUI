import logging
from ..utils import possible_attacks
from ..log import Log

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability
from dicewars.client.game.board import Board
from typing import List, Optional


class AI:
    """Agent using Strength Difference Checking (SDC) strategy

    This agent prefers moves with highest strength difference
    and doesn't make moves against areas with higher strength.
    """
    def __init__(self, player_name, board, players_order):
        """
        Parameters
        ----------
        game : Game

        Attributes
        ----------
            Areas that can make an attack
        """
        self.player_name = player_name
        self.nb_players = board.nb_players_alive()
        self.logger = logging.getLogger('AI')
        self.log = Log(self.logger)

    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn

        Creates a list with all possible moves along with associated strength
        difference. The list is then sorted in descending order with respect to
        the SD. A move with the highest SD is then made unless the highest
        SD is lower than zero - in this case, the agent ends its turn.
        """

        self.board = board
        self.log.before_turn(board, self.player_name, nb_turns_this_game, self.get_largest_region(), self.get_avg_dice())

        attacks = []
        for source, target in possible_attacks(board, self.player_name):
            area_dice = source.get_dice()
            strength_difference = area_dice - target.get_dice()
            attack = [source.get_name(), target.get_name(), strength_difference]
            attacks.append(attack)

        attacks = sorted(attacks, key=lambda attack: attack[2], reverse=True)

        if attacks and attacks[0][2] >= 0:
            return BattleCommand(attacks[0][0], attacks[0][1])

        self.log.after_turn(board, self.player_name, nb_turns_this_game, self.get_largest_region(), self.get_avg_dice())

        return EndTurnCommand()

    def get_avg_dice(self):
        sum = 0.0
        for num in range(1,self.nb_players+1):
            if(num == self.player_name): pass
            sum += self.board.get_player_dice(num)

        return sum / (self.nb_players-1)


    def get_largest_region(self):
        """Get size of the largest region, including the areas within

        Attributes
        ----------
        largest_region : list of int
            Names of areas in the largest region

        Returns
        -------
        int
            Number of areas in the largest region
        """
        self.largest_region = []

        players_regions = self.board.get_players_regions(self.player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]

        self.largest_region = max_sized_regions[0]
        return max_region_size
