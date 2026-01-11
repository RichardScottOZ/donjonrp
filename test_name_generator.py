#!/usr/bin/env python3
"""Test script for the name generator."""

import sys
import os

# Add the namegenerator directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'namegenerator'))

import name_generator
import egyptian_set

# Load the data
egyptian_set.load_egyptian_set()

# Generate names
print("Generating 10 Egyptian names:")
for name in name_generator.name_list('egyptian', 10):
    print(f"  {name}")
