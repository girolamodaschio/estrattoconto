import unittest
from main import extract_table, extract_data_tables
class TestService(unittest.TestCase):

    def test_read_pdf(self):
        filepath = './fixture/centroveneto.pdf'
        extraction = extract_table(filepath)
        self.assertIsInstance(extraction, tuple)
