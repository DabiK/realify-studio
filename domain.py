"""Shared paths, editorial concepts and data validation. No database or worker side effects."""
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONCEPTS = [
    {'id': 'villains', 'title': 'Les visages de la terreur', 'family': 'Instants cinéma',
     'reason': 'Le post méchants atteint 1,8 M de vues. Tester le cadrage, sans supposer que le sujet suffit.',
     'scene': 'Observed live-action moments in a lived-in pirate palace. Characters absorbed in an activity, unposed gestures, motivated natural light and physically credible materials.',
     'subjects': ['Donquixote Doflamingo', 'Kaido', 'Crocodile', 'Big Mom', 'Rob Lucci'],
     'image': 'doflamingo.jpg'},
    {'id': 'backstage', 'title': 'Quand la caméra s’arrête', 'family': 'Coulisses fictives',
     'reason': 'La Part 3 des coulisses atteint 7,49 % d’interactions, dans les 15 posts exportés.',
     'scene': 'Fictional behind-the-scenes photographs of a One Piece film production. Camera rigs and crew, natural daylight, candid between-takes moments, realistic props.',
     'subjects': ['Portgas D. Ace', 'Shanks', 'Nico Robin', 'Crocodile', 'Donquixote Doflamingo'],
     'image': 'ace.jpg'},
    {'id': 'creatures', 'title': 'Ils prennent vie', 'family': 'Créatures réalistes',
     'reason': 'Les Minks atteignent 57 k vues. Une piste secondaire pour répliquer un essai de cadrage.',
     'scene': 'Observed live-action creatures interacting with a lush pirate forest, physically credible fur and skin, recognizable silhouettes and spontaneous movement.',
     'subjects': ['Nekomamushi', 'Inuarashi', 'Carrot', 'Jinbe', 'Tony Tony Chopper'],
     'image': 'kaido.jpg'},
]


def uid():
    return uuid.uuid4().hex


def text(value, maximum=2000, required=True):
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        raise ValueError('Texte absent ou trop long.')
    return value.strip()


def validate_post(data):
    title = text(data.get('title'), 120)
    description = text(data.get('description'), 1800).replace('\\n', '\n')
    tags = data.get('hashtags')
    if not isinstance(tags, list) or not 1 <= len(tags) <= 5:
        raise ValueError('La fiche doit contenir 1 à 5 hashtags pertinents.')
    import re
    if any(not isinstance(t, str) or not re.fullmatch(r'#[\w]{1,60}', t) for t in tags):
        raise ValueError('Hashtag invalide.')
    return {'title': title, 'description': description, 'hashtags': list(dict.fromkeys(tags))}


