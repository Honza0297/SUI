import logging
from ..utils import possible_attacks

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability
from dicewars.client.game.board import Board
from typing import List, Optional
from dicewars.ai.DreamAI.DreamAI import Helper


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

    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn

        Creates a list with all possible moves along with associated strength
        difference. The list is then sorted in descending order with respect to
        the SD. A move with the highest SD is then made unless the highest
        SD is lower than zero - in this case, the agent ends its turn.
        """

        attacks = []
        for source, target in possible_attacks(board, self.player_name):
            area_dice = source.get_dice()
            strength_difference = area_dice - target.get_dice()
            attack = [source.get_name(), target.get_name(), strength_difference]
            attacks.append(attack)

        attacks = sorted(attacks, key=lambda attack: attack[2], reverse=True)

        if attacks and attacks[0][2] >= 0:
            return BattleCommand(attacks[0][0], attacks[0][1])

        self.board = board

        self.logger.warning("---------------------")
        self.logger.warning("{}".format(len(board.get_players_regions(self.player_name))))  # Počet regionů:
        self.logger.warning("{}".format(self.get_largest_region()))  # Njevětší region:
        self.logger.warning("{}".format(board.get_player_dice(self.player_name)))  # Počet kostek mých
        self.logger.warning("{}".format(self.get_avg_dice()))  # Prumer poctu kostek ostatnich:
        self.logger.warning("{}".format(board.nb_players_alive()))  # Aktualni pocet protihracu
        self.logger.warning("{}".format(
            len(Helper.borders_of_largest_region(board, self.player_name))))  # delka hranic nejvetsiho regionu
        self.logger.warning("{}".format(len(board.get_player_border(self.player_name))))  # celkova delka hranic
        self.logger.warning("{}".format(Helper.avg_prob_of_holding_borders(board, self.player_name,
                                                                           False)))  # prumerna pst udržení uzemi na vsech hranicich
        self.logger.warning("{}".format(Helper.avg_prob_of_holding_borders(board, self.player_name,
                                                                           True)))  # prumerna pst udržení uzemi na hranicich nejvetsiho regionu
        self.logger.warning("{}".format(Helper.avg_nb_of_border_dice(board,
                                                                     self.player_name)))  # prumerny pocet kostek na hranicich nejvetsiho regionu
        self.logger.warning("{}".format(nb_turns_this_game))  # Pocet odehranych kol:
        self.logger.warning("---------------------")

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
