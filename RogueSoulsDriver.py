import tdl
import colors
import RogueSoulsGlobals as gbl
import RogueSouls as rs


def __main__():
    #############################################
    # Initialization & Main Loop                #
    #############################################
    tdl.set_font('terminal12x12_gs_ro.png', greyscale=True, altLayout=False)
    tdl.setFPS(gbl.LIMIT_FPS)
    root = tdl.init(gbl.SCREEN_WIDTH, gbl.SCREEN_HEIGHT, title="RogueSouls", fullscreen=False)
    con = tdl.Console(gbl.MAP_WIDTH, gbl.MAP_HEIGHT)
    panel = tdl.Console(gbl.SCREEN_WIDTH, gbl.PANEL_HEIGHT)

    root.draw_str(gbl.SCREEN_WIDTH // 2 - 7, gbl.SCREEN_HEIGHT // 2 - 12, 'RogueSouls', fg=colors.crimson,
                  bg=colors.darkest_han)
    root.draw_str(gbl.SCREEN_WIDTH // 2 - 8, gbl.SCREEN_HEIGHT // 2 - 10, 'By Jerezereh')

    objects = []  # everything in the game that isn't a tile
    game_msgs = []  # buffer of the messages that appear on the screen

    fov_recompute = True
    player_action = None
    mouse_coord = (0, 0)

    rs.main_menu()
