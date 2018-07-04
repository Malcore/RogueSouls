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
import random

# Global variables
LIMIT_FPS = 30
MAX_RECURSE = 800

# actual size of the window in number of characters
# TODO: make screen size alterable/dynamic?
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 49

# size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 38

# height constants
MAX_HEIGHT = 100
MIN_HEIGHT = 0

# bottom gui panel constants
BAR_LENGTH = 20
PANEL_HEIGHT = 11
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
# Each action during combat takes a different amount of time, which is
#   modified by equip load, dex, the weight of the
# item used, etc. The base values for each type of action are given here
#    in frames (@20 fps):
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

NUMBER_MAPS = 4
########################################################################
# Major TODOs                                                          #
########################################################################
# TODO: add real-time gameplay mode
# TODO: selection between "Classic, Apprentice, and Expert" modes
# TODO: magic systems
# TODO: enemy dictionaries, with simple assembly of creatures by
#       choosing sets of stats, ai, and equipment
# TODO: overworld map
# TODO: location sub-map, procedural generation vs. handcrafted
# TODO: equipment dictionaries
# TODO: consumable item dictionaries
# TODO: random-generation of items
# TODO: equipment prefix/suffix/addon/enchantment/upgrade dictionaries
#       and systems
# TODO: level-up systems
# TODO: crafting systems?
# TODO: Dark Cloud style world building?
# TODO: change setting to Forgotten Realms/Baldur's Gate?
########################################################################


