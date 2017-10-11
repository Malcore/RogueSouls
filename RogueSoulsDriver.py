import sys
import tdl
import colors
import RogueSoulsGlobals as gbl
import RogueSoulsUtils as rsu
import Object
import Player
import Fighter
import Item
import Equipment
import WorldMap


tdl.set_font('terminal12x12_gs_ro.png', greyscale=True, altLayout=False)
tdl.setFPS(gbl.LIMIT_FPS)
root = tdl.init(gbl.SCREEN_WIDTH, gbl.SCREEN_HEIGHT, title="RogueSouls", fullscreen=False)
con = tdl.Console(gbl.MAP_WIDTH, gbl.MAP_HEIGHT)
panel = tdl.Console(gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT)
objects = []  # everything in the game that isn't a tile
game_msgs = []  # buffer of the messages that appear on the screen


def main():
    root.draw_str(gbl.SCREEN_WIDTH // 2 - 7, gbl.SCREEN_HEIGHT // 2 - 12, 'RogueSouls', fg=colors.crimson,
                  bg=colors.darkest_han)
    root.draw_str(gbl.SCREEN_WIDTH // 2 - 8, gbl.SCREEN_HEIGHT // 2 - 10, 'By Jerezereh')

    fov_recompute = True
    player_action = None
    mouse_coord = (0, 0)

    main_menu()


############################################
# intro screen functions
############################################
def main_menu():
    # img = libtcod.image_load('menu_background2.png')
    game_state = 'menu'

    while not tdl.event.is_window_closed():
        # show the background image, at twice the regular console resolution
        # libtcod.image_blit_2x(img, 0, 8, 3)

        # show options and wait for the player's choice
        choice = rsu.menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        # new game
        if choice is 0:
            new_game(objects)
            play_game()
        elif choice is 1:
            pass
        # quit
        elif choice is 2:
            quit_game()


def new_game(objects):
    global player, game_msgs, game_state

    # first create the player out of its components
    player_comp = Player.Player()
    fighter_comp = Fighter.Fighter(10, 10, 10, 10, 10, 10, 10, 10, 15)
    player = Object.Object(1, 1, '@', "Player", colors.gray, fighter=fighter_comp, player=player_comp)
    objects.append(player)

    #ai_comp = AI('ConstantAttack')
    #enemy_fighter_comp = Fighter(1, 1, 1, 1, 1, 1, 1, 1, 1, ai=ai_comp)
    #enemy = Object(0, 0, 'T', "Test Enemy", colors.dark_red, fighter=enemy_fighter_comp)
    #objects.append(enemy)

    # generate world map (at this point it's not drawn to the screen)
    WorldMap.make_world_map()

    game_state = 'playing'

    # a warm welcoming message!
    rsu.message('You awaken with a burning desire. You feel as if you should recognize this place. The walls are covered in'
            ' rot and the stench of death is in the air.', colors.red)

    # initial equipment: a broken sword
    equipment_component = Equipment.Equipment(slot='hand', durability=10, equippable_at = 'hand')
    item_comp = Item.Item(weight=2, uses=0, equipment=equipment_component)
    sword = Object.Object(0, 0, '-', name="Broken Sword", color=colors.sky, block_sight=False, item=item_comp,
                   always_visible=True)
    player.fighter.inventory.append(sword)
    player.fighter.equip(equipment_component)
    play_game()


def play_game():
    # player_action = None
    WorldMap.make_world_map()
    game_state = 'playing'

    # main loop
    while not tdl.event.is_window_closed():
        # draw all objects in the list
        render_all()
        tdl.flush()

        # handle keys and exit game if needed
        player_action = rsu.handle_keys()
        if player_action == 'exit':
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in objects:
                if obj.fighter.ai:
                    # obj.fighter.ai.take_turn()
                    pass


def quit_game():
    sys.exit()


def render_all():
    global fov_recompute
    global visible_tiles
    global player

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y, rsu.is_visible_tile, fov=gbl.FOV_ALGO, radius=gbl.WORLD_FOV_RAD, lightWalls=gbl.FOV_LIGHT_WALLS)

        # go through all tiles, and set their background color according to the FOV
        for y in range(gbl.MAP_HEIGHT):
            for x in range(gbl.MAP_WIDTH):
                visible = (x, y) in visible_tiles
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if WorldMap.world_map[x][y].explored:
                        # print(x, y)
                        print("driver func")
                        con.draw_char(x, y, WorldMap.world_map[x][y].char, WorldMap.world_map[x][y].fog_color, bg=None)
                else:
                    print("driver func")
                    con.draw_char(x, y, WorldMap.world_map[x][y].char, WorldMap.world_map[x][y].vis_color, bg=None)
                    # since it's visible, explore it
                    WorldMap.world_map[x][y].explored = True

    # draw all objects in the list
    for obj in objects:
        if obj != player:
            obj.draw()
    player.draw()
    # blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, gbl.MAP_WIDTH, gbl.MAP_HEIGHT, 0, 0)

    # prepare to render the GUI panel
    panel.clear(fg=colors.white, bg=colors.black)

    # print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        panel.draw_str(gbl.MSG_X, y, line, bg=None, fg=color)
        y += 1

    # show the player's stats
    rsu.render_bar(1, 1, gbl.BAR_LENGTH, 'HP', player.fighter.curr_hp, player.fighter.hit_points,
               colors.light_red, colors.darker_red)

    # display names of objects under the mouse
    panel.draw_str(1, 0, rsu.get_names_under_mouse(), bg=None, fg=colors.light_gray)

    # blit the contents of "panel" to the root console
    root.blit(panel, 0, gbl.PANEL_Y, gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT, 0, 0)

if __name__ == "__main__": main()