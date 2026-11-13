import unittest
from studio import fit_rate, srt_time, clean_plan, ass_escape

class CoreTests(unittest.TestCase):
    def test_rate(self):
        self.assertEqual(fit_rate(1.5, 2), 1.0)
        self.assertAlmostEqual(fit_rate(4, 2), 4/1.9)
        with self.assertRaises(ValueError): fit_rate(10, 2)
    def test_srt(self):
        self.assertEqual(srt_time(62.125), '00:01:02,125')
    def test_plan(self):
        p={'title':'Deneme','description':'Kısa', 'scenes':[
            {'narration':'Merhaba dünya.', 'image_prompt':'A 3d illustration'} for _ in range(3)]}
        self.assertEqual(len(clean_plan(p)['scenes']), 3)
        with self.assertRaises(ValueError): clean_plan({'scenes':[]})
    def test_escape(self):
        self.assertNotIn('{', ass_escape('{x}'))

if __name__ == '__main__': unittest.main()
