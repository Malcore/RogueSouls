import RogueSoulsGlobals as gbl
import Tile


############################################
# map and world functions
############################################
def make_world_map():
    global world_map

    # fill map with unblocked tiles
    world_map = [[Tile.Tile(False)
                 for y in range(gbl.MAP_HEIGHT)]
                 for x in range(gbl.MAP_WIDTH)]

    world_map[0][0].fog()
    world_map[0][1].fog()
    world_map[0][2].fog()
    world_map[0][3].fog()
    world_map[0][4].fog()
    world_map[0][5].fog()
    world_map[0][6].fog()
    world_map[0][7].fog()
    world_map[0][8].fog()
    world_map[0][9].fog()
    world_map[0][10].fog()
    world_map[0][11].fog()
    world_map[0][12].fog()
    world_map[0][13].fog()
    world_map[0][14].fog()
    world_map[0][15].fog()
    world_map[0][16].fog()
    world_map[0][17].fog()
    world_map[0][18].fog()
    world_map[0][19].fog()
    world_map[0][20].fog()
    world_map[0][21].fog()
    world_map[0][22].fog()
    world_map[0][23].fog()
    world_map[0][24].fog()
    world_map[0][25].fog()
    world_map[0][20].fog()
    world_map[0][21].fog()
    world_map[0][22].fog()
    world_map[0][23].fog()
    world_map[0][24].fog()
    world_map[0][25].fog()
    world_map[0][26].fog()
    world_map[0][27].fog()
    world_map[0][28].fog()
    world_map[0][29].fog()
    world_map[0][30].fog()
    world_map[0][31].fog()
    world_map[0][32].fog()
    world_map[0][33].fog()
    world_map[0][34].fog()
    world_map[0][35].fog()
    world_map[0][36].fog()
    world_map[0][37].fog()

    world_map[1][0].fog()
    world_map[1][1].path()
    world_map[1][2].path()
    world_map[1][3].path()
    world_map[1][4].plains()
    world_map[1][5].plains()
    world_map[1][6].forest()
    world_map[1][7].forest()
    world_map[1][8].desert()
    world_map[1][9].swamp()
    world_map[1][10].water()
    world_map[1][37].fog()

    world_map[2][0].fog()
    world_map[2][1].mountain()
    world_map[2][2].mountain()
    world_map[2][3].mountain()
    world_map[2][4].path()
    world_map[2][5].plains()
    world_map[2][6].forest()
    world_map[2][7].forest()
    world_map[2][37].fog()

    world_map[3][0].fog()
    world_map[3][1].mountain()
    world_map[3][2].city()
    world_map[3][3].mountain()
    world_map[3][4].path()
    world_map[3][5].mountain()
    world_map[3][6].fog()
    world_map[3][37].fog()

    world_map[4][0].fog()
    world_map[4][1].mountain()
    world_map[4][2].path()
    world_map[4][3].mountain()
    world_map[4][4].path()
    world_map[4][5].mountain()
    world_map[4][6].fog()
    world_map[4][37].fog()

    world_map[5][0].fog()
    world_map[5][1].path()
    world_map[5][2].mountain()
    world_map[5][3].mountain()
    world_map[5][4].path()
    world_map[5][5].mountain()
    world_map[5][6].fog()
    world_map[5][37].fog()

    world_map[6][0].fog()
    world_map[6][1].mountain()
    world_map[6][2].path()
    world_map[6][3].dungeon()
    world_map[6][4].mountain()
    world_map[6][5].mountain()
    world_map[6][6].fog()
    world_map[6][37].fog()

    world_map[7][0].fog()
    world_map[7][1].mountain()
    world_map[7][2].mountain()
    world_map[7][3].mountain()
    world_map[7][4].mountain()
    world_map[7][5].fog()
    world_map[7][6].fog()
    world_map[7][37].fog()

    world_map[8][37].fog()

    world_map[9][37].fog()

    world_map[10][37].fog()

    world_map[11][37].fog()

    world_map[12][37].fog()

    world_map[13][37].fog()

    world_map[14][37].fog()

    world_map[15][37].fog()

    world_map[16][37].fog()

    world_map[17][37].fog()

    world_map[18][37].fog()

    world_map[19][37].fog()

    world_map[20][37].fog()
