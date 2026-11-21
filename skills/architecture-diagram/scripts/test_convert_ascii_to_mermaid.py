#!/usr/bin/env python3
"""
Unit tests for convert_ascii_to_mermaid.py
"""

import unittest
import tempfile
from pathlib import Path

from convert_ascii_to_mermaid import (
    detect_diagram_type,
    parse_vertical_flow,
    parse_horizontal_flow,
    parse_tree_structure,
    ascii_to_mermaid,
    is_ascii_diagram,
    process_file,
)


class TestDiagramDetection(unittest.TestCase):
    """Test diagram type detection"""

    def test_detect_vertical_flow(self):
        block = "Item1\n↓\nItem2"
        diagram_type, orientation = detect_diagram_type(block)
        self.assertEqual(diagram_type, 'vertical_flow')
        self.assertEqual(orientation, 'TD')

    def test_detect_horizontal_flow(self):
        block = "Item1 → Item2"
        diagram_type, orientation = detect_diagram_type(block)
        self.assertEqual(diagram_type, 'horizontal_flow')
        self.assertEqual(orientation, 'LR')

    def test_detect_tree_structure(self):
        block = "Root\n├── Child1\n└── Child2"
        diagram_type, orientation = detect_diagram_type(block)
        self.assertEqual(diagram_type, 'tree')
        self.assertEqual(orientation, 'TD')

    def test_detect_tree_with_pipes(self):
        block = "Root\n│\n├── Branch"
        diagram_type, orientation = detect_diagram_type(block)
        self.assertEqual(diagram_type, 'tree')

    def test_default_detection(self):
        block = "Some text without diagram chars"
        diagram_type, orientation = detect_diagram_type(block)
        self.assertEqual(diagram_type, 'vertical_flow')
        self.assertEqual(orientation, 'TD')


class TestVerticalFlowParsing(unittest.TestCase):
    """Test parsing vertical flow diagrams"""

    def test_simple_vertical_flow(self):
        block = "A\n↓\nB\n↓\nC"
        items = parse_vertical_flow(block)
        self.assertEqual(items, ['A', 'B', 'C'])

    def test_vertical_flow_with_spaces(self):
        block = "  Item A  \n↓\n  Item B  "
        items = parse_vertical_flow(block)
        self.assertEqual(items, ['Item A', 'Item B'])

    def test_single_item(self):
        block = "Single Item"
        items = parse_vertical_flow(block)
        self.assertEqual(items, ['Single Item'])

    def test_empty_lines_ignored(self):
        block = "A\n\n↓\n\nB"
        items = parse_vertical_flow(block)
        self.assertIn('A', items)
        self.assertIn('B', items)


class TestHorizontalFlowParsing(unittest.TestCase):
    """Test parsing horizontal flow diagrams"""

    def test_simple_horizontal_flow(self):
        block = "A → B → C"
        items = parse_horizontal_flow(block)
        self.assertEqual(items, ['A', 'B', 'C'])

    def test_multiline_horizontal(self):
        block = "Start\n→\nMiddle\n→\nEnd"
        items = parse_horizontal_flow(block)
        self.assertEqual(items, ['Start', 'Middle', 'End'])


class TestTreeStructureParsing(unittest.TestCase):
    """Test parsing tree structures"""

    def test_simple_tree(self):
        block = "Root\n├── A\n└── B"
        items = parse_tree_structure(block)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0][0], 'Root')
        self.assertEqual(items[1][0], 'A')
        self.assertEqual(items[2][0], 'B')

    def test_nested_tree(self):
        block = "Root\n├── Parent\n│   └── Child"
        items = parse_tree_structure(block)
        self.assertGreater(len(items), 0)
        # First item should be Root
        self.assertIn('Root', items[0][0])

    def test_tree_with_pipes(self):
        block = "A\n│\n├── B\n│\n└── C"
        items = parse_tree_structure(block)
        self.assertGreater(len(items), 0)


class TestAsciiDiagramDetection(unittest.TestCase):
    """Test ASCII diagram detection"""

    def test_is_diagram_vertical(self):
        self.assertTrue(is_ascii_diagram("A\n↓\nB"))

    def test_is_diagram_horizontal(self):
        self.assertTrue(is_ascii_diagram("A → B"))

    def test_is_diagram_tree(self):
        self.assertTrue(is_ascii_diagram("Root\n├── A"))

    def test_is_not_diagram(self):
        self.assertFalse(is_ascii_diagram("This is just plain text"))

    def test_is_diagram_with_hyphens(self):
        self.assertTrue(is_ascii_diagram("A\n─\nB"))


