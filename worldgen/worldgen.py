#!/usr/bin/env python3
"""
worldgen.py

Fractal Worldmap Generator
Based on version 2.2 by John Olsson

Original Copyright (C) 1999 John Olsson
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Python conversion
"""

import random
import math
import sys
from PIL import Image

# Constants
PI = math.pi
INT_MIN = -2**31

# Color palettes (RGB tuples)
RED = [
    0, 0, 0, 0, 0, 0, 0, 0, 34, 68, 102, 119, 136, 153, 170, 187,
    0, 34, 34, 119, 187, 255, 238, 221, 204, 187, 170, 153,
    136, 119, 85, 68,
    255, 250, 245, 240, 235, 230, 225, 220, 215, 210, 205, 200,
    195, 190, 185, 180, 175
]

GREEN = [
    0, 0, 17, 51, 85, 119, 153, 204, 221, 238, 255, 255, 255,
    255, 255, 255, 68, 102, 136, 170, 221, 187, 170, 136,
    136, 102, 85, 85, 68, 51, 51, 34,
    255, 250, 245, 240, 235, 230, 225, 220, 215, 210, 205, 200,
    195, 190, 185, 180, 175
]

BLUE = [
    0, 68, 102, 136, 170, 187, 221, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 0, 0, 0, 0, 0, 34, 34, 34, 34, 34, 34,
    34, 34, 34, 17, 0,
    255, 250, 245, 240, 235, 230, 225, 220, 215, 210, 205, 200,
    195, 190, 185, 180, 175
]


