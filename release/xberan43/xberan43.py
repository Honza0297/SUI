import copy
import torch
import numpy as np
from dicewars.ai.utils import possible_attacks, probability_of_holding_area as can_hold, attack_succcess_probability



from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
from dicewars.client.game.board import Board
from typing import List
from dicewars.client.game.area import Area
from dicewars.ai.xberan43.trainer import LogisticRegressionMulti

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

        return self.model.prob_class_1(data)


class AI:
    def __init__(self, player_name, board, players_order):
        self.player_name = player_name
        self.nb_players = board.nb_players_alive()
        self.board=board

        self.states = []
        self.nb_turns_without_move = 0


        self.model = LogisticRegressionMulti()
        self.model.load_state_dict(torch.load("dicewars/ai/xberan43/fea11.pt"))
        self.model.eval()



    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
        self.board = board
        self.nb_players = board.nb_players_alive()


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

        current_state_val = 0.7 * self.model.prob_class_1(data) #evalution of current state is degradated on purpose, so the AI is more "agressive"

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

        if nb_moves_this_turn == 0:
            self.nb_turns_without_move += 1

        if self.nb_turns_without_move >= 3:
            best = [None, -1]
            for attack in possible_attacks(board, self.player_name):
                source, target = attack
                prob = attack_succcess_probability(source.get_dice(), target.get_dice())
                if prob > best[1]:
                    best[0] = attack
                    best[1] = prob
            self.nb_turns_without_move = 0
            source, target = best[0]
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

    @staticmethod
    def largest_region_size(board, player_name):
        """Get size of the largest region, including the areas within"""

        players_regions = board.get_players_regions(player_name)
        max_region_size = max(len(region) for region in players_regions)
        return max_region_size

    @staticmethod
    def get_avg_dice(board, nb_players, player_name):
        if nb_players == 1:
            return 1

        sum = 0.0
        for num in range(1,nb_players+1):
            if(num == player_name): pass
            sum += board.get_player_dice(num)

        return sum / (nb_players-1)



