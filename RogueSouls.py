import libtcodpy as libtcod
import random
import math
import textwrap
import sys
import dictionaries as dicts

# Global variables
LIMIT_FPS = 20

# actual size of the window in characters (or 960x720 pixels)
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 70

# size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 55

# color constants
color_dark_wall = libtcod.darker_gray
color_dark_ground = libtcod.darkest_amber
color_light_wall = libtcod.dark_gray
color_light_ground = libtcod.darker_amber

# stat bars
BAR_LENGTH = 20
PANEL_HEIGHT = 12
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

# message log
MSG_X = BAR_LENGTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_LENGTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 2

# level up info
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 30

# fov constants
FOV_ALGO = 2
FOV_LIGHT_WALLS = True
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
# number of frames that a character is invulnerable if dodging
DODGE_TIME = 8


class Object:
    def __init__(self, x, y, char, name, color, blocks=True, always_visible=False, block_sight=True, fighter=None, ai=None, item=None, player=None):
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

        self.ai = ai
        # let the ai component know who owns it
        if self.ai:
            self.ai.owner = self
            self.ai.build_queue()

        self.item = item
        if self.item:
            self.item.owner = self

        self.player = player
        if self.player:
            self.player.owner = self

    def move(self, dx, dy):
        global fov_recompute
        # move by the given amount
        if self.x + dx > MAP_WIDTH - 1 or self.x + dx < 0:
            return
        elif self.y + dy > MAP_HEIGHT - 1 or self.y + dy < 0:
            return
        for obj in objects:
            if obj.x is self.x + dx and obj.y is self.y + dy:
                if self.player:
                    fov_recompute = True
                return
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
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
        if libtcod.map_is_in_fov(fov_map, self.x, self.y) or self.always_visible and world_map[self.x][self.y].explored:
            # set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

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
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # all tiles start unexplored
        self.explored = False

        # by default, if a tile is blocked, it also blocks sight
        if blocked is None:
            block_sight = blocked
        self.block_sight = block_sight


class Player:
    def __init__(self, hunger=0, covenant=None, souls=0, skillpoints=0):
        self.hunger = hunger
        self.covenant = covenant
        self.souls = souls
        self.skillpoints = skillpoints

    def level_up(self):
        self.owner.fighter.level += 1
        self.skillpoints += 1
        # TODO


