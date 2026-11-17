import unittest
from src.coordinates import parse_coordinate


class CoordinateTests(unittest.TestCase):
    def test_sample_dms(self):
        self.assertAlmostEqual(parse_coordinate('8°15\'54.921"S', 'latitude'), -8.265255833333333)
        self.assertAlmostEqual(parse_coordinate('67°40\'24.699"W', 'longitude'), -67.6735275)

    def test_decimal_and_sign(self):
        for text, axis, expected in [('-8.2652558333', 'latitude', -8.2652558333),
                                     ('67,6735275W', 'longitude', -67.6735275),
                                     ('0', 'latitude', 0), ('180E', 'longitude', 180),
                                     ('-0 30 0', 'latitude', -0.5)]:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_coordinate(text, axis), expected)

    def test_invalid(self):
        for value, axis in [('', 'latitude'), ('NaN', 'latitude'), ('inf', 'longitude'),
                            ('91', 'latitude'), ('181', 'longitude'), ('8W', 'latitude'),
                            ('-8N', 'latitude'), ('8 60 0', 'latitude'),
                            ('8 15 60', 'latitude'), ('8.5 10 0', 'latitude'),
                            ('90 0 1', 'latitude'), ('abc8', 'latitude')]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_coordinate(value, axis)


if __name__ == '__main__':
    unittest.main()
