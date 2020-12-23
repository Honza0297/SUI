import logging
import copy
import sys
import torch
import trainer
import numpy as np
from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, probability_of_successful_attack as should_attack, attack_succcess_probability
from ..log import Log
from ..log import Helper


from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.client.game.board import Board
from dicewars.client.game.player import Player
from typing import List, Optional
from dicewars.client.game.area import Area
from trainer import LogisticRegressionMulti

class State:
    def __init__(self, board: Board, attack_sequence, probabilities, player_name, nb_turns, model):
        self.attack_sequence = attack_sequence
        self.board = board
        self.prob = probabilities
        self.player_name = player_name
        self.nb_turns = nb_turns
        self.model = model

    def push_attack(self, attack: (Area, Area), probability):
        self.attack_sequence.append(attack)
        self.prob.append(probability)

    def pop_attack(self):
        return self.attack_sequence.pop()

    def add_board(self, board: Board):
        self.board = board

    def evaluateState(self):
        board = self.board
        data = np.asarray([
            len(board.get_players_regions(self.player_name)),
            Helper.largest_region_size(board, self.player_name),
            board.get_player_dice(self.player_name),
            Helper.get_avg_dice(board, board.nb_players_alive(), self.player_name),
            board.nb_players_alive(),
            len(Helper.borders_of_largest_region(board, self.player_name)),
            len(board.get_player_border(self.player_name)),
            Helper.avg_prob_of_holding_borders(board, self.player_name, False),
            float(Helper.avg_prob_of_holding_borders(board, self.player_name, True)),
            Helper.avg_nb_of_border_dice(board, self.player_name),
            self.nb_turns])

        return self.model.prob_class_1(data) #torch.mean(self.model(data)).item()


