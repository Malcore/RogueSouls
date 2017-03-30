from collections import namedtuple


# File for all dictionaries used in main file, such as items, timings, skills, etc.
SMAPW = 20
SMAPH = 20

SkillNode = namedtuple('SkillNode', ['description', 'effect', 'taken'])
WeaponDamageTypes = namedtuple('typeName', ['l_att', 'm_att', 'h_att'])
Weapon = namedtuple('weaponName', ['wep_type', 'damage', 'l_time', 'm_time', 'h_time'])

items = []

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

# damage types: basic: slashing, blunt, piercing
# complex: thrust (slash/piercing), bludgeoning (blunt/piercing), chop (slash/blunt)
# weapon styles have
weapon_styles = {
    # fist weapons: stab, punch, smash
    'fist': WeaponDamageTypes('piercing', 'blunt', 'blunt'),

    # small swords: underhanded swing, overhand/around swing, short thrust
    'small_sword': WeaponDamageTypes('slashing', 'slashing', 'piercing'),

    # bastard swords: one-handed thrust, two-handed slash, overhead chop
    'bastard_sword': WeaponDamageTypes('thrust', 'slash', 'chop')

    # long swords: two-handed slash, two-handed
}

weapons = {
    'Unarmed': Weapon('fist', '4', '7', '10', '2'),
    'Broken Sword': Weapon('small_sword', '10', '20', '35', '4'),
    'Short Sword': Weapon('small_sword', '15', '20', '30', '10')
}

weapon_att_styles = {'Broken Sword light': 'thrust', 'Broken Sword heavy': 'slash', 'Short Sword light': 'slash', 'Short Sword heavy': 'thrust'}
weapon_times = {'Broken Sword light': 10, 'Broken Sword heavy': 35, 'Short Sword light': 15, 'Short Sword heavy': 30}