class Object:
    def __init__(self, x, y, char, name, color, blocks=True,
                 always_visible=False, block_sight=True, fighter=None, item=None,
                 player=None, player_interaction=None, fighter_interaction=None,
                 obj_interaction=None):
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

        # pseudo-inherited system of interactions, based on type of thing trying to interact with
        #  this object
        self.fighter_interaction = fighter_interaction
        self.player_interaction = player_interaction
        self.obj_interaction = obj_interaction

    def interact(self, obj):
        # if the interaction effects all objects
        if obj is not None:
            if self.obj_interaction is not None:
                return getattr(self.item, self.obj_interaction)(obj)
        # else if the interaction effects all fighter objects
        if obj.fighter is not None:
            if self.fighter_interaction is not None:
                return getattr(self.item, self.fighter_interaction)(obj)
        # else if the interaction effects only the player
        if obj.player is not None:
            if self.player_interaction is not None:
                return getattr(self.item, self.player_interaction)(obj)
        else:
            return False

    def move(self, dx, dy):
        global fov_recompute, current_map, death_coords, death_map_num

        if self.player is not None:
            death_coords = (player.x, player.y)

        # move by the given amount
        if self.x + dx > MAP_WIDTH - 1 or self.x + dx < 0:
            return
        elif self.y + dy > MAP_HEIGHT - 1 or self.y + dy < 0:
            return
        #    fov_recompute = True
        #    return
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            if current_map[self.x][self.y].linking:
                change_level(self.x, self.y)
            if self.player:
                fov_recompute = True
                render_all()
            current_map[self.x][self.y].interact(self)
            for obj in objects:
                if obj.x == self.x and obj.y == self.y:
                    obj.interact(self)
            fov_recompute = True
        elif current_map[self.x + dx][self.y + dy].interact(self):
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

    def retrieve_souls(self, obj):
        global dropped_souls, objects, spawn_soul_pool

        message("You gather your souls.")
        player.player.souls += dropped_souls
        dropped_souls = 0
        for obj in objects:
            if obj.name == 'soul_pool':
                objects.remove(obj)
                del obj
        spawn_soul_pool = False
        return True


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
                 linked_map_num=None, label=None, bg=None, dark_bg=None, player_interaction=None, fighter_interaction=None,
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
        # declares which map tile is linked to
        self.linked_map_num = linked_map_num
        self.label = label
        self.bg = bg
        self.dark_bg = dark_bg
        self.player_interaction = player_interaction
        self.fighter_interaction = fighter_interaction
        self.obj_interaction = obj_interaction
        self.open = False
        self.old_tile = ''

    def interact(self, obj):
        # if the interaction effects all objects
        if obj is not None:
            if self.obj_interaction is not None:
                return getattr(self, self.obj_interaction)(obj)
        # else if the interaction effects all fighter objects
        if obj.fighter is not None:
            if self.fighter_interaction is not None:
                return getattr(self, self.fighter_interaction)(obj)
        # else if the interaction effects only the player
        if obj.player is not None:
            if self.player_interaction is not None:
                return getattr(self, self.player_interaction)(obj)
        else:
            return False

    def open_tile(self, obj):
        # used to toggle open/closed state of doors, chests, etc.
        if not self.open:
            self.open = True
            message("You open the door...", colors.dark_green)
            getattr(self, self.label)()
            return True
        else:
            return False

    def rest(self, obj):
        global respawn_point, respawn_map_num

        message("You rest your weary soul...", colors.sea)
        respawn_map_num = map_num
        respawn_point = (obj.x, obj.y)
        load_map(map_num)
        return True

    def fall_full(self, obj):
        if obj.player is not None:
            message("You fall into the endless abyss.", colors.dark_amber)
        if obj.fighter is not None:
            obj.fighter.death()
        elif obj is not None:
            objects.remove(obj)
        return True

    def retrieve_souls(self, obj):
        global dropped_souls

        message("You gather your souls.")
        getattr(self, self.old_tile)()
        player.player.souls = dropped_souls
        dropped_souls = 0
        return True

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
        self.obj_interaction = 'fall_full'
        self.bg = colors.darker_gray
        self.dark_bg = colors.darkest_gray

    def bird_nest(self):
        self.blocked = False
        self.block_sight = True
        self.char = chr(177)
        self.vis_color = colors.dark_sepia
        self.fog_color = colors.darker_sepia
        self.linking = False
        self.label = "bird_nest"

    def bonfire(self):
        self.blocked = True
        self.block_sight = False
        self.char = '\u234e'
        self.vis_color = colors.yellow
        self.fog_color = colors.dark_yellow
        self.linking = False
        self.label = "bonfire"
        self.player_interaction = 'rest'

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
        self.bg = None  # colors.light_gray
        self.dark_bg = None  # colors.gray

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

    def ledge_small(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u25bd'
        self.vis_color = colors.white
        self.fog_color = colors.light_gray
        self.linking = True
        self.label = "ledge_small"

    def ledge_big(self):
        self.blocked = False
        self.block_sight = False
        self.char = '\u25bc'
        self.vis_color = colors.black
        self.fog_color = colors.black
        self.linking = True
        self.label = "ledge_big"

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
        self.obj_interaction = 'fall_full'

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

    def remove_weather(self):
        self.block_sight = False
        self.char = None
        self.vis_color = None
        self.fog_color = None
        self.label = None


# Originally meant for user's character only, also applies to all
# characters under the user's control.
class Player:
    def __init__(self, hunger=0, covenant=None, undead=False, souls=100):
        self.hunger = hunger
        self.covenant = covenant
        self.undead = undead
        self.souls = souls
        self.hp_mult = 1.0
        self.stam_mult = 1.0

        if self.undead:
            self.hp_mult = 0.5
            self.stam_mult = 0.5

    def level_up(self):
        self.owner.fighter.level += 1
        # TODO: implement level-up system

    def respawn(self):
        global respawn_point, dropped_souls, spawn_soul_pool

        # make souls re-obtainable at death position
        for obj in objects:
            if obj.name == 'soul_pool':
                objects.remove(obj)
                del obj
        spawn_soul_pool = True
        load_map(respawn_map_num)
        (self.owner.x, self.owner.y) = respawn_point
        self.owner.fighter.curr_hp = self.owner.fighter.hit_points
        dropped_souls = self.souls
        self.souls = 0
        self.undead = True
        message("You awaken in a familiar place.", colors.light_amber)


class Fighter:
    # defines something that can take combat actions (e.g. any living character) and gives them combat statistics as
    #   well as defining actions they can take during combat
    def __init__(self, vig=0, att=0, end=0, strn=0, dex=0, intl=0, fai=0, luc=0, wil=0, equip_load=0, poise=0, item_dis=0,
                 att_slots=0, rhand1=None, rhand2=None, lhand1=None, lhand2=None, head=None, chest=None, legs=None,
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
        self.head = head
        self.chest = chest
        self.arms = arms
        self.legs = legs
        self.neck = neck
        self.ring1 = ring1
        self.ring2 = ring2
        self.rhand1 = rhand1
        self.rhand2 = rhand2
        self.lhand1 = lhand1
        self.lhand2 = lhand2
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
        # +0.4 def/vig and 0.2 res/vig
        self.hit_points = int(math.ceil(40 * self.vig - 1.15 * self.vig))
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
        # stamina = 0.0184x^2 + 1.2896x + 78.73
        # 88 stamina at base (10) endurance
        # +1.1 lightning def/end, + 0.4 other def/end, and +0.2 elemental res/end
        self.stamina = math.floor(
            (0.0184 * self.end ** 2) + (1.2896 * self.end) + 78.73)
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
        self.curr_stam = self.stamina
        self.curr_r = rhand1
        self.curr_l = lhand1

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
            wep = get_equipped_in_slot(self, 'rhand1')
        else:
            wep = get_equipped_in_slot(self, 'lhand1')
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
            message(target.owner.name.capitalize() + " has died!")
            target.death()

    def death(self):
        # TODO: (bug) tile does not appear after removal of creature
        #       char, before player action
        if self.death_func:
            func = self.death_func
            func()
        else:
            basic_death(self)

    def equip(self, item):
        success = False
        options = ['Head', 'Chest', 'Arms', 'Legs', 'Neck',
                   'Right Hand', 'Left Hand', 'Right Ring',
                   'Left Ring', 'Right Hand Quick Slot',
                   'Left Hand Quick Slot']
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
            self.rhand1 = item
            item.equipped_at = 'rhand1'
            success = True
        elif choice is 6 and item.equippable_at is 'hand':
            self.lhand1 = item
            item.equipped_at = 'lhand1'
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
            self.rhand2 = item
            item.equipped_at = 'rhand2'
            success = True
        elif choice is 10 and item.equippable_at is 'hand':
            self.lhand2 = item
            item.equipped_at = 'lhand2'
            success = True
        if success:
            item.is_equipped = True
            message('Equipped ' + item.owner.owner.name + ' on ' +
                    options[choice] + '.', colors.light_green)

    def equip_to_slot(self, equipment, slot):
        if equipment.equippable_at in slot:
            setattr(self, slot, equipment)
            equipment.equipped_at = slot
            equipment.is_equipped = True
            message("Equipped " + equipment.owner.owner.name +
                    " to " + slot + ".", colors.light_green)
        else:
            message(equipment.owner.owner.name.capitalize() +
                    " cannot be equipped to your " + slot + ".",
                    colors.dark_green)

    # unequip object and show a message about it
    def unequip(self, equipment):
        if not equipment.is_equipped:
            return
        message("Unequipped " + equipment.owner.owner.name +
                " from " + equipment.slot + ".", colors.light_green)
        setattr(self, str(equipment.equipped_at), None)
        equipment.is_equipped = False
        equipment.equipped_at = None


class AI:
    def __init__(self, name=None, queue_size=0, profile=None, move_set=[]):
        self.name = name
        self.profile = profile
        self.queue_size = queue_size
        self.move_set = move_set
        self.queue = []

    def load_move_set(self):
        if self.name is None:
            return
        else:
            self.profile = dicts.ai[self.name]['profile']
            self.queue_size = dicts.ai[self.name]['queue_size']
            for num in range(2, dicts.ai[self.name]):
                self.move_set = dicts.ai[self.name][num]

    def build_queue(self):
        if self.move_set == []:
            return
        else:
            # choose action according to profile, add to queue, repeat until queue full
            while len(self.queue) < self.queue_size:
                choice = random.randrange(101)
                for num in dicts.ai[self.profile]:
                    if choice < dicts.ai[self.profile][num]:
                        self.queue.add(dicts.ai[self.profile][num])
                        print(dicts.ai[self.profile][num])


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
    message(target.owner.name.capitalize() +
            " was dealt " + str(final_dmg) + " damage!")


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
    target.curr_hp -= curr_wep.dmg_lightn - \
        round(dmg_reduc * curr_wep.dmg_lightn)
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
    target.bleed_amt += curr_wep.eff_bleed - \
        round(target.res_bleed / 100 * curr_wep.eff_bleed)


def add_poison(target, curr_wep):
    target.poison_amt += curr_wep.eff_poison - \
        round(target.res_poison / 100 * curr_wep.eff_poison)


def add_frost(target, curr_wep):
    target.frost_amt += curr_wep.eff_frost - \
        round(target.res_frost / 100 * curr_wep.eff_frost)


def add_curse(target, curr_wep):
    target.curse_amt += curr_wep.eff_curse - \
        round(target.res_curse / 100 * curr_wep.eff_curse)


############################################
# death functions
############################################
def player_death():
    global player, game_state, death_map_num

    death_map_num = map_num
    if player.fighter.curr_hp > 0:
        player.fighter.curr_hp = 0
    if not player.player.undead:
        player.player.undead = True
    message("You have died.", colors.dark_crimson)
    player.fighter.wil -= 1
    if player.fighter.wil == 0:
        message("You no longer have the willpower to continue. Your \
            heart and soul perish, and your body roams mindlessly as a \
            cursed undead.", colors.darker_amber)
        msgbox("Press any button to return to main menu...", 24)
        game_state = 'game_over'
        return
    else:
        while True:
            choice = menu("Would you like to continue?", [
                          'I must persevere...', 'I cannot go on...'], 24)
            if choice is 0:
                player.player.respawn()
                return
            if choice is 1:
                double_check = menu("Are you certain?", ["Yes", "No"], 24)
                if double_check == 0:
                    game_state = 'game_over'
                    return


def basic_death(fighter):
    for obj in objects:
        if obj is fighter.owner:
            objects.remove(obj)
            del obj

    player.player.souls += fighter.soul_value


############################################
# menus and related functions
############################################
def message(new_msg, color=colors.white):
    # split the message, if necessary, across multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for
        #   the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # add the new lines as a tuple, with text and color
        game_msgs.append((line, color))
    render_gui()


def menu(header, options, width, bg_a=0.7):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
        # TODO: create support for menus with more than 26 options

    # calculate total height for the header (after textwrap) and one
    #   line per option
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
    root.blit(window, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=bg_a)
    tdl.flush()

    # present the root console to the player and wait for a key-press
    keypress = False
    while not keypress:
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True

    # convert the ASCII code to an index; if it corresponds to an
    #   option, return it
    if user_input.text:
        index = ord(user_input.text) - ord('a')
    else:
        index = -1
    if 0 <= index < len(options):
        return index
    return None


# TODO: full-screen menus
def fullscreen_menu(header, options, bg_a=0.7):
    header_wrapped = textwrap.wrap(header, SCREEN_WIDTH)
    header_height = len(header_wrapped)

    # create an off-screen console that represents the menu's window
    window = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)

    # print the header, with wrapped text
    window.draw_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                     None, fg=colors.white, bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT //
                        2 - 6 + i, header_wrapped[i])

    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        window.draw_str(SCREEN_WIDTH // 2 - 11,
                        SCREEN_HEIGHT // 2 - 5 + y, text, bg=None)
        y += 1
        letter_index += 1

    root.blit(window, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
              0, 0, fg_alpha=1.0, bg_alpha=bg_a)
    tdl.flush()

    # present the root console to the player and wait for a key-press
    keypress = False
    while not keypress:
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True

    # convert the ASCII code to an index; if it corresponds to an
    #   option, return it
    if user_input.text:
        index = ord(user_input.text) - ord('a')
    else:
        index = -1
    if 0 <= index < len(options):
        return index
    return None


def msgbox(text, width=0):
    # use menu() as a sort of "message box"
    menu(text, [], width)


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
            # obj.item.equipment.slot is obj.item.equipment.is_equipped
            #   and slot:
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
# character interaction functions
############################################
def close_doors(x, y):
    global current_map

    if current_map[x - 1][y - 1].label in door_tiles:
        dx = -1
        dy = -1
    elif current_map[x][y - 1].label in door_tiles:
        dx = 0
        dy = -1
    elif current_map[x + 1][y - 1].label in door_tiles:
        dx = 1
        dy = -1
    elif current_map[x + 1][y].label in door_tiles:
        dx = 1
        dy = 0
    elif current_map[x + 1][y + 1].label in door_tiles:
        dx = 1
        dy = 1
    elif current_map[x][y + 1].label in door_tiles:
        dx = 0
        dy = 1
    elif current_map[x - 1][y + 1].label in door_tiles:
        dx = -1
        dy = 1
    elif current_map[x - 1][y].label in door_tiles:
        dx = -1
        dy = 0
    else:
        return
    if current_map[x + dx][y + dy].open:
        current_map[x + dx][y + dy].open = False
        getattr(current_map[x + dx][y + dy],
                current_map[x + dx][y + dy].label)()
        message("You close the door...", colors.darker_green)


############################################
# player interaction functions
############################################
def handle_keys(command=None):
    global fov_recompute, game_state, mouse_coord, map_tiles, fill_mode
    global fighter_mode, right_click_flag, map_num

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
            choice = menu(
                'Game Menu', ['Main Menu', 'Character Screen', 'Help'],
                30)
            if choice is 0:
                double_check = menu('Are you sure?', ['No', 'Yes'], 24)
                if double_check:
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

        elif debug_mode:
            if user_input.key == 'F1':
                for obj in objects:
                    output = obj.name + \
                        " at (" + str(obj.x) + ", " + str(obj.y) + ")"
                    message(output)

        if game_state == 'playing' or game_state == 'simulating':
            # movement keys
            if user_input.key == 'UP' or user_input.text == '8':
                player.move(0, -1)
                return "MV N"

            elif user_input.key == 'DOWN' or user_input.text == '2':
                player.move(0, 1)
                return "MV S"

            elif user_input.key == 'LEFT' or user_input.text == '4':
                player.move(-1, 0)
                return "MV W"

            elif user_input.key == 'RIGHT' or user_input.text == '6':
                player.move(1, 0)
                return "MV E"

            elif user_input.key == 'TEXT':
                if user_input.text == '7':
                    player.move(-1, -1)
                    return "MV NW"

                elif user_input.text == '9':
                    player.move(1, -1)
                    return "MV NE"

                elif user_input.text == '1':
                    player.move(-1, 1)
                    return "MV SW"

                elif user_input.text == '3':
                    player.move(1, 1)
                    return "MV SE"

                elif user_input.text == '5':
                    player.move(0, 0)
                    return "WAIT"

                elif user_input.text == 'i':
                    choice = inventory_menu()
                    if choice is not None and choice < len(
                            player.fighter.inventory):
                        item = player.fighter.inventory[choice]
                        player.fighter.equip(item.item.equipment)

                elif user_input.text == 'e':
                    equip_or_unequip(player.fighter, equipment_menu())

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

                elif user_input.text == 'E':
                    # open edit mode
                    message("Entering edit mode! Current tile order: " +
                            str(map_tiles), colors.light_azure)
                    for y in range(MAP_HEIGHT):
                        for x in range(MAP_WIDTH):
                            current_map[x][y].explored = True
                    game_state = 'editing'
                    edit_mode()

                elif user_input.text == 'S':
                    save_game()
                    message("Game saved!", colors.green)

                elif user_input.text == 'c':
                    close_doors(player.x, player.y)

        elif game_state == 'editing':
            if user_input.text == 'E':
                game_state = 'playing'
                fill_mode = False
                fighter_mode = False
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
            elif user_input.text == 'T':
                if not fighter_mode:
                    message("Left/Right click to place fighters on map.",
                            colors.light_red)
                    fighter_mode = True
                else:
                    message("Leaving fighter placement mode.",
                            colors.light_red)
                    fighter_mode = False
            elif user_input.key == 'PAGEUP':
                temp_map_num = int(map_num) + 1
                try:
                    load_map(temp_map_num)
                except AttributeError:
                    message("Map" + str(temp_map_num) +
                            ".txt is empty and could not be loaded!",
                            colors.red)
                except IOError:
                    message("Map" + str(temp_map_num) +
                            ".txt does not exist!", colors.red)
                else:
                    map_num = temp_map_num
            elif user_input.key == 'PAGEDOWN':
                temp_map_num = int(map_num) - 1
                try:
                    load_map(temp_map_num)
                except AttributeError:
                    message("Map" + str(temp_map_num) +
                            ".txt is empty and could not be loaded!",
                            colors.red)
                except IOError:
                    message("Map" + str(temp_map_num) +
                            ".txt does not exist!", colors.red)
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

    # create a list with the names of all objects at the mouse's
    #   coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in
             visible_tiles]

    names = ', '.join(names)  # join the names, separated by commas
    return names.capitalize()


