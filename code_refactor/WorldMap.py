import Tile
import Globals as gbl

############################################
# map and world functions
############################################
def make_world_map():
    # fill map with unblocked tiles
    world_map = [[Tile.Tile(False)
                 for y in range(gbl.MAP_HEIGHT)]
                 for x in range(gbl.MAP_WIDTH)]

    # Create fog border around map
    for i in range(gbl.MAP_WIDTH):
        world_map[i][0].red_fog()
        world_map[i][gbl.MAP_HEIGHT - 1].red_fog()
    for j in range(gbl.MAP_HEIGHT):
        world_map[0][j].red_fog()
        world_map[gbl.MAP_WIDTH - 1][j].red_fog()

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

    return world_map