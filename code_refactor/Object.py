import math

import RogueSoulsGlobals as gbl
import RogueSoulsUtils as rsu
import RogueSouls as rs


class Object:
    def __init__(self, x, y, char, name, color, blocks=True,
                 always_visible=False, block_sight=True, fighter=None, item=None, player=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.block_sight = block_sight

        self.fighter = fighter
        # let the fighter component know who owns it
        if self.fighter:
            self.fighter.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.player = player
        if self.player:
            self.player.owner = self

    def move(self, dx, dy):
        global fov_recompute
        # move by the given amount
        if self.x + dx > gbl.MAP_WIDTH - 1 or self.x + dx < 0:
            return
        elif self.y + dy > gbl.MAP_HEIGHT - 1 or self.y + dy < 0:
            return
        for obj in objects:
            if obj.x is self.x + dx and obj.y is self.y + dy:
                if self.player:
                    fov_recompute = True
                return
        if not rsu.is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
        if self.player:
            fov_recompute = True

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        # return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def draw(self):
        global visible_tiles

        if (self.x, self.y) in visible_tiles:
            # set the color and then draw the character that represents this object at its position
            rs.con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self):
        # erase the character that represents this object
        rs.con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def send_to_back(self):
        # make this object be drawn first, so all others appear above it if they're in the same tile
        global objects
        objects.remove(self)
        objects.insert(0, self)