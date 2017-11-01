import tdl
import colors
import math
import textwrap
import sys
import os
import ast
import shelve
import datetime
import re
import dictionaries as dicts

# Global variables
LIMIT_FPS = 30
MAX_RECURSE = 800

# actual size of the window in characters (or 960x720 pixels)
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 50

# size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 38

# height constants
MAX_HEIGHT = 100
MIN_HEIGHT = 0

# stat bars
BAR_LENGTH = 20
PANEL_HEIGHT = 12
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

# message log
MSG_X = BAR_LENGTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_LENGTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

# level up info
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 30

# fov constants
FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
WORLD_FOV_RAD = 4
TORCH_RADIUS = 10

# combat variables
# Each action during combat takes a different amount of time, which is modified by equip load, dex, the weight of the
# item used, etc. The base values for each type of action are given here in frames (20 fps):
# number of frames for a light attack to complete
L_ATT_SPEED = 20
# number of frames for a heavy attack to complete
H_ATT_SPEED = 40
# number of frames to land a parry (starts immediately)
PARRY_SPEED = 15
# number of frames to begin blocking (can be held indefinitely)
BLOCK_SPEED = 10
# number of frames to move one tile (default is 1 tile/second)
MOVE_SPEED = 20
# number of frames to turn clockwise or counterclockwise once
TURN_SPEED = 10
# number of frames that a character is invulnerable while dodging
DODGE_TIME = 8

MAX_ACTION_BUFFER = 10
########################################################################################################################
# Major TODOs                                                                                                          #
########################################################################################################################
# TODO: add real-time gameplay mode
# TODO: selection between "Classic, Apprentice, and Expert" modes
# TODO: magic systems
# TODO: enemy dictionaries, with simple assembly of creatures by choosing sets of stats, ai, and equipment
# TODO: overworld map
# TODO: location sub-map, procedural generation vs. handcrafted
# TODO: equipment dictionaries
# TODO: consumable item dictionaries
# TODO: random-generation of items
# TODO: equipment prefix/suffix/addon/enchantment/upgrade dictionaries and systems
# TODO: level-up systems
# TODO: crafting systems?
# TODO: Dark Cloud style world building?
# TODO: Map-to-image printer?
########################################################################################################################


class Object:
    def __init__(self, x, y, char, name, color, blocks=True,
                 always_visible=False, block_sight=True, fighter=None, item=None, player=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.block_sight = block_sight

        self.fighter = fighter
        # let the fighter component know who owns it
        if self.fighter:
            self.fighter.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.player = player
        if self.player:
            self.player.owner = self

    def move(self, dx, dy):
        global fov_recompute, current_map
        # move by the given amount
        if self.x + dx > MAP_WIDTH - 1 or self.x + dx < 0:
            return
        elif self.y + dy > MAP_HEIGHT - 1 or self.y + dy < 0:
            return
        if current_map[self.x + dx][self.y + dy].interact(self):
            fov_recompute = True
            return
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            if current_map[self.x][self.y].linking:
                change_level(self.x, self.y)
            elif current_map[self.x][self.y].label == "abyss":
                player.fighter.death()
        if self.player:
            fov_recompute = True

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        # return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def draw(self):
        global visible_tiles

        if (self.x, self.y) in visible_tiles:
            # set the color and then draw the character that represents this object at its position
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self):
        # erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def send_to_back(self):
        # make this object be drawn first, so all others appear above it if they're in the same tile
        global objects
        objects.remove(self)
        objects.insert(0, self)


class Item:
    def __init__(self, weight=0, uses=0, equipment=None):
        self.weight = weight
        # if uses = 0, item has unlimited uses
        self.uses = uses

        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self


