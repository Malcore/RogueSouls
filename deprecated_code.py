import random

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


def change_player_location(map_label):
    global map_changed

    if map_changed:
        if map_label == "city":
            if last_button is '1':
                current_map[MAP_WIDTH][0].entry()
                player.x = MAP_WIDTH - 1
                player.y = 0
            elif last_button is '2' or last_button is 'DOWN':
                current_map[MAP_WIDTH // 2][0].entry()
                player.x = MAP_WIDTH // 2
                player.y = 0
            elif last_button is '3':
                current_map[0][0].entry()
                player.x = 0
                player.y = 0
            elif last_button is '4' or last_button is 'LEFT':
                current_map[MAP_WIDTH - 1][MAP_HEIGHT // 2].entry()
                player.x = MAP_WIDTH - 1
                player.y = MAP_HEIGHT // 2
            elif last_button is '6' or last_button is 'RIGHT':
                current_map[0][MAP_HEIGHT // 2].entry()
                player.x = 0
                player.y = MAP_HEIGHT // 2
            elif last_button is '7':
                current_map[MAP_WIDTH - 1][MAP_HEIGHT - 1].entry()
                player.x = MAP_WIDTH - 1
                player.y = MAP_HEIGHT - 1
            elif last_button is '8' or last_button is 'UP':
                current_map[MAP_WIDTH // 2][MAP_HEIGHT - 1].entry()
                player.x = MAP_WIDTH // 2
                player.y = MAP_HEIGHT - 1
            elif last_button is '9':
                current_map[0][MAP_HEIGHT - 1].entry()
                player.x = 0
                player.y = MAP_HEIGHT - 1
        else:
            player.x, player.y = entry_coords


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


def make_world_map():
    # fill map with unblocked tiles
    world_map = [[Tile(False)
                 for y in range(MAP_HEIGHT)]
                 for x in range(MAP_WIDTH)]

    # Create fog border around map
    for i in range(MAP_WIDTH):
        world_map[i][0].red_fog()
        world_map[i][MAP_HEIGHT - 1].red_fog()
    for j in range(MAP_HEIGHT):
        world_map[0][j].red_fog()
        world_map[MAP_WIDTH - 1][j].red_fog()

    # Add other tiles
    world_map[1][1].path()
    world_map[1][2].path()
    world_map[1][3].path()
    world_map[1][4].plains()
    world_map[1][5].plains()
    world_map[1][6].forest()
    world_map[1][7].forest()
    world_map[1][8].forest()
    world_map[1][9].forest()
    world_map[1][10].forest()

    world_map[2][1].mountain()
    world_map[2][2].mountain()
    world_map[2][3].mountain()
    world_map[2][4].path()
    world_map[2][5].plains()
    world_map[2][6].forest()
    world_map[2][7].forest()
    world_map[2][8].forest()
    world_map[2][9].forest()
    world_map[2][10].forest()

    world_map[3][1].mountain()
    world_map[3][2].city()
    world_map[3][3].mountain()
    world_map[3][4].path()
    world_map[3][5].mountain()
    world_map[3][6].red_fog()

    world_map[4][1].mountain()
    world_map[4][2].path()
    world_map[4][3].mountain()
    world_map[4][4].path()
    world_map[4][5].mountain()
    world_map[4][6].red_fog()

    world_map[5][1].path()
    world_map[5][2].mountain()
    world_map[5][3].mountain()
    world_map[5][4].path()
    world_map[5][5].mountain()
    world_map[5][6].red_fog()

    world_map[6][1].mountain()
    world_map[6][2].path()
    world_map[6][3].dungeon()
    world_map[6][4].mountain()
    world_map[6][5].mountain()
    world_map[6][6].red_fog()

    world_map[7][1].mountain()
    world_map[7][2].mountain()
    world_map[7][3].mountain()
    world_map[7][4].mountain()
    world_map[7][5].red_fog()
    world_map[7][6].red_fog()

    change_map(world_map, "world")


def read_level(level_dict):
    global tile_types, weather_types, level_map, weather_map, map_tiles, map_weather_types
    level_map = [[Tile(False)
                    for y in range(MAP_HEIGHT)]
                    for x in range(MAP_WIDTH)]
    weather_map = [[WeatherEffects()
                    for y in range(MAP_HEIGHT)]
                    for x in range(MAP_WIDTH)]

    for item in level_dict:
        if item in tile_types:
            map_tiles.append(item)
        elif item in weather_types:
            map_weather_types.append(item)

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            getattr(level_map[x][y], level_dict['bg'])()

    for tile_type in map_tiles:
        if len(level_dict[tile_type]) > 0:
            for coord_range in level_dict[tile_type]:
                for y in range(coord_range[0][1], coord_range[1][1] + 1):
                    for x in range(coord_range[0][0], coord_range[1][0] + 1):
                        getattr(level_map[x][y], tile_type)()

    for weather_type in map_weather_types:
        if len(level_dict[weather_type]) > 0:
            for coord_range in level_dict[weather_type]:
                for y in range(coord_range[0][1], coord_range[1][1] + 1):
                    for x in range(coord_range[0][0], coord_range[1][0] + 1):
                        getattr(weather_map[x][y], weather_type)()

    return(level_map, weather_map, level_dict['label'])

tile_types = []
weather_types = []
map_weather_types = []