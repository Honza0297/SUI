import random
import logging
import sys

from dicewars.ai.utils import possible_attacks

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand


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
        attacks = list(possible_attacks(board, self.player_name))
        if attacks:
            self.logger.debug("Possible attacks are:")
            self.logger.debug("   *"+attack for attack in attacks)
            source, target = random.choice(attacks)
            return BattleCommand(source.get_name(), target.get_name())
        else:
            self.logger.debug("No more possible turns.")
            return EndTurnCommand()

