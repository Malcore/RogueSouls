from collections import namedtuple


# File for all dictionaries used in main file, such as items, timings, skills, etc.
SMAPW = 20
SMAPH = 20

SkillNode = namedtuple('SkillNode', ['description', 'effect', 'taken'])

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
