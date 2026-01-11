"""
warrior_data.py
written and released to the public domain by drow <drow@bin.sh>
http://creativecommons.org/publicdomain/zero/1.0/

Python conversion
"""

import generator


def load_warrior_data():
    """Load warrior generation data."""
    generator.gen_data['warrior'] = [
        'A {gender} {race} warrior, wearing {armor} and wielding {weapon}.'
    ]
    
    generator.gen_data['gender'] = [
        'male', 'female'
    ]
    
    generator.gen_data['race'] = {
        '1-3': 'human',
        '4-5': 'dwarf',
        '6': 'elf'
    }
    
    generator.gen_data['armor'] = {
        '01-50': 'leather armor',
        '51-90': 'chainmail',
        '91-00': 'plate armor'
    }
    
    generator.gen_data['weapon'] = [
        '{melee_weapon}',
        '{melee_weapon} and a shield',
        'twin blades',
        '{ranged_weapon}'
    ]
    
    generator.gen_data['melee_weapon'] = [
        'a battleaxe', 'a mace', 'a spear', 'a sword'
    ]
    
    generator.gen_data['ranged_weapon'] = [
        'a longbow and arrows', 'a heavy crossbow'
    ]


if __name__ == '__main__':
    load_warrior_data()
    print("Warrior data loaded successfully")
