import math
import random
import textwrap
import colors
import tdl
import dictionaries as dicts

import RogueSoulsGlobals as gbl
import RogueSouls as rs


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
    for obj in rs.objects:
        if obj is fighter.owner:
            rs.objects.remove(obj)
            del obj


############################################
# menus and related functions
############################################
def message(new_msg, color=colors.white):
    # split the message, if necessary, across multiple lines
    new_msg_lines = textwrap.wrap(new_msg, gbl.MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for the new one
        if len(rs.game_msgs) == gbl.MSG_HEIGHT:
            del rs.game_msgs[0]

        # add the new lines as a tuple, with text and color
            rs.game_msgs.append((line, color))


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
    x = gbl.SCREEN_WIDTH // 2 - width // 2
    y = gbl.SCREEN_HEIGHT // 2 - height // 2
    rs.root.blit(window, x, y, width, height, 0, 0, fg_alpha=1.0, bg_alpha=0.7)
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


def msgbox(text, width=0):
    # use menu() as a sort of "message box"
    menu(0, 0, text, [], width)


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    rs.panel.draw_rect(x, y, total_width, 1, None, bg=back_color)

    # now render the bar on top
    if bar_width > 0:
        rs.panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)

    # finally, some centered text with the values
    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (total_width - len(text)) // 2
    rs.panel.draw_str(x_centered, y, text, fg=colors.white, bg=None)


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
    for obj in rs.objects:
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
    for obj in rs.objects:
        if obj.x is x and obj.y is y:
            return obj
    return None


def pick_up():
    for obj in rs.objects:
        if obj.x is player.x and obj.y is player.y:
            player.fighter.inventory.append(obj)

############################################
# player interactions functions
############################################
def handle_keys():
    global fov_recompute, game_state, mouse_coord

    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

    if not keypress:
        return 'didnt-take-turn'

    if user_input.key == 'ENTER' and user_input.alt:
        # Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        # game menu
        choice = menu('Game Menu', ['Exit Game', 'Character Screen', 'Help'], 24)
        print(choice)
        if choice is 0:
            print(choice)
            double_check = menu('Are you sure?', ['No', 'Yes'], 24)
            if double_check:
                exit()
            else:
                return
        elif choice is 1:
            # TODO: add character screen
            return
        elif choice is 2:
            # TODO: add help screen
            return

    if game_state == 'playing':
        # movement keys
        if user_input.key == 'UP' or user_input.key == 'TEXT' and user_input.text == '8':
            player.move(0, -1)

        elif user_input.key == 'DOWN' or user_input.key == 'TEXT' and user_input.text == '2':
            player.move(0, 1)

        elif user_input.key == 'LEFT' or user_input.key == 'TEXT' and user_input.text == '4':
            player.move(-1, 0)

        elif user_input.key == 'RIGHT' or user_input.key == 'TEXT' and user_input.text == '6':
            player.move(1, 0)

        elif user_input.key == 'TEXT':
            if user_input.text == '7':
                player.move(-1, -1)

            elif user_input.text == '9':
                player.move(1, -1)

            elif user_input.text == '1':
                player.move(-1, 1)

            elif user_input.text == '3':
                player.move(1, 1)

            elif user_input.text == 'i':
                choice = inventory_menu()
                print(choice)
                if choice is not None:
                    item = player.fighter.inventory[choice]
                    player.fighter.equip(item.item.equipment)

            elif user_input.text == 'e':
                equip_or_unequip(equipment_menu())

            # force quit key?
            elif user_input.text == 'Q':
                exit()

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
                change_location()
            else:
                print(user_input.text)


def get_names_under_mouse():
    global mouse_coord
    # return a string with the names of all objects under the mouse
    (x, y) = mouse_coord

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in rs.objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]

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


# Indicies: head-0, chest-1, arms-2, legs-3, neck-4, rring-5, lring-6, rhand-7, lhand-8, rqslot-9, lqslot-10, close-11
def equip_or_unequip(index):
    print(index)
    item = player.fighter.inventory[inventory_menu()]
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
    index = menu("Skills", options, gbl.SCREEN_WIDTH)
    return index


def drop_menu():
    return


# TODO: update game_state var to accurately represent where player is currently at (menu, world map, city, etc)
def change_location():
    global game_state
    if game_state == 'dungeon':
        # go to next floor
        next_floor()
    elif game_state == 'world':
        enter_location(player.x, player.y)


def next_floor():
    return


def enter_location(x, y):
    if world_map[x][y].char == 'o':
        print('You enter the city...')
        pass
    elif world_map[x][y] == '*':
        print('You enter the dungeon...')
        pass


############################################
# misc. helper functions
############################################
def random_choice(chances_dict):
    # choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()
    return strings[random_choice_index(chances)]


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


def render_all():
    global fov_recompute
    global visible_tiles
    global player

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y, is_visible_tile, fov=gbl.FOV_ALGO, radius=gbl.WORLD_FOV_RAD, lightWalls=gbl.FOV_LIGHT_WALLS)

        # go through all tiles, and set their background color according to the FOV
        for y in range(gbl.MAP_HEIGHT):
            for x in range(gbl.MAP_WIDTH):
                visible = (x, y) in visible_tiles
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if world_map[x][y].explored:
                        # print(x, y)
                        rs.con.draw_char(x, y, world_map[x][y].char, world_map[x][y].fog_color, bg=None)
                else:
                    rs.con.draw_char(x, y, world_map[x][y].char, world_map[x][y].vis_color, bg=None)
                    # since it's visible, explore it
                    world_map[x][y].explored = True

    # draw all objects in the list
    for obj in rs.objects:
        if obj != player:
            obj.draw()
    player.draw()
    # blit the contents of "con" to the root console and present it
    rs.root.blit(rs.con, 0, 0, gbl.MAP_WIDTH, gbl.MAP_HEIGHT, 0, 0)

    # prepare to render the GUI panel
    rs.panel.clear(fg=colors.white, bg=colors.black)

    # print the game messages, one line at a time
    y = 1
    for (line, color) in rs.game_msgs:
        rs.panel.draw_str(gbl.MSG_X, y, line, bg=None, fg=color)
        y += 1

    # show the player's stats
    render_bar(1, 1, gbl.BAR_LENGTH, 'HP', player.fighter.curr_hp, player.fighter.hit_points,
               colors.light_red, colors.darker_red)

    # display names of objects under the mouse
    rs.panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    # blit the contents of "panel" to the root console
    rs.root.blit(rs.panel, 0, gbl.PANEL_Y, gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT, 0, 0)


def is_visible_tile(x, y):
    global world_map

    if x >= gbl.MAP_WIDTH or x < 0:
        return False
    elif y >= gbl.MAP_HEIGHT or y < 0:
        return False
    elif world_map[x][y].blocked:
        return False
    elif world_map[x][y].block_sight:
        return False
    else:
        return True