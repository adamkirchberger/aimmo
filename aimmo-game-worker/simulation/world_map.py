from collections import defaultdict, namedtuple
from enum import Enum

from .avatar_state import create_avatar_state
from .location import Location
from typing import Dict, List
from .pathfinding import astar

# how many nearby artefacts to return
SCAN_LIMIT = 3
SCAN_RADIUS = 12
ARTEFACT_TYPES = ["chest", "key", "yellow_orb"]
PICKUP_TYPES = ["damage_boost", "invulnerability", "health"] + ARTEFACT_TYPES


class ArtefactType(Enum):
    CHEST = "chest"
    KEY = "key"
    YELLOW_ORB = "yellow_orb"

    def __eq__(self, other):
        return self.value == other

    def __str__(self):
        return self.value


Artefact = namedtuple("Artefact", ["type", "location", "path"])


class Cell(object):

    """
    Any position on the world grid.
    """

    def __init__(self, location, avatar=None, **kwargs):
        self.location = Location(**location)
        self.avatar = None
        self.interactable = None
        self.obstacle = None
        if avatar:
            self.avatar = create_avatar_state(avatar)
        for (key, value) in kwargs.items():
            if not key == "habitable":
                setattr(self, key, value)

    @property
    def habitable(self):
        return not (self.avatar or self.obstacle)

    def has_artefact(self):
        return (
            self.interactable is not None
            and self.interactable["type"] in ARTEFACT_TYPES
        )

    def __repr__(self):
        return "Cell({} a={} i={})".format(
            self.location, self.avatar, self.interactable
        )

    def __eq__(self, other):
        return self.location == other.location

    def __ne__(self, other):
        return not self == other


class WorldMapCreator:
    def generate_world_map_from_cells_data(cells: List[Cell]) -> "WorldMap":
        world_map_cells: Dict[Location, Cell] = {}
        for cell_data in cells:
            cell = Cell(**cell_data)
            world_map_cells[cell.location] = cell
        return WorldMap(world_map_cells)

    def generate_world_map_from_game_state(game_state) -> "WorldMap":
        cells: Dict[Location, Cell] = {}
        for x in range(
            game_state["southWestCorner"]["x"], game_state["northEastCorner"]["x"] + 1
        ):
            for y in range(
                game_state["southWestCorner"]["y"],
                game_state["northEastCorner"]["y"] + 1,
            ):
                cell = Cell({"x": x, "y": y})
                cells[Location(x, y)] = cell

        for interactable in game_state["interactables"]:
            location = Location(
                interactable["location"]["x"], interactable["location"]["y"]
            )
            cells[location].interactable = interactable

        for obstacle in game_state["obstacles"]:
            location = Location(obstacle["location"]["x"], obstacle["location"]["y"])
            cells[location].obstacle = obstacle

        for player in game_state["players"]:
            location = Location(player["location"]["x"], player["location"]["y"])
            cells[location].player = create_avatar_state(player)

        return WorldMap(cells)


class WorldMap(object):

    """
    The non-player world state.
    """

    artefact_types = ArtefactType

    def __init__(self, cells: Dict[Location, Cell]):
        self.cells = cells

    def all_cells(self):
        return self.cells.values()

    def interactable_cells(self):
        return [cell for cell in self.all_cells() if cell.interactable]

    def pickup_cells(self):
        return [
            cell
            for cell in self.interactable_cells()
            if cell.interactable["type"] in PICKUP_TYPES
        ]

    def score_cells(self):
        return [
            cell
            for cell in self.interactable_cells()
            if "score" == cell.interactable["type"]
        ]

    def partially_fogged_cells(self):
        return [cell for cell in self.all_cells() if cell.partially_fogged]

    def is_visible(self, location):
        return location in self.cells

    def get_cell(self, location):
        cell = self.cells[location]
        assert (
            cell.location == location
        ), "location lookup mismatch: arg={}, found={}".format(location, cell.location)
        return cell

    def can_move_to(self, target_location):
        try:
            cell = self.get_cell(target_location)
        except KeyError:
            return False
        return getattr(cell, "habitable", False) and not getattr(cell, "avatar", False)

    def _scan_artefacts(self, start_location, radius):
        # get artefacts from starting location within the radius
        artefacts = []
        for x in range(start_location.x - radius, start_location.x + radius + 1):
            for y in range(start_location.y - radius, start_location.y + radius + 1):
                try:
                    cell = self.get_cell(Location(x, y))
                except KeyError:
                    continue
                if cell.has_artefact():
                    artefacts.append(cell)
        return artefacts

    def scan_nearby(self, avatar_location, radius=SCAN_RADIUS) -> List[dict]:
        """
        From the given location point search the given radius for artefacts.
        Returns list of nearest artefacts (artefact/interactable represented as dict).
        """
        artefact_cells = self._scan_artefacts(avatar_location, radius)

        # get the best path to each artefact
        nearby = defaultdict(list)
        for art_cell in artefact_cells:
            path = astar(self, self.cells.get(avatar_location), art_cell)
            # only add to the list when there's a path
            if path:
                nearby[len(path)].append((art_cell, path))

        # sort them by distance (the length of path) and take the nearest first
        nearest = []
        for distance in sorted(nearby.keys()):
            for art_cell, path in nearby[distance]:
                # use namedtuple so fields accessible by attribute lookup
                artefact = Artefact(
                    type=art_cell.interactable["type"],
                    location=art_cell.location,
                    path=path,
                )
                nearest.append(artefact)
            if len(nearest) > SCAN_LIMIT:
                break

        return nearest[:SCAN_LIMIT]

    def __repr__(self):
        return repr(self.cells)
