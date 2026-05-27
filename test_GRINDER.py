"""
GRINDER — Test Suite v0.1.14
"""

import sys, os, sqlite3, json
import unittest.mock as mock

sys.modules['PyQt6'] = mock.MagicMock()
sys.modules['PyQt6.QtWidgets'] = mock.MagicMock()
sys.modules['PyQt6.QtCore'] = mock.MagicMock()
sys.modules['PyQt6.QtGui'] = mock.MagicMock()
sys.modules['PyQt6.QtSvgWidgets'] = mock.MagicMock()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import GRINDER as G


def test_version():
    assert G.APP_VERSION == "v1.0.1"

def test_default_settings_keys():
    for key in ["engine_path", "engine_depth", "engine_time_sec", "engine_mode",
                "theme", "db_path", "lower_threshold_cp", "upper_threshold_cp",
                "form_games_shown", "player_username", "player_rating",
                "tier_upper_cutoff", "tier_lower_cutoff",
                "window_x", "window_y", "window_w", "window_h", "splitter_pos"]:
        assert key in G.DEFAULT_SETTINGS

def test_delete_position(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    game_id = G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "WIN", 600, -50)
    G.db_save_evals(db_path, game_id, [10, 20, 30])
    G.db_delete_position(db_path, pos_id)
    assert len(G.db_get_positions(db_path)) == 0
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM games WHERE position_id=?", (pos_id,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM game_evals WHERE game_id=?", (game_id,)).fetchone()[0] == 0
    conn.close()

def test_update_position(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "Old Title", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "old ideas", "")
    new_fen = "8/4pppp/8/4PPPP/8/k7/8/K7 w - - 0 1"
    G.db_update_position(db_path, pos_id, "New Title", new_fen, "new ideas")
    row = G.db_get_position(db_path, pos_id)
    assert row["title"] == "New Title"
    assert row["fen"] == new_fen
    assert row["ideas"] == "new ideas"

def test_export_import(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "Export Test", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "ideas", "")
    game_id = G.db_add_game(db_path, pos_id, "pgn", "Bot", 1400, "WIN", 600, -50)
    G.db_save_evals(db_path, game_id, [100, 200, 300])

    data = G.db_export(db_path)
    assert len(data["positions"]) == 1
    assert len(data["games"]) == 1
    assert len(data["game_evals"]) == 3

    # Import into new db
    db_path2 = str(tmp_path / "test2.db")
    G.init_db(db_path2)
    G.db_add_position(db_path2, "Should be replaced", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_import(db_path2, data)
    positions = G.db_get_positions(db_path2)
    assert len(positions) == 1
    assert positions[0]["title"] == "Export Test"
    games = G.db_get_games(db_path2, positions[0]["id"])
    assert len(games) == 1

def test_export_json_serializable(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    G.seed_data(db_path)
    data = G.db_export(db_path)
    json_str = json.dumps(data, default=str)
    assert len(json_str) > 0

def test_grinder_extension(tmp_path):
    """Verify export produces valid JSON suitable for .grinder file."""
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    data = G.db_export(db_path)
    grinder_path = str(tmp_path / "export.grinder")
    with open(grinder_path, "w") as f:
        json.dump(data, f, default=str)
    with open(grinder_path) as f:
        loaded = json.load(f)
    assert loaded["positions"][0]["title"] == "T"

def test_validate_fen():
    ok, _ = G.validate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert ok

def test_games_desc_order(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_add_game(db_path, pos_id, "pgn", "Bot1", 1400, "WIN",  600, -50)
    G.db_add_game(db_path, pos_id, "pgn", "Bot2", 1400, "LOSS", 200, -300)
    G.db_add_game(db_path, pos_id, "pgn", "Bot3", 1400, "DRAW", 300, -200)
    games = G.db_get_games(db_path, pos_id)
    assert games[0]["bot_name"] == "Bot3"

def test_pgn_validation_no_fen():
    pgn = "[Event \"Test\"]\n1. e4 e5 *"
    try:
        G.analyze_pgn(pgn, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                      "stockfish", 5, None, 500, -200, "dab327")
        assert False
    except Exception as e:
        assert "FEN" in str(e)

def test_tier_stats(tmp_path):
    db_path = str(tmp_path / "test.db")
    G.init_db(db_path)
    pos_id = G.db_add_position(db_path, "T", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "")
    G.db_add_game(db_path, pos_id, "pgn", "Hard", 2000, "WIN", 600, -50)
    tiers = G.db_get_tier_stats(db_path, pos_id, 1500, 500, -200, 400, 400)
    assert tiers["higher"]["total"] == 1
