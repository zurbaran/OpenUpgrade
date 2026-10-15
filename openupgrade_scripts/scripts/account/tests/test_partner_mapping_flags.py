# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.util
import re
from pathlib import Path

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerMappingFlags(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = Path(__file__).parents[1] / "19.0.1.4" / "post-migration.py"
        spec = importlib.util.spec_from_file_location(
            "account_post_mapping_flags", path
        )
        cls.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.migration)

    def test_common_ignorecase_flag_is_not_nested(self):
        prefix, model, label, note = self.migration._partner_mapping_patterns(
            "(?i)^COREDIGI.*", "(?i)^COREDIGI.*", None
        )
        expression = prefix + f"(?={model})({label})"
        re.compile(expression)
        for value, expected in [
            ("COREDIGI receipt", True),
            ("coredigi", True),
            ("prefix COREDIGI", False),
        ]:
            self.assertEqual(bool(re.match(expression, value)), expected)
            self.cr.execute("SELECT %s ~* %s", [value, expression])
            self.assertEqual(self.cr.fetchone()[0], expected)
        self.assertEqual(note, "")

    def test_mapping_only_global_flag(self):
        prefix, model, label, note = self.migration._partner_mapping_patterns(
            None, "(?i)^COREMUTUA.*", None
        )
        self.assertEqual(prefix + label, "(?i)^COREMUTUA.*")
        self.assertEqual(model, "")
        self.assertEqual(note, "")

    def test_unflagged_patterns_are_unchanged(self):
        self.assertEqual(
            self.migration._partner_mapping_patterns(
                "^CORE", "^[Cc][Oo][Rr][Ee]", None
            ),
            ("", "^CORE", "^[Cc][Oo][Rr][Ee]", ""),
        )

    def test_neutral_condition_does_not_force_a_flag_conflict(self):
        self.assertEqual(
            self.migration._partner_mapping_patterns(".*", "(?i)^CORE", None),
            ("(?i)", ".*", "^CORE", ""),
        )

    def test_different_flags_are_not_silently_merged(self):
        with self.assertRaises(ValueError):
            self.migration._partner_mapping_patterns("(?i)^CORE", "^CORE", None)

    def test_other_flag_semantics_are_not_guessed(self):
        with self.assertRaises(ValueError):
            self.migration._partner_mapping_patterns("(?m)^CORE", "(?m)^CORE", None)
