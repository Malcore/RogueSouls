import math
import tdl
import colors

from Globals import *
import Utils as utl
from Console import menu


class Fighter:
    # defines something that can take combat actions (e.g. any living character) and gives them combat statistics as
    # well as defining actions they can take during combat
    def __init__(self, vig=0, att=0, end=0, strn=0, dex=0, intl=0, fai=0, luc=0, wil=0, equip_load=0, poise=0, item_dis=0,
                 att_slots=0, right1=None, right2=None, left1=None, left2=None, head=None, chest=None, legs=None,
                 arms=None, ring1=None, ring2=None, neck=None, def_phys=0, def_slash=0, def_blunt=0, def_piercing=0,
                 def_mag=0, def_fire=0, def_lightn=0, def_dark=0, res_bleed=0, res_poison=0, res_frost=0, res_curse=0,
                 bleed_amt=0, poison_amt=0, frost_amt=0, curse_amt=0, facing=None, level=1, soul_value=0, wait_time=0,
                 dodge_frames=DODGE_TIME, inventory=[], blocking=False, death_func=None, ai=None):
        self.vig = vig
        self.att = att
        self.end = end
        self.strn = strn
        self.dex = dex
        self.intl = intl
        self.fai = fai
        self.luc = luc
        self.wil = wil
        self.equip_load = equip_load
        self.poise = poise
        self.item_dis = item_dis
        self.att_slots = att_slots
        self.right1 = right1
        self.right2 = right2
        self.left1 = left1
        self.left2 = left2
        self.head = head
        self.chest = chest
        self.legs = legs
        self.arms = arms
        self.ring1 = ring1
        self.ring2 = ring2
        self.neck = neck
        self.def_phys = def_phys
        self.def_slash = def_slash
        self.def_blunt = def_blunt
        self.def_piercing = def_piercing
        self.def_mag = def_mag
        self.def_fire = def_fire
        self.def_lightn = def_lightn
        self.def_dark = def_dark
        self.res_bleed = res_bleed
        self.res_poison = res_poison
        self.res_frost = res_frost
        self.res_curse = res_curse
        self.bleed_amt = bleed_amt
        self.poison_amt = poison_amt
        self.frost_amt = frost_amt
        self.curse_amt = curse_amt
        self.facing = facing
        self.level = level
        self.soul_value = soul_value
        self.wait_time = wait_time
        self.dodge_frames = dodge_frames
        self.inventory = inventory
        self.action_queue = []
        self.blocking = blocking
        self.death_func = death_func
        self.ai = ai

        # let the ai component know who owns it
        if self.ai:
            self.ai.owner = self

        # Beginning of derived statistics

        # Vigor effects
        # hp = 2E-07x^6 - 7E-05x^5 + 0.0071x^4 - 0.3803x^3 + 9.908x^2 - 81.809x + 533.94
        # 403 hp at base (10) vigor
        # +0.4 res/vig and 0.2 def/vig
        self.hit_points = int(math.ceil(40*self.vig - 1.15*self.vig))
        self.def_lightn += 0.4 * self.vig
        self.def_mag += 0.4 * self.vig
        self.def_fire += 0.4 * self.vig
        self.def_lightn += 0.4 * self.vig
        self.def_dark += 0.4 * self.vig
        self.res_bleed += 0.2 * self.vig
        self.res_poison += 0.2 * self.vig
        self.res_frost += 0.2 * self.vig
        self.res_curse += 0.2 * self.vig

        # Attunement effects
        # TODO: attunement stat effects
        self.att_points = 10

        # Endurance effects
        # stamina = 0.0184x2 + 1.2896x + 78.73
        # 88 stamina at base (10) endurance
        # +1.1 lightning res/end, + 0.4 other res/end, and +0.2 elemental def/end
        self.stamina = math.floor((0.0184 * self.end ** 2) + (1.2896 * self.end) + 78.73)
        self.def_lightn += 1.1 * self.end
        self.def_mag += 0.4 * self.end
        self.def_fire += 0.4 * self.end
        self.def_lightn += 0.4 * self.end
        self.def_dark += 0.4 * self.end
        self.res_bleed += 0.2 * self.end
        self.res_poison += 0.2 * self.end
        self.res_frost += 0.2 * self.end
        self.res_curse += 0.2 * self.end

        # Strength effects
        # TODO: strength stat effects

        # Dexterity effects
        # TODO: show effects of dex on dodge frames
        self.dodge_frames += self.dex

        # Intelligence effects
        # TODO: intelligence stat effects

        # Faith effects
        # TODO: faith stat effects

        # Luck effects
        # TODO: luck stat effects

        # Will effects
        # TODO: will stat effects

        # Other statistics
        self.curr_hp = self.hit_points
        self.curr_ap = self.att_points
        self.curr_sp = self.stamina
        self.curr_r = right1
        self.curr_l = left2

    def handle_attack_move(self, side, type):
        keypress = False
        while not keypress:
            for event in tdl.event.get():
                if event.type == 'KEYDOWN':
                    user_input = event
                    keypress = True

        if user_input.key == 'UP' or user_input.key == 'TEXT' and user_input.text == '8':
            self.attack_handler(side, (0, -1), type)

        elif user_input.key == 'DOWN' or user_input.key == 'TEXT' and user_input.text == '2':
            self.attack_handler(side, (0, 1), type)

        elif user_input.key == 'LEFT' or user_input.key == 'TEXT' and user_input.text == '4':
            self.attack_handler(side, (-1, 0), type)

        elif user_input.key == 'RIGHT' or user_input.key == 'TEXT' and user_input.text == '6':
            self.attack_handler(side, (1, 0), type)

        elif user_input.key == 'TEXT':
            if user_input.text == '7':
                self.attack_handler(side, (-1, -1), type)

            elif user_input.text == '9':
                self.attack_handler(side, (1, -1), type)

            elif user_input.text == '1':
                self.attack_handler(side, (-1, 1), type)

            elif user_input.text == '3':
                self.attack_handler(side, (1, 1), type)

    def attack_handler(self, side, dir, type):
        if side == "right":
            wep = utl.get_equipped_in_slot(self, "right1")
        else:
            wep = utl.get_equipped_in_slot(self, "left1")
        if wep is None:
            wep_name = "Unarmed"
        else:
            wep_name = wep.owner.owner.name
        wep_dict = utl.get_wep_dict(wep_name)
        dmg_type_dict = utl.get_style_from_dict(wep_dict[1][0])
        if type == "normal":
            speed = wep_dict[1][2]
        else:
            speed = wep_dict[1][3]
        self.attack(dmg_type_dict[1][0], speed, dir, type, wep_dict[1][1])

    def attack(self, dmg_type, speed, dir, type, dmg):
        target = None
        for obj in objects:
            if (obj.x - player.x, obj.y - player.y) == dir:
                target = obj
        if target:
            self.att_damage(target.fighter, dmg_type, type, int(dmg))
        self.wait_time += int(speed)

    def dodge(self):
        # TODO: add frames equal to speed plus bonuses to wait_time
        self.wait_time += DODGE_TIME

    def parry(self):
        # TODO: implement parry system
        self.wait_time += PARRY_SPEED
        return self

    def block(self):
        # TODO: implement blocking system
        self.wait_time += BLOCK_SPEED
        return self

    # function is called each frame during combat
    def take_action(self, action):
        if self.wait_time > 0:
            self.wait_time -= 1
        else:
            action()

    def att_damage(self, target, dmg_type, type, dmg):
        died = False
        eff_list = []
        if dmg_type == "slash" or dmg_type == "blunt" or dmg_type == "pierce":
            died = deal_phys_dmg(target, type, dmg, dmg_type)
        if dmg_type == "mag":
            died = deal_mag_dmg(target, type)
        if dmg_type == "fire":
            died = deal_fire_dmg(target, type)
        if dmg_type == "lightn":
            died = deal_lightn_dmg(target, type)
        if dmg_type == "dark":
            died = deal_dark_dmg(target, type)
        if "bleed" in eff_list:
            add_bleed(target, self.curr_r)
        if "poison" in eff_list:
            add_poison(target, self.curr_r)
        if "frost" in eff_list:
            add_frost(target, self.curr_r)
        if "curse" in eff_list:
            add_curse(target, self.curr_r)
        if died:
            utl.message(str(target.owner.name) + "has died!")
            target.death()

    def death(self):
        # TODO: (bug) tile does not appear after removal of creature char, before player action
        if self.death_func:
            func = self.death_func
            func()
        else:
            basic_death()

    def equip(self, item):
        success = False
        options = ['Head', 'Chest', 'Arms', 'Legs', 'Neck', 'Right Hand', 'Left Hand', 'Right Ring', 'Left Ring',
                   'Right Hand Quick Slot', 'Left Hand Quick Slot']
        choice = menu("Equip in which slot?", options, SCREEN_WIDTH)
        if choice is None or choice > len(options):
            return
        if choice is 0 and item.equippable_at is 'head':
            self.head = item
            item.equipped_at = 'head'
            success = True
        elif choice is 1 and item.equippable_at is 'chest':
            self.chest = item
            item.equipped_at = 'chest'
            success = True
        elif choice is 2 and item.equippable_at is 'arms':
            self.arms = item
            item.equipped_at = 'arms'
            success = True
        elif choice is 3 and item.equippable_at is 'legs':
            self.legs = item
            item.equipped_at = 'legs'
            success = True
        elif choice is 4 and item.equippable_at is 'neck':
            self.neck = item
            item.equipped_at = 'neck'
            success = True
        elif choice is 5 and item.equippable_at is 'hand':
            self.right1 = item
            item.equipped_at = 'right1'
            success = True
        elif choice is 6 and item.equippable_at is 'hand':
            self.left1 = item
            item.equipped_at = 'left1'
            success = True
        elif choice is 7 and item.equippable_at is 'ring':
            self.ring1 = item
            item.equipped_at = 'ring1'
            success = True
        elif choice is 8 and item.equippable_at is 'ring':
            self.ring2 = item
            item.equipped_at = 'ring2'
            success = True
        elif choice is 9 and item.equippable_at is 'hand':
            self.right2 = item
            item.equipped_at = 'right2'
            success = True
        elif choice is 10 and item.equippable_at is 'hand':
            self.left2 = item
            item.equipped_at = 'left2'
            success = True
        if success:
            item.is_equipped = True
            utl.message('Equipped ' + item.owner.owner.name + ' on ' + options[choice] + '.', colors.light_green)

    # unequip object and show a message about it
    def unequip(self, item):
        if not item.is_equipped:
            return
        utl.message('Unequipped ' + item.owner.owner.name + ' from ' + item.slot + '.', colors.light_green)
        setattr(self, str(item.equipped_at), None)
        item.is_equipped = False
        item.equipped_at = None


    def basic_death(self):
        for obj in objects:
            if obj is self.owner:
                objects.remove(obj)
                del obj


