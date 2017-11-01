# Global variables
LIMIT_FPS = 20

# actual size of the window in characters (or 960x720 pixels)
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 50

# size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 38

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
WORLD_FOV_RAD = 3
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

# Non-Constant Globals

# Game-wide vars
objects = []
game_msgs = []
player = None
player_action = False

# World/Map vars
last_button = ''
entry_coords = (1, 1)
player_action = None
mouse_coord = (0, 0)
current_map = False
map_changed = False

# render_all() vars
fov_recompute = True
visible_tiles = False