# Enclose Engine

Enclose Engine is a grid-based puzzle game engine and solver designed for [enclose.horse](https://enclose.horse). The objective is to place a limited number of walls to enclose a horse and various high-value items within a bounded area, maximizing the total score while preventing the horse from "escaping" to the edge of the board.

## Features

- **Core Game Engine:** Implements the logic for tile types, grid management, and enclosure detection.
- **Reachability Analysis:** Efficiently determines which tiles are enclosed by the horse's position.
- **ILP-Based Solver:** Uses Integer Linear Programming (via `PuLP` and `CBC`) to find mathematically optimal wall placements.
- **Interactive CLI:** Play levels manually or trigger the auto-solver from the terminal.
- **Level System:** Load levels from `.game` files, including support for portals, water hazards, and various scoring items.

## Tile Types & Scoring

| Tile Type | Character | Score | Description |
|-----------|-----------|-------|-------------|
| Grass | ` ` | 1 | Standard traversable ground. |
| Horse | `H` | 1 | The starting point for enclosure. |
| Cherry | `C` | 4 | A bonus item. |
| Golden Apple | `G` | 11 | A high-value bonus item. |
| Bee Swarm | `S` | -4 | A penalty item to be avoided. |
| Portal | `a-z, 0-9`| 1 | Links matching characters together. |
| Water | `~` | 0 | Impassable terrain (cannot place walls here). |
| Wall | `#` | 0 | Impassable terrain placed by the player. |

## Installation

### Prerequisites
- Python 3.14+ (makes use of multithreading)
- [PuLP](https://coin-or.github.io/pulp/) (ILP modeling library)
- [CBC Solver](Standard with many PuLP installations)
- `requests` (for scraping scripts)
- `uv` (optional, but ideal)

### Setup
Clone the repository and install:

```bash
uv pip install -e .
```

## Usage

### Command Line Interface
You can run the engine using the provided CLI via `uv run`:

```bash
# Run the auto-solver on a specific map
python -m enclose_engine.cli --map maps/daily/2026-03-13_9_73.game --auto-solve
```

### Scraping Levels
The project includes standalone scripts to fetch puzzles from [enclose.horse](https://enclose.horse). They use only standard Python libraries.

```bash
# Scrape all daily levels from Dec 30, 2025 to today
python ./preprocess/scrape_dailies.py

# Scrape a specific level by its ID or URL
python ./preprocess/scrape_one.py f3-ms3 maps/custom
```

Levels are saved in `.game` format, with filenames containing the level metadata (ID/Date, budget, and optimal score).

## Project Structure

- `enclose_engine/`: Core package containing engine logic and solvers.
  - `engine.py`: Board and Tile logic.
  - `solver.py`: ILP solver implementation.
  - `cli.py`: Command-line interface.
- `maps/`: Collection of daily and sample custom puzzles in `.game` format.
- `examples/`: Example scripts showing how to use the engine programmatically.
- `preprocess/`: Tools for fetching and processing new maps.

## Report

The technical report detailing the design decisions, algorithms, and performance analysis of the solver can be found in `report/experiments.pdf`. 

## Acknowledgements

This project was developed as part of the CSE 202 course at UC San Diego. The solver's design was implemented up to March 11, 2026. 