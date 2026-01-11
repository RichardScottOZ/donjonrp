#!/usr/bin/env python3
"""
name_generator.py
written and released to the public domain by drow <drow@bin.sh>
http://creativecommons.org/publicdomain/zero/1.0/

Python conversion by conversion tool
"""

import random
import math

name_set = {}
chain_cache = {}

# Markov chain weighting exponent
CHAIN_WEIGHT_EXPONENT = 1.3


def generate_name(name_type):
    """Generate a name using a Markov chain."""
    chain = markov_chain(name_type)
    if chain:
        return markov_name(chain)
    return ''


def name_list(name_type, n_of):
    """Generate multiple names."""
    names = []
    for _ in range(n_of):
        names.append(generate_name(name_type))
    return names


def markov_chain(name_type):
    """Get or construct a Markov chain for the given type."""
    if name_type in chain_cache:
        return chain_cache[name_type]
    
    if name_type in name_set:
        chain = construct_chain(name_set[name_type])
        if chain:
            chain_cache[name_type] = chain
            return chain
    
    return None


def construct_chain(name_list):
    """Construct a Markov chain from a list of names."""
    chain = {}
    
    for name_string in name_list:
        names = name_string.split()
        chain = incr_chain(chain, 'parts', len(names))
        
        for name in names:
            chain = incr_chain(chain, 'name_len', len(name))
            
            c = name[0]
            chain = incr_chain(chain, 'initial', c)
            
            last_c = c
            for i in range(1, len(name)):
                c = name[i]
                chain = incr_chain(chain, last_c, c)
                last_c = c
    
    return scale_chain(chain)


def incr_chain(chain, key, token):
    """Increment the count for a token in the chain."""
    if key not in chain:
        chain[key] = {}
    
    if token not in chain[key]:
        chain[key][token] = 0
    
    chain[key][token] += 1
    return chain


def scale_chain(chain):
    """Scale the chain weights."""
    table_len = {}
    
    for key in chain:
        table_len[key] = 0
        
        for token in chain[key]:
            count = chain[key][token]
            weighted = int(math.pow(count, CHAIN_WEIGHT_EXPONENT))
            
            chain[key][token] = weighted
            table_len[key] += weighted
    
    chain['table_len'] = table_len
    return chain


def markov_name(chain):
    """Generate a name from a Markov chain."""
    parts = select_link(chain, 'parts')
    names = []
    
    for _ in range(parts):
        name_len = select_link(chain, 'name_len')
        c = select_link(chain, 'initial')
        name = c
        last_c = c
        
        while len(name) < name_len:
            c = select_link(chain, last_c)
            name += c
            last_c = c
        
        names.append(name)
    
    return ' '.join(names)


def select_link(chain, key):
    """Select a random token from the chain."""
    length = chain['table_len'][key]
    idx = random.randint(0, length - 1)
    
    t = 0
    for token in chain[key]:
        t += chain[key][token]
        if idx < t:
            # Convert to string if it's an integer (for name_len and parts)
            if isinstance(token, int):
                return token
            return token
    
    return '-'


if __name__ == '__main__':
    # Example usage
    import sys
    import os
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and load data
    import egyptian_set
    egyptian_set.load_egyptian_set()
    
    print("Generating 10 Egyptian names:")
    for name in name_list('egyptian', 10):
        print(f"  {name}")
    sys.stdout.flush()