def get_tile_under_mouse():
    global mouse_coord, current_map
    # return a string with the names of all objects under the mouse
    (x, y) = mouse_coord

    # create a list with the names of all objects at the mouse's
    #   coordinates and in FOV
    if x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0 and \
            current_map[x][y].explored is True:
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


# Indices: head-0, chest-1, arms-2, legs-3, neck-4, rring-5, lring-6,
#   rhand-7, lhand-8, rqslot-9, lqslot-10, close-11
def equip_or_unequip(fighter, index):
    if index is None or index > 10:
        return
    if get_equipped_in_slot(fighter, equipment_slots[index]):
        for item in fighter.inventory:
            if item.item.equipment.equipped_at == equipment_slots[index]:
                equipment = item.item.equipment
        fighter.unequip(equipment)
    else:
        item_choice = inventory_menu()
        if item_choice is not None:
            equipment = fighter.inventory[item_choice].item.equipment
            fighter.equip_to_slot(equipment, equipment_slots[index])


def equipment_menu():
    # TODO: fix equipment menu by showing each equipment slot and what
    #   is currently equipped there
    options = []
    if player.fighter.head:
        options.append(
            "Head: " + str(player.fighter.head.owner.owner.name).capitalize())
    else:
        options.append("Head: None")
    if player.fighter.chest:
        options.append(
            "Chest: " + str(player.fighter.chest.owner.owner.name).capitalize())
    else:
        options.append("Chest: None")
    if player.fighter.arms:
        options.append(
            "Arms: " + str(player.fighter.arms.owner.owner.name).capitalize())
    else:
        options.append("Arms: None")
    if player.fighter.legs:
        options.append(
            "Legs: " + str(player.fighter.legs.owner.owner.name).capitalize())
    else:
        options.append("Legs: None")
    if player.fighter.neck:
        options.append(
            "Neck: " + str(player.fighter.neck.owner.owner.name).capitalize())
    else:
        options.append("Necks: None")
    if player.fighter.ring1:
        options.append("Right Ring: " +
                       str(player.fighter.ring1.owner.owner.name).capitalize())
    else:
        options.append("Right Ring: None")
    if player.fighter.ring2:
        options.append("Left Ring: " +
                       str(player.fighter.ring2.owner.owner.name).capitalize())
    else:
        options.append("Left Ring: None")
    if player.fighter.rhand1:
        options.append(
            "Right Hand: " + str(player.fighter.rhand1.owner.owner.name).capitalize())
    else:
        options.append("Right Hand: None")
    if player.fighter.lhand1:
        options.append(
            "Left Hand: " + str(player.fighter.lhand1.owner.owner.name).capitalize())
    else:
        options.append("Left Hand: None")
    if player.fighter.rhand2:
        options.append("Right Quickslot: " +
                       str(player.fighter.rhand2.owner.owner.name).capitalize())
    else:
        options.append("Right Quickslot: None")
    if player.fighter.lhand2:
        options.append("Left Quickslot: " +
                       str(player.fighter.lhand2.owner.owner.name).capitalize())
    else:
        options.append("Left Quickslot: None")
    options.append("Close menu")
    return menu("Equipment", options, 30)


