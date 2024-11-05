import pytest
from scripts.database_viewer import view_database
import io
import sys

def test_database_viewer(capsys):
    view_database()
    captured = capsys.readouterr()
    assert "Tables in the database:" in captured.out
    assert "Sample data from" in captured.out
    assert "Schema for" in captured.out
