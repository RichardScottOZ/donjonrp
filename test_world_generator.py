#!/usr/bin/env python3
"""Test script for the world generator."""

import sys
import os

# Add the worldgen directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worldgen'))

from worldgen import WorldGenerator

# Generate a world
print("Generating test world...")
world = WorldGenerator(
    width=320,
    height=160,
    seed=42,
    num_faults=1000,
    percent_water=55,
    percent_ice=8
)

world.generate()
filename = world.save_image('test_world.gif')

print(f"World generated successfully:")
print(f"  Saved to: {filename}")
print(f"  Size: {world.width}x{world.height} pixels")
print(f"  Seed: {world.seed}")
print(f"  Faults: {world.num_faults}")
print(f"  Water: {world.percent_water}%")
print(f"  Ice: {world.percent_ice}%")