class Equipment:
    def __init__(self, slot=None, element=None, durability=0, dmg_block=0, equippable_at=None):
        self.slot = slot
        self.element = element
        self.durability = durability
        self.dmg_block = dmg_block
        self.equipped_at = None
        self.equippable_at = equippable_at
        self.is_equipped = False


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None, char=None, vis_color=None, fog_color=None, linking=False, 
        linked_map_num = None, label=None, bg=None, dark_bg=None, player_interaction=None, fighter_interaction=None,
        obj_interaction=None):
        self.blocked = blocked

        # all tiles start unexplored
        self.explored = False

        # by default, if a tile is blocked, it also blocks sight
        if blocked is None:
            block_sight = blocked
        self.block_sight = block_sight

        self.char = char
        self.vis_color = vis_color
        self.fog_color = fog_color
        # declares if tile links to different map
        self.linking = linking
        # delcares which map tile is linked to
        self.linked_map_num = linked_map_num
        self.label = label
        self.bg = bg
        self.dark_bg = dark_bg
        self.player_interaction = player_interaction
        self.fighter_interaction = fighter_interaction
        self.obj_interaction = obj_interaction
        self.open = False

    def interact(self, obj):
        if obj.player is not None:
            if self.player_interaction is not None:
                return getattr(self, self.player_interaction)()
        elif obj.fighter is not None:
            if self.fighter_interaction is not None:
                return getattr(self, self.fighter_interaction)()
        elif obj is not None:
            if self.obj_interaction is not None:
                return getattr(self, self.obj_interaction)()
        else:
            return False

    def open_tile(self):
        # used to toggle open/closed state of doors, chests, etc.
        if not self.open:
            self.open = True
            message("You open the door...", colors.dark_green)
            getattr(self, self.label)()
            return True
        else:
            return False

        # Tile types, calling a function will set the tile to that type
        # Current total: 19
    def default(self):
        self.blocked = False
        self.block_sight = False
        self.char = None
        self.vis_color = colors.black
        self.fog_color = colors.black
        self.linking = False
        self.label = "default"

    def abyss(self):
        self.blocked = False
        self.block_sight = False
        self.char = None
        self.vis_color = colors.black
        self.fog_color = colors.black
        self.linking = False
        self.label = "abyss"

    def bird_nest(self):
        self.blocked = False
        self.block_sight = True
        self.char = chr(177)
        self.vis_color = colors.dark_sepia
        self.fog_color = colors.darker_sepia
        self.linking = False
        self.label = "bird_nest"

    def cave_floor(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.dark_gray
        self.fog_color = colors.darker_gray
        self.linking = False
        self.label = "cave_floor"

    def city(self):
        self.blocked = False
        self.block_sight = False
        self.char = 'o'
        self.vis_color = colors.yellow
        self.fog_color = colors.dark_yellow
        self.linking = True
        self.label = "city"

    def dead_bush(self):
        self.blocked = False
        self.block_sight = False
        self.char = '&'
        self.vis_color = colors.darker_sepia
        self.fog_color = colors.darkest_sepia
        self.linking = False
        self.label = "dead_bush"

    def desert(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(247)
        self.vis_color = colors.yellow
        self.fog_color = colors.desaturated_yellow
        self.linking = False
        self.label = "desert"

    def dirt(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.shingle_fawn
        self.fog_color = colors.west_coast
        self.linking = False
        self.label = "dirt"
        self.bg = None #colors.light_gray
        self.dark_bg = None #colors.gray

    def door_vert(self):
        if self.open:
            self.char = '+'
            self.blocked = False
            self.block_sight = False
        else:
            self.char = '\u2225'
            self.blocked = True
            self.block_sight = True
        self.vis_color = colors.dark_sepia
        self.fog_color = colors.darker_sepia
        self.linking = False
        self.label = "door_vert"
        self.player_interaction = 'open_tile'

    def door_hor(self):
        if self.open:
            self.char = '+'
            self.blocked = False
            self.block_sight = False
        else:
            self.char = '='
            self.blocked = True
            self.block_sight = True
        self.vis_color = colors.dark_sepia
        self.fog_color = colors.darker_sepia
        self.linking = False
        self.label = "door_hor"
        self.player_interaction = 'open_tile'

    def dungeon(self):
        self.blocked = False
        self.block_sight = True
        self.char = '*'
        self.vis_color = colors.darker_sepia
        self.fog_color = colors.darkest_sepia
        self.linking = True
        self.label = "dungeon"

    def entry(self):
        self.blocked = False
        self.block_sight = False
        self.char = '<'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.linking = True
        self.label = "entry"

    def fog_wall(self):
        self.blocked = False
        self.block_sight = True
        if self.open:
            self.char = '.'
        else:
            self.char = '\u203b'
            self.bg = colors.light_gray
            self.dark_bg = colors.gray
        self.vis_color = colors.dark_gray
        self.fog_color = colors.darker_gray
        self.linking = False
        self.label = "fog_wall"
        self.player_interaction = 'open_tile'

    def forest(self):
        self.blocked = False
        self.block_sight = True
        self.char = chr(209)
        self.vis_color = colors.dark_green
        self.fog_color = colors.darker_green
        self.linking = False
        self.label = "forest"

    def ladder(self):
        self.blocked = False
        self.block_sight = False
        self.char = 'H'
        self.vis_color = colors.dark_sepia
        self.fog_color = colors.darker_sepia
        self.linking = True
        self.label = "ladder"

    def marble_floor(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.dark_port_gore
        self.fog_color = colors.black
        self.linking = False
        self.label = "marble_floor"
        self.bg = colors.lighter_gray
        self.dark_bg = colors.light_gray

    def monument(self):
        self.blocked = True
        self.block_sight = False
        self.char = '#'
        self.vis_color = colors.gold
        self.fog_color = colors.golden_tips
        self.linking = False
        self.label = "monument"
        self.bg = colors.light_gray
        self.dark_bg = colors.gray

    def mountain(self):
        self.blocked = True
        self.block_sight = True
        self.char = '^'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.linking = False
        self.label = "mountain"

    def overgrowth(self):
        self.blocked = True
        self.block_sight = True
        self.char = '#'
        self.vis_color = colors.desaturated_green
        self.fog_color = colors.desaturated_amber
        self.linking = False
        self.label = "overgrowth"

    def path(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.darker_amber
        self.fog_color = colors.darkest_amber
        self.linking = False
        self.label = "path"

    def plains(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(240)
        self.vis_color = colors.light_chartreuse
        self.fog_color = colors.chartreuse
        self.linking = False
        self.label = "plains"

    def red_fog(self):
        self.blocked = True
        self.block_sight = True
        self.char = chr(178)
        self.vis_color = colors.dark_crimson
        self.fog_color = colors.darker_crimson
        self.linking = False
        self.label = "red_fog"

    def stairs_up(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2344'
        self.vis_color = colors.old_copper
        self.fog_color = colors.punga
        self.linking = True
        self.label = "stairs_up"

    def stairs_down(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2343'
        self.vis_color = colors.old_copper
        self.fog_color = colors.punga
        self.linking = True
        self.label = "stairs_down"

    def stone_stairs_up(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2344'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.linking = True
        self.label = "stone_stairs_up"

    def stone_stairs_down(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2343'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.linking = True
        self.label = "stone_stairs_down"

    def stone_wall(self):
        self.blocked = True
        self.block_sight = True
        self.char = '#'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.linking = False
        self.label = "stone_wall"
        self.bg = colors.light_gray
        self.dark_bg = colors.gray

    def swamp(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(59)
        self.vis_color = colors.darker_gray
        self.fog_color = colors.darkest_gray
        self.linking = False
        self.label = "swamp"

    def tree(self):
        self.blocked = True
        self.block_sight = True
        self.char = '\u219F'
        self.vis_color = colors.dark_green
        self.fog_color = colors.darker_green
        self.linking = False
        self.label = "tree"
        self.bg = None
        self.dark_bg = None

    def water(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2652'
        self.vis_color = colors.blue
        self.fog_color = colors.dark_blue
        self.linking = False
        self.label = "water"

    def waterfall(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2591'
        self.vis_color = colors.blue
        self.fog_color = colors.dark_blue
        self.linking = False
        self.label = "waterfall"

    def wooden_bridge(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u2630'
        self.vis_color = colors.shingle_fawn
        self.fog_color = colors.west_coast
        self.linking = False
        self.label = "wooden_bridge"

    def wooden_floor(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.shingle_fawn
        self.fog_color = colors.west_coast
        self.linking = False
        self.label = "wooden_floor"

    def wooden_wall(self):
        self.blocked = True
        self.block_sight = True
        self.char = '#'
        self.vis_color = colors.shingle_fawn
        self.fog_color = colors.west_coast
        self.linking = False
        self.label = "wooden_wall"


class WeatherEffects:
    def __init__(self, block_sight=False, char=None, vis_color=None, fog_color=None, label=None):
        # all tiles start unexplored
        self.explored = False
        self.block_sight = block_sight
        self.char = char
        self.vis_color = vis_color
        self.fog_color = fog_color
        self.label = label

    def darkness(self):
        self.block_sight = True
        self.char = chr(255)
        self.vis_color = colors.black
        self.fog_color = colors.black
        self.label = "darkness"

    def fire(self):
        self.block_sight = True
        self.char = chr(177)
        self.vis_color = colors.red
        self.fog_color = colors.dark_red
        self.label = "fire"

    def fog(self):
        self.block_sight = True
        self.char = chr(177)
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray
        self.label = "fog"

    def light_fog(self):
        self.block_sight = False
        self.char = chr(176)
        self.vis_color = colors.light_gray
        self.fog_color = colors.gray
        self.label = "light_fog"

    # rain might alternate between 221 and 222
    def rain(self):
        self.block_sight = False
        self.char = chr(176)
        self.vis_color = colors.blue
        self.fog_color = colors.dark_blue
        self.label = "rain"

    def heavy_rain(self):
        self.block_sight = True
        self.char = chr(177)
        self.vis_color = colors.blue
        self.fog_color = colors.dark_blue
        self.label = "heavy_rain"


    def change_weather(self, new_weather):
        getattr(self, new_weather)()

        '''
        self.block_sight = new_weather.block_sight
        self.char = new_weather.char
        self.vis_color = new_weather.vis_color
        self.fog_color = new_weather.fog_color
        self.label = new_weather.label
        '''

    def remove_weather(self):
        self.block_sight = False
        self.char = None
        self.vis_color = None
        self.fog_color = None
        self.label = None


class Player:
    def __init__(self, hunger=0, covenant=None, souls=0, skillpoints=0):
        self.hunger = hunger
        self.covenant = covenant
        self.souls = souls
        self.skillpoints = skillpoints

    def level_up(self):
        self.owner.fighter.level += 1
        self.skillpoints += 1
        # TODO: implement level-up system


class Fighter:
    # defines something that can take combat actions (e.g. any living character) and gives them combat statistics as
    # well as defining actions they can take during combat
    def __init__(self, vig=0, att=0, end=0, strn=0, dex=0, intl=0, fai=0, luc=0, wil=0, equip_load=0, poise=0, item_dis=0,
                 att_slots=0, right1=None, right2=None, left1=None, left2=None, head=None, chest=None, legs=None,
                 arms=None, ring1=None, ring2=None, neck=None, def_phys=0, def_slash=0, def_blunt=0, def_piercing=0,
                 def_mag=0, def_fire=0, def_lightn=0, def_dark=0, res_bleed=0, res_poison=0, res_frost=0, res_curse=0,
                 bleed_amt=0, poison_amt=0, frost_amt=0, curse_amt=0, facing=None, level=1, soul_value=0, wait_time=0,
                 dodge_frames=DODGE_TIME, inventory=[], blocking=False, death_func=None, ai=None):
        self.vig = vig
        self.att = att
        self.end = end
        self.strn = strn
        self.dex = dex
        self.intl = intl
        self.fai = fai
        self.luc = luc
        self.wil = wil
        self.equip_load = equip_load
        self.poise = poise
        self.item_dis = item_dis
        self.att_slots = att_slots
        self.right1 = right1
        self.right2 = right2
        self.left1 = left1
        self.left2 = left2
        self.head = head
        self.chest = chest
        self.legs = legs
        self.arms = arms
        self.ring1 = ring1
        self.ring2 = ring2
        self.neck = neck
        self.def_phys = def_phys
        self.def_slash = def_slash
        self.def_blunt = def_blunt
        self.def_piercing = def_piercing
        self.def_mag = def_mag
        self.def_fire = def_fire
        self.def_lightn = def_lightn
        self.def_dark = def_dark
        self.res_bleed = res_bleed
        self.res_poison = res_poison
        self.res_frost = res_frost
        self.res_curse = res_curse
        self.bleed_amt = bleed_amt
        self.poison_amt = poison_amt
        self.frost_amt = frost_amt
        self.curse_amt = curse_amt
        self.facing = facing
        self.level = level
        self.soul_value = soul_value
        self.wait_time = wait_time
        self.dodge_frames = dodge_frames
        self.inventory = inventory
        self.action_queue = []
        self.blocking = blocking
        self.death_func = death_func
        self.ai = ai

        # let the ai component know who owns it
        if self.ai:
            self.ai.owner = self

        # Beginning of derived statistics

        # Vigor effects
        # hp = 2E-07x^6 - 7E-05x^5 + 0.0071x^4 - 0.3803x^3 + 9.908x^2 - 81.809x + 533.94
        # 403 hp at base (10) vigor
        # +0.4 res/vig and 0.2 def/vig
        self.hit_points = int(math.ceil(40*self.vig - 1.15*self.vig))
        self.def_lightn += 0.4 * self.vig
        self.def_mag += 0.4 * self.vig
        self.def_fire += 0.4 * self.vig
        self.def_lightn += 0.4 * self.vig
        self.def_dark += 0.4 * self.vig
        self.res_bleed += 0.2 * self.vig
        self.res_poison += 0.2 * self.vig
        self.res_frost += 0.2 * self.vig
        self.res_curse += 0.2 * self.vig

        # Attunement effects
        # TODO: attunement stat effects
        self.att_points = 10

        # Endurance effects
        # stamina = 0.0184x2 + 1.2896x + 78.73
        # 88 stamina at base (10) endurance
        # +1.1 lightning res/end, + 0.4 other res/end, and +0.2 elemental def/end
        self.stamina = math.floor((0.0184 * self.end ** 2) + (1.2896 * self.end) + 78.73)
        self.def_lightn += 1.1 * self.end
        self.def_mag += 0.4 * self.end
        self.def_fire += 0.4 * self.end
        self.def_lightn += 0.4 * self.end
        self.def_dark += 0.4 * self.end
        self.res_bleed += 0.2 * self.end
        self.res_poison += 0.2 * self.end
        self.res_frost += 0.2 * self.end
        self.res_curse += 0.2 * self.end

        # Strength effects
        # TODO: strength stat effects

        # Dexterity effects
        # TODO: show effects of dex on dodge frames
        self.dodge_frames += self.dex

        # Intelligence effects
        # TODO: intelligence stat effects

        # Faith effects
        # TODO: faith stat effects

        # Luck effects
        # TODO: luck stat effects

        # Will effects
        # TODO: will stat effects

        # Other statistics
        self.curr_hp = self.hit_points
        self.curr_ap = self.att_points
        self.curr_sp = self.stamina
        self.curr_r = right1
        self.curr_l = left2

    def handle_attack_move(self, side, type):
        keypress = False
        while not keypress:
            for event in tdl.event.get():
                if event.type == 'KEYDOWN':
                    user_input = event
                    keypress = True

        if user_input.key == 'UP' or user_input.key == 'TEXT' and user_input.text == '8':
            self.attack_handler(side, (0, -1), type)

        elif user_input.key == 'DOWN' or user_input.key == 'TEXT' and user_input.text == '2':
            self.attack_handler(side, (0, 1), type)

        elif user_input.key == 'LEFT' or user_input.key == 'TEXT' and user_input.text == '4':
            self.attack_handler(side, (-1, 0), type)

        elif user_input.key == 'RIGHT' or user_input.key == 'TEXT' and user_input.text == '6':
            self.attack_handler(side, (1, 0), type)

        elif user_input.key == 'TEXT':
            if user_input.text == '7':
                self.attack_handler(side, (-1, -1), type)

            elif user_input.text == '9':
                self.attack_handler(side, (1, -1), type)

            elif user_input.text == '1':
                self.attack_handler(side, (-1, 1), type)

            elif user_input.text == '3':
                self.attack_handler(side, (1, 1), type)

    def attack_handler(self, side, dir, type):
        if side == "right":
            wep = get_equipped_in_slot(self, "right1")
        else:
            wep = get_equipped_in_slot(self, "left1")
        if wep is None:
            wep_name = "Unarmed"
        else:
            wep_name = wep.owner.owner.name
        wep_dict = get_wep_dict(wep_name)
        dmg_type_dict = get_style_from_dict(wep_dict[1][0])
        if type == "normal":
            speed = wep_dict[1][2]
        else:
            speed = wep_dict[1][3]
        self.attack(dmg_type_dict[1][0], speed, dir, type, wep_dict[1][1])

    def attack(self, dmg_type, speed, dir, type, dmg):
        target = None
        for obj in objects:
            if (obj.x - player.x, obj.y - player.y) == dir:
                target = obj
        if target:
            self.att_damage(target.fighter, dmg_type, type, int(dmg))
        self.wait_time += int(speed)

    def dodge(self):
        # TODO: add frames equal to speed plus bonuses to wait_time
        self.wait_time += DODGE_TIME

    def parry(self):
        # TODO: implement parry system
        self.wait_time += PARRY_SPEED
        return self

    def block(self):
        # TODO: implement blocking system
        self.wait_time += BLOCK_SPEED
        return self

    # function is called each frame during combat
    def take_action(self, action):
        if self.wait_time > 0:
            self.wait_time -= 1
        else:
            action()

    def att_damage(self, target, dmg_type, type, dmg):
        died = False
        eff_list = []
        if dmg_type == "slash" or dmg_type == "blunt" or dmg_type == "pierce":
            died = deal_phys_dmg(target, type, dmg, dmg_type)
        if dmg_type == "mag":
            died = deal_mag_dmg(target, type)
        if dmg_type == "fire":
            died = deal_fire_dmg(target, type)
        if dmg_type == "lightn":
            died = deal_lightn_dmg(target, type)
        if dmg_type == "dark":
            died = deal_dark_dmg(target, type)
        if "bleed" in eff_list:
            add_bleed(target, self.curr_r)
        if "poison" in eff_list:
            add_poison(target, self.curr_r)
        if "frost" in eff_list:
            add_frost(target, self.curr_r)
        if "curse" in eff_list:
            add_curse(target, self.curr_r)
        if died:
            message(str(target.owner.name) + "has died!")
            target.death()

    def death(self):
        # TODO: (bug) tile does not appear after removal of creature char, before player action
        if self.death_func:
            func = self.death_func
            func()
        else:
            basic_death(self)

    def equip(self, item):
        success = False
        options = ['Head', 'Chest', 'Arms', 'Legs', 'Neck', 'Right Hand', 'Left Hand', 'Right Ring', 'Left Ring',
                   'Right Hand Quick Slot', 'Left Hand Quick Slot']
        choice = menu("Equip in which slot?", options, SCREEN_WIDTH)
        if choice is None or choice > len(options):
            return
        if choice is 0 and item.equippable_at is 'head':
            self.head = item
            item.equipped_at = 'head'
            success = True
        elif choice is 1 and item.equippable_at is 'chest':
            self.chest = item
            item.equipped_at = 'chest'
            success = True
        elif choice is 2 and item.equippable_at is 'arms':
            self.arms = item
            item.equipped_at = 'arms'
            success = True
        elif choice is 3 and item.equippable_at is 'legs':
            self.legs = item
            item.equipped_at = 'legs'
            success = True
        elif choice is 4 and item.equippable_at is 'neck':
            self.neck = item
            item.equipped_at = 'neck'
            success = True
        elif choice is 5 and item.equippable_at is 'hand':
            self.right1 = item
            item.equipped_at = 'right1'
            success = True
        elif choice is 6 and item.equippable_at is 'hand':
            self.left1 = item
            item.equipped_at = 'left1'
            success = True
        elif choice is 7 and item.equippable_at is 'ring':
            self.ring1 = item
            item.equipped_at = 'ring1'
            success = True
        elif choice is 8 and item.equippable_at is 'ring':
            self.ring2 = item
            item.equipped_at = 'ring2'
            success = True
        elif choice is 9 and item.equippable_at is 'hand':
            self.right2 = item
            item.equipped_at = 'right2'
            success = True
        elif choice is 10 and item.equippable_at is 'hand':
            self.left2 = item
            item.equipped_at = 'left2'
            success = True
        if success:
            item.is_equipped = True
            message('Equipped ' + item.owner.owner.name + ' on ' + options[choice] + '.', colors.light_green)

    # unequip object and show a message about it
    def unequip(self, item):
        if not item.is_equipped:
            return
        message('Unequipped ' + item.owner.owner.name + ' from ' + item.slot + '.', colors.light_green)
        setattr(self, str(item.equipped_at), None)
        item.is_equipped = False
        item.equipped_at = None


class AI:
    def __init__(self, name=None, flag="def", move_set=[]):
        self.name = name
        self.flag = flag
        self.move_set = move_set

    def build_queue(self):
        if self.name is None:
            return
        else:
            self.move_set = dicts['AI'][self.name][self.flag]


#################################
# damage functions
#################################
def deal_phys_dmg(target, type, dmg, dmg_type=None):
    dmg_reduc = target.def_phys / 100
    if target.blocking:
        dmg_reduc += target.curr_l.def_phys / 100
    if dmg_type is "slashing":
        dmg_reduc += target.def_slash / 100
    elif dmg_type is "blunt":
        dmg_reduc += target.def_blunt / 100
    elif dmg_type is "piercing":
        dmg_reduc += target.def_piercing / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    elif type == "special":
        dmg = dmg * 1.5
    final_dmg = math.ceil(dmg - round(dmg_reduc * dmg))
    target.curr_hp -= final_dmg
    if target.curr_hp <= 0:
        return True
    message(str(target.owner.name) + " was dealt " + str(final_dmg) + " damage!")


def deal_mag_dmg(target, curr_wep):
    dmg_reduc = target.def_mag / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_mag - round(dmg_reduc * curr_wep.dmg_mag)
    if target.curr_hp <= 0:
        return True


def deal_fire_dmg(target, curr_wep):
    dmg_reduc = target.def_fire / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_fire - round(dmg_reduc * curr_wep.dmg_fire)
    if target.curr_hp <= 0:
        return True


def deal_lightn_dmg(target, curr_wep):
    dmg_reduc = target.def_lightn / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_lightn - round(dmg_reduc * curr_wep.dmg_lightn)
    if target.curr_hp <= 0:
        return True


def deal_dark_dmg(target, curr_wep):
    dmg_reduc = target.def_dark / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_dark - round(dmg_reduc * curr_wep.dmg_dark)
    if target.curr_hp <= 0:
        return True


#################################
# functions for damage effects
#################################
def add_bleed(target, curr_wep):
    target.bleed_amt += curr_wep.eff_bleed - round(target.res_bleed / 100 * curr_wep.eff_bleed)


def add_poison(target, curr_wep):
    target.poison_amt += curr_wep.eff_poison - round(target.res_poison / 100 * curr_wep.eff_poison)


def add_frost(target, curr_wep):
    target.frost_amt += curr_wep.eff_frost - round(target.res_frost / 100 * curr_wep.eff_frost)


def add_curse(target, curr_wep):
    target.curse_amt += curr_wep.eff_curse - round(target.res_curse / 100 * curr_wep.eff_curse)


############################################
# death functions
############################################
def basic_death(fighter):
    for obj in objects:
        if obj is fighter.owner:
            objects.remove(obj)
            del obj


############################################
# menus and related functions
############################################
def message(new_msg, color=colors.white):
    # split the message, if necessary, across multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # add the new lines as a tuple, with text and color
        game_msgs.append((line, color))
    render_gui()


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
        # TODO: create support for menus with more than 26 options

    # calculate total height for the header (after textwrap) and one line per option
    header_wrapped = textwrap.wrap(header, width)
    header_height = len(header_wrapped)
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = tdl.Console(width, height)

    # print the header, with wrapped text
    window.draw_rect(0, 0, width, height, None, fg=colors.white, bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(0, 0 + i, header_wrapped[i])

    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        window.draw_str(0, y, text, bg=None)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    root.blit(window, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=0.7)
    tdl.flush()

    # present the root console to the player and wait for a key-press
    keypress = False
    while not keypress:
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True

    # convert the ASCII code to an index; if it corresponds to an option, return it
    if user_input.text:
        index = ord(user_input.text) - ord('a')
    else:
        index = -1
    if 0 <= index < len(options):
        return index
    return None

#TODO: full-screen menus


def msgbox(text, width=0):
    # use menu() as a sort of "message box"
    menu(0, 0, text, [], width)


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    panel.draw_rect(x, y, total_width, 1, None, bg=back_color)

    # now render the bar on top
    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)

    # finally, some centered text with the values
    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (total_width - len(text)) // 2
    panel.draw_str(x_centered, y, text, fg=colors.white, bg=None)


############################################
# player-related functions
############################################
def get_equipped_in_slot(char, slot):
    # returns the equipment in a slot, or None if it's empty
    for obj in char.inventory:
        if obj.item.equipment and getattr(char, slot) is not None:
            # obj.item.equipment.slot is obj.item.equipment.is_equipped and slot:
            return obj.item.equipment
    return None


def get_all_equipped(obj):
    # returns a list of equipped items
    if obj is player:
        equipped_list = []
        for object in player.fighter.inventory:
            if object.item.equipment and object.item.equipment.is_equipped:
                equipped_list.append(object)
        return equipped_list
    else:
        return []  # other objects have no equipment (for now)


def get_wep_dict(wep):
    for item in dicts.weapons.items():
        if item[0] == wep:
            return item


def get_style_from_dict(style):
    for item in dicts.weapon_styles.items():
        if item[0] == style:
            return item


############################################
# object-related functions
############################################
def is_blocked(x, y):
    # first test the map tile
    if current_map[x][y].blocked:
        return True

    # now check for any blocking objects
    for obj in objects:
        if obj.fighter and obj.x == x and obj.y == y:
            return True
    return False


def is_facing(self, target):
    if self.owner.fighter.facing is 'N':
        if target.x is self.x and target.y <= self.y:
            return True
        return False
    if self.owner.fighter.facing is 'E':
        if target.x >= self.x and target.y is self.y:
            return True
        return False

    if self.owner.fighter.facing is 'S':
        if target.x is self.x and target.y >= self.y:
            return True
        return False

    if self.owner.fighter.facing is 'W':
        if target.x <= self.x and target.y is self.y:
            return True
        return False


def in_front(self, dir):
    if dir is "north":
        return occupied(self.x, self.y - 1)
    if dir is "east":
        return occupied(self.x + 1, self.y)
    if dir is "south":
        return occupied(self.x, self.y + 1)
    if dir is "west":
        return occupied(self.x - 1, self.y)


def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def occupied(x, y):
    for obj in objects:
        if obj.x is x and obj.y is y:
            return obj
    return None

def adjacent_to(x, y, obj):
    if obj.distance(x, y) <= 2:
        return True
    else:
        return False


def pick_up():
    for obj in objects:
        if obj.x is player.x and obj.y is player.y:
            player.fighter.inventory.append(obj)


############################################
# charater interaction functions
############################################
def close_doors(x, y):
    global current_map

    if current_map[x-1][y-1].label in door_tiles:
        dx = -1
        dy = -1
    elif current_map[x][y-1].label in door_tiles:
        dx = 0
        dy = -1
    elif current_map[x+1][y-1].label in door_tiles:
        dx = 1
        dy = -1
    elif current_map[x+1][y].label in door_tiles:
        dx = 1
        dy = 0
    elif current_map[x+1][y+1].label in door_tiles:
        dx = 1
        dy = 1
    elif current_map[x][y+1].label in door_tiles:
        dx = 0
        dy = 1
    elif current_map[x-1][y+1].label in door_tiles:
        dx = -1
        dy = 1
    elif current_map[x-1][y].label in door_tiles:
        dx = -1
        dy = 0
    if current_map[x + dx][y + dy].open:
        current_map[x + dx][y + dy].open = False
        getattr(current_map[x + dx][y + dy], current_map[x + dx][y + dy].label)()
        message("You close the door...", colors.darker_green)

############################################
# player interaction functions
############################################
def handle_keys(command=None):
    global fov_recompute, game_state, mouse_coord, last_button, map_tiles, fill_mode, right_click_flag, map_num

    keypress = False
    right_click_flag = False
    click_coords = None
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell
        if event.type == 'MOUSEDOWN':
            if event.button == 'RIGHT':
                right_click_flag = True
            click_coords = event.cell

    if game_state == 'simulating':
        keypress = True
        user_input = simulate_key(command)

    if game_state == 'editing':
        if click_coords:
            edit_mode(click_coords)

    if keypress:
        fov_recompute = True
        if user_input.key == 'ENTER' and user_input.alt:
            # Alt+Enter: toggle fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())

        elif user_input.key == 'ESCAPE':
            # game menu
            choice = menu('Game Menu', ['Main Menu', 'Character Screen', 'Help'], 24)
            if choice is 0:
                double_check = menu('Are you sure?', ['No', 'Yes'], 24)
                if double_check:
                    save_game()
                    main_menu()
                else:
                    return
            elif choice is 1:
                # TODO: add character screen
                message("Not yet implemented")
                return
            elif choice is 2:
                # TODO: add help screen
                message("Not yet implemented")
                return

        if game_state == 'playing' or game_state == 'simulating':
            # movement keys
            if user_input.key == 'UP' or user_input.text == '8':
                player.move(0, -1)
                last_button = '8'
                return "MV N"

            elif user_input.key == 'DOWN' or user_input.text == '2':
                player.move(0, 1)
                last_button = '2'
                return "MV S"

            elif user_input.key == 'LEFT' or user_input.text == '4':
                player.move(-1, 0)
                last_button = '4'
                return "MV W"

            elif user_input.key == 'RIGHT' or user_input.text == '6':
                player.move(1, 0)
                last_button = '6'
                return "MV E"

            elif user_input.key == 'TEXT':
                if user_input.text == '7':
                    player.move(-1, -1)
                    last_button = '7'
                    return "MV NW"

                elif user_input.text == '9':
                    player.move(1, -1)
                    last_button = '9'
                    return "MV NE"

                elif user_input.text == '1':
                    player.move(-1, 1)
                    last_button = '1'
                    return "MV SW"

                elif user_input.text == '3':
                    player.move(1, 1)
                    last_button = '3'
                    return "MV SE"

                elif user_input.text =='5':
                    player.move(0, 0)
                    last_button = '5'
                    return "WAIT"

                elif user_input.text == 'i':
                    choice = inventory_menu()
                    if choice is not None and choice < len(player.fighter.inventory):
                        item = player.fighter.inventory[choice]
                        player.fighter.equip(item.item.equipment)

                elif user_input.text == 'e':
                    equip_or_unequip(equipment_menu())

                # force quit key?
                elif user_input.text == 'Q':
                    quit_game()

                elif user_input.text == 'd':
                    drop_menu()

                elif user_input.text == ',':
                    player.fighter.handle_attack_move("left", "special")

                elif user_input.text == '.':
                    player.fighter.handle_attack_move("right", "special")

                elif user_input.text == 'k':
                    player.fighter.handle_attack_move("left", "normal")

                elif user_input.text == 'l':
                    player.fighter.handle_attack_move("right", "normal")

                elif user_input.text == '>':
                    enter_location(player.x, player.y)

                elif user_input.text == '<':
                    exit_location(player.x, player.y)
                elif user_input.text == 'E':
                    # open edit mode
                    message("Entering edit mode! Current tile order: " + str(map_tiles), colors.light_azure)
                    for y in range(MAP_HEIGHT):
                        for x in range(MAP_WIDTH):
                            current_map[x][y].explored = True
                    game_state = 'editing'
                    edit_mode()
                elif user_input.text == 'S':
                    if not debug_flag:
                        save_game()
                    message("Game saved!", colors.green)
                elif user_input.text == 'c':
                    close_doors(player.x, player.y)

        elif game_state == 'editing':
            if user_input.text == 'E':
                game_state = 'playing'
                fill_mode = False
                message("Leaving edit mode!", colors.light_azure)
            elif user_input.text == 'S':
                message("Saving map...", colors.azure)
                save_map()
            elif user_input.text == 'F':
                if not fill_mode:
                    message('Click group of tiles to fill.', colors.light_red)
                    fill_mode = True
                else:
                    message('Leaving fill mode.', colors.light_red)
                    fill_mode = False
            elif user_input.text == 'Q':
                quit_game()
            elif user_input.text == 'N':
                new_map(int(map_num) + 1)
            elif user_input.text == 'R':
                choice = menu('Which tile to remove from map?', map_tiles, 24)
                if choice is not None:
                    if choice < len(map_tiles):
                        map_tiles.remove(map_tiles[choice])
            elif user_input.key == 'PAGEUP':
                temp_map_num = int(map_num) + 1
                try:
                    load_map(temp_map_num)
                except AttributeError:
                    message("Map" + temp_map_num +".txt is empty and could not be loaded!", colors.red)
                else:
                    map_num = temp_map_num
            elif user_input.key == 'PAGEDOWN':
                temp_map_num = int(map_num) - 1
                try:
                    load_map(temp_map_num)
                except AttributeError:
                    message("Map" + temp_map_num +".txt is empty and could not be loaded!", colors.red)
                else:
                    map_num = temp_map_num
    else:
        return 'didnt-take-turn'


def simulate_key(command):
    user_input = tdl.event.KeyDown(key='', text='')
    if command == "MV N":
        user_input.key = 'TEXT'
        user_input.text = u'8'
        return user_input
    if command == "MV NE":
        user_input.key = 'TEXT'
        user_input.text = u'9'
        return user_input
    if command == "MV E":
        user_input.key = 'TEXT'
        user_input.text = u'6'
        return user_input
    if command == "MV SE":
        user_input.key = 'TEXT'
        user_input.text = u'3'
        return user_input
    if command == "MV S":
        user_input.key = 'TEXT'
        user_input.text = u'2'
        return user_input
    if command == "MV SW":
        user_input.key = 'TEXT'
        user_input.text = u'1'
        return user_input
    if command == "MV W":
        user_input.key = 'TEXT'
        user_input.text = u'4'
        return user_input
    if command == "MV NW":
        user_input.key = 'TEXT'
        user_input.text = u'7'
        return user_input
    if command == "WAIT":
        user_input.key = 'TEXT'
        user_input.text = u'5'
        return user_input


def get_names_under_mouse():
    global mouse_coord
    # return a string with the names of all objects under the mouse
    (x, y) = mouse_coord

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]

    names = ', '.join(names)  # join the names, separated by commas
    return names.capitalize()


def get_tile_under_mouse():
    global mouse_coord, current_map
    # return a string with the names of all objects under the mouse
    (x, y) = mouse_coord

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    if x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0 and current_map[x][y].explored == True:
        tile = current_map[x][y].label
    else:
        tile = 'unknown'

    return tile.capitalize()


def inventory_menu():
    if len(player.fighter.inventory) is 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in player.fighter.inventory]
        options.append("Close menu")
    index = menu("Inventory", options, 30)
    return index


# Indices: head-0, chest-1, arms-2, legs-3, neck-4, rring-5, lring-6, rhand-7, lhand-8, rqslot-9, lqslot-10, close-11
def equip_or_unequip(index):
    item_choice = inventory_menu()
    if item_choice is not None:
        item = player.fighter.inventory[item_choice]
    #player.fighter.equip(item)
    '''
    if index is not None and index < len(player.fighter.inventory):
        item_obj = player.fighter.inventory[index]
        if item_obj.item.equipment:
            for obj in player.fighter.inventory:
                if obj == item_obj:
                    if item_obj in get_all_equipped(player):
                        player.fighter.unequip(item_obj.item.equipment)
                    else:
                        player.fighter.equip(item_obj.item.equipment)
    '''


def equipment_menu():
    # TODO: fix equipment menu by showing each equipment slot and what is currently equipped there
    options = []
    if player.fighter.head:
        options.append("Head: " + str(player.fighter.head.owner.owner.name))
    else:
        options.append("Head: None")
    if player.fighter.chest:
        options.append("Chest: " + str(player.fighter.chest.owner.owner.name))
    else:
        options.append("Chest: None")
    if player.fighter.arms:
        options.append("Arms: " + str(player.fighter.arms.owner.owner.name))
    else:
        options.append("Arms: None")
    if player.fighter.legs:
        options.append("Legs: " + str(player.fighter.legs.owner.owner.name))
    else:
        options.append("Legs: None")
    if player.fighter.neck:
        options.append("Neck: " + str(player.fighter.neck.owner.owner.name))
    else:
        options.append("Necks: None")
    if player.fighter.ring1:
        options.append("Right Ring: " + str(player.fighter.ring1.owner.owner.name))
    else:
        options.append("Right Ring: None")
    if player.fighter.ring2:
        options.append("Left Ring: " + str(player.fighter.ring2.owner.owner.name))
    else:
        options.append("Left Ring: None")
    if player.fighter.right1:
        options.append("Right Hand: " + str(player.fighter.right1.owner.owner.name))
    else:
        options.append("Right Hand: None")
    if player.fighter.left1:
        options.append("Left Hand: " + str(player.fighter.left1.owner.owner.name))
    else:
        options.append("Left Hand: None")
    if player.fighter.right2:
        options.append("Right Quickslot: " + str(player.fighter.right2.owner.owner.name))
    else:
        options.append("Right Quickslot: None")
    if player.fighter.left2:
        options.append("Left Quickslot: " + str(player.fighter.left2.owner.owner.name))
    else:
        options.append("Left Quickslot: None")
    options.append("Close menu")
    return menu("Equipment", options, 30)


def skill_menu():
    options = ['abc']
    index = menu("Skills", options, SCREEN_WIDTH)
    return index


def drop_menu():
    return


def next_floor():
    return


############################################
# map and world functions
############################################
def change_map(new_map, label, new_num):
    global current_map, old_map, fov_recompute, map_changed, map_label, map_num

    if current_map:
        old_map = current_map
    current_map = new_map
    fov_recompute = True
    map_changed = True
    map_label = label
    map_num = new_num
    objects = []
    objects.append(player)
    # objects.append(current_map.objects)


def load_map(map_num):
    try:
        change_map(*load_map_from_file(map_num))
    except IOError:
        print("Map number: " + str(map_num), "load_map()")
        quit_game()


def load_map_from_file(map_num):
    global level_map, map_tiles

    level_map = [[Tile(False)
                    for y in range(MAP_HEIGHT)]
                    for x in range(MAP_WIDTH)]

    count = 1
    map_label = None
    map_tiles = None
    file_name = "map" + str(map_num) + ".txt"
    with open(file_name) as f:
        for line in f.readlines():
            if count == 2:
                map_label = line
            elif count == 5:
                map_tiles = ast.literal_eval(line)
            elif count >= 8:
                line = line.replace('\n', '')
                content = line.split(':')
                if count < 3807:
                    if int(content[0]) != -1:
                        getattr(level_map[int(content[1])][int(content[2])], map_tiles[int(content[0])])()
                elif count >= 3810:
                    setattr(level_map[int(content[0])][int(content[1])], "linked_map_num", content[2])
            count += 1

    return(level_map, map_label, map_num)


def change_level(x, y):
    global current_map

    load_map(current_map[x][y].linked_map_num)


############################################
# rendering functions
############################################
# TODO: implement weather effects 
def render_all():
    global fov_recompute, visible_tiles, current_map, map_changed

    if map_changed:
        map_changed = False
        con.clear()
    
    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y, is_visible_tile, fov=FOV_ALGO, radius=WORLD_FOV_RAD, lightWalls=FOV_LIGHT_WALLS)

        # go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = (x, y) in visible_tiles
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if current_map[x][y].explored:
                        con.draw_char(x, y, current_map[x][y].char, current_map[x][y].fog_color, bg=current_map[x][y].dark_bg)
                    else:
                        con.draw_char(x, y, None, None, bg=None)
                else:
                    con.draw_char(x, y, current_map[x][y].char, current_map[x][y].vis_color, bg=current_map[x][y].bg)

                    # since it's visible, explore it
                    current_map[x][y].explored = True


    # draw all objects in the list for current map
    for obj in objects:
        if obj != player:
            obj.draw()
    player.draw()
    
    # blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0)

    render_gui()


def render_gui():
    global player

    # prepare to render the GUI panel
    panel.clear(fg=colors.white, bg=colors.black)

    # print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        panel.draw_str(MSG_X, y, line, bg=None, fg=color)
        y += 1

    # show the player's stats
    render_bar(1, 1, BAR_LENGTH, 'HP', player.fighter.curr_hp, player.fighter.hit_points,
               colors.light_red, colors.darker_red)
    render_bar(1, 3, BAR_LENGTH, 'MP', player.fighter.curr_hp, player.fighter.hit_points,
               colors.light_blue, colors.darker_blue)

    # display names of objects under the mouse
    if mouse_coord:
        panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)
        panel.draw_str(1, -1, get_tile_under_mouse(), bg=None, fg=colors.light_gray)


    # blit the contents of "panel" to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)


def is_visible_tile(x, y):
    global current_map

    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif current_map[x][y].blocked:
        return False
    elif current_map[x][y].block_sight:
        return False
    else:
        return True


def explore_tiles(x, y):
    visible_tiles = tdl.map.quickFOV(x, y, is_visible_tile, fov=FOV_ALGO, radius=WORLD_FOV_RAD, lightWalls=FOV_LIGHT_WALLS)
    for (x, y) in visible_tiles:
        current_map[x][y].explored = True


############################################
# real-time functions
############################################
def update_queue():
    # for each fighter in objects:
    #   for each action in fighter.action_queue:
    #       action.timer -= 1
    #       if action.timer is 0:
    #           action.effect()
    return


############################################
# developer functions
############################################
def edit_mode(click_coords=None):
    global current_map, objects, fov_recompute, map_tiles, fill_mode, map_num, right_click_flag

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if click_coords:
                if x == click_coords[0] and y == click_coords[1]:
                    if fill_mode:
                        fill_area(current_map[x][y].label, x, y)
                    else:
                        if current_map[x][y].label in map_tiles:
                            if not right_click_flag:
                                if map_tiles.index(current_map[x][y].label) + 1 < len(map_tiles):
                                    getattr(current_map[x][y], map_tiles[map_tiles.index(current_map[x][y].label) + 1])()
                                else:
                                    getattr(current_map[x][y], map_tiles[0])()
                            else:
                                if map_tiles.index(current_map[x][y].label) - 1 >= 0:
                                    getattr(current_map[x][y], map_tiles[map_tiles.index(current_map[x][y].label) - 1])()
                                else:
                                    getattr(current_map[x][y], map_tiles[len(map_tiles) - 1])()
                        else:
                            getattr(current_map[x][y], map_tiles[0])()

    fov_recompute = True


def save_map():
    global current_map, objects, map_num, map_tiles, map_label

    map_file = open("map" + str(map_num) + ".txt", "w")
    map_file.write("[MAP LABEL]\n")
    map_file.write(map_label + "\n")
    map_file.write("[TILESET]\n")
    map_file.write(str(map_tiles) + "\n\n")
    map_file.write("[MAP DATA]\n")

    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if current_map[x][y].label is not None:
                map_file.write(str(map_tiles.index(current_map[x][y].label)))
            else:
                map_file.write('-1')
            map_file.write(':' + str(x) + ':' + str(y))
            map_file.write("\n")

    map_file.write("\n")

    map_file.write("[MAP LINKS]\n")
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if current_map[x][y].linking:
                if current_map[x][y].linked_map_num is not None:
                    linked_map_num = current_map[x][y].linked_map_num
                else:
                    linked_map_num = None
                    while linked_map_num is None:
                        message("The tile at (" + str(x) + ", " + str(y) + ") (" + current_map[x][y].label +
                        ") is not linked. Please enter the number of the map you wish to link it to and press enter.", colors.orange)
                        try:
                            input_str = link_tiles(x, y)
                            linked_map_num = int(input_str)
                        except(ValueError):
                            message("Input of " + input_str + " cannot be converted to a number. Please try again.", colors.red)
                    message("The number you selected was " + input_str + ".", colors.azure)
                    current_map[x][y].linked_map_num = linked_map_num
                map_file.write(str(x) + ':' + str(y) + ':' + str(linked_map_num))
                map_file.write("\n")

    map_file.close()
    message("Map saved!", colors.azure)


def fill_area(target_type, x, y):
    global current_map, map_tiles, max_recurse_flag

    replacement_type = menu('Fill are with which tile?', map_tiles, 24)
    if replacement_type is None:
        return
    elif replacement_type == current_map[x][y].label:
        return
    else:
        flood_fill(x, y, target_type, map_tiles[replacement_type])
        if max_recurse_flag:
            message("Reached maximum recursion depth, please fill additional areas seprately.", colors.dark_red)


def flood_fill(x, y, target_type, replacement_type):
    global current_map, recurse_count, max_recurse_flag
    if recurse_count > MAX_RECURSE:
        max_recurse_flag = True
        return
    if x >= MAP_WIDTH or x < 0:
        return
    if y >= MAP_HEIGHT or y < 0:
        return
    if current_map[x][y].label == replacement_type:
        return
    elif current_map[x][y].label != target_type:
        return
    recurse_count += 1
    getattr(current_map[x][y], replacement_type)()
    flood_fill(x, y+1, target_type, replacement_type) # south
    flood_fill(x, y-1, target_type, replacement_type) # north
    flood_fill(x+1, y, target_type, replacement_type) # east
    flood_fill(x-1, y, target_type, replacement_type) # west
    recurse_count -= 1
    return


def link_tiles(x, y):
    num_str = ""
    user_input = tdl.event.key_wait()
    while user_input.key != 'ENTER':
        num_str += user_input.char
        user_input = tdl.event.key_wait()
    return num_str


def new_map(map_num):
    global map_tiles, map_label

    choice = menu("Make a new map of number " + str(map_num) + "?", ["No", "Yes"], 24)

    if choice:
        file_name = "map" + str(map_num) + ".txt"
        try:
            map_file = open(file_name, 'r')
        except IOError:
            map_file = open(file_name, 'w')
            map_file.write("[MAP LABEL]\n")
            map_file.write(map_label + "\n")
            map_file.write("[TILESET]\n")
            map_file.write(str(map_tiles) + "\n\n")
            map_file.write("[MAP DATA]\n")
            map
        else:
            message("A map with the given number already exists.", colors.red)
        map_file.close()
        return True
    return False


############################################
# intro screen functions
############################################()
def main_menu():
    global game_state, game_msgs, objects, map_num, debug_flag, player_action
    # img = libtcod.image_load('menu_background2.png')
    game_state = 'menu'
    game_msgs = []
    objects = []
    map_num = 0
    debug_flag = False
    player_action = None

    while not tdl.event.is_window_closed():
        # show the background image, at twice the regular console resolution
        # libtcod.image_blit_2x(img, 0, 8, 3)

        # show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        # new game
        if choice is 0:
            new_game()
            save_game()
            play_game()
        elif choice is 1:
            if load_game_menu():
                play_game()
        # quit
        elif choice is 2:
            exit()


def new_game():
    global player, debug_flag, game_state

    if game_state != 'simulating':
        choice = menu("Debug mode?", ['Yes', 'No'], 24)
        if choice == 0:
            debug_flag = True

        # generate game seed based on current time
        generate_seed()

    # first create the player out of its components
    player_comp = Player()
    fighter_comp = Fighter(10, 10, 10, 10, 10, 10, 10, 10, 15)
    player = Object(entry_coords[0], entry_coords[1], '@', "Player", colors.gray, fighter=fighter_comp, player=player_comp)
    objects.append(player)

    # load map0.txt and draw to screen
    load_map(0)

    #ai_comp = AI('ConstantAttack')
    #enemy_fighter_comp = Fighter(1, 1, 1, 1, 1, 1, 1, 1, 1, ai=ai_comp)
    #enemy = Object(0, 0, 'T', "Test Enemy", colors.dark_red, fighter=enemy_fighter_comp)
    #objects.append(enemy)

    # a warm welcoming message!
    message('You awaken with a burning desire to act. You feel as if you should recognize this place.', colors.light_flame)

    # initial equipment: a broken sword
    equipment_component = Equipment(slot='hand', durability=10, equippable_at = 'hand')
    item_comp = Item(weight=2, uses=0, equipment=equipment_component)
    sword = Object(0, 0, '-', name="Broken Sword", color=colors.sky, block_sight=False, item=item_comp,
                   always_visible=True)
    player.fighter.inventory.append(sword)
    # player.fighter.equip(equipment_component)


def play_game():
    global game_state

    player_action = None
    game_state = 'playing'

    message("The seed of this game is: " + str(seed) + ".")

    # main loop
    while not tdl.event.is_window_closed():
        # draw all objects in the list
        render_all()
        tdl.flush()

        # handle keys and exit game if needed
        player_action = handle_keys()

        if player_action is not None and player_action != 'didnt-take-turn':
            save_action(player_action)

        if player_action == 'exit':
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in objects:
                if obj.fighter.ai:
                    # obj.fighter.ai.take_turn()
                    pass


# to reduce filesize, 2 methods:
#   1. seed game and record player actions from beginning, as in debug mode
#   2. record entire game map in more compressed format, by recording only (x, y) of each tile that has been explored
#       and re-creating the maps by loading each tile from files and setting explored values iteratively
def save_game():
    if debug_flag:
        file_name = player.name + "_debug_savegame"
        savefile = shelve.open("./saves/" + file_name, 'n')
        savefile['player_actions'] = []
        # serialize and save initial game state...all based off seed
        # serialize and save every player action
        # only works if game is deterministic, e.g. all randomization determined by seed
    else:
        file_name = player.name + "_savegame"
        savefile = shelve.open("./saves/" + file_name, 'n')
        savefile['current_map'] = current_map
    savefile['seed'] = seed
    savefile['objects'] = objects
    # don't save player object seperately because shelf module will create two player instances on load
    savefile['player_index'] = objects.index(player)
    savefile['game_msgs'] = game_msgs
    savefile['game_state'] = game_state
    savefile['map_num'] = map_num
    savefile.close()
        # also need to save all changes to map data (e.g. exploration of tiles)

def save_action(action):
    if debug_flag:
        file_name = player.name + "_debug_savegame"
        savefile = shelve.open("./saves/" + file_name, 'c')
        temp_list = savefile['player_actions']
        temp_list.append(str(serialize_action(action)))
        savefile['player_actions'] = temp_list
        savefile.close()


def load_game_menu():
    saved_games = []
    choice = None
    for file in os.listdir("./saves"):
        if file.endswith("_savegame"):
            saved_games.append(file[0:-9])
    choice = menu("Choose a save game to load.", saved_games + ['Back'], SCREEN_WIDTH)
    if choice == len(saved_games) or choice is None:
        return 0
    if "debug" in saved_games[choice]:
        load_game(saved_games[choice] + "_savegame", True)
    else:
        load_game(saved_games[choice] + "_savegame")
    return 1


def load_game(file_name, debug=False):
    #open the previously saved shelve and load the game data
    global seed, objects, player, game_msgs, game_state, current_map, map_num

    if debug:
        savefile = shelve.open('./saves/' + file_name, 'r')
        player_actions = savefile['player_actions']
        seed = savefile['seed']
        simulate_game(player_actions)
    else:
        savefile = shelve.open('./saves/' + file_name, 'r')
        seed = savefile['seed']
        objects = savefile['objects']
        player = objects[savefile['player_index']]  # get index of player in objects list and access it
        game_msgs = savefile['game_msgs']
        game_state = savefile['game_state']
        map_num = savefile['map_num']
        current_map = savefile['current_map']

    savefile.close()


def quit_game():
    sys.exit()


def generate_seed():
    global seed

    time = datetime.datetime.now()
    seed = int(re.sub('[-: \.]', '', str(time)))


def serialize_action(action):
    if action in dicts.possible_player_actions:
        return dicts.possible_player_actions.index(action)


def deserialize_action(serial):
    if serial < len(dicts.possible_player_actions):
        return dicts.possible_player_actions[serial]


def simulate_game(player_actions):
    global seed, game_state, debug_flag

    game_state = 'simulating'
    new_game()
    for item in player_actions:
        # simulate the action
        command = deserialize_action(int(item))
        handle_keys(command)
        explore_tiles(player.x, player.y)
    debug_flag = True


#############################################
# Initialization & Main Loop                #
#############################################
#tdl.set_font('terminal12x12_gs_ro.png', greyscale=True, altLayout=False)
tdl.set_font('unifont_9x15.png')
tdl.setFPS(LIMIT_FPS)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="RogueSouls", fullscreen=False)
con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

root.draw_str(SCREEN_WIDTH // 2 - 7, SCREEN_HEIGHT // 2 - 12, 'RogueSouls', fg=colors.crimson, bg=colors.darkest_han)
root.draw_str(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 - 10, 'By Jerezereh')

objects = []  # everything in the game that isn't a tile
game_msgs = []  # buffer of the messages that appear on the screen
last_button = ''
entry_coords = (12, 24)

fov_recompute = True
player_action = None
mouse_coord = (0, 0)
game_state = ''

map_num = 0
map_changed = False
current_map = []
level_map = []
map_tiles = []
map_label = ""
map_enemies_types = []
map_items_types = []

fill_mode = False
recurse_count = 0
max_recurse_flag = False

seed = 0
debug_flag = False

door_tiles = ['door_hor', 'door_vert']
special_tiles = ['fog_wall']

main_menu()