def drop_menu():
    return


def next_floor():
    return


############################################
# map and world functions
############################################
def load_map(map_num):
    global objects

    objects = []
    objects.append(player)
    change_map(*load_map_from_file(map_num))


def change_map(next_map, label, new_num):
    global current_map, old_map, fov_recompute, map_changed, map_label, map_num

    if current_map:
        old_map = current_map
    current_map = next_map
    fov_recompute = True
    map_changed = True
    map_label = label
    map_num = new_num

    # add all temporary objects to map that belong there
    if map_num == death_map_num and spawn_soul_pool is True:
        create_item('soul_pool', death_coords[0], death_coords[1])


def load_map_from_file(map_num):
    global level_map, map_tiles, map_fighters

    level_map = [[Tile(False)
                  for y in range(MAP_HEIGHT)]
                 for x in range(MAP_WIDTH)]

    map_label = None
    map_tiles = None
    map_fighters = None
    lastline = None
    file_label = None
    file_name = "./maps/map" + str(map_num) + ".txt"
    with open(file_name) as f:
        for line in f.readlines():
            line = line.replace('\n', '')
            if file_label == "[MAP LABEL]":
                if line == "[TILESET]":
                    file_label = line
                elif line != '':
                    map_label = line
            elif file_label == "[TILESET]":
                if line == "[FIGHTER SET]":
                    file_label = line
                elif line != '':
                    map_tiles = ast.literal_eval(line)
            elif file_label == "[FIGHTER SET]":
                if line == "[ITEM SET]":
                    file_label = line
                elif line != '':
                    map_fighters = ast.literal_eval(line)
            elif file_label == "[ITEM SET]":
                if line == "[MAP TILES]":
                    file_label = line
                elif line != '':
                    map_items = ast.literal_eval(line)
            elif file_label == "[MAP TILES]":
                if line == "[MAP LINKS]":
                    file_label = line
                elif line != '':
                    content = line.split(':')
                    if int(content[0]) != -1:
                        getattr(level_map[int(content[1])][int(
                            content[2])], map_tiles[int(content[0])])()
            elif file_label == "[MAP LINKS]":
                if line == "[FIGHTERS]":
                    file_label = line
                elif line != '':
                    content = line.split(':')
                    setattr(level_map[int(content[0])][int(
                        content[1])], "linked_map_num", content[2])
            elif file_label == "[FIGHTERS]":
                content = line.split(':')
                if len(content) == 3:
                    create_fighter(map_fighters[int(content[2])], int(
                        content[0]), int(content[1]))
            elif file_label == "[ITEMS]":
                content = line.split(':')
                if len(content) == 3:
                    # create_item()
                    pass
            elif file_label is None:
                file_label = line

    return(level_map, map_label, map_num)


