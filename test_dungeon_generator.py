#!/usr/bin/env python3
"""Test script for the dungeon generator."""

import sys
import os

# Add the dungeon directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dungeon'))

from dungeon import DungeonGenerator

# Generate a dungeon
print("Generating test dungeon...")
dungeon = DungeonGenerator(
    seed=12345,
    n_rows=39,
    n_cols=39,
    room_layout='Scattered',
    corridor_layout='Bent',
    remove_deadends=50,
    add_stairs=2,
    cell_size=18
)

dungeon.generate()
filename = dungeon.save_image('test_dungeon.gif')

print(f"Dungeon generated successfully:")
print(f"  Saved to: {filename}")
print(f"  Rooms: {dungeon.n_rooms}")
print(f"  Doors: {len(dungeon.doors)}")
print(f"  Stairs: {len(dungeon.stairs_list)}")
print(f"  Size: {dungeon.n_rows}x{dungeon.n_cols} cells")
