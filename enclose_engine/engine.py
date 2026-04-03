from enum import Enum
from typing import List, Tuple, Set, Dict

class TileType(Enum):
    GRASS = 0
    WALL = 1
    WATER = 2
    HORSE = 3
    CHERRY = 4 # +4 total
    GOLDEN_APPLE = 5 # +11
    BEE_SWARM = 6 # -4
    PORTAL = 7

    @property
    def score(self) -> int:
        return {
            TileType.GRASS: 1,
            TileType.HORSE: 1,
            TileType.CHERRY: 4,
            TileType.GOLDEN_APPLE: 11,
            TileType.BEE_SWARM: -4,
            TileType.PORTAL: 1,
            TileType.WATER: 0,
            TileType.WALL: 0
        }.get(self, 0)

    @property
    def char(self) -> str:
        return {
            TileType.GRASS: ' ',
            TileType.WALL: '#',
            TileType.WATER: 'W',
            TileType.HORSE: 'h',
            TileType.CHERRY: 'c',
            TileType.GOLDEN_APPLE: 'A',
            TileType.BEE_SWARM: 'b',
            TileType.PORTAL: 'O'
        }.get(self, '?')

class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[TileType.GRASS for _ in range(width)] for _ in range(height)]
        self.horse_pos = (0, 0)
        self.portals: Dict[str, List[Tuple[int, int]]] = {}
        self.portal_tiles: Dict[Tuple[int, int], str] = {}

    @classmethod
    def load(cls, file_path: str) -> "Board":
        if file_path.endswith('.game'):
            return cls.load_from_game(file_path)
        else:
            raise ValueError("Unsupported file format. Must be .game")

    @classmethod
    def load_from_game(cls, file_path: str) -> "Board":
        with open(file_path, 'r') as f:
            lines = [line.rstrip('\r\n') for line in f if line.strip('\r\n')]
        
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0
        board = cls(width, height)
        
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == '~':
                    board.set_tile(x, y, TileType.WATER)
                elif char == 'C':
                    board.set_tile(x, y, TileType.CHERRY)
                elif char == 'H':
                    board.set_tile(x, y, TileType.HORSE)
                elif char == 'S':
                    board.set_tile(x, y, TileType.BEE_SWARM)
                elif char == 'G':
                    board.set_tile(x, y, TileType.GOLDEN_APPLE)
                elif char.isalnum() and (char.islower() or char.isdigit()):
                    board.set_tile(x, y, TileType.PORTAL, portal_id=f"P{char}")
                elif char == '#':
                    board.set_tile(x, y, TileType.WALL)
                # Spaces or '.' are Grass (already default)
        return board

    def set_tile(self, x: int, y: int, tile_type: TileType, portal_id: str = None):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile_type
            if tile_type == TileType.HORSE:
                self.horse_pos = (x, y)
            elif tile_type == TileType.PORTAL and portal_id is not None:
                if portal_id not in self.portals:
                    self.portals[portal_id] = []
                self.portals[portal_id].append((x, y))
                self.portal_tiles[(x, y)] = portal_id

    def count_walls(self) -> int:
        return sum(row.count(TileType.WALL) for row in self.grid)

    def place_walls(self, walls: List[Tuple[int, int]], budget: int = None) -> bool:
        """
        Attempts to place walls. If budget is provided, enforces it.
        """
        if budget is not None and len(walls) > budget:
            return False
        for x, y in walls:
            self.set_tile(x, y, TileType.WALL)
        return True

    def get_tile(self, x: int, y: int) -> TileType:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return TileType.WALL

    def calculate_enclosure(self) -> Tuple[Set[Tuple[int, int]], int]:
        """
        Calculates the enclosed area starting from the horse's position.
        If the horse can reach the boundary, it's not enclosed (score 0).
        """
        visited = set()
        stack = [self.horse_pos]
        enclosed_tiles = set()
        is_enclosed = True
        
        score = 0
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            
            visited.add((x, y))
            
            if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                is_enclosed = False
            
            tile = self.get_tile(x, y)
            if tile != TileType.WALL and tile != TileType.WATER:
                enclosed_tiles.add((x, y))
                score += tile.score
                
                if tile == TileType.PORTAL:
                    portal_id = self.portal_tiles.get((x, y))
                    if portal_id:
                        for px, py in self.portals.get(portal_id, []):
                            if (px, py) not in visited:
                                stack.append((px, py))

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        ntile = self.get_tile(nx, ny)
                        if ntile != TileType.WALL and ntile != TileType.WATER and (nx, ny) not in visited:
                            stack.append((nx, ny))
            
        if not is_enclosed:
            return set(), 0
        
        return enclosed_tiles, score

if __name__ == "__main__":
    board = Board(10, 10)
    board.set_tile(5, 5, TileType.HORSE)
    for i in range(3, 8):
        board.set_tile(i, 3, TileType.WALL)
        board.set_tile(i, 7, TileType.WALL)
        board.set_tile(3, i, TileType.WALL)
        board.set_tile(7, i, TileType.WALL)
    board.set_tile(4, 4, TileType.CHERRY)
    enclosed, score = board.calculate_enclosure()
    print(f"Enclosed tiles: {len(enclosed)}")
    print(f"Score: {score}")
