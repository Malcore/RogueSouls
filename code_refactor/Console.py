import tdl
import textwrap
import colors
import os

import Globals as gbl
import Utils as utl


tdl.set_font(os.path.abspath('roguelike-development/code_refactor/terminal12x12_gs_ro.png'), greyscale=True,
             altLayout=False)
tdl.setFPS(gbl.LIMIT_FPS)
root = tdl.init(gbl.SCREEN_WIDTH, gbl.SCREEN_HEIGHT, title="RogueSouls", fullscreen=False)
con = tdl.Console(gbl.MAP_WIDTH, gbl.MAP_HEIGHT)
panel = tdl.Console(gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT)


def render_all():
    if gbl.map_changed:
        gbl.map_changed = False
        con.clear()
    
    if gbl.fov_recompute:
        gbl.fov_recompute = False
        gbl.visible_tiles = tdl.map.quickFOV(gbl.player.x, gbl.player.y, is_visible_tile, fov=gbl.FOV_ALGO,
                                             radius=gbl.WORLD_FOV_RAD, lightWalls=gbl.FOV_LIGHT_WALLS)

        # go through all tiles, and set their background color according to the FOV
        for y in range(gbl.MAP_HEIGHT):
            for x in range(gbl.MAP_WIDTH):
                visible = (x, y) in gbl.visible_tiles
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if gbl.current_map[x][y].explored:
                        con.draw_char(x, y, gbl.current_map[x][y].char, gbl.current_map[x][y].fog_color, bg=None)
                    else:
                        con.draw_char(x, y, None, None, bg=None)
                else:
                    con.draw_char(x, y, gbl.current_map[x][y].char, gbl.current_map[x][y].vis_color, bg=None)
                    # since it's visible, explore it
                    gbl.current_map[x][y].explored = True

    # draw all objects in the list for current map
    for obj in gbl.objects:
        if obj != gbl.player:
            draw(obj)
    draw(gbl.player)
    
    # blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, gbl.MAP_WIDTH, gbl.MAP_HEIGHT, 0, 0)

    # prepare to render the GUI panel
    panel.clear(fg=colors.white, bg=colors.black)

    # print the game messages, one line at a time
    y = 1
    for (line, color) in gbl.game_msgs:
        panel.draw_str(gbl.MSG_X, y, line, bg=None, fg=color)
        y += 1

    # show the player's stats
    render_bar(1, 1, gbl.BAR_LENGTH, 'HP', gbl.player.fighter.curr_hp, gbl.player.fighter.hit_points,
               colors.light_red, colors.darker_red)

    # display names of objects under the mouse
    panel.draw_str(1, 0, utl.get_names_under_mouse(), bg=None, fg=colors.light_gray)

    # blit the contents of "panel" to the root console
    root.blit(panel, 0, gbl.PANEL_Y, gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT, 0, 0)


def is_visible_tile(x, y):
    if x >= gbl.MAP_WIDTH or x < 0:
        return False
    elif y >= gbl.MAP_HEIGHT or y < 0:
        return False
    elif gbl.current_map[x][y].blocked:
        return False
    elif gbl.current_map[x][y].block_sight:
        return False
    else:
        return True


def draw(obj):
    if (obj.x, obj.y) in gbl.visible_tiles:
        # set the color and then draw the character that represents this object at its position
        con.draw_char(obj.x, obj.y, obj.char, obj.color, bg=None)


def clear(obj):
    # erase the character that represents this object
    con.draw_char(obj.x, obj.y, ' ', obj.color, bg=None)


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
