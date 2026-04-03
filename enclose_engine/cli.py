import argparse
import sys
import os
import re
import time
import threading
from .engine import Board, TileType
from .solver import EncloseSolverAlt4

def print_board(board: Board):
    header = "   " + "".join([str(x % 10) for x in range(board.width)])
    print(header)
    print("  +" + "-" * board.width + "+")

    for y in range(board.height):
        row = f"{y:2}|"
        for x in range(board.width):
            tile = board.get_tile(x, y)
            if tile == TileType.PORTAL:
                portal_id = board.portal_tiles.get((x, y))
                if portal_id:
                    row += portal_id[-1] if len(portal_id) > 1 else 'O'
                else:
                    row += 'O'
            else:
                row += tile.char
        row += "|"
        print(row)
    print("  +" + "-" * board.width + "+")

def print_value_table(board: Board, enclosed: set):
    header = "   " + "".join([str(x % 10) for x in range(board.width)])
    print(header)
    print("  +" + "-" * board.width + "+")

    for y in range(board.height):
        row = f"{y:2}|"
        for x in range(board.width):
            if (x, y) in enclosed:
                tile = board.get_tile(x, y)
                val = tile.score
                if tile == TileType.GOLDEN_APPLE:
                    row += "A" 
                elif tile == TileType.BEE_SWARM:
                    row += "b"
                else:
                    row += str(val)
            else:
                row += " "
        row += "|"
        print(row)
    print("  +" + "-" * board.width + "+")
    print(f"(A={TileType.GOLDEN_APPLE.score}, b={TileType.BEE_SWARM.score})")

def display_solve_results(board: Board, walls: list, budget: int, optimal: int = None):
    """The 'Art' of the CLI: Detailed visual reporting of the solution."""
    for x, y in walls:
        board.set_tile(x, y, TileType.WALL)
    
    enclosed, score = board.calculate_enclosure()
    print("\nFinal Board View:")
    print_board(board)
    print("\nEnclosed Values Table:")
    print_value_table(board, enclosed)
    print(f"\nTotal Enclosed Tiles: {len(enclosed)}")
    print(f"ILP Score: {score}")
    print(f"Max Online Score: {optimal if optimal is not None else 'N/A'}")

def get_solver(board: Board, budget: int, time_limit: int = None, threads: int = None):
    """Centralized factory for solver instantiation."""
    return EncloseSolverAlt4(board, wall_budget=budget, time_limit=time_limit, threads=threads)

def timer_thread_func(stop_event, start_time, game_id=None, count=None, limit=None, optimal_score=None):
    """Generalized live display for the solver."""
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        parts = []
        if count and limit: parts.append(f"Solving game {count}/{limit}")
        if game_id: parts.append(f"ID {game_id}")
        parts.append(f"Elapsed: {elapsed:.1f}s")
        if optimal_score is not None: parts.append(f"Optimal: {optimal_score}")
        
        sys.stdout.write(f"\r{' | '.join(parts)} | ")
        sys.stdout.flush()
        time.sleep(0.1)

def solve_with_timer(solver, game_id=None, count=None, limit=None, optimal_score=None):
    """Executes a solver with a live-updating thread."""
    stop_event = threading.Event()
    start_time = time.time()
    t = threading.Thread(target=timer_thread_func, args=(stop_event, start_time, game_id, count, limit, optimal_score))
    t.start()
    
    try:
        walls = solver.solve()
    finally:
        stop_event.set()
        t.join()
        
    time_taken = time.time() - start_time
    return walls, time_taken

def auto_solve(board: Board, game_id: str, budget: int, silent: bool, optimal: int = None, time_limit: int = None):
    """Simplified entry point using shared logic."""
    print(f"Solving using ILP solver with (Budget: {budget})...")
    solver = get_solver(board, budget, time_limit=time_limit)
    
    walls, time_taken = solve_with_timer(solver, game_id=game_id, optimal_score=optimal)
    print(f"\rTime taken: {time_taken:.2f} seconds\033[K")
    
    if walls:
        print(f"ILP solution found with {len(walls)} walls.")
        if not silent:
            display_solve_results(board, walls, budget, optimal)
    else:
        print("No solution found to enclose the horse.")

def main():
    parser = argparse.ArgumentParser(description="Enclose.horse Engine")
    parser.add_argument("--width", type=int, default=10, help="Width of an empty board")
    parser.add_argument("--height", type=int, default=10, help="Height of an empty board")
    parser.add_argument("--map", type=str, help="Path to a .game map file")
    parser.add_argument("--auto-solve", action="store_true", help="Automatically solve the map")
    parser.add_argument("-l", "--limit", type=int, help="Time limit in seconds per puzzle")
    parser.add_argument("-b", "--budget", type=int, help="Wall budget (overrides automatic detection)")
    parser.add_argument("-s", "--silent", action="store_true", help="Does not print the board")
    args = parser.parse_args()

    if args.map:
        try:
            board = Board.load(args.map)
        except Exception as e:
            print(f"Failed to load map: {e}")
            sys.exit(1)
    else:
        board = Board(args.width, args.height)
        board.set_tile(args.width // 2, args.height // 2, TileType.HORSE)

    optimal = None
    budget = 10
    board_name = "Board"

    if args.map:
        # Extract metadata from filename if possible
        pattern = re.compile(r"(.+)_(\d+)_(-?\d+)\.game")
        filename = os.path.basename(args.map)
        match = pattern.match(filename)
        if match:
            board_name = match.group(1)
            budget = int(match.group(2))
            optimal = int(match.group(3))
        else:
            board_name = filename.split('.')[0]

    # Argument budget overrides everything
    if args.budget:
        budget = args.budget
        
    if args.auto_solve:
        auto_solve(board, board_name, budget, args.silent, optimal, time_limit=args.limit)
        return

    print(f"Welcome to Enclose.horse Engine! (Wall Budget: {budget})")
    print("Commands: x,y wall | x,y cherry | x,y bee | x,y horse | x,y grass | solve | auto-solve | exit")
    
    while True:
        print_board(board)
        cmd = input("> ").strip().lower()
        if cmd == "exit":
            break
        elif cmd == "solve":
            enclosed, score = board.calculate_enclosure()
            if enclosed:
                print(f"Horse is enclosed in {len(enclosed)} tiles.")
                print(f"ILP Score: {score}")
            else:
                print("Horse is NOT enclosed!")
        elif cmd == "auto-solve":
            auto_solve(board, board_name, budget, args.silent, optimal, time_limit=args.limit)
        else:
            try:
                parts = cmd.split()
                if len(parts) == 1 and ',' in parts[0]:
                    x, y = map(int, parts[0].split(','))
                    if board.count_walls() < budget:
                        board.set_tile(x, y, TileType.WALL)
                    else:
                        print(f"Wall budget exceeded! Max {budget} walls.")
                elif len(parts) == 2:
                    coords, type_str = parts
                    x, y = map(int, coords.split(','))
                    type_map = {
                        "wall": TileType.WALL, "cherry": TileType.CHERRY,
                        "apple": TileType.GOLDEN_APPLE, "bee": TileType.BEE_SWARM,
                        "horse": TileType.HORSE, "grass": TileType.GRASS
                    }
                    if type_str in type_map:
                        if type_str == "wall" and board.count_walls() >= budget:
                            print(f"Wall budget exceeded! Max {budget} walls.")
                        else:
                            board.set_tile(x, y, type_map[type_str])
                    else:
                        print(f"Unknown type: {type_str}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