class Fighter:
    # defines something that can take combat actions (e.g. any living character) and gives them combat statistics as
    # well as defining actions they can take during combat
    def __init__(self, vig=0, att=0, end=0, str=0, dex=0, int=0, fai=0, luc=0, wil=0, equip_load=0, poise=0, item_dis=0,
                 att_slots=0, right1=None, right2=None, left1=None, left2=None, head=None, chest=None, legs=None,
                 arms=None, ring1=None, ring2=None, neck=None, def_phys=0, def_slash=0, def_blunt=0, def_piercing=0,
                 def_mag=0, def_fire=0, def_lightn=0, def_dark=0, res_bleed=0, res_poison=0, res_frost=0, res_curse=0,
                 bleed_amt=0, poison_amt=0, frost_amt=0, curse_amt=0, facing=None, level=1, soul_value=0, wait_time=0,
                 dodge_frames=DODGE_TIME, in_combat=False, inventory=[], blocking=False, death_func=None):
        self.vig = vig
        self.att = att
        self.end = end
        self.str = str
        self.dex = dex
        self.int = int
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
        self.in_combat = in_combat
        self.inventory = inventory
        self.action_queue = []
        self.blocking = blocking
        self.death_func = death_func

        # Beginning of derived statistics

        # Vigor effects
        # hp = 2E-07x^6 - 7E-05x^5 + 0.0071x^4 - 0.3803x^3 + 9.908x^2 - 81.809x + 533.94
        # 403 hp at base (10) vigor
        # +0.4 res/vig and 0.2 def/vig
        self.hit_points = math.ceil(40*self.vig - 1.15*self.vig)
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
        # TODO
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
        # TODO

        # Dexterity effects
        # TODO: show effects of dex on dodge frames
        self.dodge_frames += self.dex

        # Intelligence effects
        # TODO

        # Faith effects
        # TODO

        # Luck effects
        # TODO

        # Will effects
        # TODO

        # Other statistics
        self.curr_hp = self.hit_points
        self.curr_ap = self.att_points
        self.curr_sp = self.stamina
        self.curr_r = right1
        self.curr_l = left2

    def handle_attack_move(self, side, type):
        libtcod.console_wait_for_keypress(True)
        libtcod.console_wait_for_keypress(True)

        if libtcod.console_is_key_pressed(libtcod.KEY_UP) or libtcod.console_is_key_pressed(libtcod.KEY_KP8):
            self.attack_handler(side, (0, -1), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or libtcod.console_is_key_pressed(libtcod.KEY_KP2):
            self.attack_handler(side, (0, 1), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or libtcod.console_is_key_pressed(libtcod.KEY_KP4):
            self.attack_handler(side, (-1, 0), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or libtcod.console_is_key_pressed(libtcod.KEY_KP6):
            self.attack_handler(side, (1, 0), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
            self.attack_handler(side, (-1, -1), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
            self.attack_handler(side, (1, -1), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
            self.attack_handler(side, (-1, 1), type)

        elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
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
        # TODO
        self.wait_time += PARRY_SPEED
        return self

    def block(self):
        # TODO
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
            message('Equipped ' + item.owner.owner.name + ' on ' + options[choice] + '.', libtcod.light_green)

    # unequip object and show a message about it
    def unequip(self, item):
        if not item.is_equipped:
            return
        message('Unequipped ' + item.owner.owner.name + ' from ' + item.slot + '.', libtcod.light_green)
        setattr(self, str(item.equipped_at), None)
        item.is_equipped = False
        item.equipped_at = None


class AI:
    def __init__(self, ai_type=None):
        self.ai_type = ai_type

    def build_queue(self):
        if self.ai_type is None:
            return
        if self.ai_type is 'ConstantAttack':
            if is_facing(self, player):
                if distance_to(player) is 0:
                    self.owner.fighter.action_queue = ['att_right_l', 'att_left_l']
                else:
                    self.owner.fighter.action_queue = ['move_p', 'att_right_l', 'att_left_l']
            else:
                self.owner.fighter.action_queue = ['face_p', 'move_p', 'att_right_l', 'att_left_l']


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
def message(new_msg, color=libtcod.white):
    # split the message, if necessary, across multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # add the new lines as a tuple, with text and color
        game_msgs.append((line, color))


def menu(header, options, width, ordered=True, align=libtcod.LEFT, head_color=libtcod.white):

    num_pages = int(math.ceil(len(options)/26))
    pages = []
    curr_page = 0
    height = 0
    header_height = 0

    for i in range(num_pages):
        # calculate total height for the header (after auto-wrap) and one line per option
        header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
        if header == '':
            header_height = 0
        height = len(options) + header_height

        # create an off-screen console that represents the menu's window
        pages.append(libtcod.console_new(width, height))

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(pages[0], head_color)
    libtcod.console_print_rect_ex(pages[curr_page], 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    # print all the options
    y = header_height
    letter_index = ord('a')
    if ordered:
        for option_text in options:
            text = '(' + chr(letter_index) + ') ' + option_text
            libtcod.console_print_ex(pages[curr_page], 0, y, libtcod.BKGND_NONE, align, text)
            y += 1
            letter_index += 1
    else:
        for option_text in options:
            text = option_text
            libtcod.console_print_ex(pages[curr_page], 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
            y += 1

    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    libtcod.console_blit(pages[curr_page], 0, 0, width, height, 0, x, y, 1.0, 0.7)

    # compute x and y offsets to convert console position to menu position
    # x is the left edge of the menu
    x_offset = x
    # subtract the height of the header from the top edge of the menu
    y_offset = y + header_height

    while True:
        # present the root console to the player and check for input
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        if mouse.lbutton_pressed:
            (menu_x, menu_y) = (mouse.cx - x_offset, mouse.cy - y_offset)
            # check if click is within the menu and on a choice
            if 0 <= menu_x < width and 0 <= menu_y < height - header_height:
                return menu_y

        if mouse.rbutton_pressed or key.vk is libtcod.KEY_ESCAPE:
            # cancel if the player right-clicked or pressed Escape
            return None

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        # convert the ASCII code to an index; if it corresponds to an option, return it
        index = key.c - ord('a')
        if 0 <= index < len(options):
            return index
        # if they pressed a letter that is not an option, return None
        if 0 <= index <= 26:
            return None
        if libtcod.console_is_key_pressed(libtcod.KEY_PAGEUP) and len(pages) > curr_page + 1:
            curr_page += 1
            libtcod.console_blit(pages[curr_page], 0, 0, width, height, 0, SCREEN_WIDTH // 2 - width // 2, SCREEN_HEIGHT
                                 // 2 - height // 2, 1.0, 0.7)
        if libtcod.console_is_key_pressed(libtcod.KEY_PAGEDOWN) and curr_page > 0:
            curr_page -= 1
            libtcod.console_blit(pages[curr_page], 0, 0, width, height, 0, SCREEN_WIDTH // 2 - width // 2, SCREEN_HEIGHT
                                 // 2 - height // 2, 1.0, 0.7)


def msgbox(text, width=0):
    # use menu() as a sort of "message box"
    menu(0, 0, text, [], width)


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width // 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))


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
    if world_map[x][y].blocked:
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


def pick_up():
    for obj in objects:
        if obj.x is player.x and obj.y is player.y:
            player.fighter.inventory.append(obj)


############################################
# map and world functions
############################################
def make_world_map():
    global world_map

    # fill map with unblocked tiles
    world_map = [[Tile(False)
                 for y in range(MAP_HEIGHT)]
                 for x in range(MAP_WIDTH)]

    world_map[30][22].blocked = True
    world_map[30][22].block_sight = True
    world_map[50][22].blocked = True
    world_map[50][22].block_sight = True


############################################
# player interactions functions
############################################
def handle_keys():
    global fov_recompute, game_state
    # key = libtcod.console_check_for_keypress()  #real-time
    key = libtcod.console_wait_for_keypress(True)  # turn-based

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        # game menu
        choice = menu('Game Menu', ['Exit Game', 'Character Screen', 'Help'], 24)
        if choice is 0:
            double_check = menu('Are you sure?', ['No', 'Yes'], 24)
            if double_check:
                sys.exit()
            else:
                return
        elif choice is 1:
            # TODO: add character screen
            return
        elif choice is 2:
            # TODO: add help screen
            return

    # movement keys
    elif libtcod.console_is_key_pressed(libtcod.KEY_UP) or libtcod.console_is_key_pressed(libtcod.KEY_KP8):
        player.move(0, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or libtcod.console_is_key_pressed(libtcod.KEY_KP2):
        player.move(0, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or libtcod.console_is_key_pressed(libtcod.KEY_KP4):
        player.move(-1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or libtcod.console_is_key_pressed(libtcod.KEY_KP6):
        player.move(1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
        player.move(-1, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
        player.move(1, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
        player.move(-1, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
        player.move(1, 1)

    elif key.c == ord('i'):
        inventory_menu()

    elif key.c == ord('e'):
        equip_or_unequip(equipment_menu())

    # force quit key?
    elif key.c == ord('Q'):
        return None

    elif key.c == ord('d'):
        drop_menu()

    elif key.c == ord(','):
        player.fighter.handle_attack_move("left", "special")
        return

    elif key.c == ord('.'):
        player.fighter.handle_attack_move("right", "special")
        return

    elif key.c == ord('k'):
        player.fighter.handle_attack_move("left", "normal")

    elif key.c == ord('l'):
        player.fighter.handle_attack_move("right", "normal")


def get_names_under_mouse():
    global mouse
    # return a string with the names of all objects under the mouse

    (x, y) = (mouse.cx, mouse.cy)
    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names)  # join the names, separated by commas
    return names.capitalize()


def inventory_menu():
    if len(player.fighter.inventory) is 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in player.fighter.inventory]
        options.append("Close menu")
    index = menu("Inventory", options, 30)
    return index


def equip_or_unequip(index):
    if index is not None and index < len(player.fighter.inventory):
        item_obj = player.fighter.inventory[index]
        if item_obj.item.equipment:
            for obj in player.fighter.inventory:
                if obj == item_obj:
                    if item_obj in get_all_equipped(player):
                        player.fighter.unequip(item_obj.item.equipment)
                    else:
                        player.fighter.equip(item_obj.item.equipment)


def equipment_menu():
    # TODO: fix equipment menu by showing each equipment slot and what is currently equipped there
    equipped = get_all_equipped(player)
    if len(equipped) is 0:
        options = ['No items equipped']
    else:
        options = [item.name for item in equipped]
        options.append("Close menu")
    return menu("Equipment", options, 30)


def skill_menu():
    options = ['abc']
    index = menu("Skills", options, SCREEN_WIDTH)
    return index


def drop_menu():
    return


############################################
# misc. helper functions
############################################
def random_choice_index(chances):
    # choose one option from list of chances, returning its index
    # the dice will land on some number between 1 and the sum of the chances
    dice = random.randint(1, sum(chances))

    # go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        # see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1


def random_choice(chances_dict):
    # choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()
    return strings[random_choice_index(chances)]


def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True

    # create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not world_map[x][y].block_sight, not world_map[x][y].blocked)

    libtcod.console_clear(con)  # unexplored areas start black (which is the default background color)


def render_all():
    global fov_map, fov_recompute

    if fov_recompute:
        # recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

        # go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = world_map[x][y].block_sight
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if world_map[x][y].explored:
                        if wall:
                            libtcod.console_put_char_ex(con, x, y, "#", color_dark_wall, libtcod.black)
                        else:
                            libtcod.console_put_char_ex(con, x, y, '.', color_dark_ground, libtcod.black)
                else:
                    # it's visible
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, "#", color_light_wall, libtcod.black)
                    else:
                        libtcod.console_put_char_ex(con, x, y, ".", color_light_ground, libtcod.black)
                        # since it's visible, explore it
                    world_map[x][y].explored = True

    # draw all objects in the list
    for object in objects:
        if object not in object.fighter.inventory:
            object.draw()

    # blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

    # show the player's stats
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # print the messages, one line at a time
    y = 2
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    render_bar(1, 6, BAR_LENGTH, 'HP', player.fighter.curr_hp, player.fighter.hit_points, libtcod.light_red,
               libtcod.darker_red)
    render_bar(1, 8, BAR_LENGTH, 'AP', player.fighter.curr_ap, player.fighter.att_points, libtcod.blue,
               libtcod.dark_blue)
    render_bar(1, 10, BAR_LENGTH, 'SP', player.fighter.curr_sp, player.fighter.stamina, libtcod.light_gray,
               libtcod.dark_gray)

    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Level: ' + str(player.fighter.level))
    libtcod.console_print_ex(panel, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'Souls: ' + str(player.player.souls))
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Level Cost: ' +
                             str((LEVEL_UP_BASE + player.fighter.level * LEVEL_UP_FACTOR)))

    if player.fighter.right1:
        libtcod.console_print_ex(panel, 52, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Right Hand: ' +
                                 str(player.fighter.right1.owner.owner.name))
    else:
        libtcod.console_print_ex(panel, 52, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Right Hand: Empty')
    if player.fighter.left1:
        libtcod.console_print_ex(panel, 22, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Left Hand: ' +
                                 str(player.fighter.left1.owner.owner.name))
    else:
        libtcod.console_print_ex(panel, 22, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Left Hand: Empty')

    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

############################################
# intro screen functions
############################################


def main_menu():
    img = libtcod.image_load('menu_background2.png')

    while not libtcod.console_is_window_closed():
        # show the background image, at twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 8, 3)

        # show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        # new game
        if choice is 0:
            new_game()
            play_game()
        elif choice is 1:
            pass
        # quit
        elif choice is 2:
            quit_game()


def new_game():
    global player, game_msgs, game_state

    # first create the player out of its components
    player_comp = Player()
    fighter_comp = Fighter(10, 10, 10, 10, 10, 10, 10, 10, 15)
    player = Object(0, 0, '@', "Player", libtcod.gray, fighter=fighter_comp, player=player_comp)
    objects.append(player)

    enemy_fighter_comp = Fighter(1, 1, 1, 1, 1, 1, 1, 1, 1)
    ai_comp = AI('ConstantAttack')
    enemy = Object(15, 15, 'T', "Test Enemy", libtcod.dark_red, fighter=enemy_fighter_comp, ai=ai_comp)
    objects.append(enemy)

    # generate world map (at this point it's not drawn to the screen)
    make_world_map()
    initialize_fov()

    game_state = 'playing'

    # a warm welcoming message!
    message('You awaken with a burning desire. You feel as if you should recognize this place. The walls are covered in'
            ' rot and the stench of death is in the air.', libtcod.red)

    # initial equipment: a broken sword
    equipment_component = Equipment(slot='hand', durability=10, equippable_at = 'hand')
    item_comp = Item(weight=2, uses=0, equipment=equipment_component)
    sword = Object(0, 0, '-', name="Broken Sword", color=libtcod.sky, block_sight=False, item=item_comp,
                   always_visible=True)
    player.fighter.inventory.append(sword)
    player.fighter.equip(equipment_component)


def play_game():
    player_action = None
    make_world_map()

    # main loop
    while game_state == 'playing':
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        # render the screen
        render_all()
        libtcod.console_flush()

        # erase all objects at their old locations, before they move
        for obj in objects:
            obj.clear()

        # handle keys and exit game if needed
        player_action = handle_keys()

        if game_state == 'exit':
            # save_game()
            quit_game()

        # let monsters take their turn
        if game_state == 'combat':
            for obj in objects:
                if obj.in_combat:
                    # combat()
                    pass


def quit_game():
    sys.exit()

# Initialization of game-state variables and game functions
mouse = libtcod.Mouse()
key = libtcod.Key()
objects = [] # everything in the game that isn't a tile
game_msgs = [] # buffer of the messages that appear on the screen
game_state = 'menu'

# libtcod.console_set_custom_font('terminal10x10_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "RogueSouls", False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)

# show the game's title, and some credits!
libtcod.console_set_default_foreground(con, libtcod.light_yellow)
libtcod.console_print_ex(con, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10, libtcod.BKGND_NONE, libtcod.CENTER, 'RogueSouls')
libtcod.console_print_ex(con, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 8, libtcod.BKGND_NONE, libtcod.CENTER, 'By Malcore')

main_menu()
