import dictionaries as dicts


class AI:
    def __init__(self, name=None, flag="def", move_set=[]):
        self.name = name
        self.flag = flag
        self.move_set = move_set

    def build_queue(self):
        if self.name is None:
            return
        else:
            self.move_set = dicts['AI'][self.name][self.flag]