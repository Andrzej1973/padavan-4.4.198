#!/usr/bin/env python3
"""Regression checks for the actual route verifier, before firmware compilation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('routes', Path(__file__).with_name('check-web-routes.py'))
routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes)


class WebRoutes(unittest.TestCase):
    def enumerate(self, names, linked=True, target='/opt/share/www/custom'):
        root = Path('/fixture/www')
        with patch.object(routes.os, 'walk', return_value=[(str(root), [], names)]), \
                patch.object(routes.os.path, 'islink', return_value=linked), \
                patch.object(routes.os, 'readlink', return_value=target):
            return routes.served_files(root)

    def test_dangling_stock_directory_link(self):
        self.assertEqual(self.enumerate(['custom', 'index.asp', 'dlink.js']), ['dlink.js', 'index.asp'])

    def test_regular_custom_file_is_checked(self):
        self.assertEqual(self.enumerate(['custom'], linked=False), ['custom'])

    def test_unexpected_custom_target_is_checked(self):
        self.assertEqual(self.enumerate(['custom'], target='/unexpected'), ['custom'])

    def test_other_dangling_links_are_checked(self):
        self.assertEqual(self.enumerate(['other.js']), ['other.js'])

    def test_translation_files_are_internal(self):
        self.assertEqual(self.enumerate(['UK.dict', 'RU.dict', 'EN.header', 'index.asp']), ['index.asp'])

    def test_json_nested_routes(self):
        self.assertTrue(routes.match('**.json', 'catalog/dot.json'))
        self.assertFalse(routes.match('*.json', 'catalog/dot.json'))

    def test_resolved_directory_links_not_traversed(self):
        root = Path('/fixture/www')
        dirs = ['custom', 'assets']
        with patch.object(routes.os, 'walk', return_value=[(str(root), dirs, ['index.asp'])]), \
                patch.object(routes.os.path, 'islink', side_effect=lambda name: Path(name).name == 'custom'):
            self.assertEqual(routes.served_files(root), ['index.asp'])
        self.assertEqual(dirs, ['assets'])


if __name__ == '__main__':
    unittest.main()
