import unittest

from altvoice.numerals import normalize_numbers


class NumberTests(unittest.TestCase):
    def test_year_date_amount_percent(self):
        text = "今天二零二五年十一月七日，价格三千五百块，增长百分之三十。"
        self.assertEqual(
            normalize_numbers(text),
            "今天2025年11月7日，价格3500块，增长30%。",
        )

    def test_decimal_and_negative(self):
        self.assertEqual(normalize_numbers("温度负三度，比例百分之三点五。"), "温度-3度，比例3.5%。")

    def test_phone(self):
        self.assertEqual(normalize_numbers("电话一三八零零一三八零零零"), "电话13800138000")

    def test_idioms_are_untouched(self):
        self.assertEqual(normalize_numbers("一起走，十分重要。"), "一起走，十分重要。")
