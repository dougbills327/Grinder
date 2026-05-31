"""
GRINDER — Test Suite v1.1.2
"""

import sys, os, sqlite3
import unittest.mock as mock

sys.modules['PyQt6'] = mock.MagicMock()
sys.modules['PyQt6.QtWidgets'] = mock.MagicMock()
sys.modules['PyQt6.QtCore'] = mock.MagicMock()
sys.modules['PyQt6.QtGui'] = mock.MagicMock()
sys.modules['PyQt6.QtSvgWidgets'] = mock.MagicMock()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import GRINDER as G


def test_version():
    assert G.APP_VERSION == "v1.1.2"

def test_playstyle_stats_includes_results(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "WIN",  600, -50, playstyle="Savage")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "LOSS", 200, -300, playstyle="Savage")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "DRAW", 300, -100, playstyle="Savage")
    stats = G.db_get_playstyle_stats(db_path, pos_id)
    assert "results" in stats["Savage"]
    assert len(stats["Savage"]["results"]) == 3
    assert stats["Savage"]["results"][0] == "WIN"  # oldest first

def test_playstyle_stats_win_rate(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "WIN", 600, -50, playstyle="Guardian")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "WIN", 700, -30, playstyle="Guardian")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "LOSS",200,-300, playstyle="Guardian")
    G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "LOSS",100,-400, playstyle="Guardian")
    stats = G.db_get_playstyle_stats(db_path, pos_id)
    assert stats["Guardian"]["win_rate"] == 50

def test_bulk_playstyle_update(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_add_game(db_path, pos_id, "pgn", "HunterBot", 1400, "WIN",  600, -50)
    G.db_add_game(db_path, pos_id, "pgn", "HunterBot", 1400, "LOSS", 200, -300)
    G.db_add_game(db_path, pos_id, "pgn", "OtherBot",  1500, "WIN",  500, -50)
    G.db_update_all_games_playstyle_for_bot(db_path, "HunterBot", "Hunter")
    stats = G.db_get_playstyle_stats(db_path, pos_id)
    assert stats["Hunter"]["total"] == 2
    assert stats["Unknown"]["total"] == 1

def test_rename_folder(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    fid = G.db_add_folder(db_path, "Old")
    G.db_rename_folder(db_path, fid, "New")
    assert G.db_get_folders(db_path)[0]["name"] == "New"

def test_validate_fen():
    ok, _ = G.validate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert ok

def test_playstyles_list():
    assert set(G.PLAYSTYLES) == {"Guardian", "Observer", "Mediator", "Hunter", "Savage"}

def test_result_colors():
    for r in ["WIN", "LOSS", "DRAW"]:
        assert r in G.RESULT_COLORS

def test_chessiverse_url():
    url = G.build_chessiverse_url("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert url and "side=white" in url
