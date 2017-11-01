import sys
import tdl
import colors
import Globals as gbl
import Utils as utl
import Object
import Player
import Fighter
import Item
import Equipment
import AI
import WorldMap as wm
import Console as con


def main():
    con.root.draw_str(gbl.SCREEN_WIDTH // 2 - 7, gbl.SCREEN_HEIGHT // 2 - 12, 'RogueSouls', fg=colors.crimson,
                  bg=colors.darkest_han)
    con.root.draw_str(gbl.SCREEN_WIDTH // 2 - 8, gbl.SCREEN_HEIGHT // 2 - 10, 'By Jerezereh')

    fov_recompute = True
    player_action = None
    mouse_coord = (0, 0)

    main_menu()


############################################
# intro screen functions
############################################
def main_menu():
    # img = libtcod.image_load('menu_background2.png')
    gbl.game_state = 'menu'

    while not tdl.event.is_window_closed():
        # show the background image, at twice the regular console resolution
        # libtcod.image_blit_2x(img, 0, 8, 3)

        # show options and wait for the player's choice
        choice = con.menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

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
    global player

    # first create the player out of its components
    player_comp = Player.Player()
    fighter_comp = Fighter.Fighter(10, 10, 10, 10, 10, 10, 10, 10, 15)
    gbl.player = Object.Object(1, 1, '@', "Player", colors.gray, fighter=fighter_comp, player=player_comp)
    gbl.objects.append(gbl.player)

    #ai_comp = AI('ConstantAttack')
    #enemy_fighter_comp = Fighter(1, 1, 1, 1, 1, 1, 1, 1, 1, ai=ai_comp)
    #enemy = Object(0, 0, 'T', "Test Enemy", colors.dark_red, fighter=enemy_fighter_comp)
    #objects.append(enemy)

    # generate world map (at this point it's not drawn to the screen)
    gbl.current_map = wm.make_world_map()

    # a warm welcoming message!
    utl.message('You awaken with a burning desire to act. You feel as if you should recognize this place.', colors.red)

    # initial equipment: a broken sword
    equipment_component = Equipment.Equipment(slot='hand', durability=10, equippable_at = 'hand')
    item_comp = Item.Item(weight=2, uses=0, equipment=equipment_component)
    sword = Object.Object(0, 0, '-', name="Broken Sword", color=colors.sky, block_sight=False, item=item_comp,
                   always_visible=True)
    gbl.player.fighter.inventory.append(sword)
    # player.fighter.equip(equipment_component)
    play_game()


def play_game():
    global game_state
    # player_action = None
    gbl.game_state = 'playing'

    # main loop
    while not tdl.event.is_window_closed():
        # draw all objects in the list
        con.render_all()
        tdl.flush()

        # handle keys and exit game if needed
        player_action = utl.handle_keys()
        if player_action == 'exit':
            break

        # let monsters take their turn
        if gbl.game_state == 'playing' and gbl.player_action != 'didnt-take-turn':
            for obj in gbl.objects:
                if obj.fighter.ai:
                    # obj.fighter.ai.take_turn()
                    pass


def quit_game():
    sys.exit()


if __name__ == "__main__": main()