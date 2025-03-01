from __future__ import absolute_import

import unittest

from simulation import action
from simulation import event
from simulation.avatar.avatar_manager import AvatarManager
from simulation.direction import EAST
from simulation.game_state import GameState
from simulation.interactables.pickups.artefacts import YellowOrbArtefact
from simulation.location import Location
from .dummy_avatar import MoveDummy
from .maps import InfiniteMap, EmptyMap, AvatarMap, PickupMap

ORIGIN = Location(x=0, y=0)
EAST_OF_ORIGIN = Location(x=1, y=0)
NORTH_OF_ORIGIN = Location(x=0, y=1)


class TestAction(unittest.TestCase):
    def setUp(self):
        self.avatar = MoveDummy(1, ORIGIN, EAST)
        self.other_avatar = MoveDummy(2, EAST_OF_ORIGIN, EAST)
        self.avatar_manager = AvatarManager()

    def test_successful_move_action(self):
        # Move north
        game_state = GameState(InfiniteMap(), self.avatar_manager)
        action.MoveAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        target_cell = game_state.world_map.get_cell(NORTH_OF_ORIGIN)
        assert self.avatar.location == NORTH_OF_ORIGIN
        assert self.avatar == target_cell.avatar

        assert self.avatar.events == [event.MovedEvent(ORIGIN, NORTH_OF_ORIGIN)]

        # Move east
        self.setUp()
        game_state = GameState(InfiniteMap(), self.avatar_manager)
        action.MoveAction(self.avatar, {"x": 1, "y": 0}).process(game_state.world_map)

        assert self.avatar.location == EAST_OF_ORIGIN
        assert self.avatar.events == [event.MovedEvent(ORIGIN, EAST_OF_ORIGIN)]

    def test_successful_move_east_twice_action(self):
        game_state = GameState(InfiniteMap(), self.avatar_manager)
        action.MoveAction(self.avatar, {"x": 1, "y": 0}).process(game_state.world_map)
        action.MoveAction(self.avatar, {"x": 1, "y": 0}).process(game_state.world_map)

        assert self.avatar.location == Location(2, 0)

    def test_failed_move_action(self):
        game_state = GameState(EmptyMap(), self.avatar_manager)
        action.MoveAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        assert self.avatar.location == ORIGIN
        assert self.avatar.events == [event.FailedMoveEvent(ORIGIN, NORTH_OF_ORIGIN)]

    def test_successful_attack_action(self):
        game_state = GameState(AvatarMap(self.other_avatar), self.avatar_manager)
        action.AttackAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        target_location = NORTH_OF_ORIGIN
        damage_dealt = 1

        assert self.avatar.location == ORIGIN
        assert self.other_avatar.location == EAST_OF_ORIGIN
        assert self.other_avatar.times_died == 0
        assert self.other_avatar.health == 4

        assert self.avatar.events == [
            event.PerformedAttackEvent(self.other_avatar, target_location, damage_dealt)
        ]
        assert self.other_avatar.events == [
            event.ReceivedAttackEvent(self.avatar, damage_dealt)
        ]

    def test_successful_multiple_attack_actions(self):
        game_state = GameState(AvatarMap(self.other_avatar), self.avatar_manager)
        action.AttackAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        assert self.other_avatar.events == [event.ReceivedAttackEvent(self.avatar, 1)]

        action.AttackAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        assert self.other_avatar.events == [
            event.ReceivedAttackEvent(self.avatar, 1),
            event.ReceivedAttackEvent(self.avatar, 1),
        ]

        assert self.avatar.location == ORIGIN
        assert self.other_avatar.location == EAST_OF_ORIGIN
        assert self.other_avatar.times_died == 0
        assert self.other_avatar.health == 3

    def test_failed_attack_action(self):
        game_state = GameState(InfiniteMap(), self.avatar_manager)
        action.AttackAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        target_location = NORTH_OF_ORIGIN

        assert self.avatar.location == ORIGIN
        assert self.other_avatar.location == EAST_OF_ORIGIN
        assert self.avatar.events == [event.FailedAttackEvent(target_location)]
        assert self.other_avatar.events == []

    def test_avatar_dies(self):
        self.other_avatar.health = 1
        game_state = GameState(AvatarMap(self.other_avatar), self.avatar_manager)
        action.AttackAction(self.avatar, {"x": 0, "y": 1}).process(game_state.world_map)

        target_location = NORTH_OF_ORIGIN
        damage_dealt = 1
        assert self.avatar.events == [
            event.PerformedAttackEvent(self.other_avatar, target_location, damage_dealt)
        ]
        assert self.other_avatar.events == [
            event.ReceivedAttackEvent(self.avatar, damage_dealt)
        ]

        assert self.avatar.location == ORIGIN
        assert self.other_avatar.health == 0
        assert self.other_avatar.times_died == 1
        assert self.other_avatar.location == Location(10, 10)

    def test_no_move_in_wait(self):
        game_state = GameState(InfiniteMap(), self.avatar_manager)
        action.WaitAction(self.avatar).process(game_state.world_map)
        assert self.avatar.location == ORIGIN

    def test_successful_pickup_action(self):
        game_state = GameState(PickupMap(YellowOrbArtefact), self.avatar_manager)
        game_state.world_map.setup_cell(self.avatar.location)
        artefact = game_state.world_map.get_cell(self.avatar.location).interactable

        assert artefact.in_backpack == False

        action.PickupAction(self.avatar).process(game_state.world_map)

        assert self.avatar.events == [event.PickedUpEvent({"type": "yellow_orb"})]
        assert artefact.in_backpack == True

    def test_failed_pickup_action(self):
        game_state = GameState(InfiniteMap(), self.avatar_manager)

        action.PickupAction(self.avatar).process(game_state.world_map)

        assert self.avatar.events == [event.FailedPickupEvent()]

    def test_failed_pickup_action_if_backpack_full(self):
        game_state = GameState(PickupMap(YellowOrbArtefact), self.avatar_manager)
        game_state.world_map.setup_cell(self.avatar.location)
        artefact = game_state.world_map.get_cell(self.avatar.location).interactable

        self.avatar.backpack = [
            YellowOrbArtefact for _ in range(self.avatar.BACKPACK_SIZE)
        ]

        action.PickupAction(self.avatar).process(game_state.world_map)

        assert self.avatar.events == [event.FailedPickupEvent()]
        assert artefact.in_backpack == False