def change_level(x, y):
    global current_map, death_coords

    death_coords = (player.x, player.y)
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
        visible_tiles = tdl.map.quickFOV(
            player.x, player.y, is_visible_tile, fov=FOV_ALGO, radius=WORLD_FOV_RAD, lightWalls=FOV_LIGHT_WALLS)

        # go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = (x, y) in visible_tiles
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if current_map[x][y].explored:
                        con.draw_char(
                            x, y, current_map[x][y].char, current_map[x][y].fog_color, bg=current_map[x][y].dark_bg)
                    else:
                        con.draw_char(x, y, None, None, bg=None)
                else:
                    con.draw_char(
                        x, y, current_map[x][y].char, current_map[x][y].vis_color, bg=current_map[x][y].bg)

                    # since it's visible, explore it
                    current_map[x][y].explored = True

        # draw all objects in the list for current map
        for obj in objects:
            if obj != player:
                if (obj.x, obj.y) in visible_tiles or obj.always_visible:
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
               colors.dark_red, colors.darker_red)
    render_bar(1, 3, BAR_LENGTH, 'Stamina', player.fighter.curr_stam, player.fighter.stamina,
               colors.dark_green, colors.darker_green)
    panel.draw_str(1, 5, "Souls: " + str(player.player.souls),
                   bg=None, fg=colors.white)
    panel.draw_str(1, 7, "Willpower: " + str(player.fighter.wil),
                   bg=None, fg=colors.white)

    # display names of objects under the mouse
    if mouse_coord:
        panel.draw_str(1, 0, get_names_under_mouse(),
                       bg=None, fg=colors.light_gray)
        panel.draw_str(1, -1, get_tile_under_mouse(),
                       bg=None, fg=colors.light_gray)

    if game_state == 'editing':
        panel.draw_str(SCREEN_WIDTH - 20, PANEL_HEIGHT - 1, "Map File: map" +
                       str(map_num) + ".txt", bg=None, fg=colors.white)

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
    visible_tiles = tdl.map.quickFOV(
        x, y, is_visible_tile, fov=FOV_ALGO, radius=WORLD_FOV_RAD, lightWalls=FOV_LIGHT_WALLS)
    for (x, y) in visible_tiles:
        current_map[x][y].explored = True


