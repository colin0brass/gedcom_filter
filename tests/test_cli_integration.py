import subprocess
import os
import pytest

def test_cli_basic(tmp_path):
    gedcom_file = "geo_gedcom/samples/bronte.ged"
    output_filename = "test_output.ged"

    output_foldername = "output"
    output_folder = tmp_path / output_foldername
    output_file = output_folder / output_filename

    photo_foldername = "photos"
    photo_dir = output_folder / photo_foldername

    result = subprocess.run([
        "python", "gedcom_filter.py", gedcom_file,
        "--ancestor_generations", "2",
        "--descendant_generations", "1",
        "--output_file", output_filename,
        "--photo_subdir", photo_foldername,
        "--output_folder", output_folder
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert output_file.exists()
    assert photo_dir.exists()
