#!/usr/bin/env python3
"""
dungeon.py

Random Dungeon Generator by drow
http://donjon.bin.sh/

This code is provided under the
Creative Commons Attribution-NonCommercial 3.0 Unported License
http://creativecommons.org/licenses/by-nc/3.0/

Python conversion
"""

import random
import math
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict

# Cell bit flags
NOTHING = 0x00000000
BLOCKED = 0x00000001
ROOM = 0x00000002
CORRIDOR = 0x00000004
PERIMETER = 0x00000010
ENTRANCE = 0x00000020
ROOM_ID = 0x0000FFC0

ARCH = 0x00010000
DOOR = 0x00020000
LOCKED = 0x00040000
TRAPPED = 0x00080000
SECRET = 0x00100000
PORTC = 0x00200000
STAIR_DN = 0x00400000
STAIR_UP = 0x00800000

LABEL = 0xFF000000

OPENSPACE = ROOM | CORRIDOR
DOORSPACE = ARCH | DOOR | LOCKED | TRAPPED | SECRET | PORTC
ESPACE = ENTRANCE | DOORSPACE | 0xFF000000
STAIRS = STAIR_DN | STAIR_UP

BLOCK_ROOM = BLOCKED | ROOM
BLOCK_CORR = BLOCKED | PERIMETER | CORRIDOR
BLOCK_DOOR = BLOCKED | DOORSPACE

# Directions
DI = {'north': -1, 'south': 1, 'west': 0, 'east': 0}
DJ = {'north': 0, 'south': 0, 'west': -1, 'east': 1}
DIRS = ['north', 'south', 'west', 'east']

OPPOSITE = {
    'north': 'south',
    'south': 'north',
    'west': 'east',
    'east': 'west'
}

