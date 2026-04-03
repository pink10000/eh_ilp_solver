import pulp as pl
import os
from .engine import Board, TileType

class EncloseSolverAlt4:
    """
    Optimized ILP Solver.
    - Fixed portal adjacency (deduplicated links).
    - Reduced variable count (sparsity filtering for water/horse).
    - Strengthened constraints (W + R + E <= 1).
    - Proper reachability propagation for negative tiles (Bees).
    """
    def __init__(self, board: Board, wall_budget: int = 10, time_limit: int = None, threads: int = None):
        self.board = board
        self.k = wall_budget
        self.model = pl.LpProblem("Enclose_Horse_Optimized", pl.LpMaximize)
        self.time_limit = time_limit
        self.threads = threads

        self.hx, self.hy = self.board.horse_pos
        
        # SPARSITY FILTERING: Only create variables for tiles that aren't water or the horse
        self.tiles = [(i, j) for i in range(board.width) for j in range(board.height) 
                      if self.board.get_tile(i, j) != TileType.WATER and (i, j) != (self.hx, self.hy)]
        
        self.W = {pos: pl.LpVariable(f"W_{pos[0]}_{pos[1]}", 0, 1, cat="Binary") for pos in self.tiles}
        self.E = {pos: pl.LpVariable(f"E_{pos[0]}_{pos[1]}", 0, 1, cat="Binary") for pos in self.tiles}
        self.R = {pos: pl.LpVariable(f"R_{pos[0]}_{pos[1]}", 0, 1, cat="Binary") for pos in self.tiles}

    def _get_W(self, i, j): 
        return self.W.get((i, j), 0)

    def _get_E(self, i, j): 
        if (i, j) == (self.hx, self.hy): 
            return 0
        return self.E.get((i, j), 0)

    def _get_R(self, i, j): 
        if (i, j) == (self.hx, self.hy): 
            return 1
        return self.R.get((i, j), 0)

    def F(self, i: int, j: int) -> int:
        tile = self.board.get_tile(i, j)
        mapping = {
            TileType.WATER: 0, TileType.GOLDEN_APPLE: 11, TileType.CHERRY: 4,
            TileType.BEE_SWARM: -4, TileType.PORTAL: 1, TileType.HORSE: 1, TileType.GRASS: 1
        }
        return mapping.get(tile, 0)

    def solve(self):
        M = self.board.width * self.board.height
        f = {} 

        # 1. Wall constraints: placement and budget
        self.model += pl.lpSum(self.W.values()) <= self.k
        for pos, var in self.W.items():
            if self.board.get_tile(*pos) != TileType.GRASS:
                self.model += var == 0

        # B. MUTUAL EXCLUSION (Optimized SOS)
        # A tile is either a Wall, Reachable, Escapable, or None (if blocked off elsewhere)
        # i.e. explored, frontier, unexplored, or blocked in a separate component
        for pos in self.tiles:
            self.model += self.W[pos] + self.E[pos] + self.R[pos] <= 1

        # C. ESCAPABILITY & REACHABILITY PROPAGATION
        for j in range(self.board.height):
            for i in range(self.board.width):
                tile = self.board.get_tile(i, j)
                if tile == TileType.WATER: 
                    continue
                
                # Boundary Escapability: A non-wall tile on the boundary is escapable unless it's the horse's starting position
                if i == 0 or i == self.board.width - 1 or j == 0 or j == self.board.height - 1:
                    if (i, j) != (self.hx, self.hy):
                        self.model += self.E[(i, j)] >= 1 - self.W[(i, j)]
                
                # Portal Logic:
                if tile == TileType.PORTAL:
                    p_id = self.board.portal_tiles.get((i, j))
                    # If a non-horse tile is a portal and its pair is on the boundary, it is escapable
                    if self._is_portal_pair_on_boundary(p_id) and (i, j) != (self.hx, self.hy):
                        self.model += self.E[(i, j)] == 1
                    
                    # Connection Logic
                    for ni, nj in self._unique_links(i, j):
                        # A portal tile is escapable if any of its linked neighbors are escapable, a portal tile cannot be a wall
                        if (i, j) in self.E:
                            self.model += self.E[(i, j)] >= self._get_E(ni, nj)
                        # A neighbor tile is reachable if the portal tile is reachable and the neighbor itself is not a wall
                        if (ni, nj) in self.R:
                            self.model += self.R[(ni, nj)] >= self._get_R(i, j) - self._get_W(ni, nj)
                else:
                    # Standard Adjacency
                    for ni, nj in self._adj(i, j):
                        # A tile is escapable if any of its neighbors are escapable and it itself is not a wall
                        if (i, j) in self.E:
                            self.model += self.E[(i, j)] >= self._get_E(ni, nj) - self._get_W(i, j)
                        # A neighbor tile is reachable if the current tile is reachable and the neighbor itself is not a wall
                        if (ni, nj) in self.R:
                            self.model += self.R[(ni, nj)] >= self._get_R(i, j) - self._get_W(ni, nj)

        # D. FLOW CONSERVATION (Connectivity)
        for j in range(self.board.height):
            for i in range(self.board.width):
                # Water tiles have no flow variables, are not reachable, or escapable. 
                if self.board.get_tile(i, j) == TileType.WATER: 
                    continue
                
                links = self._unique_links(i, j)
                for ni, nj in links:
                    # Flow variable from (i, j) to (ni, nj) is bounded above by max flow
                    f_var = pl.LpVariable(f"f_{i}_{j}_{ni}_{nj}", 0, M)
                    f[(i, j, ni, nj)] = f_var
                    # Optimized bounds: Flow only exists between reachable tiles
                    self.model += f_var <= M * self._get_R(i, j)
                    self.model += f_var <= M * self._get_R(ni, nj)

        r_sum_others = pl.lpSum(self.R.values())
        for j in range(self.board.height):
            for i in range(self.board.width):
                if self.board.get_tile(i, j) == TileType.WATER: 
                    continue
                
                # Get flow in and flow out for the tile
                links = self._unique_links(i, j)
                f_out = [f[(i, j, ni, nj)] for ni, nj in links]
                f_in = [f[(ni, nj, i, j)] for ni, nj in links if (ni, nj, i, j) in f]
                
                if (i, j) == (self.hx, self.hy):
                    # if the tile is the horse, total flow out must equal total reachable tiles (since horse is the source)
                    self.model += pl.lpSum(f_out) - pl.lpSum(f_in) == r_sum_others
                else:
                    # if the tile is not the horse, the tile must consume 1 unit of flow to be reachable (R=1) or consume 0 if not reachable (R=0)
                    self.model += pl.lpSum(f_in) - pl.lpSum(f_out) == self.R[(i, j)]

        # E. OBJECTIVE
        obj = pl.lpSum([self._get_R(i, j) * self.F(i, j) 
                        for i in range(self.board.width) for j in range(self.board.height)])
        self.model.setObjective(obj)
        
        threads_count = self.threads if self.threads else os.cpu_count()
        self.model.solve(pl.PULP_CBC_CMD(msg=0, threads=threads_count, gapRel=0, timeLimit=self.time_limit))
        
        status = pl.LpStatus[self.model.status]
        if status in ['Optimal', 'Feasible']:
            return [pos for pos, var in self.W.items() if pl.value(var) > 0.5]
        return None

    # Standard neighbor logic for normal tiles, exclude water for flow/propagation
    def _adj(self, i, j):
        res = []
        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.board.width and 0 <= nj < self.board.height:
                # Only consider non-water neighbors for flow/propagation
                if self.board.get_tile(ni, nj) != TileType.WATER:
                    res.append((ni, nj))
        return res

    # Unique neighbor logic that includes portals but deduplicates to prevent variable name collisions
    def _unique_links(self, i, j):
        links = self._adj(i, j)
        tile = self.board.get_tile(i, j)
        if tile == TileType.PORTAL:
            p_id = self.board.portal_tiles.get((i, j))
            if p_id in self.board.portals:
                for pi, pj in self.board.portals[p_id]:
                    # If portals are next to each other, they are already added in the direct neighbor list, so we deduplicate
                    if (pi, pj) != (i, j) and self.board.get_tile(pi, pj) != TileType.WATER:
                        links.append((pi, pj))
        return sorted(list(set(links)))

    # Get all neighbors of both portals in a pair for escapability logic
    def _get_portal_pair_neighbors(self, portal_id):
        all_neighbors = []
        if portal_id in self.board.portals:
            for pi, pj in self.board.portals[portal_id]:
                all_neighbors.extend(self._adj(pi, pj))
        return list(set(all_neighbors))

    # Check if any portal in the pair is on the boundary, which would make them escapable regardless of walls
    def _is_portal_pair_on_boundary(self, portal_id):
        if portal_id not in self.board.portals: 
            return False
        for i, j in self.board.portals[portal_id]:
            if i == 0 or i == self.board.width - 1 or j == 0 or j == self.board.height - 1: 
                return True
        return False