############################################
# real-time functions
############################################
def update_queue():
    # while(in_combat):
    #   for each fighter in objects:
    #       for each action in fighter.action_queue:
    #           action.timer -= 1
    #           if action.timer is 0:
    #               action.effect()
    return


############################################
# developer functions
############################################
def edit_mode(click_coords=None):
    global current_map, objects, fov_recompute, map_tiles, fill_mode, fighter_mode, map_num, right_click_flag

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if click_coords:
                if x == click_coords[0] and y == click_coords[1]:
                    if fill_mode:
                        fill_area(current_map[x][y].label, x, y)
                    elif fighter_mode:
                        if right_click_flag:
                            remove_fighter(x, y)
                        else:
                            place_fighter(x, y)
                    else:
                        if current_map[x][y].label in map_tiles:
                            if not right_click_flag:
                                if map_tiles.index(current_map[x][y].label) + 1 < len(map_tiles):
                                    getattr(current_map[x][y], map_tiles[map_tiles.index(
                                        current_map[x][y].label) + 1])()
                                else:
                                    getattr(current_map[x][y], map_tiles[0])()
                            else:
                                if map_tiles.index(current_map[x][y].label) - 1 >= 0:
                                    getattr(current_map[x][y], map_tiles[map_tiles.index(
                                        current_map[x][y].label) - 1])()
                                else:
                                    getattr(
                                        current_map[x][y], map_tiles[len(map_tiles) - 1])()
                        else:
                            getattr(current_map[x][y], map_tiles[0])()

    fov_recompute = True


def save_map():
    global current_map, objects, map_num, map_tiles, map_label

    map_file = open("./maps/map" + str(map_num) + ".txt", "w")
    map_file.write("[MAP LABEL]\n")
    map_file.write(map_label + "\n\n")
    map_file.write("[TILESET]\n")
    map_file.write(str(map_tiles) + "\n\n")
    map_file.write("[FIGHTER SET]\n")
    map_file.write(str(map_fighters) + "\n\n")
    map_file.write("[ITEM SET]\n")
    map_file.write(str(map_items) + "\n\n")
    map_file.write("[MAP TILES]\n")

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
                            message(
                                "Input of " + input_str + " cannot be converted to a number. Please try again.", colors.red)
                    message("The number you selected was " +
                            input_str + ".", colors.azure)
                    current_map[x][y].linked_map_num = linked_map_num
                map_file.write(str(x) + ':' + str(y) +
                               ':' + str(linked_map_num))
                map_file.write("\n")

    map_file.write("\n")

    map_file.write("[FIGHTERS]\n")
    for obj in objects:
        if obj.fighter is not None and obj.player is None:
            map_file.write(str(obj.x) + ':' + str(obj.y) + ':' +
                           str(map_fighters.index(obj.name)) + "\n")
    map_file.write("\n")

    map_file.write("[ITEMS]\n")
    for obj in objects:
        if obj.item is not None:
            map_file.write(str(obj.x) + ':' + str(oby.y) + ':' +
                           str(map_items.index(obj.name)) + "\n")
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
            message(
                "Reached maximum recursion depth, please fill additional areas separately.", colors.dark_red)


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
    flood_fill(x, y + 1, target_type, replacement_type)  # south
    flood_fill(x, y - 1, target_type, replacement_type)  # north
    flood_fill(x + 1, y, target_type, replacement_type)  # east
    flood_fill(x - 1, y, target_type, replacement_type)  # west
    recurse_count -= 1
    return


def place_object(x, y):
    obj_type = menu("Which type of object would you like to place?", [
                    "Fighters", "Items", "Other"], 30)
    if obj_type is 0:
        place_fighter(x, y)
    elif obj_type is 1:
        place_item(x, y)
    elif obj_type is 2:
        # place special/general types of objects?
        pass


