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

# AI Notation:
# Right-hand attack: R
# Left-hand attack: L
# Two-hand attack: T
# Block: B
# Dodge: D
# Wait: W
# Repeat pattern: +
# Attack Modifier (Heavy): H

# If AI attempts to attack with one-hand when wielding two-handed weapon, consume two one-handed inputs for each two-
# handed attack. E.g. if pattern is RLRR+ and creature only has two-handed weapon, pattern is converted to TT+.
# If an attack modifier is present, the attack changes accordingly. If an attack is being consumed to become a two-
# handed, it gains all modifiers of the individual attacks, if applicable (each modifier can only be applied once).
ai = {
    'basic': {
        'def': ['R', 'B', '+'],
        'dual': ['R', 'L', 'R', 'L', 'D', 'D', '+'],
        'th': ['T', 'T', 'B', 'B', '+']
    },

    'aggressive': {
        'def': ['R', 'R', 'R', 'R', 'W', '+'],
        'dual': ['R', 'L', 'R', 'L', 'R', 'L', 'W', '+'],
        'th': ['T', '+']
    },

    'none': {

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
        'soul_value': 500
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
        'soul_value': 100
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
        'soul_value': 25
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
        'soul_value': 10
    }
}
