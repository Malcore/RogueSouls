import math
import random
import textwrap
import colors
import tdl
import dictionaries as dicts

import Globals as gbl


############################################
# menus and related functions
############################################
def message(new_msg, color=colors.white):
    # split the message, if necessary, across multiple lines
    new_msg_lines = textwrap.wrap(new_msg, gbl.MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for the new one
        if len(gbl.game_msgs) == gbl.MSG_HEIGHT:
            del gbl.game_msgs[0]

        # add the new lines as a tuple, with text and color
            gbl.game_msgs.append((line, color))


def msgbox(text, width=0):
    # use menu() as a sort of "message box"
    menu(0, 0, text, [], width)


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
    if gbl.current_map[x][y].blocked:
        return True

    # now check for any blocking objects
    for obj in gbl.objects:
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
    for obj in gbl.objects:
        if obj.x is x and obj.y is y:
            return obj
    return None


def pick_up():
    for obj in gbl.objects:
        if obj.x is player.x and obj.y is player.y:
            player.fighter.inventory.append(obj)

############################################
# player interactions functions
############################################
def handle_keys():
    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            gbl.mouse_coord = event.cell

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

    if gbl.game_state == 'playing':
        # movement keys
        if user_input.key == 'UP' or user_input.key == 'TEXT' and user_input.text == '8':
            gbl.player.move(0, -1)

        elif user_input.key == 'DOWN' or user_input.key == 'TEXT' and user_input.text == '2':
            gbl.player.move(0, 1)

        elif user_input.key == 'LEFT' or user_input.key == 'TEXT' and user_input.text == '4':
            gbl.player.move(-1, 0)

        elif user_input.key == 'RIGHT' or user_input.key == 'TEXT' and user_input.text == '6':
            gbl.player.move(1, 0)

        elif user_input.key == 'TEXT':
            if user_input.text == '7':
                gbl.player.move(-1, -1)

            elif user_input.text == '9':
                gbl.player.move(1, -1)

            elif user_input.text == '1':
                gbl.player.move(-1, 1)

            elif user_input.text == '3':
                gbl.player.move(1, 1)

            elif user_input.text == 'i':
                choice = inventory_menu()
                if choice is not None:
                    item = player.fighter.inventory[choice]
                    gbl.player.fighter.equip(item.item.equipment)

            elif user_input.text == 'e':
                equip_or_unequip(equipment_menu())

            # force quit key?
            elif user_input.text == 'Q':
                exit()

            elif user_input.text == 'd':
                drop_menu()

            elif user_input.text == ',':
                gbl.player.fighter.handle_attack_move("left", "special")

            elif user_input.text == '.':
                gbl.player.fighter.handle_attack_move("right", "special")

            elif user_input.text == 'k':
                gbl.player.fighter.handle_attack_move("left", "normal")

            elif user_input.text == 'l':
                gbl.player.fighter.handle_attack_move("right", "normal")
            elif user_input.text == '>':
                change_location()
            else:
                print(user_input.text)


def get_names_under_mouse():
    # return a string with the names of all objects under the mouse
    (x, y) = gbl.mouse_coord

    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in gbl.objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in gbl.visible_tiles]

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


def next_floor():
    return


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


