import logging
import sys

from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand


class AI:
    def __init__(self, player_name, board, players_order):
        self.player_name = player_name
        self.nb_players = board.nb_players_alive()
        self.board=board
        self.logger = logging.getLogger('AI')
        self.logger.setLevel(logging.WARN)
        # Pred odevzdanim zmenit na stderr!!!
        #print(self.logger)
        self.logger.info("DreamAI started.")
        self.logger.debug("player_name is :{}".format(player_name))
        self.logger.debug("players order is :{}".format(players_order))
        self.logger.debug("board is :{}".format(board.areas))



    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
        self.board = board
        self.logger.warning("---------------------")
        self.logger.warning("{}".format(len(board.get_players_regions(self.player_name))))#Počet regionů:
        self.logger.warning("{}".format(self.get_largest_region()))#Njevětší region:
        self.logger.warning("{}".format(board.get_player_dice(self.player_name))) # Počet kostek mých
        self.logger.warning("{}".format(self.get_avg_dice()))#Prumer poctu kostek ostatnich:
        self.logger.warning("{}".format(nb_turns_this_game)) #Pocet odehranych kol:
        self.logger.warning("---------------------")

        for region in board.get_players_regions(self.player_name):
            self.logger.debug("{}".format(region))

        attacks = list(possible_attacks(board, self.player_name))
        while attacks:
            source, target = attacks.pop()
            if attack_succcess_probability(source.get_dice(), target.get_dice()) > 0.5 or source.get_dice() == 8:
                return BattleCommand(source.get_name(), target.get_name())
        else:
            self.logger.debug("No more possible turns.")

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