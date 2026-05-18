# BeastGame 🎮

A Python-based game simulation where AI-controlled beasts navigate a dynamic environment, manage resources, and compete for survival.

## Overview

BeastGame is a strategic game where beasts must:
- Navigate a wrapping game map with intelligent movement algorithms
- Manage energy resources efficiently
- Hunt smaller enemies for survival
- Flee from larger threats
- Collect food to sustain themselves
- Reproduce by splitting when conditions are favorable

## Features

### Core Mechanics
- **Beast Management**: Create, track, and manage multiple beasts with unique behaviors and energy levels
- **Intelligent Movement**: Priority-based decision making system that evaluates threats and opportunities
- **Energy System**: Realistic energy costs based on Euclidean distance calculations
- **Environment Awareness**: Beasts maintain a 7x7 perception grid showing nearby entities
- **Dynamic Splitting**: Beasts reproduce when they accumulate sufficient energy
- **Spatial Wrapping**: Game map wraps around at boundaries, enabling continuous exploration

### AI Decision Making
The `Beast` class implements a sophisticated decision-making hierarchy:
1. **Threat Assessment**: Detect and prioritize fleeing from larger enemies
2. **Hunting**: Identify and pursue smaller beasts for consumption
3. **Resource Gathering**: Seek and collect food when safe
4. **Exploration**: Random movement when no immediate priorities exist

### Entity Types
- **Beasts**: Controllable entities with energy, position, and movement capability
  - Represented by symbols: `>` (larger), `<` (smaller), `=` (same size)
- **Food**: Static resources represented by `*`
- **Empty Cells**: Safe terrain represented by `.`

## Project Structure

```
BeastGame/
├── README.md           # This file
└── beast.py           # Core game logic and Beast class
```

## Installation

### Requirements
- Python 3.7+
- No external dependencies (uses only standard library: `math`, `random`, `sys`)

### Setup
```bash
git clone https://github.com/JEOfficial/BeastGame.git
cd BeastGame
```

## Usage

### Basic Beast Creation
```python
from beast_game.beast import Beast

# Create a new beast with ID 1, energy 1000, and environment string
environment = "." * 49  # 7x7 grid of empty cells
beast = Beast(beast_id=1, energy=1000, environment=environment)
```

### Decision Making
```python
# Get the next move command
command = beast.decide_movement()
# Returns: "1 MOVE 1 -1" or "1 SPLIT 0 1" depending on situation
```

### Game State Management
```python
# Update the current game turn
Beast.update_current_turn()

# Remove a beast from the game
Beast.remove_beast(beast_id=1)
```

## API Reference

### Beast Class Methods

#### Movement & Action
- `decide_movement()`: Determines the next movement or split action based on current game state
- `move_and_update(move_x, move_y)`: Executes movement and updates all related state
- `find_safe_moves(...)`: Complex priority-based move selection considering all entities

#### Environment Interaction
- `update_environment()`: Updates global game map based on beast's local perception
- `find_entity_positions(symbols)`: Locates specific entity types in visible area
- `string_to_grid(environment)`: Converts environment string to 2D grid format

#### Game State
- `remove_beast(beast_id)`: Class method to remove beast from game
- `update_current_turn()`: Class method to advance turn and clean old map data
- `print_game_map()`: Class method to display current game state

#### Energy & Cost Calculation
- `calculate_energy_cost(current_position, target_position)`: Euclidean distance-based cost
- `calculate_energy_cost_relative(dx, dy)`: Relative movement cost
- `calculate_movement(target_position)`: Constrain movement to ±2 steps

#### Safety & Detection
- `is_safe_position(position, big_enemy_positions)`: Check if position is outside threat range
- `is_within_attack_range(entity_position, radius)`: Verify if entity is attackable
- `find_closest_entity(entity_positions, current_position)`: Locate nearest target

### Utility Functions
- `wrap_coordinates(x, y)`: Applies modulo wrapping for map boundaries
- `print_and_flush(message)`: Prints and flushes output stream for logging

## Game Constants

From `beast_game.constants`:
- `MAP_WIDTH`: Game map width in cells
- `MAP_HEIGHT`: Game map height in cells
- `CELL_DURATION`: Turns before cell information expires (memory decay)
- `cmd.MOVE`: Movement command constant
- `cmd.SPLIT`: Reproduction command constant

## Strategy & AI Logic

### Priority System (When No Large Enemies Nearby)
1. Attack small beasts in adjacent positions (if main beast or after cooldown)
2. Chase small beasts outside attack range (main beast only)
3. Collect food in adjacent positions
4. Pursue distant food sources
5. Random exploration

### Defensive Strategy (When Large Enemies Nearby)
1. Prioritize small enemies in immediate vicinity
2. Collect accessible food
3. Move to safe adjacent positions
4. Hunt reachable small enemies
5. Gather safe food
6. Flee with lowest-cost safe movement

### Splitting Logic
- **Main Beast**: Splits when energy > 50,000 (initial), then 600, then energy/2
- **Secondary Beasts**: Split when energy > 300 (if no large threats visible)
- Main beast prioritizes attacking; secondary beasts hunt after attack counter > 5

## Game Flow

```
┌─────────────────────────────────────────┐
│ Initialize Beast with ID, Energy, Env  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Update Global Map with Local Perception │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Evaluate Nearby Entities & Threats     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Find Safe Moves Based on Priorities    │
└──────────────┬──────────────────────────┘
               │
         ┌─────┴──────┐
         ▼            ▼
    ┌────────┐  ┌──────────┐
    │ MOVE   │  │ SPLIT    │
    └────────┘  └──────────┘
         │            │
         └─────┬──────┘
              ▼
    ┌──────────────────────┐
    │ Update Beast Position│
    │ & Energy Level       │
    └──────────────────────┘
```

## Class Variables (Shared State)

- `beasts`: Dictionary of all active Beast instances
- `game_map`: 2D grid of cell data (type, symbol, last_seen turn)
- `current_turn`: Global game turn counter
- `main_beast`: Primary beast ID (set after first beast creation)
- `main_beast2`: Secondary beast ID (set after main beast splits)
- `beast_amount`: Total number of beasts alive
- `split_counter`: Dynamic threshold for reproduction
- `attack_counter`: Tracks hunting activity
- `flee_counter`: Tracks evasion actions
- `kill_counter`: Tracks successful hunts

## Development Notes

### Design Patterns
- **Class-Level State**: Shared game map and turn counter across all beasts
- **Instance State**: Individual beast properties (position, energy, ID)
- **Strategy Pattern**: Multiple decision paths based on game state
- **Utility Methods**: Static methods for calculations and entity detection

### Performance Considerations
- Grid-based perception (7x7) limits computational cost
- Cell data decay prevents unlimited memory growth
- Closest entity search uses Euclidean distance
- Safe position filtering excludes blocked areas

---