############################################
# map and world functions
############################################
def generate_city():
    city_map = [[Tile(False)
                for y in range(MAP_HEIGHT)]
                for x in range(MAP_WIDTH)]
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            city_map[x][y].plains()

    """
    # logic for city map generation
    1. divide map into sectors (residential, governmental, etc)
    2. create roads between sectors
    2. generate random buildings corresponding to sector type
    3. delete buildings intersecting roads or other buildings
    4. add additional structures/features in open spaces
    5. add characters

    # pseudocode
    
    # create randomized number of sectors
    num_sectors = random.randint(4, 8)
    sector_width = MAP_WIDTH - 1 / num_sectors / 2
    sector_height = MAP_HEIGHT - 1 / num_sectors / 2

    # create individual sector maps
    # first create sectors dictionary, then create a sector map item for each sector
    sectors = {}
    for i in range(num_sectors):
        sectors["sector_map{0}".format(i)] = random.choice(dicts.sector_list)

    # next add each x and y coordinate within that sector to that sector's item
    for x i range(num_sectors):
        for y in range(sector_height + x * sector_height):
            for x in range(sector_width + x * sector_width):
                sectors["sector_map{1}".format(i)] += str(x, y)

    # add roads between sectors
    for j in range(num_sectors):
        if(x,y) not in sectors[sector_map{1}.format(j)]:
            city_map[x][y].path()

    # add random buildings to each sector
    for k in range(num_sectors):
        if sectors[sector_map{0}.format(k)] = 'res':
            # add res buildings
        elif sectors[sector_map{0}.format(k)] = 'gov':
            # add gov buildings
        elif sectors[sector_map{0}.format(k)] = 'mil':
            # add mil buildings
    """
    

    # city_map[random.randint(0, MAP_WIDTH)][random.randint(0, MAP_HEIGHT)].entry()

    return city_map


def enter_location(x, y):
    global entry_coords

    entry_coords = (x, y)
    if current_map[x][y].char is 'o':
        message('You enter the city...', colors.gold)
        change_map(generate_city(), "city")
    elif current_map[x][y].char is '*':
        message('You attempt to enter the dungeon, but a mysterious force blocks you...', colors.gold)
        # change_map(generate_dungeon(), "dungeon")


def exit_location(x, y):
    if current_map[x][y].char is '<':
        message('You leave the location and continue your quest.', colors.gold)
        change_map(old_map, "world")


def change_map(new_map, label):
    if gbl.current_map:
        gbl.old_map = gbl.current_map
    gbl.current_map = new_map
    gbl.fov_recompute = True
    gbl.map_changed = True
    change_player_location(label)
    gbl.objects = []
    gbl.objects.append(player)
    # objects.append(current_map.objects)


def change_player_location(map_label):
    if gbl.map_changed:
        if map_label == "city":
            if last_button is '1':
                current_map[gbl.MAP_WIDTH][0].entry()
                gbl.player.x = gbl.MAP_WIDTH - 1
                gbl.player.y = 0
            elif last_button is '2' or last_button is 'DOWN':
                current_map[gbl.MAP_WIDTH // 2][0].entry()
                gbl.player.x = gbl.MAP_WIDTH // 2
                gbl.player.y = 0
            elif last_button is '3':
                print("button is 3")
                current_map[0][0].entry()
                gbl.player.x = 0
                gbl.player.y = 0
            elif last_button is '4' or last_button is 'LEFT':
                current_map[gbl.MAP_WIDTH - 1][gbl.MAP_HEIGHT // 2].entry()
                gbl.player.x = gbl.MAP_WIDTH - 1
                gbl.player.y = gbl.MAP_HEIGHT // 2
            elif last_button is '6' or last_button is 'RIGHT':
                current_map[0][gbl.MAP_HEIGHT // 2].entry()
                gbl.player.x = 0
                gbl.player.y = MAP_HEIGHT // 2
            elif last_button is '7':
                current_map[gbl.MAP_WIDTH - 1][gbl.MAP_HEIGHT - 1].entry()
                gbl.player.x = MAP_WIDTH - 1
                gbl.player.y = MAP_HEIGHT - 1
            elif last_button is '8' or last_button is 'UP':
                current_map[gbl.MAP_WIDTH // 2][gbl.MAP_HEIGHT - 1].entry()
                gbl.player.x = gbl.MAP_WIDTH // 2
                gbl.player.y = gbl.MAP_HEIGHT - 1
            elif last_button is '9':
                current_map[0][gbl.MAP_HEIGHT - 1].entry()
                gbl.player.x = 0
                gbl.player.y = gbl.MAP_HEIGHT - 1
        elif map_label is "world":
            gbl.player.x, gbl.player.y = entry_coords
