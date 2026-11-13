import copy, json, unittest
from pathlib import Path
from animation.schema import validate, BACKGROUNDS, CHARACTERS, ANIMATIONS, PALETTES
from animation.renderer import frame

class AnimationTest(unittest.TestCase):
    def setUp(self): self.plan=json.loads(Path('samples/octopus.json').read_text(encoding='utf8'))
    def test_valid(self): self.assertEqual(validate(self.plan)['duration'],15)
    def test_reject_command(self):
        self.plan['scenes'][0]['animation']='__import__("os")'
        with self.assertRaises(ValueError): validate(self.plan)
    def test_reject_gaps(self):
        self.plan['scenes'][1]['start']=4
        with self.assertRaises(ValueError): validate(self.plan)
    def test_frames_differ(self):
        self.assertNotEqual(frame(self.plan,0.6,270,480).tobytes(),frame(self.plan,1.2,270,480).tobytes())
    def test_all_assets_and_commands(self):
        for key, options in [('character', CHARACTERS), ('background', BACKGROUNDS), ('animation', ANIMATIONS), ('palette', PALETTES)]:
            for item in options:
                plan=copy.deepcopy(self.plan); plan['scenes'][0][key]=item
                self.assertEqual(frame(plan,1,270,480).size,(270,480))
    def test_scene_boundaries(self):
        for t in [0,2.99,3,9.99,10,14.9]: self.assertEqual(frame(self.plan,t,270,480).size,(270,480))

if __name__=='__main__': unittest.main()
