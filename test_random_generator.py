#!/usr/bin/env python3
"""Test script for the random generator."""

import sys
import os

# Add the randomgenerator directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'randomgenerator'))

import generator
import warrior_data

# Load the data
warrior_data.load_warrior_data()

# Generate warriors
print("Generating 10 warriors:")
for warrior in generator.generate_list('warrior', 10):
    print(f"  {warrior}")