def place_fighter(x, y):
    choice = menu("Which fighter would you like to place?", map_fighters, 30)
    if choice is not None:
        if choice < len(map_fighters):
            name = map_fighters[choice]
            create_fighter(name, x, y)


def create_fighter(name, x, y):
    global objects

    fdict = dicts.fighters[name]
    fighter_comp = Fighter(fdict['vig'], fdict['att'], fdict['end'], fdict['strn'],
                           fdict['dex'], fdict['intl'], fdict['fai'], fdict['luc'], fdict['wil'], level=fdict['level'],
                           soul_value=fdict['soul_value'])
    fighter = Object(x, y, fdict['char'], name, getattr(
        colors, fdict['color']), fighter=fighter_comp)
    objects.append(fighter)


def remove_fighter(x, y):
    global objects

    for obj in objects:
        if obj.x == x and obj.y == y:
            if obj.fighter is not None:
                objects.remove(obj)
                del obj


def place_item(x, y):
    global objects

    choice = menu("Which item would you like to place?", map_items, 30)
    if choice is not None:
        if choice < len(map_items):
            name = map_items[choice]
            create_item(name, x, y)


def create_item(name, x, y):
    global objects

    item_type = dicts.items[name]
    idict = getattr(dicts, item_type)[name]
    item_comp = Item()
    item = Object(x, y, idict['char'], name, getattr(colors, idict['color']), item=item_comp,
                  obj_interaction=idict['object_interaction'], fighter_interaction=idict['fighter_interaction'],
                  player_interaction=idict['player_interaction'])
    objects.append(item)


def remove_item(x, y):
    global objects

    for obj in objects:
        if obj.x == x and obj.y == y:
            if obj.item is not None:
                objects.remove(obj)
                del obj


def link_tiles(x, y):
    num_str = ""
    user_input = tdl.event.key_wait()
    while user_input.key != 'ENTER':
        num_str += user_input.char
        user_input = tdl.event.key_wait()
    return num_str


def new_map(map_num):
    choice = menu("Make a new map of number " +
                  str(map_num) + "?", ["No", "Yes"], 24)

    if choice:
        file_name = "./maps/map" + str(map_num) + ".txt"
        try:
            map_file = open(file_name, 'r')
        except IOError:
            map_file = open(file_name, 'w')
            map_file.write("[MAP LABEL]\n")
            map_file.write(map_label + "\n\n")
            map_file.write("[TILESET]\n")
            map_file.write(str(map_tiles) + "\n\n")
            map_file.write("[FIGHTER SET]\n")
            map_file.write(str(map_fighters) + "\n\n")
            map_file.write("[ITEM SET]\n")
            map_file.write(str(map_items) + "\n\n")
            map_file.write("[MAP TILES]\n")
        else:
            message("A map with the given number already exists.", colors.red)
        map_file.close()
        return True
    return False


############################################
# intro screen functions
# ()
def main_menu():
    global game_state, game_msgs, objects, map_num, player_action, debug_mode

    # img = libtcod.image_load('img/menu_background2.png')
    game_state = 'menu'
    game_msgs = []
    objects = []
    map_num = 0
    player_action = None

    while not tdl.event.is_window_closed():
        # show the background image, at twice the regular console resolution
        # libtcod.image_blit_2x(img, 0, 8, 3)

        root.draw_str(SCREEN_WIDTH // 2 - 7, SCREEN_HEIGHT // 2 -
                      12, 'RogueSouls', fg=colors.crimson, bg=colors.darkest_han)
        root.draw_str(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT //
                      2 - 10, 'By Jerezereh')

        # show options and wait for the player's choice
        choice = menu(
            '', ['Play a new game', 'Continue last game', 'Quit', 'Debug'], 24)

        # new game
        if choice is 0:
            initialize_variables()
            new_game()
            save_game()
            play_game()
        # continue saved game
        elif choice is 1:
            if load_game_menu():
                #initialize_variables()
                play_game()
            else:
                root.clear()
        # quit
        elif choice is 2:
            quit_game()
        # debug
        elif choice is 3:
            initialize_variables()
            debug_mode = True
            new_game()
            save_game()
            play_game()


def new_game():
    global player, game_state

    if game_state != 'simulating':
        # generate game seed based on current time
        random.seed()

    # first create the player out of its components
    player_comp = Player()
    fighter_comp = Fighter(10, 10, 10, 10, 10, 10, 10,
                           10, 3, death_func=player_death)
    player = Object(entry_coords[0], entry_coords[1], '@', "Player",
                    colors.gray, fighter=fighter_comp, player=player_comp)
    objects.append(player)

    # load map0.txt and draw to screen
    load_map(0)

    #enemy_fighter_comp = Fighter(1, 1, 1, 1, 1, 1, 1, 1, 1)
    #enemy = Object(12, 26, 'T', "Test Enemy", colors.dark_red, fighter=enemy_fighter_comp)
    # objects.append(enemy)

    # a warm welcoming message!
    message('You awaken with a burning desire to act. You feel as if you should recognize this place.', colors.light_flame)
    #message("The seed of this game is: " + str(seed) + ".")

    # initial equipment: a broken sword
    equipment_component = Equipment(
        slot='hand', durability=10, equippable_at='hand')
    item_comp = Item(weight=2, uses=0, equipment=equipment_component)
    sword = Object(0, 0, '-', name="Broken Sword", color=colors.sky, block_sight=False, item=item_comp,
                   always_visible=True)
    player.fighter.inventory.append(sword)


