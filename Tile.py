import colors


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None, char=None, vis_color=None, fog_color=None):
        self.blocked = blocked

        # all tiles start unexplored
        self.explored = False

        # by default, if a tile is blocked, it also blocks sight
        if blocked is None:
            block_sight = blocked
        self.block_sight = block_sight

        self.char = char
        self.vis_color = vis_color
        self.fog_color = fog_color

    def city(self):
        self.blocked = False
        self.block_sight = False
        self.char = 'o'
        self.vis_color = colors.yellow
        self.fog_color = colors.dark_yellow

    def dungeon(self):
        self.blocked = False
        self.block_sight = True
        self.char = '*'
        self.vis_color = colors.darker_sepia
        self.fog_color = colors.darkest_sepia

    def fog(self):
        self.blocked = True
        self.block_sight = True
        self.char = chr(178)
        self.vis_color = colors.dark_crimson
        self.fog_color = colors.darker_crimson

    def mountain(self):
        self.blocked = True
        self.block_sight = True
        self.char = '^'
        self.vis_color = colors.gray
        self.fog_color = colors.dark_gray

    def path(self):
        self.blocked = False
        self.block_sight = False
        self.char = '.'
        self.vis_color = colors.darker_amber
        self.fog_color = colors.darkest_amber

    def plains(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(240)
        self.vis_color = colors.light_chartreuse
        self.fog_color = colors.chartreuse

    def water(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(247)
        self.vis_color = colors.blue
        self.fog_color = colors.dark_blue

    def swamp(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(59)
        self.vis_color = colors.darker_gray
        self.fog_color = colors.darkest_gray

    def desert(self):
        self.blocked = False
        self.block_sight = False
        self.char = chr(247)
        self.vis_color = colors.yellow
        self.fog_color = colors.desaturated_yellow

    def forest(self):
        self.blocked = False
        self.block_sight = True
        self.char = chr(209)
        self.vis_color = colors.dark_green
        self.fog_color = colors.darker_green