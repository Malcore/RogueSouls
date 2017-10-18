class Player:
    def __init__(self, hunger=0, covenant=None, souls=0, skillpoints=0):
        self.hunger = hunger
        self.covenant = covenant
        self.souls = souls
        self.skillpoints = skillpoints

    def level_up(self):
        self.owner.fighter.level += 1
        self.skillpoints += 1
        # TODO: implement level-up system