#################################
# damage functions
#################################
def deal_phys_dmg(target, type, dmg, dmg_type=None):
    dmg_reduc = target.def_phys / 100
    if target.blocking:
        dmg_reduc += target.curr_l.def_phys / 100
    if dmg_type is "slashing":
        dmg_reduc += target.def_slash / 100
    elif dmg_type is "blunt":
        dmg_reduc += target.def_blunt / 100
    elif dmg_type is "piercing":
        dmg_reduc += target.def_piercing / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    elif type == "special":
        dmg = dmg * 1.5
    final_dmg = math.ceil(dmg - round(dmg_reduc * dmg))
    target.curr_hp -= final_dmg
    if target.curr_hp <= 0:
        return True
    utl.message(str(target.owner.name) + " was dealt " + str(final_dmg) + " damage!")


def deal_mag_dmg(target, curr_wep):
    dmg_reduc = target.def_mag / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_mag - round(dmg_reduc * curr_wep.dmg_mag)
    if target.curr_hp <= 0:
        return True


def deal_fire_dmg(target, curr_wep):
    dmg_reduc = target.def_fire / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_fire - round(dmg_reduc * curr_wep.dmg_fire)
    if target.curr_hp <= 0:
        return True


def deal_lightn_dmg(target, curr_wep):
    dmg_reduc = target.def_lightn / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_lightn - round(dmg_reduc * curr_wep.dmg_lightn)
    if target.curr_hp <= 0:
        return True


def deal_dark_dmg(target, curr_wep):
    dmg_reduc = target.def_dark / 100
    if dmg_reduc > 1:
        dmg_reduc = 1
    target.curr_hp -= curr_wep.dmg_dark - round(dmg_reduc * curr_wep.dmg_dark)
    if target.curr_hp <= 0:
        return True


#################################
# functions for damage effects
#################################
def add_bleed(target, curr_wep):
    target.bleed_amt += curr_wep.eff_bleed - round(target.res_bleed / 100 * curr_wep.eff_bleed)


def add_poison(target, curr_wep):
    target.poison_amt += curr_wep.eff_poison - round(target.res_poison / 100 * curr_wep.eff_poison)


def add_frost(target, curr_wep):
    target.frost_amt += curr_wep.eff_frost - round(target.res_frost / 100 * curr_wep.eff_frost)


def add_curse(target, curr_wep):
    target.curse_amt += curr_wep.eff_curse - round(target.res_curse / 100 * curr_wep.eff_curse)