class AI:
    def __init__(self, player_name, board, players_order):
        self.player_name = player_name
        self.nb_players = board.nb_players_alive()
        self.board=board

        self.states = []
        self.nb_turns_without_move = 0


        self.logger = logging.getLogger('AI')
        self.logger.setLevel(logging.WARN)

        self.logger.info("DreamAI started.")
        self.logger.debug("player_name is :{}".format(player_name))
        self.logger.debug("players order is :{}".format(players_order))
        self.logger.debug("board is :{}".format(board.areas))
        self.log = Log(self.logger)

        self.model = LogisticRegressionMulti()
        self.model.load_state_dict(torch.load("fea11.pt"))
        self.model.eval()
        # print("jsem ", player_name)



    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
        self.board = board
        self.nb_players = board.nb_players_alive()
        # self.log.before_turn(board, self.player_name, nb_turns_this_game, self.get_largest_region(), self.get_avg_dice())


        if time_left < 0.3:
            return self.lite_version(nb_moves_this_turn)


        data = np.asarray([
            len(board.get_players_regions(self.player_name)),
            Helper.largest_region_size(board, self.player_name),
            board.get_player_dice(self.player_name),
            Helper.get_avg_dice(board, self.nb_players, self.player_name),
            board.nb_players_alive(),
            len(Helper.borders_of_largest_region(board, self.player_name)),
            len(board.get_player_border(self.player_name)),
            Helper.avg_prob_of_holding_borders(board, self.player_name, False),
            Helper.avg_prob_of_holding_borders(board, self.player_name, True),
            Helper.avg_nb_of_border_dice(board, self.player_name),
            nb_turns_this_game])
        #output = self.model(data)
        current_state_val = 0.7 * self.model.prob_class_1(data) #torch.mean(output).item()

        self.states = []
        self.state_search(State(copy.deepcopy(board), [], [], self.player_name, nb_turns_this_game, self.model))

        max_combinated = 0
        winner_state = None # type: State
        for state in self.states:
            val = state.evaluateState()
            if val > current_state_val:
                combinated = state.prob[0] * val
                if combinated > max_combinated:
                    max_combinated = combinated
                    winner_state = state

        if(winner_state):
            source, target = winner_state.pop_attack()
            self.nb_turns_without_move = 0
            return BattleCommand(source.get_name(), target.get_name())


        # ELSE


        # self.log.after_turn(board, self.player_name, nb_turns_this_game, self.get_largest_region(), self.get_avg_dice())
        # self.logger.warning(str(nb_turns_this_game) + ":" + str(nb_moves_this_turn))
        if nb_moves_this_turn == 0:
            self.nb_turns_without_move += 1
        if self.nb_turns_without_move >= 8:
            for attack in possible_attacks(board, self.player_name):
                source, target = attack
                self.nb_turns_without_move = 0
                return BattleCommand(source.get_name(), target.get_name())

        return EndTurnCommand()

    def lite_version(self, nb_moves_this_turn):
        self.logger.warning("fallback")
        attacks = list(possible_attacks(self.board, self.player_name)) #TODO asi to nechat yieldovat, kvuli uspore casu, ne?
        while attacks:
            source, target = attacks.pop()
            if attack_succcess_probability(source.get_dice(), target.get_dice()) > 0.5 or source.get_dice() == 8:
                self.nb_turns_without_move = 0
                return BattleCommand(source.get_name(), target.get_name())

        if nb_moves_this_turn == 0:
            self.nb_turns_without_move += 1
        return EndTurnCommand()

    # def state_search(self, board: Board, attack_sequence = [], probabilities=[]):
    #     attack_sequence = attack_sequence
    #     probabilities = probabilities
    #     for attack in possible_attacks(board, self.player_name):
    #         source, target = attack
    #         success_probability = attack_succcess_probability(source.get_dice(), target.get_dice())
    #         if success_probability < 0.5 and source.get_dice() != 8:
    #             return
    #
    #         attack_sequence.append(attack)
    #         probabilities.append(success_probability)
    #         board_copy = self.create_board_after_attack(board, source, target)
    #         self.states.append(State(board_copy, attack_sequence, probabilities))
    #
    #         self.state_search(board_copy, attack_sequence)

    def state_search(self, state: State, recursive_level = 0):
        """Vygeneruje vsechny mozne stavy """
        # if(recursive_level > 3):
        #     return
        attacks = list(possible_attacks(state.board, self.player_name))
        for attack in attacks :
            source, target = attack
            success_probability = attack_succcess_probability(source.get_dice(), target.get_dice())
            if success_probability < 0.5 and source.get_dice() != 8:
                continue
            state_copy = copy.deepcopy(state) # type: State
            state_copy.push_attack(attack, success_probability)
            self.simulate_attack(state_copy.board, source.get_name(), target.get_name())
            self.states.append(state_copy)

            # self.state_search(state_copy, recursive_level + 1)


    def simulate_attack(self, board: Board, source: int, target: int):
        """Sets board to state after my successful attack"""
        board.get_area(target).set_owner(self.player_name)  # set me as new owner of target
        board.get_area(target).set_dice(board.get_area(source).get_dice() - 1)  # set number of dice in my new area as source dice - 1
        board.get_area(source).set_dice(1)  # set number of dice in source are to 1
        return board

    # def get_avg_dice(self):
    #     sum = 0.0
    #     for num in range(1,self.nb_players+1):
    #         if(num == self.player_name): pass
    #         sum += self.board.get_player_dice(num)
    #
    #     return sum / (self.nb_players-1)


    # def get_largest_region(self):
    #     """Get size of the largest region, including the areas within
    #
    #     Attributes
    #     ----------
    #     largest_region : list of int
    #         Names of areas in the largest region
    #
    #     Returns
    #     -------
    #     int
    #         Number of areas in the largest region
    #     """
    #     self.largest_region = []
    #
    #     players_regions = self.board.get_players_regions(self.player_name)
    #     max_region_size = max(len(region) for region in players_regions)
    #     max_sized_regions = [region for region in players_regions if len(region) == max_region_size]
    #
    #     self.largest_region = max_sized_regions[0]
    #     return max_region_size