# Dungeon and corridor layouts
DUNGEON_LAYOUT = {
    'Box': [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
    'Cross': [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
}

CORRIDOR_LAYOUT = {
    'Labyrinth': 0,
    'Bent': 50,
    'Straight': 100,
}

# Map styles
MAP_STYLE = {
    'Standard': {
        'fill': (0, 0, 0),
        'open': (255, 255, 255),
        'open_grid': (204, 204, 204),
    },
}


def hex_to_rgb(hex_str):
    """Convert hex color string to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


class DungeonGenerator:
    """Random dungeon generator."""
    
    def __init__(self, **opts):
        """Initialize dungeon generator with options."""
        self.seed = opts.get('seed', None)
        self.n_rows = opts.get('n_rows', 39)
        self.n_cols = opts.get('n_cols', 39)
        self.dungeon_layout = opts.get('dungeon_layout', 'None')
        self.room_min = opts.get('room_min', 3)
        self.room_max = opts.get('room_max', 9)
        self.room_layout = opts.get('room_layout', 'Scattered')
        self.corridor_layout = opts.get('corridor_layout', 'Bent')
        self.remove_deadends = opts.get('remove_deadends', 50)
        self.add_stairs = opts.get('add_stairs', 2)
        self.map_style = opts.get('map_style', 'Standard')
        self.cell_size = opts.get('cell_size', 18)
        
        # Initialize
        if self.seed is not None:
            random.seed(self.seed)
        
        self.n_i = self.n_rows // 2
        self.n_j = self.n_cols // 2
        self.n_rows = self.n_i * 2
        self.n_cols = self.n_j * 2
        self.max_row = self.n_rows - 1
        self.max_col = self.n_cols - 1
        self.n_rooms = 0
        
        self.room_base = (self.room_min + 1) // 2
        self.room_radix = (self.room_max - self.room_min) // 2 + 1
        
        self.cell = None
        self.rooms = []
        self.doors = []
        self.stairs_list = []
    
    def generate(self):
        """Generate the dungeon."""
        self.init_cells()
        self.emplace_rooms()
        self.open_rooms()
        self.label_rooms()
        self.corridors()
        if self.add_stairs:
            self.emplace_stairs()
        self.clean_dungeon()
        return self
    
    def init_cells(self):
        """Initialize the cell grid."""
        self.cell = [[NOTHING for _ in range(self.n_cols + 1)] 
                     for _ in range(self.n_rows + 1)]
        
        # Apply mask if specified
        if self.dungeon_layout in DUNGEON_LAYOUT:
            self.mask_cells(DUNGEON_LAYOUT[self.dungeon_layout])
        elif self.dungeon_layout == 'Round':
            self.round_mask()
    
    def mask_cells(self, mask):
        """Apply a mask pattern to cells."""
        r_x = len(mask) / (self.n_rows + 1)
        c_x = len(mask[0]) / (self.n_cols + 1)
        
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                if not mask[int(r * r_x)][int(c * c_x)]:
                    self.cell[r][c] = BLOCKED
    
    def round_mask(self):
        """Apply a circular mask to cells."""
        center_r = self.n_rows / 2
        center_c = self.n_cols / 2
        
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                d = math.sqrt((r - center_r)**2 + (c - center_c)**2)
                if d > center_c:
                    self.cell[r][c] = BLOCKED
    
    def emplace_rooms(self):
        """Place rooms in the dungeon."""
        if self.room_layout == 'Packed':
            self.pack_rooms()
        else:
            self.scatter_rooms()
    
    def pack_rooms(self):
        """Pack rooms in a grid pattern."""
        for i in range(self.n_i):
            r = (i * 2) + 1
            for j in range(self.n_j):
                c = (j * 2) + 1
                
                if self.cell[r][c] & ROOM:
                    continue
                if (i == 0 or j == 0) and random.randint(0, 1):
                    continue
                
                proto = {'i': i, 'j': j}
                self.emplace_room(proto)
    
    def scatter_rooms(self):
        """Scatter rooms randomly."""
        n_rooms = self.alloc_rooms()
        for _ in range(n_rooms):
            self.emplace_room()
    
    def alloc_rooms(self):
        """Calculate number of rooms to create."""
        dungeon_area = self.n_cols * self.n_rows
        room_area = self.room_max * self.room_max
        return dungeon_area // room_area
    
    def emplace_room(self, proto=None):
        """Place a single room."""
        if self.n_rooms == 999:
            return
        
        if proto is None:
            proto = {}
        
        # Set room dimensions
        proto = self.set_room(proto)
        
        # Calculate boundaries
        r1 = (proto['i'] * 2) + 1
        c1 = (proto['j'] * 2) + 1
        r2 = ((proto['i'] + proto['height']) * 2) - 1
        c2 = ((proto['j'] + proto['width']) * 2) - 1
        
        if r1 < 1 or r2 > self.max_row:
            return
        if c1 < 1 or c2 > self.max_col:
            return
        
        # Check for collisions
        hit = self.sound_room(r1, c1, r2, c2)
        if hit.get('blocked'):
            return
        
        hit_list = [k for k in hit.keys() if k != 'blocked']
        if len(hit_list) > 0:
            return
        
        # Place the room
        room_id = self.n_rooms + 1
        self.n_rooms = room_id
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if self.cell[r][c] & ENTRANCE:
                    self.cell[r][c] &= ~ESPACE
                elif self.cell[r][c] & PERIMETER:
                    self.cell[r][c] &= ~PERIMETER
                self.cell[r][c] |= ROOM | (room_id << 6)
        
        height = ((r2 - r1) + 1) * 10
        width = ((c2 - c1) + 1) * 10
        
        room_data = {
            'id': room_id, 'row': r1, 'col': c1,
            'north': r1, 'south': r2, 'west': c1, 'east': c2,
            'height': height, 'width': width, 'area': height * width,
            'doors': {}
        }
        
        # Ensure rooms list is large enough
        while len(self.rooms) <= room_id:
            self.rooms.append(None)
        self.rooms[room_id] = room_data
        
        # Block corridors from room boundary
        for r in range(r1 - 1, r2 + 2):
            if not (self.cell[r][c1 - 1] & (ROOM | ENTRANCE)):
                self.cell[r][c1 - 1] |= PERIMETER
            if not (self.cell[r][c2 + 1] & (ROOM | ENTRANCE)):
                self.cell[r][c2 + 1] |= PERIMETER
        
        for c in range(c1 - 1, c2 + 2):
            if not (self.cell[r1 - 1][c] & (ROOM | ENTRANCE)):
                self.cell[r1 - 1][c] |= PERIMETER
            if not (self.cell[r2 + 1][c] & (ROOM | ENTRANCE)):
                self.cell[r2 + 1][c] |= PERIMETER
    
    def set_room(self, proto):
        """Set room position and size."""
        base = self.room_base
        radix = self.room_radix
        
        if 'height' not in proto:
            if 'i' in proto:
                a = self.n_i - base - proto['i']
                a = max(0, a)
                r = min(a, radix)
                proto['height'] = random.randint(0, r - 1) + base if r > 0 else base
            else:
                proto['height'] = random.randint(0, radix - 1) + base
        
        if 'width' not in proto:
            if 'j' in proto:
                a = self.n_j - base - proto['j']
                a = max(0, a)
                r = min(a, radix)
                proto['width'] = random.randint(0, r - 1) + base if r > 0 else base
            else:
                proto['width'] = random.randint(0, radix - 1) + base
        
        if 'i' not in proto:
            proto['i'] = random.randint(0, self.n_i - proto['height'] - 1)
        
        if 'j' not in proto:
            proto['j'] = random.randint(0, self.n_j - proto['width'] - 1)
        
        return proto
    
    def sound_room(self, r1, c1, r2, c2):
        """Check for room collisions."""
        hit = {}
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if self.cell[r][c] & BLOCKED:
                    return {'blocked': True}
                if self.cell[r][c] & ROOM:
                    room_id = (self.cell[r][c] & ROOM_ID) >> 6
                    hit[room_id] = hit.get(room_id, 0) + 1
        
        return hit
    
    def open_rooms(self):
        """Create door openings for all rooms."""
        self.connect = {}
        
        for room_id in range(1, self.n_rooms + 1):
            if room_id < len(self.rooms) and self.rooms[room_id]:
                self.open_room(self.rooms[room_id])
        
        del self.connect
    
    def open_room(self, room):
        """Create door openings for a room."""
        sills = self.door_sills(room)
        if not sills:
            return
        
        n_opens = self.alloc_opens(room)
        
        for _ in range(n_opens):
            if not sills:
                break
            
            sill = sills.pop(random.randint(0, len(sills) - 1))
            door_r, door_c = sill['door_r'], sill['door_c']
            
            if self.cell[door_r][door_c] & DOORSPACE:
                continue
            
            out_id = sill.get('out_id')
            if out_id:
                connect = ','.join(map(str, sorted([room['id'], out_id])))
                if connect in self.connect:
                    self.connect[connect] += 1
                    continue
                self.connect[connect] = 1
            
            open_r, open_c = sill['sill_r'], sill['sill_c']
            open_dir = sill['dir']
            
            # Open door
            for x in range(3):
                r = open_r + (DI[open_dir] * x)
                c = open_c + (DJ[open_dir] * x)
                self.cell[r][c] &= ~PERIMETER
                self.cell[r][c] |= ENTRANCE
            
            door_type = self.door_type()
            door = {'row': door_r, 'col': door_c}
            
            if door_type == ARCH:
                self.cell[door_r][door_c] |= ARCH
                door['key'] = 'arch'
                door['type'] = 'Archway'
            elif door_type == DOOR:
                self.cell[door_r][door_c] |= DOOR
                self.cell[door_r][door_c] |= (ord('o') << 24)
                door['key'] = 'open'
                door['type'] = 'Unlocked Door'
            elif door_type == LOCKED:
                self.cell[door_r][door_c] |= LOCKED
                self.cell[door_r][door_c] |= (ord('x') << 24)
                door['key'] = 'lock'
                door['type'] = 'Locked Door'
            elif door_type == TRAPPED:
                self.cell[door_r][door_c] |= TRAPPED
                self.cell[door_r][door_c] |= (ord('t') << 24)
                door['key'] = 'trap'
                door['type'] = 'Trapped Door'
            elif door_type == SECRET:
                self.cell[door_r][door_c] |= SECRET
                self.cell[door_r][door_c] |= (ord('s') << 24)
                door['key'] = 'secret'
                door['type'] = 'Secret Door'
            elif door_type == PORTC:
                self.cell[door_r][door_c] |= PORTC
                self.cell[door_r][door_c] |= (ord('#') << 24)
                door['key'] = 'portc'
                door['type'] = 'Portcullis'
            
            if out_id:
                door['out_id'] = out_id
            
            if open_dir not in room['doors']:
                room['doors'][open_dir] = []
            room['doors'][open_dir].append(door)
    
    def alloc_opens(self, room):
        """Calculate number of door openings for a room."""
        room_h = ((room['south'] - room['north']) / 2) + 1
        room_w = ((room['east'] - room['west']) / 2) + 1
        flumph = int(math.sqrt(room_w * room_h))
        n_opens = flumph + random.randint(0, flumph - 1)
        return n_opens
    
    def door_sills(self, room):
        """Get list of potential door locations."""
        sills = []
        
        if room['north'] >= 3:
            for c in range(room['west'], room['east'] + 1, 2):
                sill = self.check_sill(room, room['north'], c, 'north')
                if sill:
                    sills.append(sill)
        
        if room['south'] <= (self.n_rows - 3):
            for c in range(room['west'], room['east'] + 1, 2):
                sill = self.check_sill(room, room['south'], c, 'south')
                if sill:
                    sills.append(sill)
        
        if room['west'] >= 3:
            for r in range(room['north'], room['south'] + 1, 2):
                sill = self.check_sill(room, r, room['west'], 'west')
                if sill:
                    sills.append(sill)
        
        if room['east'] <= (self.n_cols - 3):
            for r in range(room['north'], room['south'] + 1, 2):
                sill = self.check_sill(room, r, room['east'], 'east')
                if sill:
                    sills.append(sill)
        
        random.shuffle(sills)
        return sills
    
    def check_sill(self, room, sill_r, sill_c, direction):
        """Check if a sill location is valid for a door."""
        door_r = sill_r + DI[direction]
        door_c = sill_c + DJ[direction]
        door_cell = self.cell[door_r][door_c]
        
        if not (door_cell & PERIMETER):
            return None
        if door_cell & BLOCK_DOOR:
            return None
        
        out_r = door_r + DI[direction]
        out_c = door_c + DJ[direction]
        out_cell = self.cell[out_r][out_c]
        
        if out_cell & BLOCKED:
            return None
        
        out_id = None
        if out_cell & ROOM:
            out_id = (out_cell & ROOM_ID) >> 6
            if out_id == room['id']:
                return None
        
        return {
            'sill_r': sill_r, 'sill_c': sill_c, 'dir': direction,
            'door_r': door_r, 'door_c': door_c, 'out_id': out_id
        }
    
    def door_type(self):
        """Randomly select a door type."""
        i = random.randint(0, 109)
        
        if i < 15:
            return ARCH
        elif i < 60:
            return DOOR
        elif i < 75:
            return LOCKED
        elif i < 90:
            return TRAPPED
        elif i < 100:
            return SECRET
        else:
            return PORTC
    
    def label_rooms(self):
        """Add room ID labels to cells."""
        for room_id in range(1, self.n_rooms + 1):
            if room_id >= len(self.rooms) or not self.rooms[room_id]:
                continue
            
            room = self.rooms[room_id]
            label = str(room['id'])
            label_r = (room['north'] + room['south']) // 2
            label_c = (room['west'] + room['east'] - len(label)) // 2 + 1
            
            for i, char in enumerate(label):
                self.cell[label_r][label_c + i] |= (ord(char) << 24)
    
    def corridors(self):
        """Generate corridors between rooms."""
        for i in range(1, self.n_i):
            r = (i * 2) + 1
            for j in range(1, self.n_j):
                c = (j * 2) + 1
                
                if self.cell[r][c] & CORRIDOR:
                    continue
                self.tunnel(i, j)
    
    def tunnel(self, i, j, last_dir=None):
        """Recursively create corridors."""
        dirs = self.tunnel_dirs(last_dir)
        
        for direction in dirs:
            if self.open_tunnel(i, j, direction):
                next_i = i + DI[direction]
                next_j = j + DJ[direction]
                self.tunnel(next_i, next_j, direction)
    
    def tunnel_dirs(self, last_dir=None):
        """Get tunnel direction order."""
        p = CORRIDOR_LAYOUT.get(self.corridor_layout, 0)
        dirs = DIRS.copy()
        random.shuffle(dirs)
        
        if last_dir and p:
            if random.randint(0, 99) < p:
                dirs.insert(0, last_dir)
        
        return dirs
    
    def open_tunnel(self, i, j, direction):
        """Try to open a tunnel in a direction."""
        this_r = (i * 2) + 1
        this_c = (j * 2) + 1
        next_r = ((i + DI[direction]) * 2) + 1
        next_c = ((j + DJ[direction]) * 2) + 1
        mid_r = (this_r + next_r) // 2
        mid_c = (this_c + next_c) // 2
        
        if self.sound_tunnel(mid_r, mid_c, next_r, next_c):
            return self.delve_tunnel(this_r, this_c, next_r, next_c)
        return False
    
    def sound_tunnel(self, mid_r, mid_c, next_r, next_c):
        """Check if tunnel location is valid."""
        if next_r < 0 or next_r > self.n_rows:
            return False
        if next_c < 0 or next_c > self.n_cols:
            return False
        
        r1, r2 = sorted([mid_r, next_r])
        c1, c2 = sorted([mid_c, next_c])
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if self.cell[r][c] & BLOCK_CORR:
                    return False
        
        return True
    
    def delve_tunnel(self, this_r, this_c, next_r, next_c):
        """Create a tunnel between two points."""
        r1, r2 = sorted([this_r, next_r])
        c1, c2 = sorted([this_c, next_c])
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                self.cell[r][c] &= ~ENTRANCE
                self.cell[r][c] |= CORRIDOR
        
        return True
    
    def emplace_stairs(self):
        """Add stairs to the dungeon."""
        if self.add_stairs <= 0:
            return
        
        ends = self.stair_ends()
        if not ends:
            return
        
        for i in range(self.add_stairs):
            if not ends:
                break
            
            stair = ends.pop(random.randint(0, len(ends) - 1))
            r, c = stair['row'], stair['col']
            stair_type = 0 if i < 2 else random.randint(0, 1)
            
            if stair_type == 0:
                self.cell[r][c] |= STAIR_DN
                self.cell[r][c] |= (ord('d') << 24)
                stair['key'] = 'down'
            else:
                self.cell[r][c] |= STAIR_UP
                self.cell[r][c] |= (ord('u') << 24)
                stair['key'] = 'up'
            
            self.stairs_list.append(stair)
    
    def stair_ends(self):
        """Find potential stair locations."""
        ends = []
        
        # Stair end patterns (simplified - full patterns omitted for brevity)
        stair_end = {
            'north': {'walled': [[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1],[0,1],[1,1]],
                     'corridor': [[0,0],[1,0],[2,0]]},
            'south': {'walled': [[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1]],
                     'corridor': [[0,0],[-1,0],[-2,0]]},
            'west': {'walled': [[-1,1],[-1,0],[-1,-1],[0,-1],[1,-1],[1,0],[1,1]],
                    'corridor': [[0,0],[0,1],[0,2]]},
            'east': {'walled': [[-1,-1],[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1]],
                    'corridor': [[0,0],[0,-1],[0,-2]]},
        }
        
        for i in range(self.n_i):
            r = (i * 2) + 1
            for j in range(self.n_j):
                c = (j * 2) + 1
                
                if self.cell[r][c] != CORRIDOR:
                    continue
                if self.cell[r][c] & STAIRS:
                    continue
                
                for direction, check in stair_end.items():
                    if self.check_tunnel_pattern(r, c, check):
                        ends.append({'row': r, 'col': c})
                        break
        
        return ends
    
    def check_tunnel_pattern(self, r, c, check):
        """Check if a tunnel matches a pattern."""
        if 'corridor' in check:
            for p in check['corridor']:
                if self.cell[r + p[0]][c + p[1]] != CORRIDOR:
                    return False
        
        if 'walled' in check:
            for p in check['walled']:
                if self.cell[r + p[0]][c + p[1]] & OPENSPACE:
                    return False
        
        return True
    
    def clean_dungeon(self):
        """Final cleanup of dungeon."""
        if self.remove_deadends:
            self.remove_deadends_func()
        self.fix_doors()
        self.empty_blocks()
    
    def remove_deadends_func(self):
        """Remove dead-end corridors."""
        p = self.remove_deadends
        if not p:
            return
        
        all_deadends = (p == 100)
        
        # Close end patterns
        close_end = {
            'north': {'walled': [[0,-1],[1,-1],[1,0],[1,1],[0,1]],
                     'close': [[0,0]], 'recurse': [-1,0]},
            'south': {'walled': [[0,-1],[-1,-1],[-1,0],[-1,1],[0,1]],
                     'close': [[0,0]], 'recurse': [1,0]},
            'west': {'walled': [[-1,0],[-1,1],[0,1],[1,1],[1,0]],
                    'close': [[0,0]], 'recurse': [0,-1]},
            'east': {'walled': [[-1,0],[-1,-1],[0,-1],[1,-1],[1,0]],
                    'close': [[0,0]], 'recurse': [0,1]},
        }
        
        for i in range(self.n_i):
            r = (i * 2) + 1
            for j in range(self.n_j):
                c = (j * 2) + 1
                
                if not (self.cell[r][c] & OPENSPACE):
                    continue
                if self.cell[r][c] & STAIRS:
                    continue
                if not all_deadends and random.randint(0, 99) >= p:
                    continue
                
                self.collapse(r, c, close_end)
    
    def collapse(self, r, c, xc):
        """Recursively collapse dead-ends."""
        if not (self.cell[r][c] & OPENSPACE):
            return
        
        for direction, check in xc.items():
            if self.check_tunnel_pattern(r, c, check):
                for p in check['close']:
                    self.cell[r + p[0]][c + p[1]] = NOTHING
                
                if 'recurse' in check:
                    p = check['recurse']
                    self.collapse(r + p[0], c + p[1], xc)
    
    def fix_doors(self):
        """Fix door lists after cleanup."""
        fixed = [[False] * (self.n_cols + 1) for _ in range(self.n_rows + 1)]
        self.doors = []
        
        for room in self.rooms:
            if not room:
                continue
            
            new_doors = {}
            for direction, door_list in room.get('doors', {}).items():
                shiny = []
                for door in door_list:
                    door_r, door_c = door['row'], door['col']
                    if not (self.cell[door_r][door_c] & OPENSPACE):
                        continue
                    
                    if not fixed[door_r][door_c]:
                        out_id = door.get('out_id')
                        if out_id and out_id < len(self.rooms) and self.rooms[out_id]:
                            out_dir = OPPOSITE[direction]
                            if 'doors' not in self.rooms[out_id]:
                                self.rooms[out_id]['doors'] = {}
                            if out_dir not in self.rooms[out_id]['doors']:
                                self.rooms[out_id]['doors'][out_dir] = []
                            self.rooms[out_id]['doors'][out_dir].append(door)
                        
                        shiny.append(door)
                        self.doors.append(door)
                        fixed[door_r][door_c] = True
                
                if shiny:
                    new_doors[direction] = shiny
            
            room['doors'] = new_doors
    
    def empty_blocks(self):
        """Remove blocked cells."""
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                if self.cell[r][c] & BLOCKED:
                    self.cell[r][c] = NOTHING
    
    def save_image(self, filename=None):
        """Generate and save dungeon image."""
        if filename is None:
            filename = f"{self.seed if self.seed else 'dungeon'}.gif"
        
        # Calculate image dimensions
        width = (self.n_cols + 1) * self.cell_size + 1
        height = (self.n_rows + 1) * self.cell_size + 1
        
        # Get color palette
        style = MAP_STYLE.get(self.map_style, MAP_STYLE['Standard'])
        fill_color = style.get('fill', (0, 0, 0))
        open_color = style.get('open', (255, 255, 255))
        
        # Create image
        img = Image.new('RGB', (width, height), fill_color)
        draw = ImageDraw.Draw(img)
        
        # Draw open spaces
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                if self.cell[r][c] & OPENSPACE:
                    x1 = c * self.cell_size
                    y1 = r * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    draw.rectangle([x1, y1, x2, y2], fill=open_color)
        
        # Draw walls
        wall_color = fill_color
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                if self.cell[r][c] & OPENSPACE:
                    x1 = c * self.cell_size
                    y1 = r * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    
                    # Draw walls where adjacent cells are not open
                    if not (self.cell[r-1][c] & OPENSPACE if r > 0 else False):
                        draw.line([x1, y1, x2, y1], fill=wall_color)
                    if not (self.cell[r][c-1] & OPENSPACE if c > 0 else False):
                        draw.line([x1, y1, x1, y2], fill=wall_color)
                    if not (self.cell[r][c+1] & OPENSPACE if c < self.n_cols else False):
                        draw.line([x2, y1, x2, y2], fill=wall_color)
                    if not (self.cell[r+1][c] & OPENSPACE if r < self.n_rows else False):
                        draw.line([x1, y2, x2, y2], fill=wall_color)
        
        # Draw room labels
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols + 1):
                if self.cell[r][c] & OPENSPACE:
                    char_code = (self.cell[r][c] >> 24) & 0xFF
                    if char_code and chr(char_code).isdigit():
                        x = c * self.cell_size + self.cell_size // 3
                        y = r * self.cell_size + self.cell_size // 3
                        draw.text((x, y), chr(char_code), fill=fill_color)
        
        # Save image
        img.save(filename)
        return filename


def main():
    """Main function for command-line usage."""
    import time
    
    seed = int(time.time())
    print(f"Generating dungeon with seed {seed}")
    
    dungeon = DungeonGenerator(
        seed=seed,
        n_rows=39,
        n_cols=39,
        dungeon_layout='None',
        room_min=3,
        room_max=9,
        room_layout='Scattered',
        corridor_layout='Bent',
        remove_deadends=50,
        add_stairs=2,
        map_style='Standard',
        cell_size=18
    )
    
    dungeon.generate()
    filename = dungeon.save_image()
    print(f"Dungeon saved to {filename}")
    print(f"  Rooms: {dungeon.n_rooms}")
    print(f"  Doors: {len(dungeon.doors)}")
    print(f"  Stairs: {len(dungeon.stairs_list)}")


if __name__ == '__main__':
    main()
