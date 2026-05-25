"""
GRINDER — Test Suite
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_version():
    from GRINDER import APP_VERSION
    assert APP_VERSION == "v0.0.1"


def test_app_name():
    from GRINDER import APP_NAME
    assert APP_NAME == "GRINDER"
