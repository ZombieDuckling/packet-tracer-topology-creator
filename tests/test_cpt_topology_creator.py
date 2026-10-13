import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import cpt_topology_creator as creator


VALID_TOPOLOGY = """
-pc, pc0, 192.168.1.10
-pc, pc1, 192.168.1.11
-Switch, sw0
-Router, r0
-Network, ntw0
-ntw0, pc0, sw0
-ntw0, pc1, sw0
-ntw0, r0, sw0
"""


class ParseTopologyTests(unittest.TestCase):
    def test_parses_documented_topology(self):
        topology, errors = creator.parse_topology(VALID_TOPOLOGY)

        self.assertEqual([], errors)
        self.assertTrue(topology.is_valid)
        self.assertEqual(2, len(topology.end_devices))
        self.assertEqual(2, len(topology.network_devices))
        self.assertEqual(["-Network, ntw0"], topology.networks)
        self.assertEqual(3, len(topology.links))

    def test_rejects_invalid_ipv4_octets(self):
        topology, errors = creator.parse_topology("-pc, pc0, 999.168.1.10")

        self.assertFalse(topology.is_valid)
        self.assertEqual(["Line 1: Invalid IPv4 address -> '999.168.1.10'"], errors)

    def test_rejects_unknown_lines(self):
        _topology, errors = creator.parse_topology("not a topology line")

        self.assertEqual(["Line 1: Unrecognised format -> 'not a topology line'"], errors)


class CliTests(unittest.TestCase):
    def test_main_summarises_valid_text_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            topology_file = Path(tmpdir) / "topology.txt"
            topology_file.write_text(VALID_TOPOLOGY, encoding="utf-8")

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = creator.main([str(topology_file)])

        self.assertEqual(0, exit_code)
        output = stdout.getvalue()
        self.assertIn("=== Topology Summary ===", output)
        self.assertIn("End devices (2):", output)
        self.assertIn("Links (3):", output)

    def test_main_fails_for_incomplete_topology(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            topology_file = Path(tmpdir) / "empty.txt"
            topology_file.write_text("-pc, pc0, 192.168.1.10\n", encoding="utf-8")

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = creator.main([str(topology_file)])

        self.assertEqual(1, exit_code)
        self.assertIn("Topology is incomplete", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
