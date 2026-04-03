from enclose_engine.engine import Board, TileType
from enclose_engine.cli import print_board

def create_puzzle_board():
    # 16x16 grid as seen in the image
    board = Board(16, 16)
    
    # 1. Set Water (Rough mapping from the image)
    water_coords = [
        # Top-left L-shape
        (0,0), (1,0), (2,0), (0,1), (1,1), (2,1), (0,2), (0,3), (1,3), (0,4), (1,4), (2,4),
        # Top middle inverted U
        (5,0), (6,0), (7,0), (8,0), (5,1), (8,1), (5,2), (8,2), (5,3), (8,3), (5,4), (8,4),
        # Top right cluster
        (11,0), (11,1), (14,1), (15,1), (11,2), (14,2), (15,2), (11,3), (12,3), (15,3), (13,4), (14,4), (15,4),
        # Middle left T-shape
        (0,7), (0,8), (1,8), (2,8), (0,9), (1,9), (2,9), (0,10), (0,11), (1,11), (2,11),
        # Middle C-shape (enclosing bees)
        (4,6), (5,6), (6,6), (4,7), (4,8), (4,9), (5,9), (6,9),
        # Middle right cluster
        (8,7), (9,7), (10,7), (11,7), (12,7), (11,8), (11,9), (10,10), (11,10),
        # Right T-shape
        (13,8), (14,8), (15,8), (14,9), (14,10), (13,11), (14,11), (15,11),
        # Bottom left
        (0,13), (1,13), (2,13), (1,14), (1,15), (0,15),
        # Bottom middle large complex
        (5,10), (6,10), (7,10), (8,10), (5,11), (5,12), (4,13), (5,13), (6,13), (9,13), (10,13), 
        (4,14), (5,14), (6,14), (7,14), (8,14), (9,14), (10,14), (7,15), (8,15),
        # Bottom right
        (11,14), (12,14), (13,14), (14,14), (11,15), (12,15), (13,15), (14,15)
    ]
    for x, y in water_coords:
        board.set_tile(x, y, TileType.WATER)
        
    # 2. Set Bees (Bee Swarms are -4 points)
    bee_clusters = [
        (6, 2), (6, 3), (6, 4), (7, 2), (7, 3), (7, 4), # Cluster 1
        (11, 2), (11, 3), (12, 2),                      # Cluster 2
        (1, 8), (1, 9), (2, 8), (2, 9),                 # Cluster 3
        (5, 7), (5, 8), (6, 7), (6, 8),                 # Cluster 4
        (9, 8), (9, 9), (9, 10), (10, 8), (10, 9),      # Cluster 5
        (14, 9), (14, 10), (15, 9), (15, 10),           # Cluster 6
        (7, 12), (7, 13), (8, 12), (8, 13)              # Cluster 7
    ]
    for x, y in bee_clusters:
        board.set_tile(x, y, TileType.BEE_SWARM)
        
    # 3. Set Horse
    board.set_tile(7, 5, TileType.HORSE)
    
    return board

def solve_with_walls(walls):
    if len(walls) > 10:
        print("Error: Too many walls! Maximum 10 allowed.")
        return
    
    board = create_puzzle_board()
    print("Initial Board:")
    print_board(board)
    
    for x, y in walls:
        board.set_tile(x, y, TileType.WALL)
    
    print("\nBoard with Walls:")
    print_board(board)
    
    enclosed, score = board.calculate_enclosure()
    print(f"Results for walls {walls}:")
    if not enclosed:
        print("Horse is NOT enclosed!")
    else:
        print(f"Horse is enclosed in {len(enclosed)} tiles.")
        print(f"Total Score: {score}")
    return score

if __name__ == "__main__":
    # Example: Attempting to enclose with 10 walls
    # This is just a placeholder set of walls to demonstrate the limit.
    my_walls = [
        (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), 
        (9, 9), (10, 10), (4, 5), (4, 6), (4, 7)
    ]
    solve_with_walls(my_walls)