class WorldGenerator:
    """Fractal world map generator."""
    
    def __init__(self, width=320, height=160, seed=None, num_faults=1000, 
                 percent_water=50, percent_ice=10):
        """
        Initialize the world generator.
        
        Args:
            width: Width of the map
            height: Height of the map
            seed: Random seed (None for random)
            num_faults: Number of fault iterations
            percent_water: Percentage of world that is water (0-100)
            percent_ice: Percentage of ice caps (0-100)
        """
        self.width = width
        self.height = height
        self.num_faults = num_faults
        self.percent_water = percent_water
        self.percent_ice = percent_ice
        
        # Set random seed
        if seed is not None:
            random.seed(seed)
            self.seed = seed
        else:
            import time
            self.seed = int(time.time())
            random.seed(self.seed)
        
        # Initialize world map array
        self.world_map = [[0 for _ in range(height)] for _ in range(width)]
        
        # Precompute sin values for efficiency
        self.sin_iter_phi = [math.sin(i * 2 * PI / width) for i in range(2 * width)]
        
        self.y_range_div_2 = height / 2
        self.y_range_div_pi = height / PI
    
    def generate(self):
        """Generate the world map."""
        # Initialize first row to 0, rest to INT_MIN
        for x in range(self.width):
            self.world_map[x][0] = 0
            for y in range(1, self.height):
                self.world_map[x][y] = INT_MIN
        
        # Generate faults
        for _ in range(self.num_faults):
            self.generate_fault()
        
        # Copy data due to symmetry (using half the image)
        for x in range(self.width // 2):
            for y in range(1, self.height):
                self.world_map[x + self.width // 2][self.height - y] = self.world_map[x][y]
        
        # Reconstruct the real world map
        for x in range(self.width):
            color = self.world_map[x][0]
            for y in range(1, self.height):
                if self.world_map[x][y] != INT_MIN:
                    color += self.world_map[x][y]
                self.world_map[x][y] = color
        
        # Find min and max values
        max_z = max(max(row) for row in self.world_map)
        min_z = min(min(row) for row in self.world_map)
        
        # Compute histogram
        histogram = [0] * 256
        for x in range(self.width):
            for y in range(self.height):
                color = self.world_map[x][y]
                color = int(((color - min_z + 1) / (max_z - min_z + 1)) * 30) + 1
                histogram[color] += 1
        
        # Determine sea level threshold
        threshold = self.percent_water * self.width * self.height // 100
        count = 0
        for j in range(256):
            count += histogram[j]
            if count > threshold:
                break
        
        threshold = j * (max_z - min_z + 1) // 30 + min_z
        
        # Scale world map to color range
        for x in range(self.width):
            for y in range(self.height):
                color = self.world_map[x][y]
                
                if color < threshold:
                    # Water
                    color = int(((color - min_z) / (threshold - min_z)) * 15) + 1
                else:
                    # Land
                    color = int(((color - threshold) / (max_z - threshold)) * 15) + 16
                
                # Clamp values
                color = max(1, min(31, color))
                self.world_map[x][y] = color
        
        # Add ice caps if requested
        if self.percent_ice > 0:
            self.add_ice_caps()
        
        return self
    
    def generate_fault(self):
        """Generate a single fault line."""
        # Random flag for raising north or south hemisphere
        flag1 = random.randint(0, 1)
        
        # Create a random great circle by rotating an equator
        alpha = (random.random() - 0.5) * PI  # Rotate around x-axis
        beta = (random.random() - 0.5) * PI   # Rotate around y-axis
        
        tan_b = math.tan(math.acos(math.cos(alpha) * math.cos(beta)))
        
        xsi = int(self.width / 2 - (self.width / PI) * beta)
        
        for phi in range(self.width // 2):
            sin_val = self.sin_iter_phi[xsi - phi + self.width]
            theta = int(self.y_range_div_pi * math.atan(sin_val * tan_b)) + int(self.y_range_div_2)
            
            if theta < 0 or theta >= self.height:
                continue
            
            if flag1:
                # Rise northern hemisphere (lower southern)
                if self.world_map[phi][theta] != INT_MIN:
                    self.world_map[phi][theta] -= 1
                else:
                    self.world_map[phi][theta] = -1
            else:
                # Rise southern hemisphere
                if self.world_map[phi][theta] != INT_MIN:
                    self.world_map[phi][theta] += 1
                else:
                    self.world_map[phi][theta] = 1
    
    def add_ice_caps(self):
        """Add ice caps to poles using flood fill."""
        threshold = self.percent_ice * self.width * self.height // 100
        
        # North pole
        filled = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.world_map[x][y] < 32:
                    filled = self.flood_fill_4(x, y, self.world_map[x][y], filled)
                    if filled > threshold:
                        break
            if filled > threshold:
                break
        
        # South pole
        filled = 0
        for y in range(self.height - 1, -1, -1):
            for x in range(self.width):
                if self.world_map[x][y] < 32:
                    filled = self.flood_fill_4(x, y, self.world_map[x][y], filled)
                    if filled > threshold:
                        break
            if filled > threshold:
                break
    
    def flood_fill_4(self, x, y, old_color, filled_pixels):
        """4-connective flood fill for ice caps."""
        if self.world_map[x][y] != old_color:
            return filled_pixels
        
        # Color as ice
        if self.world_map[x][y] < 16:
            self.world_map[x][y] = 32
        else:
            self.world_map[x][y] += 17
        
        filled_pixels += 1
        
        # Recursively fill adjacent cells
        if y - 1 >= 0:
            filled_pixels = self.flood_fill_4(x, y - 1, old_color, filled_pixels)
        if y + 1 < self.height:
            filled_pixels = self.flood_fill_4(x, y + 1, old_color, filled_pixels)
        
        # Handle wrapping in x direction
        if x - 1 < 0:
            filled_pixels = self.flood_fill_4(self.width - 1, y, old_color, filled_pixels)
        else:
            filled_pixels = self.flood_fill_4(x - 1, y, old_color, filled_pixels)
        
        if x + 1 >= self.width:
            filled_pixels = self.flood_fill_4(0, y, old_color, filled_pixels)
        else:
            filled_pixels = self.flood_fill_4(x + 1, y, old_color, filled_pixels)
        
        return filled_pixels
    
    def save_image(self, filename=None):
        """Save the world map as an image."""
        if filename is None:
            filename = f"world_{self.seed}.gif"
        
        # Create image
        img = Image.new('P', (self.width, self.height))
        
        # Set up palette (256 colors, 3 bytes each RGB)
        palette = []
        for i in range(256):
            if i < len(RED):
                palette.extend([RED[i], GREEN[i], BLUE[i]])
            else:
                palette.extend([0, 0, 0])
        
        img.putpalette(palette)
        
        # Set pixel data
        for y in range(self.height):
            for x in range(self.width):
                img.putpixel((x, y), self.world_map[x][y])
        
        # Save as GIF
        img.save(filename)
        return filename


def main():
    """Main function for command-line usage."""
    print("Fractal World Generator")
    print()
    
    # Get parameters
    try:
        seed = int(input("Seed: "))
    except (ValueError, EOFError):
        import time
        seed = int(time.time())
        print(f"Using seed: {seed}")
    
    try:
        num_faults = int(input("Number of faults: "))
    except (ValueError, EOFError):
        num_faults = 1000
        print(f"Using faults: {num_faults}")
    
    try:
        percent_water = int(input("Percent water: "))
    except (ValueError, EOFError):
        percent_water = 50
        print(f"Using water: {percent_water}%")
    
    try:
        percent_ice = int(input("Percent ice: "))
    except (ValueError, EOFError):
        percent_ice = 10
        print(f"Using ice: {percent_ice}%")
    
    try:
        save_name = input("Save as (.gif will be appended): ")
    except EOFError:
        save_name = "world"
        print(f"Using filename: {save_name}")
    
    # Generate world
    print()
    print("Generating world map...")
    
    world = WorldGenerator(
        width=320,
        height=160,
        seed=seed,
        num_faults=num_faults,
        percent_water=percent_water,
        percent_ice=percent_ice
    )
    
    world.generate()
    filename = world.save_image(f"{save_name}.gif")
    
    print(f"Map created, saved as {filename}.")


if __name__ == '__main__':
    main()
