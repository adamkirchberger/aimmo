from abc import ABCMeta, abstractmethod

from .direction import Direction


class Action:
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialise(self):
        pass


class WaitAction(Action):
    def serialise(self):
        return {"action_type": "wait"}


class PickupAction(Action):
    def serialise(self):
        return {"action_type": "pickup"}


class MoveAction(Action):
    def __init__(self, direction):
        self.direction = direction

    def serialise(self):
        return {
            "action_type": "move",
            "options": {"direction": self.direction.serialise()},
        }


class MoveTowardsAction(Action):
    def __init__(self, artefact):
        self.direction = None

        if not artefact:
            print("MoveTowardsAction got an invalid parameter. Is it empty?")
            return

        if len(artefact.path) < 2:
            return  # not a valid path

        # the first cell in the path is the starting cell
        avatar_location = artefact.path[0].location
        next_location = artefact.path[1].location

        # calculate direction
        x = next_location.x - avatar_location.x
        y = next_location.y - avatar_location.y
        self.direction = Direction(x, y)

    def serialise(self):
        if not self.direction:
            return {}
        return {
            "action_type": "move",
            "options": {"direction": self.direction.serialise()},
        }


class AttackAction(Action):
    def __init__(self, direction):
        self.direction = direction

    def serialise(self):
        return {
            "action_type": "attack",
            "options": {"direction": self.direction.serialise()},
        }
