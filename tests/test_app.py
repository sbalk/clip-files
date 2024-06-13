"""Test suite for `clip-files`."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

import pyperclip

import clip_files

if TYPE_CHECKING:
    from pathlib import Path


def test_get_token_count() -> None:
    """Test the get_token_count function."""
    text = "Hello, how are you?"
    model = "gpt-4"
    token_count = clip_files.get_token_count(text, model)
    assert isinstance(token_count, int), "Token count should be an integer"
    assert token_count > 0, "Token count should be greater than 0"


def test_get_files_with_extension() -> None:
    """Test the get_files_with_extension function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some temporary files
        file1_path = os.path.join(temp_dir, "test1.py")
        file2_path = os.path.join(temp_dir, "test2.py")
        with open(file1_path, "w", encoding="utf-8") as f1:
            f1.write("print('Hello, world!')\n")
        with open(file2_path, "w", encoding="utf-8") as f2:
            f2.write("print('Another file')\n")

        file_contents, total_tokens, file_paths = clip_files.get_files_with_extension(temp_dir, ".py")

        assert len(file_contents) == 2, "Should find two .py files"  # noqa: PLR2004
        assert total_tokens > 0, "Total tokens should be greater than 0"
        assert file1_path in file_paths, "File path should be in the list"
        assert file2_path in file_paths, "File path should be in the list"
        assert file_contents[0].startswith("# File:"), "File content should start with # File:"


@patch("builtins.open", new_callable=mock_open, read_data="These are initial instructions.\n")
def test_generate_combined_content_with_initial_file(mock_file: MagicMock, tmp_path: Path) -> None:  # noqa: ARG001
    """Test the generate_combined_content function with an initial file provided."""
    # Create a test Python file in the temporary directory
    file_path = tmp_path / "test.py"
    file_path.write_text("print('Hello, world!')\n", encoding="utf-8")

    # Create an initial instructions file in the temporary directory
    initial_file_path = tmp_path / "initial.txt"
    initial_file_path.write_text("These are initial instructions.\n", encoding="utf-8")

    # Call the generate_combined_content function
    combined_content, total_tokens = clip_files.generate_combined_content(
        folder_path=str(tmp_path),
        file_extension=".py",
        initial_file_path=str(initial_file_path),
    )

    # Verify the combined content includes the initial instructions
    assert "These are initial instructions." in combined_content, combined_content
    assert "# File:" in combined_content, "File content should be included"
    assert "test.py" in combined_content, "File path should be included in the combined content"
    assert "print('Hello, world!')" in combined_content, "File content should be included in the combined content"
    assert "My question is:" in combined_content, "Question prompt should be at the end"

    # Copy the combined content to clipboard for further verification
    pyperclip.copy(combined_content)
    clipboard_content = pyperclip.paste()

    assert clipboard_content == combined_content, "Clipboard content should match the combined content generated"

    # Ensure total tokens are counted correctly
    assert total_tokens > 0, "Total tokens should be a positive integer"


def test_generate_combined_content_without_initial_file(tmp_path: Path) -> None:
    """Test the generate_combined_content function without an initial file provided."""
    # Create a test Python file in the temporary directory
    file_path = tmp_path / "test.py"
    file_path.write_text("print('Hello, world!')\n", encoding="utf-8")

    # Call the generate_combined_content function
    combined_content, total_tokens = clip_files.generate_combined_content(folder_path=str(tmp_path), file_extension=".py")

    # Verify the combined content includes the default initial message
    assert "Hello! Below are the code files from my project" in combined_content, "Default initial message should be included"
    assert "# File:" in combined_content, "File content should include file path and content"
    assert "test.py" in combined_content, "File path should be included in the combined content"
    assert "print('Hello, world!')" in combined_content, "File content should be included in the combined content"
    assert "My question is:" in combined_content, "Question prompt should be at the end"

    # Copy the combined content to clipboard for further verification
    pyperclip.copy(combined_content)
    clipboard_content = pyperclip.paste()

    assert clipboard_content == combined_content, "Clipboard content should match the combined content generated"

    # Ensure total tokens are counted correctly
    assert total_tokens > 0, "Total tokens should be a positive integer"


def test_main_without_initial_file() -> None:
    """Test the main function without an initial file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("print('Hello, world!')\n")

        args = [temp_dir, ".py"]

        with patch("sys.argv", ["clip_files.py", *args]):
            clip_files.main()

        clipboard_content = pyperclip.paste()
        assert "Hello! Below are the code files from my project" in clipboard_content, "Default initial message should be included"
        assert "# File:" in clipboard_content, "File content should be included"
        assert "My question is:" in clipboard_content, "Question prompt should be at the end"
