"""
Beast Game Core Module.

This module provides the core logic and functionality for managing and simulating
the behavior of beasts in the Beast Game. It includes the `Beast` class, which represents
individual beasts, as well as utility functions and methods for handling movement,
environment updates, and interactions with the game map.

Features:
- **Beast Management**: Create, update, and remove beasts with unique behaviors.
- **Movement Logic**: Calculate safe movements, handle priorities like fleeing,
  attacking, or collecting food.
- **Environment Interaction**: Update the global game map based on local surroundings,
  and manage visibility and positions of entities.
- **Energy Costs**: Calculate energy consumption for movements and actions.
- **Splitting Logic**: Manage beast splitting based on energy thresholds.

Usage:
The `Beast` class is the primary interface for creating and interacting with beasts.
The module includes various methods to control their behavior, manage their environment,
and calculate optimal strategies.

Classes:
- `Beast`: Represents a beast in the game, with methods to control its movement, energy,
  and interactions with other entities.

Functions:
- `wrap_coordinates(x, y)`: Ensures coordinates wrap around the map boundaries.
- `print_and_flush(message)`: Prints a message to the console and flushes the output stream.

Class Methods:
- `Beast.decide_movement()`: Determines the next movement or action for the beast.
- `Beast.update_environment()`: Updates the global game map with the beast's local view.
- `Beast.remove_beast(beast_id)`: Removes a beast from the game.
- `Beast.update_current_turn()`: Advances the game turn and cleans old data.

Static Methods:
- Various utility methods for entity detection, movement calculation, and cost evaluation,
  including `find_entities`, `calculate_energy_cost`, `is_safe_position`, etc.

Constants:
- `MAP_WIDTH` and `MAP_HEIGHT`: Dimensions of the game map.
- `CELL_DURATION`: The number of turns before a cell's information expires.

Dependencies:
- `math`: For calculating distances and energy costs.
- `random`: For generating random movements.
- `sys`: For console output flushing.
- `beast_game.constants`: Module for game-wide constants and command definitions.

This module forms the core logic for the Beast Game and should be integrated into a larger
framework that handles game state, server communication, and additional gameplay logic.
"""

import math
import random
import sys
from beast_game.constants import cmd, MAP_WIDTH, MAP_HEIGHT, CELL_DURATION

def wrap_coordinates(x, y):
    """
    Wraps coordinates within the game map dimensions using modulo operation.

    Args:
        x (int): x-coordinate.
        y (int): y-coordinate.

    Returns:
        tuple: Wrapped coordinates (x, y).
    """
    wrapped_x = x % MAP_WIDTH
    wrapped_y = y % MAP_HEIGHT
    return wrapped_x, wrapped_y


def print_and_flush(message: str):
    """
    Prints a given message to the console and flushes the
    output stream.

    Args:
        message (str): The message to be printed.
    """
    print(message)
    sys.stdout.flush()


