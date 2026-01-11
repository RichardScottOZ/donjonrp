#!/usr/bin/env python3
"""
generator.py
written and released to the public domain by drow <drow@bin.sh>
http://creativecommons.org/publicdomain/zero/1.0/

Python conversion
"""

import random
import re

gen_data = {}


def generate_text(gen_type):
    """Generate text from a generator type."""
    if gen_type in gen_data:
        data = gen_data[gen_type]
        string = select_from(data)
        if string:
            return expand_tokens(string)
    return ''


def generate_list(gen_type, n_of):
    """Generate multiple text strings."""
    result = []
    for _ in range(n_of):
        result.append(generate_text(gen_type))
    return result


def select_from(data):
    """Select from list or table."""
    if isinstance(data, list):
        return select_from_array(data)
    elif isinstance(data, dict):
        return select_from_table(data)
    return ''


def select_from_array(data):
    """Select randomly from an array."""
    if not data:
        return ''
    return random.choice(data)


def select_from_table(data):
    """Select from a weighted table."""
    length = scale_table(data)
    if not length:
        return ''
    
    idx = random.randint(1, length)
    
    for key in data:
        r = key_range(key)
        if idx >= r[0] and idx <= r[1]:
            return data[key]
    
    return ''


def scale_table(data):
    """Calculate the total range of a table."""
    length = 0
    
    for key in data:
        r = key_range(key)
        if r[1] > length:
            length = r[1]
    
    return length


def key_range(key):
    """Parse a key to get its range."""
    # Match patterns like "1-3", "01-50", "00", etc.
    match = re.match(r'(\d+)-00$', key)
    if match:
        return [int(match.group(1)), 100]
    
    match = re.match(r'(\d+)-(\d+)$', key)
    if match:
        return [int(match.group(1)), int(match.group(2))]
    
    if key == '00':
        return [100, 100]
    
    try:
        num = int(key)
        return [num, num]
    except ValueError:
        return [0, 0]


def expand_tokens(string):
    """Expand {token} references in string."""
    # Keep expanding until no more tokens
    max_iterations = 100  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        match = re.search(r'\{(\w+)\}', string)
        if not match:
            break
        
        token = match.group(1)
        replacement = generate_text(token)
        
        if replacement:
            string = string.replace('{' + token + '}', replacement, 1)
        else:
            string = string.replace('{' + token + '}', token, 1)
        
        iteration += 1
    
    return string


if __name__ == '__main__':
    # Example usage
    import sys
    import os
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and load data
    import warrior_data
    warrior_data.load_warrior_data()
    
    print("Generating 10 warriors:")
    for warrior in generate_list('warrior', 10):
        print(f"  {warrior}")
    sys.stdout.flush()