class TestAsciiToMermaidConversion(unittest.TestCase):
    """Test ASCII to Mermaid conversion"""

    def test_vertical_to_mermaid(self):
        block = "A\n↓\nB\n↓\nC"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart TD", mermaid)
        self.assertIn("[A]", mermaid)
        self.assertIn("[B]", mermaid)
        self.assertIn("[C]", mermaid)
        self.assertIn("-->", mermaid)

    def test_horizontal_to_mermaid(self):
        block = "A → B → C"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart LR", mermaid)
        self.assertIn("[A]", mermaid)
        self.assertIn("[B]", mermaid)
        self.assertIn("[C]", mermaid)

    def test_tree_to_mermaid(self):
        block = "Root\n├── A\n└── B"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart TD", mermaid)
        self.assertIn("[Root]", mermaid)
        self.assertIn("[A]", mermaid)
        self.assertIn("[B]", mermaid)

    def test_multiline_items(self):
        block = "Manual Scheduling (MVP)\n↓\nDependency Scheduling"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("Manual Scheduling (MVP)", mermaid)
        self.assertIn("Dependency Scheduling", mermaid)

    def test_preserves_item_names(self):
        block = "Start\n↓\nMiddle Process\n↓\nEnd"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("Start", mermaid)
        self.assertIn("Middle Process", mermaid)
        self.assertIn("End", mermaid)


class TestProcessFile(unittest.TestCase):
    """Test file processing"""

    def test_process_file_with_diagrams(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n\n```\nA\n↓\nB\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_converted = process_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertGreater(num_converted, 0)

            content = filepath.read_text()
            self.assertIn("```mermaid", content)
            self.assertIn("flowchart TD", content)
        finally:
            filepath.unlink()

    def test_process_file_no_diagrams(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n\nJust plain text\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_converted = process_file(filepath, dry_run=False)
            self.assertFalse(changed)
            self.assertEqual(num_converted, 0)
        finally:
            filepath.unlink()

    def test_process_file_dry_run(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n\n```\nA\n↓\nB\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            original_content = filepath.read_text()
            changed, num_converted = process_file(filepath, dry_run=True)

            # File should not be modified in dry run
            self.assertEqual(filepath.read_text(), original_content)
        finally:
            filepath.unlink()

    def test_process_file_multiple_diagrams(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("```\nA\n↓\nB\n```\n\n")
            f.write("```\nC → D\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_converted = process_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertGreaterEqual(num_converted, 2)

            content = filepath.read_text()
            # Both should be converted
            self.assertEqual(content.count("```mermaid"), 2)
        finally:
            filepath.unlink()

    def test_preserves_non_diagram_code_blocks(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("```python\nprint('hello')\n```\n\n")
            f.write("```\nA\n↓\nB\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_converted = process_file(filepath, dry_run=False)
            content = filepath.read_text()

            # Python block should remain unchanged
            self.assertIn("```python", content)
            # ASCII diagram should be converted
            self.assertIn("```mermaid", content)
        finally:
            filepath.unlink()


class TestAlignmentPreservation(unittest.TestCase):
    """Test that alignment is preserved in conversions"""

    def test_vertical_alignment_preserved(self):
        block = "Top\n↓\nMiddle\n↓\nBottom"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart TD", mermaid)
        # TD means top-down (vertical)

    def test_horizontal_alignment_preserved(self):
        block = "Left → Center → Right"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart LR", mermaid)
        # LR means left-right (horizontal)

    def test_tree_uses_vertical_alignment(self):
        block = "Root\n├── A\n└── B"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("flowchart TD", mermaid)


class TestComplexDiagrams(unittest.TestCase):
    """Test more complex diagram scenarios"""

    def test_long_vertical_chain(self):
        items = ['Item ' + str(i) for i in range(10)]
        block = '\n↓\n'.join(items)
        mermaid = ascii_to_mermaid(block)

        # Should have all items
        for item in items:
            self.assertIn(f"[{item}]", mermaid)

        # Should have connections
        connection_count = mermaid.count("-->")
        self.assertEqual(connection_count, 9)  # 10 items = 9 connections

    def test_diagram_with_special_characters(self):
        block = "Service-A\n↓\nData (Cache)\n↓\nResponse-Handler"
        mermaid = ascii_to_mermaid(block)
        self.assertIn("Service-A", mermaid)
        self.assertIn("Data (Cache)", mermaid)
        self.assertIn("Response-Handler", mermaid)

    def test_file_with_mixed_content(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Architecture\n\n")
            f.write("## Flow 1\n\n```\nA\n↓\nB\n```\n\n")
            f.write("Some explanation text.\n\n")
            f.write("## Flow 2\n\n```\nX → Y → Z\n```\n\n")
            f.write("More description.\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_converted = process_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertEqual(num_converted, 2)

            content = filepath.read_text()
            # Check structure is preserved
            self.assertIn("# Architecture", content)
            self.assertIn("## Flow 1", content)
            self.assertIn("Some explanation text", content)
        finally:
            filepath.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
