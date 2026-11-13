"""Modelin sahne planı yalnızca burada tanımlanan komutları kullanabilir."""
import math

BACKGROUNDS = ('ocean', 'space', 'lab', 'nature', 'abstract')
CHARACTERS = ('octopus', 'heart', 'planet', 'star', 'book', 'atom', 'bulb')
ANIMATIONS = ('enter_bounce', 'pulse', 'orbit', 'blood_flow', 'float')
PALETTES = ('ocean', 'sunset', 'forest', 'violet')
TIMELINE = ((0, 3), (3, 10), (10, 15))


def validate(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get('title'), str) or not plan['title'].strip():
        raise ValueError('title metni gerekli')
    if not isinstance(plan.get('description'), str): raise ValueError('description metni gerekli')
    scenes = plan.get('scenes')
    if not isinstance(scenes, list) or len(scenes) != 3: raise ValueError('Üç sahne gerekli')
    if plan.get('duration') != 15: raise ValueError('duration 15 olmalı')
    for i, (scene, interval) in enumerate(zip(scenes, TIMELINE), 1):
        if not isinstance(scene, dict): raise ValueError('Sahne nesne olmalı')
        if scene.get('id') != i: raise ValueError('Sahne id sıralı olmalı')
        if (scene.get('start'), scene.get('end')) != interval: raise ValueError('Sahneler 0–3, 3–10, 10–15 olmalı')
        for key, values in [('background',BACKGROUNDS),('character',CHARACTERS),('animation',ANIMATIONS),('palette',PALETTES)]:
            if scene.get(key) not in values: raise ValueError(f'Bilinmeyen {key}: {scene.get(key)}')
        for key, limit in [('text',60), ('narration',280)]:
            if not isinstance(scene.get(key),str) or not scene[key].strip() or len(scene[key]) > limit:
                raise ValueError(f'Geçersiz {key}')
    return plan
