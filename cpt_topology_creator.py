https://github.com/ZombieDuckling/packet-tracer-topology-creator/new/main
#!/usr/bin/env python3
"""
Simple Packet Tracer Topology Creator
------------------------------------

This script provides a minimal, reliable way to generate network
topology definitions for Cisco Packet Tracer based on either a
plain‑text or PDF description.  It combines the validation ideas
from the `CiscoPacketTracerAutomator` project with the OS and
window‑management scaffolding from `topology‑creator‑cpt`.  The goal
is to remain simple and robust: it reads a single input file,
parses each line into one of four categories (end devices,
network devices, networks and links), validates the format of
each line and prints a summary of the parsed topology.  The
automation function that actually drives Packet Tracer is left
as a stub for you to implement on a machine with Packet Tracer
installed.

Usage:
    python cpt_topology_creator.py <path_to_txt_or_pdf>

If the file is a PDF, the script requires the `pdfplumber`
package.  Install it with `pip install pdfplumber`.  For text
files, no external dependencies are needed.

Example input (plain text or in the body of a PDF):

    -pc, pc0, 192.168.1.10
    -pc, pc1, 192.168.1.11
    -Switch, sw0
    -Router, r0
    -Network, ntw0
    -ntw0, pc0, sw0
    -ntw0, pc1, sw0
    -ntw0, r0, sw0

This script is intentionally conservative: it expects each line to
match one of the known patterns.  If it encounters an unknown
pattern, it reports an error and stops.

The stub `run_automation` function demonstrates where you would
invoke your Packet Tracer automation routine.  For a real
implementation you could import `pyautogui` and use the
window‑management code from `topology-creator-cpt` to start
Packet Tracer, then iterate over the parsed data to place
devices, connect them and configure IP addresses.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    import pdfplumber  # type: ignore
except ImportError:
    pdfplumber = None  # pdf support is optional


@dataclass
class Topology:
    """Holds lists of parsed topology elements."""
    end_devices: List[str]
    network_devices: List[str]
    networks: List[str]
    links: List[str]

    @property
    def is_valid(self) -> bool:
        """True if there is at least one network and one end device."""
        return bool(self.end_devices and (self.networks or self.network_devices))


def extract_text_from_file(path: Path) -> str:
    """Return the contents of a text file or extract text from a PDF.

    Args:
        path: Path to a `.txt` or `.pdf` file.

    Raises:
        RuntimeError: if PDF extraction is requested but pdfplumber is not
            installed or the file cannot be read.
    """
    if path.suffix.lower() == ".pdf":
        if pdfplumber is None:
            raise RuntimeError(
                "PDF support requires the 'pdfplumber' package. "
                "Install it with 'pip install pdfplumber' and try again."
            )
        text_parts: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    else:
        return path.read_text(encoding="utf-8")


def parse_topology(text: str) -> Tuple[Topology, List[str]]:
    """Parse topology definitions from a block of text.

    Returns a tuple `(topology, errors)` where `topology` contains
    lists of end devices, network devices, networks and links, and
    `errors` contains strings describing any lines that failed to
    match the expected patterns.  A link is defined as a line with
    three comma separated values starting with a '-' that does not
    match the device or network patterns.
    """
    # Regular expressions for each type of line.  These are adapted
    # from CiscoPacketTracerAutomator's Controller.java
    end_device_pattern = re.compile(
        r"^-[A-Za-z]+,\s*[A-Za-z]+\d*,\s*\d{1,3}(?:\.\d{1,3}){3}$"
    )
    network_device_pattern = re.compile(r"^-[A-Za-z]+,\s*[A-Za-z]+\d*$")
    network_pattern = re.compile(r"^-[A-Za-z]+,\s*[A-Za-z]+\d*$")

    end_devices: List[str] = []
    network_devices: List[str] = []
    networks: List[str] = []
    links: List[str] = []
    errors: List[str] = []

    for idx, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue  # skip empty lines
        # Determine the type of line by counting commas
        comma_count = line.count(",")
        # End device lines have two commas and an IP address
        if end_device_pattern.match(line):
            end_devices.append(line)
        # Network/device lines have one comma; decide based on keyword
        elif comma_count == 1 and network_device_pattern.match(line):
            keyword = line.split(",")[0].strip("-").lower()
            if keyword in {"pc", "laptop", "host"}:
                # treat as end device even though it looks like network device
                end_devices.append(line)
            elif keyword in {"router", "switch", "firewall"}:
                network_devices.append(line)
            else:
                networks.append(line)
        # Links have two commas but no IP address
        elif comma_count == 2:
            links.append(line)
        else:
            errors.append(f"Line {idx}: Unrecognised format → '{line}'")
    return Topology(end_devices, network_devices, networks, links), errors


def run_automation(topology: Topology) -> None:
    """Stub function to run Packet Tracer automation.

    In a real implementation this function would use a library such as
    `pyautogui` together with OS/window management code to launch
    Cisco Packet Tracer, place the appropriate devices on the canvas,
    connect them and assign IP addresses.  For now we simply print
    what would be done.
    """
    print("\n=== Topology Summary ===")
    print(f"End devices ({len(topology.end_devices)}):")
    for d in topology.end_devices:
        print(f"  {d}")
    print(f"Network devices ({len(topology.network_devices)}):")
    for d in topology.network_devices:
        print(f"  {d}")
    print(f"Networks ({len(topology.networks)}):")
    for n in topology.networks:
        print(f"  {n}")
    print(f"Links ({len(topology.links)}):")
    for l in topology.links:
        print(f"  {l}")

    print("\n[Simulation] Would now launch Packet Tracer and build the topology...")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a simple network topology description from a text or PDF "
            "file, validate it and summarise the devices and links."
        )
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the .txt or .pdf file containing the topology description",
    )
    args = parser.parse_args(argv)

    if not args.file.exists():
        print(f"Error: '{args.file}' does not exist.", file=sys.stderr)
        return 1

    try:
        text = extract_text_from_file(args.file)
    except Exception as e:
        print(f"Failed to read file: {e}", file=sys.stderr)
        return 1

    topology, errors = parse_topology(text)

    if errors:
        print("Input validation failed:\n")
        for err in errors:
            print(err)
        print(
            "\nPlease correct the above lines and try again.  Each line must "
            "begin with '-' and follow one of the supported patterns."
        )
        return 1

    if not topology.is_valid:
        print(
            "Topology is incomplete: please specify at least one end device and "
            "one network or network device."
        )
        return 1

    run_automation(topology)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