class Beast:
    """
    A class representing a Beast in the game.

    Attributes:
        id (int): Unique identifier for the Beast.
        energy (float): Current energy.
        x (int): Current x coordinate.
        y (int): Current y coordinate.
        steps (int): Number of steps taken.
        attack_counter (int): Counter for attack actions.
        split_counter (int): Threshold for splitting.
        environment_str (str): String representing the Beast's surroundings.
        environment (list): 2D grid representing the Beast's surroundings.
        total_energy_cost (float): Total energy cost.
        next_move (tuple): Next movement coordinates.
    """

    # Class variables
    beasts = {}  # Dictionary to store all beast instances

    game_map = [
        [{"type": "empty", "symbol": ".", "last_seen": 0} for _ in range(MAP_HEIGHT)]
        for _ in range(MAP_WIDTH)
    ]

    current_turn = 0

    # Global
    attack_counter = 0
    beast_amount = 1
    current_round = 0
    flee_counter = 0
    kill_counter = 0
    split_counter = 200

    main_beast = None
    main_beast2 = None

    def __init__(self, beast_id: int, energy: float, environment: str):
        """
        Initializes a Beast with an ID, energy, and environment.

        Args:
            beast_id (int): Unique identifier for the Beast.
            energy (float): Initial energy level of the Beast.
            environment (str): String representing the Beast's surroundings.
        """
        self.id = beast_id
        self.energy = energy
        self.environment_str = environment
        self.environment = self.string_to_grid(environment)
        self.attack_counter = 0
        # self.split_counter = 200  # Initial split threshold
        self.steps = 0
        self.total_energy_cost = 0
        self.next_move = (None, None)
        # ton
        self.flee = 0
        self.follow_attack = 0
        self.kills = 0
        self.first_split = False
        self.attack = True

        # Initial position (assumed to be at (0, 0) unless updated)
        self.x = 0
        self.y = 0

        # Add this beast to the class-level dictionary
        Beast.beasts[beast_id] = self

        # Update the environment on the global map
        self.update_environment()

    @staticmethod
    def string_to_grid(environment: str):
        """
        Converts an environment string into a 2D grid.

        Args:
            environment (str): String representing the environment.

        Returns:
            list: A 2D list representing the environment grid.
        """
        return [list(environment[i:i + 7]) for i in range(0, len(environment), 7)]

    @staticmethod
    def is_safe_position(position, big_enemy_positions):
        """
        Check if a position is safe, i.e., outside the movement range of all large enemy beasts.

        Args:
            position: A position (x, y) to check for safety.
            big_enemy_positions: position list of all larger enemies

        Returns:
            bool: Returns True if the position is safe,
              and False if it lies within the movement range of any large enemy beast.
        """
        if not big_enemy_positions:
            return True  # No larger enemies. Position is safe

        for big_enemy_x, big_enemy_y in big_enemy_positions:
            for dx in range(-2, 3):  # x moves from -2 to 2
                for dy in range(-2, 3):  # y moves from -2 to 2
                    if (big_enemy_x + dx, big_enemy_y + dy) == position:
                        return False  # The position is in the moving range of a larger enemy
        return True

    @staticmethod
    def find_entities(grid, entity_symbol):
        """
            Find all positions of a specific entities in the environment-grid
        Args:
            grid: String representing the environment.
            entity_symbol: symbol of the entities.
        Returns:
            list: list of entities in the environment
        """
        return [(col - 3, row - 3) for row in range(7) for col in range(7) if grid[row][col] == entity_symbol]

    def find_entity_positions(self, symbols):
        """
        Finds positions of specified entities in the environment.

        Args:
            symbols (list): List of symbols representing entities.

        Returns:
            list: List of positions (dx, dy) relative to the beast.
        """
        return [(col - 3, row - 3)
                for row in range(7) for col in range(7)
                if self.environment[row][col] in symbols]

    @staticmethod
    def find_closest_entity(entity_positions, current_position):
        """
        Finds the closest entity to the current position based on the Euclidean distance.

        Args:
            entity_positions (list of tuple): List of positions (x,y) of an entity.
            current_position (tuple): The position (x,y) of the beast.

        Returns:
            tuple or None: The position (x, y) of the closest entity. Returns None if no entities are provided.
        """
        entity_positions.sort(
            key=lambda pos: math.sqrt((pos[0] - current_position[0]) ** 2 + (pos[1] - current_position[1]) ** 2))
        return entity_positions[0] if entity_positions else None

    @staticmethod
    def calculate_move_towards_entity(entity_position):
        """
        Calculates the movement towards the given entity position, limited to a maximum of 2 steps in each direction.

        Args:
            entity_position (tuple): A tuple of the form (x, y) representing the position of the entity.

        Returns:
            tuple: A tuple (move_x, move_y) representing the movement in the x and y directions, respectively.
                   The values are limited to a range between -2 and 2.
        """
        x, y = entity_position
        move_x = min(2, max(-2, x))
        move_y = min(2, max(-2, y))
        return move_x, move_y

    @staticmethod
    def calculate_movement(target_position):
        """
        Calculates movement towards a target position.

        Args:
            target_position (tuple): Relative position (dx, dy) of the target.

        Returns:
            tuple: Movement (move_x, move_y) limited to maximum steps.
        """
        x, y = target_position
        move_x = min(2, max(-2, x))
        move_y = min(2, max(-2, y))
        return move_x, move_y

    @staticmethod
    def is_within_attack_range(entity_position, radius=2):
        """
        Checks if an entity is within attack range.

        Args:
            entity_position (tuple): Relative position (dx, dy) of the entity.
            radius (int): Attack range radius.

        Returns:
            bool: True if within range, False otherwise.
        """
        x, y = entity_position
        return abs(x) <= radius and abs(y) <= radius

    @staticmethod
    def calculate_energy_cost_relative(d_x, d_y):
        """
        Calculates the energy cost for a movement.

        Args:
            d_x (int): Movement in x-direction.
            d_y (int): Movement in y-direction.

        Returns:
            float: Energy cost for the movement.
        """
        if d_x == 0 and d_y == 0:
            return 0.5  # Energy cost for standing still
        return math.sqrt(d_x ** 2 + d_y ** 2)

    @staticmethod
    def calculate_energy_cost(current_position, target_position):
        """
        Calculates the energy cost of a movement based on Euclidean distance.

        Args:
            current_position (tuple): Current position of the beast
            target_position (tuple): Target position the beast could move to

        Returns:
            float: The energy cost for the movement, calculated as the Euclidean distance between the
               current and target positions. If the current position and target position are the same,
               the cost is 0.5.
        """
        d_x = target_position[0] - current_position[0]
        d_y = target_position[1] - current_position[1]
        return math.sqrt(d_x ** 2 + d_y ** 2) if (d_x, d_y) != (0, 0) else 0.5

    def find_lowest_cost_safe_move(self, safe_positions, current_position):
        """
        Find safe field with the smallest energy cost, but exclude no movement (0,0)

        Args:
            safe_positions (list): A list of valid positions that are considered safe for movement.
            current_position (tuple): Current position (x,y) of the beast.

        Returns:
            tuple: Position (x,y) of the move with the lowest energy cost.
                If no valid move exists, returns (0,0) representing no movement.
        """
        # Filter the positions to exclude (0.0) no movement.
        filtered_positions = [pos for pos in safe_positions if pos != current_position]

        # If there is no possible move, return None
        if not filtered_positions:
            lowest_cost_move = (0, 0)
            return lowest_cost_move
        # Find move with the lowest energy cost
        lowest_cost_move = min(filtered_positions, key=lambda pos: self.calculate_energy_cost(current_position, pos))
        return lowest_cost_move

    @staticmethod
    def small_in_sight(small_enemy_positions):
        """
        Find the smallest beast in the view range (Manhattan-Distance ≤ 3)

        Args:
            small_enemy_positions (list): A list of positions with smaller enemies

        Returns:
            list: A list of the small enemies positions within the view range
        """
        return [pos for pos in small_enemy_positions if abs(pos[0]) <= 3 and abs(pos[1]) <= 3]

    @staticmethod
    def small_within_attack(small_enemy_positions):
        """
        Find smaller enemy in attack range (Manhattan-Distance ≤ 2)

        Args:
            small_enemy_positions (list): A list of positions (x,y) with smaller enemies

        Returns:
            list: A list of the small enemies positions (x,y) within the attack range
        """
        return [pos for pos in small_enemy_positions if abs(pos[0]) <= 2 and abs(pos[1]) <= 2]

    @staticmethod
    def food_in_sight(food_positions):
        """
        Find food in view range (Manhattan-Distance ≤ 3)

        Args:
            food_positions (list): A list of positions (x,y) with food

        Returns:
            list: A list of food positions (x,y) within the view range
        """
        return [pos for pos in food_positions if abs(pos[0]) <= 3 and abs(pos[1]) <= 3]

    @staticmethod
    def food_within_attack(food_positions):
        """
        Find food in view range (Manhattan-Distance ≤ 2)

        Args:
            food_positions (list): A list of positions (x,y) with food

        Returns:
            list: A list of food positions (x,y) within the attack range
        """
        return [pos for pos in food_positions if abs(pos[0]) <= 2 and abs(pos[1]) <= 2]

    def split_logic(self, d_x, d_y):
        """
        Logic for splitting the Beast.

        Args:
            d_x (int): Movement in x-direction for the new beast.
            d_y (int): Movement in y-direction for the new beast.

        Returns:
            str: Command to split the Beast.
        """
        self.attack_counter = 0
        return f"{self.id} {cmd.SPLIT} {d_x} {d_y}"

    def kill_logic(self, closest_small_enemy):
        """
        Logic for attacking smaller enemies.

        Args:
            closest_small_enemy (tuple): Relative position of the small enemy.

        Returns:
            tuple: Movement (d_x, d_y) towards the enemy.
        """
        d_x, d_y = self.calculate_movement(closest_small_enemy)
        return d_x, d_y

    def flee_logic(self, closest_big_enemy):
        """
        Logic for fleeing from bigger enemies.

        Args:
            closest_big_enemy (tuple): Relative position of the big enemy.

        Returns:
            tuple: Movement (d_x, d_y) away from the enemy.
        """
        d_x, d_y = self.calculate_movement((-closest_big_enemy[0], -closest_big_enemy[1]))
        return d_x, d_y

    def food_logic(self, closest_food):
        """
        Logic for moving towards food.

        Args:
            closest_food (tuple): Relative position of the food.

        Returns:
            tuple: Movement (d_x, d_y) towards the food.
        """
        self.attack_counter += 1
        d_x, d_y = self.calculate_movement(closest_food)
        return d_x, d_y

    @staticmethod
    def no_prio_near():
        """
        Logic when no prioritized entities are nearby.

        Returns:
            tuple: Random movement (d_x, d_y).
        """
        d_x = random.randint(-2, 2)
        d_y = random.randint(-2, 2)
        return d_x, d_y

    def is_cell_occupied_by_own_beast(self, target_dx, target_dy):
        """
        Checks if the target cell is occupied by another own beast.

        Args:
            target_dx (int): Movement in x-direction.
            target_dy (int): Movement in y-direction.

        Returns:
            bool: True if occupied by own beast, False otherwise.
        """
        target_x, target_y = wrap_coordinates(self.x + target_dx, self.y + target_dy)
        cell = Beast.game_map[target_x][target_y]
        if (
                isinstance(cell, dict)
                and cell.get("type") == "own_beast"
                and cell.get("id") != self.id
        ):
            print(f"cell: {cell}")
            return True
        return False

    def update_environment(self):
        """
        Updates the global map based on the beast's local environment.
        """
        grid = self.environment

        for row in range(7):
            for col in range(7):
                symbol = grid[row][col]
                dx = col - 3
                dy = row - 3
                global_x, global_y = wrap_coordinates(self.x + dx, self.y + dy)

                # Determine entity type
                if symbol == ".":
                    entity_type = "empty"
                elif symbol == "*":
                    entity_type = "food"
                elif symbol in [">", "=", "<"]:
                    entity_type = "enemy_beast"
                else:
                    entity_type = "unknown"

                # Mark the position of the own beast
                if dx == 0 and dy == 0:
                    entity_type = "own_beast"

                cell_data = {
                    "type": entity_type,
                    "symbol": symbol,
                    "last_seen": Beast.current_turn,
                }

                existing_cell = Beast.game_map[global_x][global_y]
                existing_last_seen = existing_cell.get("last_seen", 0) if isinstance(existing_cell, dict) else 0

                if existing_last_seen < Beast.current_turn:
                    Beast.game_map[global_x][global_y] = cell_data

    def move_and_update(self, move_x, move_y):
        """
        Moves the beast, updates the map, and the beast's information.

        Args:
            move_x (int): Movement in x-direction.
            move_y (int): Movement in y-direction.
        """
        current_x = self.x
        current_y = self.y
        current_energy = self.energy

        # Calculate new position
        new_x, new_y = wrap_coordinates(current_x + move_x, current_y + move_y)

        # Check if own beast is at the new position
        # cell = Beast.game_map[new_x][new_y]
        # if (
        #     isinstance(cell, dict)
        #     and cell.get("type") == "own_beast"
        #     and cell.get("id") != self.id
        # ):
        #     print(f"Beast {self.id} is trying to move onto its own beast. Movement aborted.")
        #     return

        # Remove beast from old position
        Beast.game_map[current_x][current_y] = {
            "type": "empty",
            "symbol": ".",
            "last_seen": Beast.current_turn,
        }

        move_cost = self.calculate_energy_cost_relative(move_x, move_y)
        new_energy = max(current_energy - move_cost, 0)

        # Save beast at new position
        Beast.game_map[new_x][new_y] = {
            "id": self.id,
            "type": "own_beast",
            "energy": new_energy,
            "steps": self.steps + 1,
            "position": (new_x, new_y),
            "last_seen": Beast.current_turn,
        }

        # Update beast information
        self.x = new_x
        self.y = new_y
        self.energy = new_energy
        self.steps += 1

        # Update environment
        self.update_environment()

        if self.id == Beast.main_beast:
            self.print_game_map()

    @classmethod
    def print_game_map(cls):
        """
        Prints the current map to the console, showing the IDs of own beasts.
        """
        for y in range(MAP_HEIGHT):
            row = ""
            for x in range(MAP_WIDTH):
                cell = cls.game_map[x][y]
                if isinstance(cell, dict):
                    if cell.get("type") == "own_beast" and "id" in cell:
                        symbol = str(cell["id"]).ljust(1)
                    else:
                        symbol = cell.get("symbol", "?")
                else:
                    symbol = cell
                row += symbol
            print(row)

    @classmethod
    def clean_old_cells(cls):
        """
        Cleans the map by overwriting cells whose information is older than CELL_DURATION rounds.
        """
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                cell = cls.game_map[x][y]
                if isinstance(cell, dict):
                    last_seen = cell.get('last_seen', 0)
                    if cls.current_turn - last_seen >= CELL_DURATION - 1:
                        cls.game_map[x][y] = {
                            "type": "empty",
                            "symbol": ".",
                            "last_seen": 0,
                        }

    def find_safe_moves(self, safe_positions, food_positions, small_enemy_positions, big_enemy_positions,
                        current_position):
        """
        Find the safest move based on priorities and the attack range of various entities.

        This method evaluates the current game state and decides the best move for the entity
        considering safe positions, food availability, and enemy threats. The move is determined
        based on predefined priorities, including attacking smaller enemies, collecting food,
        or fleeing from larger enemies.

        Args:
            safe_positions : list of tuple
                List of positions (x, y) that are considered safe for movement.
            food_positions : list of tuple
                List of positions (x, y) where food is located.
            small_enemy_positions : list of tuple
                List of positions (x, y) of smaller enemies within sight.
            big_enemy_positions : list of tuple
                List of positions (x, y) of larger enemies within sight.
            current_position : tuple
                The current position (x, y) of the entity.

        Returns:
            tuple
                The best move as a tuple (dx, dy), representing the change in position.
                If no safe moves are found, it defaults to (0, 0).
         """
        # Global variables to track various counters and states for the game
        # global attack_counter, beast_amount, kill_counter, kill_main, kill_main2, flee_counter, flee_main, flee_main2
        # global follow_main, follow_main2, main_attack, main_attack2, main_beast, main_beast2, main_beast_gone, main_beast_gone2
        best_move = None

        # Determine if there are larger enemies in sight
        big_enemy_in_sight = any(abs(ex) <= 3 and abs(ey) <= 3 for ex, ey in big_enemy_positions)

        # Positions to be excluded from consideration
        excluded_positions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

        if not big_enemy_in_sight and self.first_split == True:
            # Filter safe positions by removing excluded positions
            safe_positions = [pos for pos in safe_positions if pos not in excluded_positions]

        # Small enemies within attack range
        small_within_attack_positions = self.small_within_attack(small_enemy_positions)
        ## Small enemies within sight but not necessarily in attack range
        small_in_sight_positions = self.small_in_sight(small_enemy_positions)
        # Safe small enemies within attack range
        safe_small_enemies_within_attack = [pos for pos in small_within_attack_positions if pos in safe_positions]
        # Safe small enemies outside of attack range
        safe_small_enemies_outside_attack = [pos for pos in small_in_sight_positions if
                                             pos not in small_within_attack_positions]

        # Food within attack range
        food_within_attack_positions = self.food_within_attack(food_positions)
        # Food within sight but not necessarily in attack range
        food_in_sight_positions = self.food_in_sight(food_positions)
        # Safe food positions within attack range
        safe_food_within_attack = [pos for pos in food_within_attack_positions if pos in safe_positions]
        # Safe food positions outside attack range
        safe_food_outside_attack = [pos for pos in food_in_sight_positions if pos not in food_within_attack_positions]

        # If there are no safe positions available (e.g., surrounded by multiple large enemies)
        if not safe_positions:
            best_move = (0, 0)
            return best_move

        # If a large enemy is in sight, prioritize small enemies and safe food
        if big_enemy_in_sight:
            self.flee += 1
            # Define immediate adjacent positions (radius 1)
            adjacent_positions = [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ]
            # Priority 1: Check for a small enemy in adjacent positions
            for adj_pos in adjacent_positions:
                if adj_pos in safe_small_enemies_within_attack:
                    move_to_enemy = self.calculate_move_towards_entity(adj_pos)
                    new_position = (current_position[0] + move_to_enemy[0], current_position[1] + move_to_enemy[1])
                    if new_position in safe_positions:
                        best_move = move_to_enemy
                        return best_move

            # Priority 2: Check for food in adjacent positions
            for adj_pos in adjacent_positions:
                if adj_pos in safe_food_within_attack:
                    move_to_food = self.calculate_move_towards_entity(adj_pos)
                    new_position = (current_position[0] + move_to_food[0], current_position[1] + move_to_food[1])

                    if new_position in safe_positions:
                        self.__class__.attack_counter += 1
                        best_move = move_to_food
                        return best_move
            # Priority 3: Check for a safe empty field in adjacent positions
            for adj_pos in adjacent_positions:
                if adj_pos in safe_positions:
                    best_move = self.calculate_move_towards_entity(adj_pos)
                    return best_move
            # Priority 4: Move towards a safe small enemy within attack range
            if safe_small_enemies_within_attack:
                closest_safe_enemy = self.find_closest_entity(safe_small_enemies_within_attack, current_position)
                if closest_safe_enemy:
                    move_to_enemy = self.calculate_move_towards_entity(closest_safe_enemy)
                    new_position = (current_position[0] + move_to_enemy[0], current_position[1] + move_to_enemy[1])

                    # Ensure the move itself is safe
                    if new_position in safe_positions:
                        best_move = move_to_enemy
                        self.kills += 1
                        # kill_counter += 1
                        return best_move

            # Priority 5: Move towards safe food if small enemies are not reachable
            if safe_food_within_attack:
                closest_safe_food = self.find_closest_entity(safe_food_within_attack, current_position)
                if closest_safe_food:
                    move_to_food = self.calculate_move_towards_entity(closest_safe_food)
                    new_position = (current_position[0] + move_to_food[0], current_position[1] + move_to_food[1])

                    # Move only if target position is safe
                    if new_position in safe_positions:
                        self.__class__.attack_counter += 1
                        best_move = move_to_food
                        return best_move

            # Priority 6: If no small enemies or food are visible, move away from the large enemy
            else:
                best_move = self.find_lowest_cost_safe_move(safe_positions, current_position)
                return best_move

        # No large beast in sight
        else:
            # Main beast will only attack again after the first split when the small beast has no large beast in sight
            if self.id != self.__class__.main_beast:
                self.attack = True
            # Priority on small beasts or food when no large enemies are in sight
            # Priority 1: Move towards a safe small beast within attack range
            if safe_small_enemies_within_attack:
                # Only the main beast can eat small beasts
                if (self.id == self.__class__.main_beast and self.attack == True) or (
                        self.id != self.__class__.main_beast and self.__class__.attack_counter > 5):
                    closest_safe_enemy = self.find_closest_entity(safe_small_enemies_within_attack, current_position)
                    if closest_safe_enemy:
                        move_to_enemy = self.calculate_move_towards_entity(closest_safe_enemy)
                        new_position = (current_position[0] + move_to_enemy[0], current_position[1] + move_to_enemy[1])

                        # Ensure that the move itself is safe
                        if new_position in safe_positions:
                            best_move = move_to_enemy
                            self.kills += 1
                            # kill_counter += 1
                            return best_move

            # Chase small beasts when acting as the main beast
            if safe_small_enemies_outside_attack:
                if self.id == self.__class__.main_beast:
                    self.follow_attack += 1
                if self.id == self.__class__.main_beast and self.attack == True and self.follow_attack < 3:
                    # Search for food within a radius of 1 around the small beast
                    for enemy_pos in safe_small_enemies_outside_attack:
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1),
                                       (1, 1)]:  # Neighbors within a 1-tile radius
                            possible_food_position = (enemy_pos[0] + dx, enemy_pos[1] + dy)
                            if possible_food_position in food_positions and possible_food_position in safe_positions:
                                # Move towards the food near the small beast
                                move_to_food = self.calculate_move_towards_entity(possible_food_position)
                                new_position = (
                                current_position[0] + move_to_food[0], current_position[1] + move_to_food[1])
                                if new_position in safe_positions:
                                    best_move = move_to_food
                                    return best_move

                    # If no small beast is safely reachable within move range,
                    # move towards the nearest visible small beast outside attack range.
                    closest_safe_enemy = self.find_closest_entity(safe_small_enemies_outside_attack, current_position)
                    if closest_safe_enemy and self.energy > 1000:
                        move_to_enemy = self.calculate_move_towards_entity(closest_safe_enemy)
                        new_position = (current_position[0] + move_to_enemy[0], current_position[1] + move_to_enemy[1])

                        # Only move if the target position is safe
                        if new_position in safe_positions:
                            best_move = move_to_enemy
                            return best_move

            if self.follow_attack > 3:
                self.follow_attack = 0
            # Priority 2: If no small beast is safely reachable, but food is in a safe area
            if safe_food_within_attack:
                closest_safe_food = self.find_closest_entity(safe_food_within_attack, current_position)
                if closest_safe_food:
                    move_to_food = self.calculate_move_towards_entity(closest_safe_food)
                    # Main beast makes single-tile steps
                    if self.id == self.__class__.main_beast and self.flee > 1 or (self.id != self.__class__.main_beast):
                        move_to_food = (
                            min(1, max(-1, closest_safe_food[0] - current_position[0])),
                            min(1, max(-1, closest_safe_food[1] - current_position[1]))
                        )
                    new_position = (current_position[0] + move_to_food[0], current_position[1] + move_to_food[1])

                    # Only move if the target position is safe
                    if new_position in safe_positions:
                        self.__class__.attack_counter += 1
                        best_move = move_to_food
                        return best_move

            if safe_food_outside_attack:
                closest_safe_food = self.find_closest_entity(safe_food_outside_attack, current_position)
                if closest_safe_food:
                    move_to_food = self.calculate_move_towards_entity(closest_safe_food)
                    # Main-Beast macht 1er steps
                    if self.id == self.__class__.main_beast or (self.id != self.__class__.main_beast):
                        move_to_food = (
                            min(1, max(-1, closest_safe_food[0] - current_position[0])),
                            min(1, max(-1, closest_safe_food[1] - current_position[1]))
                        )
                    new_position = (current_position[0] + move_to_food[0], current_position[1] + move_to_food[1])

                    # Only move if the target position is safe
                    if new_position in safe_positions:
                        best_move = move_to_food
                        return best_move

        # Random movement if no safe options are available

        if not best_move:
            if self.energy > 6:
                best_move = (random.randint(-1, 1), random.randint(-1, 1))
            else:
                best_move = (0, 0)

        return best_move

    def check_main_beast(self):
        """

        Returns:

        """
        if Beast.main_beast is None and Beast.main_beast2 is None:
            Beast.main_beast = self.id

        if Beast.main_beast is None and Beast.main_beast2 is not None:
            Beast.main_beast = Beast.main_beast2.id

        if Beast.main_beast2 is None and Beast.main_beast is not None:
            Beast.main_beast2 = self.id

    def decide_movement(self):
        """
        Determines the beast's next movement based on the current situation.

        Returns:
            str: Command string to send to the server.
        """

        self.check_main_beast()

        # # Find positions of entities
        # food_positions = self.find_entity_positions(["*"])
        # small_enemy_positions = self.find_entity_positions(["<"])
        # big_enemy_positions = self.find_entity_positions([">"])

        grid = self.string_to_grid(self.environment_str)

        food_positions = self.find_entities(grid, '*')
        small_enemy_positions = self.find_entities(grid, '<')
        big_enemy_positions = self.find_entities(grid, '>')

        # Calculate safe positions
        safe_positions = []
        for x in range(-2, 3):
            for y in range(-2, 3):
                if self.is_safe_position((x, y), big_enemy_positions):
                    safe_positions.append((x, y))

        # closest_small_enemy = self.find_closest_entity(small_enemy_positions)
        # closest_big_enemy = self.find_closest_entity(big_enemy_positions)
        # closest_food = self.find_closest_entity(food_positions)

        # d_x, d_y = 0, 0  # Default is to stay in place

        current_position = (0, 0)
        d_x, d_y = self.find_safe_moves(safe_positions, food_positions, small_enemy_positions, big_enemy_positions,
                                        current_position)

        # if (
        #     closest_small_enemy
        #     and self.is_within_attack_range(closest_small_enemy)
        #     and self.attack_counter > 5
        # ):
        #     d_x, d_y = self.kill_logic(closest_small_enemy)
        #     self.attack_counter = 0
        # elif closest_big_enemy:
        #     d_x, d_y = self.flee_logic(closest_big_enemy)
        # elif closest_food:
        #     self.attack_counter += 1
        #     d_x, d_y = self.food_logic(closest_food)
        # elif self.energy >= 6:
        #     d_x, d_y = self.no_prio_near()
        # else:
        #     return f"{self.id} {cmd.MOVE} {0} {0}"
        #
        # Check if the target cell is occupied by own beast
        # TODO: in find_safe_moves() einbauen
        # if self.is_cell_occupied_by_own_beast(d_x, d_y):
        #     # print(f"Beast {self.id} avoids moving onto its own beast.")
        #     d_x, d_y = 0, 0  # Beast stays in place

        # Calculate energy cost for the movement
        energy_cost = self.calculate_energy_cost_relative(d_x, d_y)
        if energy_cost > self.energy:
            d_x, d_y = 0, 0  # Beast stays in place

        # Decide whether to split
        if self.id == Beast.main_beast:
            if self.energy > 50_000:
                Beast.split_counter = 200
                self.first_split = True
            elif self.energy > 600:
                Beast.split_counter = 300
            elif self.energy > 80:
                Beast.split_counter = self.energy / 2

        # Main-Beast split
        if self.energy > Beast.split_counter and not (
                ">" in self.environment or "<" in self.environment) and self.id == Beast.main_beast and self.first_split == False:
            print_and_flush(
                "------------------------------------------MAIN SPLIT-------------------------------------------")
            print_and_flush(
                f"current Split: {Beast.split_counter} Energy (ID: {self.id}, Energy: {round(self.energy, 2)})")
            print_and_flush("MAIN-BEAST has divided!")
            # Main-Beast will no longer split afterward unless it is alone again
            self.first_split = True
            self.attack = False
            self.attack_counter = 0
            d_x, d_y = random.choice(((0, 1), (0, -1), (-1, 0), (1, 0)))
            # server_command = f"{self.id} {cmd.SPLIT} {d_x} {d_y}"
            command = self.split_logic(d_x, d_y)
            return command

        #########################
        if self.energy > Beast.split_counter and not any(
                ">" in row for row in self.environment_str) and self.id != Beast.main_beast:
            self.attack_counter = 0
            d_x, d_y = random.choice(((0, 1), (0, -1), (-1, 0), (1, 0)))
            command = self.split_logic(d_x, d_y)
        else:
            command = f"{self.id} {cmd.MOVE} {d_x} {d_y}"

        self.next_move = (d_x, d_y)
        return command

    @classmethod
    def remove_beast(cls, beast_id):
        """
        Removes a beast from the map and the beasts data structure.

        Args:
            beast_id (int): ID of the beast to remove.
        """
        if beast_id in cls.beasts:
            beast = cls.beasts[beast_id]
            x = beast.x
            y = beast.y
            cls.game_map[x][y] = {
                "type": "empty",
                "symbol": ".",
                "last_seen": cls.current_turn,
            }
            del cls.beasts[beast_id]

        if beast_id == Beast.main_beast.id:
            Beast.main_beast = None
        if beast_id == Beast.main_beast2.id:
            Beast.main_beast2 = None

    @classmethod
    def update_current_turn(cls):
        """
        Updates the current turn and cleans old cells.
        """
        cls.current_turn += 1
        cls.clean_old_cells()