def play_game():
    global game_state

    player_action = None
    game_state = 'playing'

    # main loop
    while not tdl.event.is_window_closed():
        # draw all objects in the list
        render_all()
        tdl.flush()

        # handle keys and exit game if needed
        player_action = handle_keys()

        #if player_action is not None and player_action != 'didnt-take-turn':
        #    save_action(player_action)

        if player_action == 'exit':
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in objects:
                if obj.fighter is not None:
                    if obj.fighter.ai is not None:
                        # obj.fighter.ai.take_turn()
                        pass

        if game_state == 'game_over':
            return


# TODO: finish new save_game function
def save_game():
    file_name = player.name + "_savegame"
    sf = shelve.open("./saves/" + file_name, 'n')
    sf['seed'] = seed
    sf['game_msgs'] = game_msgs
    sf['respawn_point'] = respawn_point
    sf['respawn_map_num'] = respawn_map_num
    sf['dropped_souls'] = dropped_souls
    sf['death_coords'] = death_coords
    sf['death_map_num'] = death_map_num
    sf['player_action'] = player_action
    sf['game_state'] = game_state
    sf['objects'] = objects[1:]
    sf['map_num'] = map_num
    sf['current_map'] = current_map
    sf['map_tiles'] = map_tiles
    sf['map_fighters'] = map_fighters
    sf['map_items'] = map_items
    sf['map_label'] = map_label
    sf['player'] = player
    sf.close();


def load_game_menu():
    saved_games = []
    choice = None
    for file in os.listdir("./saves"):
        if file.endswith("_savegame.dat"):
            saved_games.append(file[0:-13])
    choice = menu("Choose a save game to load.", saved_games + ['Back'], 30)
    if choice == len(saved_games) or choice is None:
        return 0
    else:
        load_game(saved_games[choice] + "_savegame")
        return 1


def load_game(file_name):
    global seed, game_msgs, respawn_point, respawn_map_num, dropped_souls
    global death_coords, death_map_num, player_action, game_state, objects
    global map_num, current_map, map_tiles, map_fighters, map_items, map_label
    global player

    sf = shelve.open("./saves/" + file_name, 'r')
    seed = sf['seed']
    game_msgs = sf['game_msgs']
    respawn_point = sf['respawn_point']
    respawn_map_num = sf['respawn_map_num']
    dropped_souls = sf['dropped_souls']
    death_coords = sf['death_coords']
    death_map_num = sf['death_map_num']
    player_action = sf['player_action']
    game_state = sf['game_state']
    objects = sf['objects']
    map_num = sf['map_num']
    current_map = sf['current_map']
    map_tiles = sf['map_tiles']
    map_fighters = sf['map_fighters']
    map_items = sf['map_items']
    map_label = sf['map_label']
    player = sf['player']


def quit_game():
    sys.exit(0)


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


def simulate_game(player_actions, state='simulating'):
    global game_state

    game_state = state
    new_game()
    simulate_actions(player_actions)


def simulate_actions(player_actions):
    for item in player_actions:
        # simulate the action
        command = deserialize_action(int(item))
        handle_keys(command)
        explore_tiles(player.x, player.y)


def initialize_variables():
    global objects, game_msgs, entry_coords, respawn_point, respawn_map_num, dropped_souls
    global death_coords, death_map_num, fov_recompute, player_action, mouse_coord, game_state
    global map_num, map_changed, current_map, level_map, map_tiles, map_label, map_fighters, map_items
    global fill_mode, fighter_mode, recurse_count, max_recurse_flag, seed, filename

    objects = []  # everything in the game that isn't a tile
    game_msgs = []  # buffer of the messages that appear on the screen
    entry_coords = (12, 24)
    respawn_point = entry_coords
    respawn_map_num = 0
    dropped_souls = 0
    death_coords = None
    death_map_num = None
    spawn_soul_pool = False

    fov_recompute = True
    player_action = None
    mouse_coord = (0, 0)
    game_state = ''

    map_num = 0
    map_changed = False
    current_map = []
    level_map = []
    map_tiles = []
    map_fighters = []
    map_items = []
    map_label = ""

    fill_mode = False
    fighter_mode = False
    recurse_count = 0
    max_recurse_flag = False
    debug_mode = False

    seed = 0
    filename = ''


#############################################
# Initialization & Main Loop                #
#############################################
tdl.set_font('img/unifont_9x15.png')
tdl.setFPS(LIMIT_FPS)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT,
                title="RogueSouls", fullscreen=False)
con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

objects = []  # everything in the game that isn't a tile
game_msgs = []  # buffer of the messages that appear on the screen
entry_coords = (12, 24)
respawn_point = entry_coords
respawn_map_num = 0
dropped_souls = 0
death_coords = None
death_map_num = None
spawn_soul_pool = False

fov_recompute = True
player_action = None
mouse_coord = (0, 0)
game_state = ''

map_num = 0
map_changed = False
current_map = []
level_map = []
map_tiles = []
map_fighters = []
map_items = []
map_label = ""

fill_mode = False
fighter_mode = False
recurse_count = 0
max_recurse_flag = False
debug_mode = False

seed = 0
filename = ''

door_tiles = ['door_hor', 'door_vert']
special_tiles = ['fog_wall']
equipment_slots = ['head', 'chest', 'arms', 'legs', 'neck',
                   'rring', 'lring', 'rhand1', 'rhand2', 'lhand1', 'lhand2']

main_menu()
