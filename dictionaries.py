from collections import namedtuple


# File for all dictionaries used in main file, such as items, timings, skills, etc.
SMAPW = 20
SMAPH = 20

SkillNode = namedtuple('SkillNode', ['description', 'effect', 'taken'])
WeaponDamageTypes = namedtuple('typeName', ['l_att', 'h_att'])
Weapon = namedtuple('weaponName', ['wep_type', 'damage', 'l_time', 'h_time'])
Fix = namedtuple('fix', ['bonus', 'stat', 'special_text', 'rarity'])

skills = {
    'skill1': SkillNode('Your skin hardens.', '+1 END', False),
    'skill2': SkillNode('Your moves grow quicker.', '+1 AGI', False),
    'skill3': SkillNode('Your mind sharpens.', '+1 PER', False),
    'skill4': SkillNode('Your faith strengthens.', '+1 FAI', False)
}

skillgraph = {
    'skill1': ['skill2', 'skill3'],
    'skill2': ['skill1', 'skill3'],
    'skill3': ['skill4'],
    'skill4': []
}

# damage types: basic: slash, blunt, pierce
# complex: thrust (slash/piercing), bludgeoning (blunt/piercing), chop (slash/blunt)
# weapon styles have
weapon_styles = {
    # fist weapons: punch, smash
    'fist': WeaponDamageTypes('blunt', 'blunt'),

    # small swords: underhanded swing, short thrust
    'small_sword': WeaponDamageTypes('slash', 'pierce'),

    # bastard swords: one-handed slash, overhead chop
    'bastard_sword': WeaponDamageTypes('slash', 'chop'),

    # long swords: two-handed slash, two-handed
    'long_swords': WeaponDamageTypes('thrust', 'slash')
}

weapons = {
    'Unarmed': Weapon('fist', '4', '7', '12'),
    'Broken Sword': Weapon('small_sword', '6', '10', '10'),
    'Short Sword': Weapon('small_sword', '15', '10', '12')
}

weapon_prefix = {
    '': '',
    'Hardened': Fix('+1', 'dmg', '', 'superior'),
    'Battered': Fix('-1', 'dmg', '', 'lq'),
    'Tiered': Fix('', '', '', 'superior')
}

weapon_affix = {
    '': '',
    'of the Moon': Fix('', '', 'Upon each successful hit, add an amount of SP to your pool equal to the damage the hit'
                               'dealt.', 'unique'),
    'of Storms': Fix(['+2', '-1'], ['int', 'vig'], '', 'rare')
}

armor_prefix = {
    '': ''
}

armor_affix = {
    '': ''
}

acc_prefix = {
    '': ''
}

acc_affix = {
    '': ''
}

# AI classified into profiles which will determine likelihood of enemy using actions. Each enemy has definitions of actions
#   and a chosen profile.
ai = {
    'aggressive': {

    },

    'basic': {
        'move_towards_or_attack': 100
    },

    'coward': {
        'move_away': 75,
        'move_towards_or_attack': 25
    },

    'none': {

    },

    # new ai system: each enemy has an ai profile and dictionary of possible actions, each action has
    #   a name, number of frames needed, 
    'prowler_hound': {
        'profile': 'coward',
        'queue_size': 2,
        'move': 5,
        'bite': ['attack', 10]
    }
}


possible_player_actions = ["MV N", "MV NE", "MV E", "MV SE", "MV S", "MV SW", "MV W", "MV NW", "WAIT", "PICK UP", ""]

# list of all items in game and in which dictionary their variables are specified in
items = {
    'soul_pool': 'map_items'
}

# list of all items that are interactable on map; map items cannot be picked up
map_items = {
    'soul_pool': {
        'char': 'O',
        'color': 'white',
        'fighter_interaction': None,
        'player_interaction': 'retrieve_souls',
        'object_interaction': None
    }
}

# list of all items that are consumable, such as potions or 'solid' souls
consumable_items = {}

# list of all items that can be equipped to a fighter object
equippable_items = {}

# dictionary of all fighters in game with all attributes of each
# most attributes are self-explanatory, but here is documentation of each stat in case
# char = character used to represent it on the screen
# color = color of the char
# vig = vigor stat
# att = attunement stat
# end = endurance stat
# ...
# level = level of the enemy
# soul_value = how many souls player receives
# morale = %hp at which the fighter loses its will to fight and runs (e.g. a 10 means fighter runs if at 10% hp or less)
fighters = {
    'cyclops': {
        'char': 'C',
        'color': 'gray',
        'vig': 1,
        'att': 1,
        'end': 1,
        'strn': 2,
        'dex': 2,
        'intl': 1,
        'fai': 0,
        'luc': 1,
        'wil': 0,
        'level': 1,
        'soul_value': 500,
        'morale': 10
    },

    'firekeeper': {
        'char': 'F',
        'color': 'red',
        'vig': 1,
        'att': 1,
        'end': 1,
        'strn': 2,
        'dex': 2,
        'intl': 1,
        'fai': 0,
        'luc': 1,
        'wil': 0,
        'level': 1,
        'soul_value': 100,
        'morale': 0
    },

    'hollow': {
        'char': 'h',
        'color': 'light_green',
        'vig': 1,
        'att': 0,
        'end': 1,
        'strn': 2,
        'dex': 2,
        'intl': 1,
        'fai': 0,
        'luc': 1,
        'wil': 0,
        'level': 1,
        'soul_value': 25,
        'morale': 0
    },

    'prowler_hound': {
        'char': 'r',
        'color': 'light_gray',
        'vig': 1,
        'att': 0,
        'end': 1,
        'strn': 2,
        'dex': 2,
        'intl': 1,
        'fai': 0,
        'luc': 1,
        'wil': 0,
        'level': 1,
        'soul_value': 10,
        'morale': 100
    }
}
