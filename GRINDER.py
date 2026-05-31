"""
GRINDER — Position Training Tool
"""

import sys
import os
import json
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QMenu,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QDialogButtonBox, QVBoxLayout, QHBoxLayout, QMessageBox,
    QListWidgetItem, QSplitter, QTextEdit,
    QGroupBox, QPushButton, QScrollArea, QWidget,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QAbstractItemView,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QByteArray
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from PyQt6.QtSvgWidgets import QSvgWidget

APP_VERSION = "v1.1.2"
APP_NAME = "GRINDER"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GRINDER")
SETTINGS_FILE = os.path.join(APPDATA_DIR, "settings.json")
DEFAULT_DB_PATH = os.path.join(APPDATA_DIR, "grinder.db")

DEFAULT_SETTINGS = {
    "engine_path": "stockfish",
    "engine_depth": 20,
    "engine_time_sec": 3,
    "theme": "light",
    "db_path": DEFAULT_DB_PATH,
    "lower_threshold_cp": -200,
    "upper_threshold_cp": 500,
    "form_games_shown": 5,
    "window_x": 100,
    "window_y": 100,
    "window_w": 1200,
    "window_h": 750,
    "splitter_pos": 320,
    "engine_mode": "depth",
    "player_username": "dab327",
    "player_rating": 1500,
    "tier_upper_cutoff": 400,
    "tier_lower_cutoff": 400,
}

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

THEME = {
    "light": {
        "bg":           "#f0f6ff",
        "panel":        "#ddeeff",
        "card":         "#ffffff",
        "accent":       "#3a7bd5",
        "accent_hover": "#2f63b0",
        "text":         "#1a1a2e",
        "subtext":      "#4a5568",
        "border":       "#b0c8e8",
        "list_sel":     "#3a7bd5",
        "list_sel_txt": "#ffffff",
    },
    "dark": {
        "bg":           "#1a1f2e",
        "panel":        "#242938",
        "card":         "#2d3347",
        "accent":       "#3a7bd5",
        "accent_hover": "#4a8be5",
        "text":         "#e8eaf0",
        "subtext":      "#9aa5b4",
        "border":       "#3a4a6a",
        "list_sel":     "#3a7bd5",
        "list_sel_txt": "#ffffff",
    },
}


def get_stylesheet(theme="light"):
    t = THEME.get(theme, THEME["light"])
    return f"""
        QMainWindow, QDialog {{
            background-color: {t['bg']};
        }}
        QWidget {{
            background-color: {t['bg']};
            color: {t['text']};
            font-family: 'DM Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
        }}
        QGroupBox {{
            background-color: {t['card']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            margin-top: 10px;
            padding: 8px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            color: {t['accent']};
        }}
        QTreeWidget {{
            background-color: {t['card']};
            border: 1px solid {t['border']};
            border-radius: 4px;
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 5px 4px;
            border-bottom: 1px solid {t['border']};
        }}
        QTreeWidget::item:selected {{
            background-color: {t['list_sel']};
            color: {t['list_sel_txt']};
        }}
        QTreeWidget::item:hover:!selected {{
            background-color: {t['panel']};
        }}
        QPushButton {{
            background-color: {t['accent']};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 7px 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {t['accent_hover']};
        }}
        QPushButton:disabled {{
            background-color: {t['border']};
            color: {t['subtext']};
        }}
        QLineEdit, QTextEdit, QSpinBox, QComboBox {{
            background-color: {t['card']};
            border: 1px solid {t['border']};
            border-radius: 4px;
            padding: 5px 8px;
            color: {t['text']};
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
            border: 1px solid {t['accent']};
        }}
        QLabel {{
            background-color: transparent;
            color: {t['text']};
        }}
        QSplitter::handle {{
            background-color: {t['border']};
        }}
        QMenuBar {{
            background-color: {t['panel']};
            color: {t['text']};
        }}
        QMenuBar::item:selected {{
            background-color: {t['accent']};
            color: #ffffff;
        }}
        QMenu {{
            background-color: {t['card']};
            border: 1px solid {t['border']};
        }}
        QMenu::item:selected {{
            background-color: {t['accent']};
            color: #ffffff;
        }}
        QScrollArea {{
            border: none;
        }}
    """


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def load_settings():
    os.makedirs(APPDATA_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    os.makedirs(APPDATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS folders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            parent_id   INTEGER REFERENCES folders(id),
            sort_order  INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS positions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL DEFAULT '',
            fen         TEXT NOT NULL,
            ideas       TEXT,
            strategies  TEXT,
            folder_id   INTEGER REFERENCES folders(id),
            date_added  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS games (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id     INTEGER NOT NULL REFERENCES positions(id),
            pgn             TEXT NOT NULL,
            bot_name        TEXT,
            bot_rating      INTEGER,
            result          TEXT,
            max_advantage   INTEGER,
            min_eval        INTEGER,
            date_played     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS postmortems (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id     INTEGER NOT NULL REFERENCES games(id),
            explanation TEXT
        );
        CREATE TABLE IF NOT EXISTS game_evals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id     INTEGER NOT NULL REFERENCES games(id),
            move_number INTEGER NOT NULL,
            eval_cp     INTEGER
        );
    """)
    for stmt in [
        "ALTER TABLE positions ADD COLUMN title TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE positions ADD COLUMN folder_id INTEGER REFERENCES folders(id)",
        "ALTER TABLE folders ADD COLUMN parent_id INTEGER REFERENCES folders(id)",
        "ALTER TABLE games ADD COLUMN player_rating INTEGER",
        "ALTER TABLE games ADD COLUMN playstyle TEXT",
    ]:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            pass
    conn.close()


def db_add_position(db_path, title, fen, ideas, strategies, folder_id=None):
    conn = get_db_connection(db_path)
    cur = conn.execute(
        "INSERT INTO positions (title, fen, ideas, strategies, folder_id) VALUES (?, ?, ?, ?, ?)",
        (title, fen, ideas, strategies, folder_id)
    )
    pos_id = cur.lastrowid
    conn.commit()
    conn.close()
    return pos_id


def db_update_position_title(db_path, position_id, title):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE positions SET title=? WHERE id=?", (title, position_id))
    conn.commit()
    conn.close()


def db_update_position_ideas(db_path, position_id, ideas):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE positions SET ideas=? WHERE id=?", (ideas, position_id))
    conn.commit()
    conn.close()


def db_delete_position(db_path, position_id):
    conn = get_db_connection(db_path)
    game_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM games WHERE position_id=?", (position_id,)
    ).fetchall()]
    for gid in game_ids:
        conn.execute("DELETE FROM game_evals WHERE game_id=?", (gid,))
        conn.execute("DELETE FROM postmortems WHERE game_id=?", (gid,))
    conn.execute("DELETE FROM games WHERE position_id=?", (position_id,))
    conn.execute("DELETE FROM positions WHERE id=?", (position_id,))
    conn.commit()
    conn.close()


def db_update_position(db_path, position_id, title, fen, ideas):
    conn = get_db_connection(db_path)
    conn.execute(
        "UPDATE positions SET title=?, fen=?, ideas=? WHERE id=?",
        (title, fen, ideas, position_id)
    )
    conn.commit()
    conn.close()


def db_get_positions(db_path, folder_id=None):
    conn = get_db_connection(db_path)
    if folder_id is None:
        rows = conn.execute(
            "SELECT id, title, fen, ideas, strategies, folder_id, date_added "
            "FROM positions WHERE folder_id IS NULL ORDER BY date_added DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, fen, ideas, strategies, folder_id, date_added "
            "FROM positions WHERE folder_id=? ORDER BY date_added DESC",
            (folder_id,)
        ).fetchall()
    conn.close()
    return rows


def db_get_position(db_path, position_id):
    conn = get_db_connection(db_path)
    row = conn.execute(
        "SELECT id, title, fen, ideas, strategies, folder_id, date_added FROM positions WHERE id=?",
        (position_id,)
    ).fetchone()
    conn.close()
    return row


def db_move_position_to_folder(db_path, position_id, folder_id):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE positions SET folder_id=? WHERE id=?", (folder_id, position_id))
    conn.commit()
    conn.close()


def db_add_folder(db_path, name, parent_id=None):
    conn = get_db_connection(db_path)
    cur = conn.execute("INSERT INTO folders (name, parent_id) VALUES (?, ?)", (name, parent_id))
    folder_id = cur.lastrowid
    conn.commit()
    conn.close()
    return folder_id


def db_delete_folder(db_path, folder_id):
    conn = get_db_connection(db_path)

    def _collect_ids(fid):
        ids = [fid]
        children = conn.execute("SELECT id FROM folders WHERE parent_id=?", (fid,)).fetchall()
        for c in children:
            ids.extend(_collect_ids(c["id"]))
        return ids

    all_ids = _collect_ids(folder_id)
    for fid in all_ids:
        conn.execute("UPDATE positions SET folder_id=NULL WHERE folder_id=?", (fid,))
        conn.execute("DELETE FROM folders WHERE id=?", (fid,))
    conn.commit()
    conn.close()


def db_move_folder_to_parent(db_path, folder_id, parent_id):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE folders SET parent_id=? WHERE id=?", (parent_id, folder_id))
    conn.commit()
    conn.close()


def db_get_folders(db_path, parent_id=None):
    conn = get_db_connection(db_path)
    if parent_id is None:
        rows = conn.execute(
            "SELECT id, name, parent_id FROM folders WHERE parent_id IS NULL ORDER BY sort_order, name"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, parent_id FROM folders WHERE parent_id=? ORDER BY sort_order, name",
            (parent_id,)
        ).fetchall()
    conn.close()
    return rows


def db_add_game(db_path, position_id, pgn, bot_name, bot_rating, result, max_advantage, min_eval, player_rating=None, playstyle=None):
    conn = get_db_connection(db_path)
    cur = conn.execute(
        "INSERT INTO games (position_id, pgn, bot_name, bot_rating, result, max_advantage, min_eval, player_rating, playstyle) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (position_id, pgn, bot_name, bot_rating, result, max_advantage, min_eval, player_rating, playstyle)
    )
    game_id = cur.lastrowid
    conn.commit()
    conn.close()
    return game_id


def db_get_games(db_path, position_id):
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT id, position_id, pgn, bot_name, bot_rating, result, max_advantage, min_eval, date_played, player_rating, playstyle "
        "FROM games WHERE position_id=? ORDER BY date_played DESC, id DESC",
        (position_id,)
    ).fetchall()
    conn.close()
    return rows


def db_get_form(db_path, position_id, n=5):
    """Return last n game results oldest-first."""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT result FROM games WHERE position_id=? ORDER BY date_played DESC LIMIT ?",
        (position_id, n)
    ).fetchall()
    conn.close()
    return [r["result"] for r in reversed(rows)]


def db_get_tier_stats(db_path, position_id, player_rating, upper_threshold, lower_threshold,
                      tier_upper_cutoff=400, tier_lower_cutoff=400):
    """Return stats broken into rating tiers relative to player_rating."""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT result, bot_rating, max_advantage, min_eval FROM games WHERE position_id=?",
        (position_id,)
    ).fetchall()
    conn.close()

    upper_bound = player_rating + tier_upper_cutoff
    lower_bound = player_rating - tier_lower_cutoff

    tiers = {
        "higher": {"label": f"Higher Rated Players (>{upper_bound})", "games": []},
        "equal":  {"label": f"Equal Rated Players ({lower_bound}–{upper_bound})", "games": []},
        "lower":  {"label": f"Lower Rated Players (<{lower_bound})", "games": []},
        "unknown":{"label": "Unknown Rating", "games": []},
    }

    for r in rows:
        br = r["bot_rating"]
        if br is None:
            tiers["unknown"]["games"].append(r)
        elif br > upper_bound:
            tiers["higher"]["games"].append(r)
        elif br < lower_bound:
            tiers["lower"]["games"].append(r)
        else:
            tiers["equal"]["games"].append(r)

    result = {}
    for key in ["higher", "equal", "lower", "unknown"]:
        tier = tiers[key]
        games = tier["games"]
        total = len(games)
        wins   = sum(1 for g in games if g["result"] == "WIN")
        losses = sum(1 for g in games if g["result"] == "LOSS")
        draws  = sum(1 for g in games if g["result"] == "DRAW")
        win_rate = round(100 * wins / total) if total else 0
        result[key] = {
            "label": tier["label"],
            "total": total, "wins": wins, "losses": losses,
            "draws": draws, "win_rate": win_rate,
        }
    return result


def db_update_game_playstyle(db_path, game_id, playstyle):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE games SET playstyle=? WHERE id=?", (playstyle, game_id))
    conn.commit()
    conn.close()


def db_update_all_games_playstyle_for_bot(db_path, bot_name, playstyle):
    """Update playstyle for all games played against a given bot."""
    conn = get_db_connection(db_path)
    conn.execute("UPDATE games SET playstyle=? WHERE bot_name=?", (playstyle, bot_name))
    conn.commit()
    conn.close()


def db_get_playstyle_stats(db_path, position_id):
    """Return win/loss/draw counts and ordered results list per playstyle."""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT playstyle, result FROM games WHERE position_id=? ORDER BY date_played ASC, id ASC",
        (position_id,)
    ).fetchall()
    conn.close()

    styles = ["Guardian", "Observer", "Mediator", "Hunter", "Savage"]
    stats = {s: {"total": 0, "wins": 0, "losses": 0, "draws": 0, "win_rate": 0, "results": []} for s in styles}
    stats["Unknown"] = {"total": 0, "wins": 0, "losses": 0, "draws": 0, "win_rate": 0, "results": []}

    for r in rows:
        ps = r["playstyle"] if r["playstyle"] in styles else "Unknown"
        stats[ps]["total"] += 1
        stats[ps]["results"].append(r["result"])
        if r["result"] == "WIN":    stats[ps]["wins"]   += 1
        elif r["result"] == "LOSS": stats[ps]["losses"] += 1
        elif r["result"] == "DRAW": stats[ps]["draws"]  += 1

    for ps in stats:
        t = stats[ps]["total"]
        stats[ps]["win_rate"] = round(100 * stats[ps]["wins"] / t) if t else 0

    return stats


# ---------------------------------------------------------------------------
# Bot Playstyle Lookup
# ---------------------------------------------------------------------------

PLAYSTYLES = ["Guardian", "Observer", "Mediator", "Hunter", "Savage"]
BOT_PLAYSTYLES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_playstyles.json")


def load_bot_playstyles():
    if os.path.exists(BOT_PLAYSTYLES_FILE):
        try:
            with open(BOT_PLAYSTYLES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_bot_playstyles(data):
    with open(BOT_PLAYSTYLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def lookup_bot_playstyle(bot_name):
    """Return playstyle string or None if unknown."""
    data = load_bot_playstyles()
    return data.get(bot_name)


def register_bot_playstyle(bot_name, playstyle):
    """Save a bot→playstyle mapping."""
    data = load_bot_playstyles()
    data[bot_name] = playstyle
    save_bot_playstyles(data)


def db_rename_folder(db_path, folder_id, new_name):
    conn = get_db_connection(db_path)
    conn.execute("UPDATE folders SET name=? WHERE id=?", (new_name, folder_id))
    conn.commit()
    conn.close()


def db_save_evals(db_path, game_id, evals):
    """Save list of (move_number, eval_cp) tuples."""
    conn = get_db_connection(db_path)
    conn.executemany(
        "INSERT INTO game_evals (game_id, move_number, eval_cp) VALUES (?, ?, ?)",
        [(game_id, i + 1, cp) for i, cp in enumerate(evals)]
    )
    conn.commit()
    conn.close()


def db_get_evals(db_path, game_id):
    """Return list of eval_cp values in move order."""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT eval_cp FROM game_evals WHERE game_id=? ORDER BY move_number ASC",
        (game_id,)
    ).fetchall()
    conn.close()
    return [r["eval_cp"] for r in rows]


def db_get_stats(db_path, position_id, upper_threshold, lower_threshold):
    """Return summary stats dict for a position."""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        "SELECT result, max_advantage, min_eval FROM games WHERE position_id=?",
        (position_id,)
    ).fetchall()
    conn.close()
    total = len(rows)
    wins   = sum(1 for r in rows if r["result"] == "WIN")
    losses = sum(1 for r in rows if r["result"] == "LOSS")
    draws  = sum(1 for r in rows if r["result"] == "DRAW")
    above  = sum(1 for r in rows if r["max_advantage"] is not None and r["max_advantage"] >= upper_threshold)
    below  = sum(1 for r in rows if r["min_eval"] is not None and r["min_eval"] <= lower_threshold)
    win_rate = round(100 * wins / total) if total else 0
    return {
        "total": total, "wins": wins, "losses": losses, "draws": draws,
        "win_rate": win_rate, "above_upper": above, "below_lower": below,
    }


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

def db_export(db_path):
    """Export all data to a dict suitable for JSON serialisation."""
    conn = get_db_connection(db_path)

    positions = [dict(r) for r in conn.execute(
        "SELECT * FROM positions"
    ).fetchall()]

    games = [dict(r) for r in conn.execute(
        "SELECT * FROM games"
    ).fetchall()]

    evals = [dict(r) for r in conn.execute(
        "SELECT * FROM game_evals"
    ).fetchall()]

    folders = [dict(r) for r in conn.execute(
        "SELECT * FROM folders"
    ).fetchall()]

    conn.close()
    return {
        "version": APP_VERSION,
        "positions": positions,
        "games": games,
        "game_evals": evals,
        "folders": folders,
    }


def db_import(db_path, data):
    """Wipe and restore all data from exported dict."""
    conn = get_db_connection(db_path)
    conn.executescript("""
        DELETE FROM game_evals;
        DELETE FROM postmortems;
        DELETE FROM games;
        DELETE FROM positions;
        DELETE FROM folders;
    """)

    for f in data.get("folders", []):
        conn.execute(
            "INSERT INTO folders (id, name, parent_id, sort_order) VALUES (?,?,?,?)",
            (f.get("id"), f.get("name"), f.get("parent_id"), f.get("sort_order", 0))
        )

    for p in data.get("positions", []):
        conn.execute(
            "INSERT INTO positions (id, title, fen, ideas, strategies, folder_id, date_added) "
            "VALUES (?,?,?,?,?,?,?)",
            (p.get("id"), p.get("title",""), p.get("fen",""), p.get("ideas",""),
             p.get("strategies",""), p.get("folder_id"), p.get("date_added"))
        )

    for g in data.get("games", []):
        conn.execute(
            "INSERT INTO games (id, position_id, pgn, bot_name, bot_rating, result, "
            "max_advantage, min_eval, date_played, player_rating) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (g.get("id"), g.get("position_id"), g.get("pgn",""), g.get("bot_name"),
             g.get("bot_rating"), g.get("result"), g.get("max_advantage"),
             g.get("min_eval"), g.get("date_played"), g.get("player_rating"))
        )

    for e in data.get("game_evals", []):
        conn.execute(
            "INSERT INTO game_evals (id, game_id, move_number, eval_cp) VALUES (?,?,?,?)",
            (e.get("id"), e.get("game_id"), e.get("move_number"), e.get("eval_cp"))
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Chessiverse Integration
# ---------------------------------------------------------------------------

def build_chessiverse_url(fen):
    ok, board = validate_fen(fen)
    if not ok:
        return None
    side = "white" if board.turn else "black"
    encoded_fen = fen.replace(" ", "+")
    return f"https://chessiverse.com/game?type=custom&fen={encoded_fen}&side={side}"


def open_in_chrome(url):
    import subprocess
    import webbrowser
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            subprocess.Popen([path, url])
            return True
    webbrowser.open(url)
    return False


# ---------------------------------------------------------------------------
# FEN / Board helpers
# ---------------------------------------------------------------------------

def validate_fen(fen):
    try:
        import chess
        board = chess.Board(fen)
        return True, board
    except Exception as e:
        return False, str(e)


def fen_side(fen):
    ok, board = validate_fen(fen)
    if ok:
        return "white" if board.turn else "black"
    return "white"


def render_board_svg(fen, size=280):
    try:
        import chess, chess.svg
        ok, board = validate_fen(fen)
        if not ok:
            return None
        orientation = chess.WHITE if board.turn == chess.WHITE else chess.BLACK
        svg_str = chess.svg.board(
            board, size=size, orientation=orientation,
            coordinates=False
        )
        return svg_str.encode("utf-8")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Form Circle Widget
# ---------------------------------------------------------------------------

RESULT_COLORS = {
    "WIN":  "#2ecc71",
    "LOSS": "#e74c3c",
    "DRAW": "#95a5a6",
}


class FormCircle(QLabel):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        self.setFixedSize(12, 12)
        color = RESULT_COLORS.get(result, "#95a5a6")
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 6px;
            border: none;
        """)
        self.setToolTip(result)


# ---------------------------------------------------------------------------
# Analysis Worker Thread
# ---------------------------------------------------------------------------

from PyQt6.QtCore import QThread, pyqtSignal

class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current move, total moves

    def __init__(self, pgn_text, position_fen, engine_path, engine_depth,
                 engine_time_sec, upper_threshold, lower_threshold, username):
        super().__init__()
        self.pgn_text         = pgn_text
        self.position_fen     = position_fen
        self.engine_path      = engine_path
        self.engine_depth     = engine_depth
        self.engine_time_sec  = engine_time_sec
        self.upper_threshold  = upper_threshold
        self.lower_threshold  = lower_threshold
        self.username         = username
        self._cancelled       = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        import chess, chess.pgn, chess.engine, io
        try:
            game = chess.pgn.read_game(io.StringIO(self.pgn_text))
            if game is None:
                self.error.emit("Could not parse PGN.")
                return

            pgn_fen = game.headers.get("FEN", "").strip()
            if not pgn_fen:
                self.error.emit("PGN does not contain a FEN header.")
                return

            def normalize(f): return " ".join(f.strip().split()[:4])
            if normalize(pgn_fen) != normalize(self.position_fen):
                self.error.emit(
                    "PGN FEN does not match this position.\n\n"
                    f"Expected: {self.position_fen}\n\nGot: {pgn_fen}"
                )
                return

            ok, start_board = validate_fen(self.position_fen)
            if not ok:
                self.error.emit("Invalid position FEN.")
                return
            player_is_white = start_board.turn == chess.WHITE

            white_player = game.headers.get("White", "")
            black_player = game.headers.get("Black", "")
            if player_is_white and white_player.lower() != self.username.lower():
                self.error.emit(
                    f"Expected {self.username} to play White, but White is '{white_player}'."
                )
                return
            if not player_is_white and black_player.lower() != self.username.lower():
                self.error.emit(
                    f"Expected {self.username} to play Black, but Black is '{black_player}'."
                )
                return

            if player_is_white:
                player_rating_str = game.headers.get("WhiteElo", "")
                bot_rating_str    = game.headers.get("BlackElo", "")
                bot_name          = black_player or "Unknown"
            else:
                player_rating_str = game.headers.get("BlackElo", "")
                bot_rating_str    = game.headers.get("WhiteElo", "")
                bot_name          = white_player or "Unknown"

            try: bot_rating = int(bot_rating_str)
            except: bot_rating = None
            try: player_rating = int(player_rating_str)
            except: player_rating = None

            moves = list(game.mainline_moves())
            total = len(moves)
            board = game.board()
            max_advantage = None
            min_eval = None
            result = "DRAW"
            evals_list = []

            limit = (chess.engine.Limit(depth=self.engine_depth)
                     if self.engine_depth
                     else chess.engine.Limit(time=self.engine_time_sec))

            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                for i, move in enumerate(moves):
                    if self._cancelled:
                        return
                    board.push(move)
                    info = engine.analyse(board, limit)
                    score = info["score"]
                    cp = (score.white().score(mate_score=10000) if player_is_white
                          else score.black().score(mate_score=10000))
                    evals_list.append(cp)
                    if cp is not None:
                        if max_advantage is None or cp > max_advantage: max_advantage = cp
                        if min_eval is None or cp < min_eval: min_eval = cp
                        if result == "DRAW":
                            if cp >= self.upper_threshold: result = "WIN"
                            elif cp <= self.lower_threshold: result = "LOSS"
                    self.progress.emit(i + 1, total)

            self.finished.emit({
                "bot_name": bot_name, "bot_rating": bot_rating,
                "player_rating": player_rating, "result": result,
                "max_advantage": max_advantage, "min_eval": min_eval,
                "pgn": self.pgn_text, "evals": evals_list,
            })

        except Exception as e:
            self.error.emit(f"Engine error: {e}")


# ---------------------------------------------------------------------------
# Eval Graph Window
# ---------------------------------------------------------------------------

class EvalGraphWindow(QDialog):
    """Popup showing evaluation graph for a single game."""

    def __init__(self, evals, upper_threshold, lower_threshold, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Evaluation Graph — {result}")
        self.setMinimumSize(700, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        try:
            import pyqtgraph as pg
            self._build_pyqtgraph(layout, evals, upper_threshold, lower_threshold, result)
        except ImportError:
            self._build_fallback(layout, evals, upper_threshold, lower_threshold)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_pyqtgraph(self, layout, evals, upper_threshold, lower_threshold, result):
        import pyqtgraph as pg
        pg.setConfigOption('background', '#ffffff')
        pg.setConfigOption('foreground', '#1a1a2e')

        plot = pg.PlotWidget()
        plot.setLabel('left', 'Evaluation (cp)')
        plot.setLabel('bottom', 'Move')
        plot.showGrid(x=True, y=True, alpha=0.3)

        valid = [e for e in evals if e is not None]
        y_min = min(lower_threshold * 1.5, min(valid) - 50) if valid else lower_threshold * 1.5
        y_max = max(upper_threshold * 1.5, max(valid) + 50) if valid else upper_threshold * 1.5
        plot.setYRange(y_min, y_max)

        # Force integer x-axis ticks
        ax = plot.getAxis('bottom')
        n = len(evals)
        tick_spacing = max(1, n // 10)
        ticks = [(i, str(i)) for i in range(1, n + 1) if (i - 1) % tick_spacing == 0]
        ax.setTicks([ticks])

        xs = list(range(1, n + 1))
        ys = [e if e is not None else 0 for e in evals]

        # Eval line — always blue
        plot.plot(xs, ys, pen=pg.mkPen(color='#3a7bd5', width=2),
                  symbol='o', symbolSize=5, symbolBrush='#3a7bd5')

        # Upper threshold — thick green dashed + label
        upper_line = pg.InfiniteLine(
            pos=upper_threshold, angle=0,
            pen=pg.mkPen(color='#2ecc71', width=3, style=pg.QtCore.Qt.PenStyle.DashLine),
            label=f'Upper +{upper_threshold}',
            labelOpts={'color': '#2ecc71', 'position': 0.95, 'fill': (255,255,255,180)}
        )
        plot.addItem(upper_line)

        # Lower threshold — thick red dashed + label
        lower_line = pg.InfiniteLine(
            pos=lower_threshold, angle=0,
            pen=pg.mkPen(color='#e74c3c', width=3, style=pg.QtCore.Qt.PenStyle.DashLine),
            label=f'Lower {lower_threshold}',
            labelOpts={'color': '#e74c3c', 'position': 0.95, 'fill': (255,255,255,180)}
        )
        plot.addItem(lower_line)

        # Zero line
        zero_line = pg.InfiniteLine(pos=0, angle=0,
                                    pen=pg.mkPen(color='#aaaaaa', width=1))
        plot.addItem(zero_line)

        layout.addWidget(plot)

    def _build_fallback(self, layout, evals, upper_threshold, lower_threshold):
        """Simple SVG fallback if pyqtgraph not available."""
        valid = [e for e in evals if e is not None]
        if not valid:
            layout.addWidget(QLabel("No evaluation data."))
            return

        W, H = 660, 280
        margin = 40
        y_min = min(lower_threshold * 1.5, min(valid) - 50)
        y_max = max(upper_threshold * 1.5, max(valid) + 50)
        y_range = y_max - y_min or 1
        n = len(evals)

        def px(i): return margin + (i / max(n - 1, 1)) * (W - 2 * margin)
        def py(v): return H - margin - ((v - y_min) / y_range) * (H - 2 * margin)

        pts = " ".join(f"{px(i)},{py(e if e is not None else 0)}" for i, e in enumerate(evals))
        upper_y = py(upper_threshold)
        lower_y = py(lower_threshold)
        zero_y  = py(0)

        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'>
  <rect width='{W}' height='{H}' fill='white'/>
  <line x1='{margin}' y1='{zero_y:.1f}' x2='{W-margin}' y2='{zero_y:.1f}' stroke='#aaa' stroke-width='1'/>
  <line x1='{margin}' y1='{upper_y:.1f}' x2='{W-margin}' y2='{upper_y:.1f}' stroke='#2ecc71' stroke-width='1' stroke-dasharray='4'/>
  <line x1='{margin}' y1='{lower_y:.1f}' x2='{W-margin}' y2='{lower_y:.1f}' stroke='#e74c3c' stroke-width='1' stroke-dasharray='4'/>
  <polyline points='{pts}' fill='none' stroke='#3a7bd5' stroke-width='2'/>
</svg>"""

        from PyQt6.QtSvgWidgets import QSvgWidget
        from PyQt6.QtCore import QByteArray
        svg_widget = QSvgWidget()
        svg_widget.load(QByteArray(svg.encode()))
        svg_widget.setFixedSize(W, H)
        layout.addWidget(svg_widget)


# ---------------------------------------------------------------------------
# Analysis Progress Dialog
# ---------------------------------------------------------------------------

class AnalysisProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysing…")
        self.setFixedSize(360, 120)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.status_lbl = QLabel("Starting engine…")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_progress(self, current, total):
        pct = int(100 * current / total) if total else 0
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(f"Analysing move {current} of {total}…")


# ---------------------------------------------------------------------------
# Import PGN Dialog
# ---------------------------------------------------------------------------

class ImportPgnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import PGN")
        self.setMinimumWidth(520)
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("Paste PGN from Chessiverse below:")
        layout.addWidget(lbl)

        self.pgn_input = QTextEdit()
        self.pgn_input.setPlaceholderText("[Event \"...\"]\n1. e4 e5 ...")
        layout.addWidget(self.pgn_input)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_pgn(self):
        return self.pgn_input.toPlainText().strip()


# ---------------------------------------------------------------------------
# Add Position Dialog
# ---------------------------------------------------------------------------

class AddPositionDialog(QDialog):
    def __init__(self, parent=None, prefill=None):
        """prefill: dict with title, fen, ideas for editing an existing position."""
        super().__init__(parent)
        self.setWindowTitle("Edit Position" if prefill else "Add Position")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title_group = QGroupBox("Position Title")
        title_layout = QVBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Weak d5 Square Drill")
        self.title_input.textChanged.connect(self._check_save)
        title_layout.addWidget(self.title_input)
        layout.addWidget(title_group)

        fen_group = QGroupBox("Position (FEN)")
        fen_layout = QVBoxLayout(fen_group)
        self.fen_input = QLineEdit()
        self.fen_input.setPlaceholderText("Paste FEN string here…")
        self.fen_status = QLabel("")
        self.fen_status.setStyleSheet("color: #888; font-size: 11px;")
        self.fen_input.textChanged.connect(self._on_fen_changed)
        fen_layout.addWidget(self.fen_input)
        fen_layout.addWidget(self.fen_status)
        layout.addWidget(fen_group)

        ideas_group = QGroupBox("Key Ideas")
        ideas_layout = QVBoxLayout(ideas_group)
        self.ideas_input = QTextEdit()
        self.ideas_input.setPlaceholderText("e.g. exploit weak d5 square, bishop pair advantage…")
        self.ideas_input.setFixedHeight(80)
        ideas_layout.addWidget(self.ideas_input)
        layout.addWidget(ideas_group)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)
        self.buttons.accepted.connect(self._on_save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._fen_valid = False

        # Pre-fill for edit mode
        if prefill:
            self.title_input.setText(prefill.get("title", ""))
            self.fen_input.setText(prefill.get("fen", ""))
            self.ideas_input.setPlainText(prefill.get("ideas", ""))

    def _check_save(self):
        enabled = self._fen_valid and bool(self.title_input.text().strip())
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(enabled)

    def _on_fen_changed(self, text):
        text = text.strip()
        if not text:
            self.fen_status.setText("")
            self._fen_valid = False
        else:
            ok, result = validate_fen(text)
            if ok:
                side = "White" if result.turn else "Black"
                self.fen_status.setText(f"✓ Valid — {side} to move")
                self.fen_status.setStyleSheet("color: #2a9d2a; font-size: 11px;")
                self._fen_valid = True
            else:
                self.fen_status.setText("✗ Invalid FEN")
                self.fen_status.setStyleSheet("color: #cc2222; font-size: 11px;")
                self._fen_valid = False
        self._check_save()

    def _on_save(self):
        if not self._fen_valid or not self.title_input.text().strip():
            return
        self.accept()

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "fen": self.fen_input.text().strip(),
            "ideas": self.ideas_input.toPlainText().strip(),
            "strategies": "",
        }


# ---------------------------------------------------------------------------
# Engine Detection
# ---------------------------------------------------------------------------

def detect_engine(path):
    """
    Run engine binary and read 'id name' response.
    Returns (True, "Stockfish 18") or (False, "error message").
    """
    import subprocess
    import time
    try:
        proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        name = None
        start = time.time()
        while time.time() - start < 5:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("id name"):
                name = line[len("id name"):].strip()
            if line == "uciok":
                break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=3)
        if name:
            return True, name
        return False, "Engine did not respond with a name."
    except FileNotFoundError:
        return False, "File not found."
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Engine ---
        engine_group = QGroupBox("Engine")
        engine_form = QFormLayout(engine_group)
        engine_form.setSpacing(8)

        path_row = QHBoxLayout()
        self.engine_path = QLineEdit(settings.get("engine_path", "stockfish"))
        path_row.addWidget(self.engine_path)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse_engine)
        path_row.addWidget(self.browse_btn)
        engine_form.addRow("Engine Path:", path_row)

        self.engine_detected = QLabel("")
        self.engine_detected.setStyleSheet("color: #2a9d2a; font-size: 11px;")
        engine_form.addRow("", self.engine_detected)

        # Analysis mode toggle
        mode_row = QHBoxLayout()
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup
        self.mode_depth = QRadioButton("Depth")
        self.mode_time  = QRadioButton("Time Per Move")
        self._mode_group = QButtonGroup()
        self._mode_group.addButton(self.mode_depth)
        self._mode_group.addButton(self.mode_time)
        mode_row.addWidget(self.mode_depth)
        mode_row.addWidget(self.mode_time)
        mode_row.addStretch()
        engine_form.addRow("Analysis Mode:", mode_row)

        self.engine_depth = QSpinBox()
        self.engine_depth.setRange(1, 40)
        self.engine_depth.setValue(settings.get("engine_depth", 20))
        self.depth_row_label = QLabel("Depth:")
        engine_form.addRow(self.depth_row_label, self.engine_depth)

        self.engine_time = QSpinBox()
        self.engine_time.setRange(1, 60)
        self.engine_time.setValue(settings.get("engine_time_sec", 3))
        self.time_row_label = QLabel("Time Per Move (sec):")
        engine_form.addRow(self.time_row_label, self.engine_time)

        mode = settings.get("engine_mode", "depth")
        if mode == "time":
            self.mode_time.setChecked(True)
        else:
            self.mode_depth.setChecked(True)
        self._update_mode_visibility()
        self.mode_depth.toggled.connect(self._update_mode_visibility)
        self.mode_time.toggled.connect(self._update_mode_visibility)

        layout.addWidget(engine_group)

        # --- General ---
        general_group = QGroupBox("General")
        general_form = QFormLayout(general_group)
        general_form.setSpacing(8)

        self.player_username = QLineEdit(settings.get("player_username", "dab327"))
        general_form.addRow("Your Username:", self.player_username)

        self.player_rating = QSpinBox()
        self.player_rating.setRange(0, 3500)
        self.player_rating.setValue(settings.get("player_rating", 1500))
        general_form.addRow("Your Rating:", self.player_rating)

        self.tier_upper = QSpinBox()
        self.tier_upper.setRange(0, 1000)
        self.tier_upper.setValue(settings.get("tier_upper_cutoff", 400))
        general_form.addRow("Tier Upper Cutoff (+):", self.tier_upper)

        self.tier_lower = QSpinBox()
        self.tier_lower.setRange(0, 1000)
        self.tier_lower.setValue(settings.get("tier_lower_cutoff", 400))
        general_form.addRow("Tier Lower Cutoff (-):", self.tier_lower)

        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])
        self.theme.setCurrentText(settings.get("theme", "light"))
        general_form.addRow("Theme:", self.theme)

        self.db_path = QLineEdit(settings.get("db_path", DEFAULT_DB_PATH))
        general_form.addRow("Database Path:", self.db_path)

        self.form_games = QSpinBox()
        self.form_games.setRange(1, 20)
        self.form_games.setValue(settings.get("form_games_shown", 5))
        general_form.addRow("Form Games Shown:", self.form_games)

        layout.addWidget(general_group)

        # --- Thresholds ---
        thresh_group = QGroupBox("Thresholds")
        thresh_form = QFormLayout(thresh_group)
        thresh_form.setSpacing(8)

        self.lower_threshold = QSpinBox()
        self.lower_threshold.setRange(-2000, 0)
        self.lower_threshold.setValue(settings.get("lower_threshold_cp", -200))
        thresh_form.addRow("Lower Threshold (cp):", self.lower_threshold)

        self.upper_threshold = QSpinBox()
        self.upper_threshold.setRange(0, 2000)
        self.upper_threshold.setValue(settings.get("upper_threshold_cp", 500))
        thresh_form.addRow("Upper Threshold (cp):", self.upper_threshold)

        layout.addWidget(thresh_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Try to show detected engine on open
        self._try_detect_current()

    def _update_mode_visibility(self):
        depth_mode = self.mode_depth.isChecked()
        self.engine_depth.setVisible(depth_mode)
        self.depth_row_label.setVisible(depth_mode)
        self.engine_time.setVisible(not depth_mode)
        self.time_row_label.setVisible(not depth_mode)
        self.adjustSize()

    def _browse_engine(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Engine Binary", "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.engine_path.setText(path)
            self._try_detect(path)

    def _try_detect_current(self):
        path = self.engine_path.text().strip()
        if path:
            self._try_detect(path)

    def _try_detect(self, path):
        ok, name = detect_engine(path)
        if ok:
            self.engine_detected.setText(f"✓ {name}")
            self.engine_detected.setStyleSheet("color: #2a9d2a; font-size: 11px;")
        else:
            self.engine_detected.setText(f"✗ {name}")
            self.engine_detected.setStyleSheet("color: #cc2222; font-size: 11px;")

    def get_settings(self):
        return {
            "engine_path": self.engine_path.text().strip(),
            "engine_mode": "time" if self.mode_time.isChecked() else "depth",
            "engine_depth": self.engine_depth.value(),
            "engine_time_sec": self.engine_time.value(),
            "theme": self.theme.currentText(),
            "db_path": self.db_path.text().strip(),
            "lower_threshold_cp": self.lower_threshold.value(),
            "upper_threshold_cp": self.upper_threshold.value(),
            "form_games_shown": self.form_games.value(),
            "player_username": self.player_username.text().strip(),
            "player_rating": self.player_rating.value(),
            "tier_upper_cutoff": self.tier_upper.value(),
            "tier_lower_cutoff": self.tier_lower.value(),
        }


# ---------------------------------------------------------------------------
# Position Tree
# ---------------------------------------------------------------------------

POSITION_ITEM_TYPE = QTreeWidgetItem.ItemType.UserType + 1
FOLDER_ITEM_TYPE   = QTreeWidgetItem.ItemType.UserType + 2
ROLE_POS_ID        = Qt.ItemDataRole.UserRole
ROLE_FOLDER_ID     = Qt.ItemDataRole.UserRole + 1


class PositionTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setIndentation(16)

    def _show_context_menu(self, pos):
        item = self.itemAt(pos)
        menu = QMenu(self)
        if item and item.type() == POSITION_ITEM_TYPE:
            menu.addAction("Edit Position").triggered.connect(
                lambda: self._main_window().edit_position(item)
            )
            menu.addAction("Delete Position").triggered.connect(
                lambda: self._main_window().delete_position(item)
            )
            menu.addSeparator()
        menu.addAction("New Folder").triggered.connect(self._main_window().add_folder)
        if item and item.type() == FOLDER_ITEM_TYPE:
            menu.addSeparator()
            menu.addAction("Rename Folder").triggered.connect(
                lambda: self._main_window().rename_folder(item)
            )
            menu.addAction("Delete Folder").triggered.connect(
                lambda: self._main_window().delete_folder(item)
            )
        menu.exec(self.viewport().mapToGlobal(pos))

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt as _Qt
        key = event.key()
        current = self.currentItem()
        if key in (_Qt.Key.Key_Return, _Qt.Key.Key_Enter):
            if current and current.type() == POSITION_ITEM_TYPE:
                self._main_window().play_selected_position()
            return
        super().keyPressEvent(event)

    def _main_window(self):
        w = self.parent()
        while w and not isinstance(w, MainWindow):
            w = w.parent()
        return w

    def dropEvent(self, event):
        dragged = self.currentItem()
        if not dragged:
            event.ignore()
            return
        target = self.itemAt(event.position().toPoint())
        mw = self._main_window()

        if dragged.type() == POSITION_ITEM_TYPE:
            pos_id = dragged.data(0, ROLE_POS_ID)
            if target is None:
                mw.move_position_to_folder(pos_id, None)
            elif target.type() == FOLDER_ITEM_TYPE:
                mw.move_position_to_folder(pos_id, target.data(0, ROLE_FOLDER_ID))
            elif target.type() == POSITION_ITEM_TYPE:
                parent = target.parent()
                fid = parent.data(0, ROLE_FOLDER_ID) if (parent and parent.type() == FOLDER_ITEM_TYPE) else None
                mw.move_position_to_folder(pos_id, fid)
            else:
                event.ignore(); return
        elif dragged.type() == FOLDER_ITEM_TYPE:
            fid = dragged.data(0, ROLE_FOLDER_ID)
            if target is None:
                mw.move_folder_to_parent(fid, None)
            elif target.type() == FOLDER_ITEM_TYPE:
                tfid = target.data(0, ROLE_FOLDER_ID)
                if tfid != fid:
                    mw.move_folder_to_parent(fid, tfid)
                else:
                    event.ignore(); return
            else:
                event.ignore(); return
        else:
            event.ignore(); return
        # Do NOT call super().dropEvent() — _refresh_tree() is sole source of truth
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()


# ---------------------------------------------------------------------------
# Side indicator
# ---------------------------------------------------------------------------

def make_side_indicator(side):
    lbl = QLabel()
    lbl.setFixedSize(12, 12)
    if side == "white":
        lbl.setStyleSheet("background-color: #ffffff; border: 1px solid #555;")
    else:
        lbl.setStyleSheet("background-color: #1a1a1a; border: 1px solid #999;")
    return lbl


# ---------------------------------------------------------------------------
# Stats Bar Widget
# ---------------------------------------------------------------------------

class StatsBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(16)

        def stat(label, obj_name):
            col = QVBoxLayout()
            col.setSpacing(0)
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel("—")
            val.setObjectName(obj_name)
            val.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent;")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(val)
            layout.addLayout(col)
            return val

        self.total_lbl  = stat("GAMES",    "stat_total")
        self.wins_lbl   = stat("WINS",     "stat_wins")
        self.losses_lbl = stat("LOSSES",   "stat_losses")
        self.draws_lbl  = stat("DRAWS",    "stat_draws")
        self.rate_lbl   = stat("WIN RATE", "stat_rate")
        self.above_lbl  = stat("≥ UPPER",  "stat_above")
        self.below_lbl  = stat("≤ LOWER",  "stat_below")
        layout.addStretch()

    def update_stats(self, stats):
        self.total_lbl.setText(str(stats["total"]))
        self.wins_lbl.setText(str(stats["wins"]))
        self.wins_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71; background: transparent;")
        self.losses_lbl.setText(str(stats["losses"]))
        self.losses_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c; background: transparent;")
        self.draws_lbl.setText(str(stats["draws"]))
        self.rate_lbl.setText(f"{stats['win_rate']}%")
        self.above_lbl.setText(str(stats["above_upper"]))
        self.below_lbl.setText(str(stats["below_lower"]))

    def clear(self):
        for lbl in [self.total_lbl, self.wins_lbl, self.losses_lbl,
                    self.draws_lbl, self.rate_lbl, self.above_lbl, self.below_lbl]:
            lbl.setText("—")


# ---------------------------------------------------------------------------
# Tier Stats Widget
# ---------------------------------------------------------------------------

class TierStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._rows = {}
        self._build()

    def _build(self):
        # Header row
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        for text, width in [("Tier", 160), ("G", 36), ("W", 36), ("L", 36), ("D", 36), ("Win%", 50)]:
            lbl = QLabel(text)
            lbl.setFixedWidth(width)
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #888; background: transparent;")
            h.addWidget(lbl)
        h.addStretch()
        self._layout.addWidget(header)

        for key in ["higher", "equal", "lower", "unknown"]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(0)

            tier_lbl = QLabel("—")
            tier_lbl.setFixedWidth(160)
            tier_lbl.setStyleSheet("font-size: 12px; background: transparent;")
            h.addWidget(tier_lbl)

            stats_labels = {}
            for col in ["total", "wins", "losses", "draws", "win_rate"]:
                widths = {"total": 36, "wins": 36, "losses": 36, "draws": 36, "win_rate": 50}
                lbl = QLabel("—")
                lbl.setFixedWidth(widths[col])
                lbl.setStyleSheet("font-size: 12px; background: transparent;")
                h.addWidget(lbl)
                stats_labels[col] = lbl

            h.addStretch()
            self._layout.addWidget(row)
            self._rows[key] = {"tier_lbl": tier_lbl, "stats": stats_labels, "widget": row}

    def update_tiers(self, tier_data):
        for key in ["higher", "equal", "lower", "unknown"]:
            data = tier_data.get(key)
            if not data or key not in self._rows:
                continue
            row = self._rows[key]
            row["tier_lbl"].setText(data["label"])
            row["stats"]["total"].setText(str(data["total"]))
            row["stats"]["wins"].setText(str(data["wins"]))
            row["stats"]["wins"].setStyleSheet(
                "font-size: 12px; background: transparent;" +
                (" color: #2ecc71;" if data["wins"] > 0 else "")
            )
            row["stats"]["losses"].setText(str(data["losses"]))
            row["stats"]["losses"].setStyleSheet(
                "font-size: 12px; background: transparent;" +
                (" color: #e74c3c;" if data["losses"] > 0 else "")
            )
            row["stats"]["draws"].setText(str(data["draws"]))
            row["stats"]["win_rate"].setText(f"{data['win_rate']}%")
            row["widget"].setVisible(data["total"] > 0)

    def clear(self):
        for row in self._rows.values():
            row["tier_lbl"].setText("—")
            for lbl in row["stats"].values():
                lbl.setText("—")


# ---------------------------------------------------------------------------
# Playstyle Stats Widget
# ---------------------------------------------------------------------------

class PlaystyleStatsWidget(QWidget):
    STYLE_COLORS = {
        "Guardian": "#3a7bd5",
        "Observer": "#8e44ad",
        "Mediator": "#27ae60",
        "Hunter":   "#e67e22",
        "Savage":   "#e74c3c",
        "Unknown":  "#95a5a6",
    }
    # Fixed column widths — must match header and data rows exactly
    COL_WIDTHS = [("Playstyle", 90), ("G", 28), ("W", 28), ("L", 28), ("D", 28), ("Win%", 44)]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._n_form = 5
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(3)
        self._rows = {}
        self._build()

    def set_n_form(self, n):
        self._n_form = n

    def _build(self):
        # Header
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        for text, width in self.COL_WIDTHS:
            lbl = QLabel(text)
            lbl.setFixedWidth(width)
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #888; background: transparent;")
            h.addWidget(lbl)
        # Form header
        form_lbl = QLabel("Form")
        form_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #888; background: transparent; margin-left: 6px;")
        h.addWidget(form_lbl)
        h.addStretch()
        self._layout.addWidget(header)

        for style in ["Guardian", "Observer", "Mediator", "Hunter", "Savage", "Unknown"]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(0)
            color = self.STYLE_COLORS.get(style, "#888")

            name_lbl = QLabel(style)
            name_lbl.setFixedWidth(self.COL_WIDTHS[0][1])
            name_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color}; background: transparent;")
            h.addWidget(name_lbl)

            cols = {}
            for col, (_, width) in zip(["total","wins","losses","draws","win_rate"], self.COL_WIDTHS[1:]):
                lbl = QLabel("—")
                lbl.setFixedWidth(width)
                lbl.setStyleSheet("font-size: 12px; background: transparent;")
                h.addWidget(lbl)
                cols[col] = lbl

            # Form dots container
            form_container = QWidget()
            form_container.setStyleSheet("background: transparent;")
            form_h = QHBoxLayout(form_container)
            form_h.setContentsMargins(6, 0, 0, 0)
            form_h.setSpacing(3)
            h.addWidget(form_container)
            h.addStretch()

            self._layout.addWidget(row)
            self._rows[style] = {
                "widget": row,
                "cols": cols,
                "form_h": form_h,
                "form_container": form_container,
            }

    def _clear_form_dots(self, form_h):
        while form_h.count():
            item = form_h.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_stats(self, stats, n_form=None):
        n = n_form or self._n_form
        for style, data in stats.items():
            if style not in self._rows:
                continue
            row = self._rows[style]
            cols = row["cols"]
            cols["total"].setText(str(data["total"]))
            cols["wins"].setText(str(data["wins"]))
            cols["losses"].setText(str(data["losses"]))
            cols["draws"].setText(str(data["draws"]))
            cols["win_rate"].setText(f"{data['win_rate']}%")

            # Form dots — last n results oldest→newest
            form_h = row["form_h"]
            self._clear_form_dots(form_h)
            results = data.get("results", [])
            recent = results[-n:] if len(results) > n else results
            for r in recent:
                dot = FormCircle(r)
                form_h.addWidget(dot)

            row["widget"].setVisible(data["total"] > 0)

    def clear(self):
        for row in self._rows.values():
            for lbl in row["cols"].values():
                lbl.setText("—")
            self._clear_form_dots(row["form_h"])


# ---------------------------------------------------------------------------
# Game History Widget
# ---------------------------------------------------------------------------

class GameHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self._db_path_fn = None
        self._settings_fn = None

    def set_providers(self, db_path_fn, settings_fn):
        self._db_path_fn = db_path_fn
        self._settings_fn = settings_fn

    def _show_graph(self, game_id):
        if not self._db_path_fn or not self._settings_fn:
            return
        evals = db_get_evals(self._db_path_fn(), game_id)
        s = self._settings_fn()
        conn = get_db_connection(self._db_path_fn())
        row = conn.execute("SELECT result FROM games WHERE id=?", (game_id,)).fetchone()
        conn.close()
        result = row["result"] if row else "DRAW"
        graph = EvalGraphWindow(
            evals,
            s.get("upper_threshold_cp", 500),
            s.get("lower_threshold_cp", -200),
            result,
            parent=self
        )
        graph.exec()

    def _set_playstyle(self, game_id, bot_name):
        if not self._db_path_fn or not self._settings_fn:
            return
        from PyQt6.QtWidgets import QInputDialog
        styles = PLAYSTYLES
        current_ps = ""
        conn = get_db_connection(self._db_path_fn())
        row = conn.execute("SELECT playstyle FROM games WHERE id=?", (game_id,)).fetchone()
        conn.close()
        if row and row["playstyle"]:
            current_ps = row["playstyle"]

        style, ok = QInputDialog.getItem(
            self, "Set Playstyle", f"Playstyle for {bot_name}:",
            styles, styles.index(current_ps) if current_ps in styles else 0, False
        )
        if ok and style:
            if bot_name:
                # Update all games for this bot across the entire database
                db_update_all_games_playstyle_for_bot(self._db_path_fn(), bot_name, style)
                register_bot_playstyle(bot_name, style)
            else:
                db_update_game_playstyle(self._db_path_fn(), game_id, style)
            # Reload stats
            if hasattr(self, '_reload_fn') and self._reload_fn:
                self._reload_fn()

    def set_reload_fn(self, fn):
        self._reload_fn = fn

    def load_games(self, games):
        # Clear
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not games:
            lbl = QLabel("No games recorded yet.")
            lbl.setStyleSheet("color: #888; font-size: 12px;")
            self.layout.addWidget(lbl)
            return

        for g in games:
            row = QFrame()
            row.setStyleSheet("QFrame { border: 1px solid #b0c8e8; border-radius: 4px; background: #fff; padding: 4px; }")
            h = QHBoxLayout(row)
            h.setContentsMargins(6, 4, 6, 4)
            h.setSpacing(8)

            result = g["result"] or "DRAW"
            color = RESULT_COLORS.get(result, "#95a5a6")
            res_lbl = QLabel(result)
            res_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; border: none; background: transparent;")
            res_lbl.setFixedWidth(40)
            h.addWidget(res_lbl)

            bot = g["bot_name"] or "Unknown"
            rating = f" ({g['bot_rating']})" if g["bot_rating"] else ""
            bot_lbl = QLabel(f"{bot}{rating}")
            bot_lbl.setStyleSheet("font-size: 12px; border: none; background: transparent;")
            h.addWidget(bot_lbl)
            h.addStretch()

            adv = f"+{g['max_advantage']}cp" if g["max_advantage"] is not None else "—"
            ev = f"{g['min_eval']}cp" if g["min_eval"] is not None else "—"
            stats_lbl = QLabel(f"max {adv}  min {ev}")
            stats_lbl.setStyleSheet("font-size: 11px; color: #666; border: none; background: transparent;")
            h.addWidget(stats_lbl)

            date = (g["date_played"] or "")[:10]
            date_lbl = QLabel(date)
            date_lbl.setStyleSheet("font-size: 11px; color: #888; border: none; background: transparent;")
            h.addWidget(date_lbl)

            # Playstyle tag
            ps = g["playstyle"] if "playstyle" in g.keys() and g["playstyle"] else "?"
            ps_btn = QPushButton(ps)
            ps_btn.setFixedSize(80, 24)
            ps_btn.setToolTip("Set playstyle")
            ps_btn.setStyleSheet("font-size: 10px; padding: 0; border-radius: 3px; background-color: #b0c8e8; color: #1a1a2e;")
            game_id = g["id"]
            bot_name = g["bot_name"] or ""
            ps_btn.clicked.connect(lambda _, gid=game_id, bn=bot_name: self._set_playstyle(gid, bn))
            h.addWidget(ps_btn)

            graph_btn = QPushButton("📈")
            graph_btn.setFixedSize(28, 24)
            graph_btn.setToolTip("View Evaluation Graph")
            graph_btn.setStyleSheet("font-size: 13px; padding: 0; border-radius: 3px;")
            graph_btn.clicked.connect(lambda _, gid=game_id: self._show_graph(gid))
            h.addWidget(graph_btn)

            self.layout.addWidget(row)


# ---------------------------------------------------------------------------
# Position Detail Panel
# ---------------------------------------------------------------------------

class PositionDetailPanel(QWidget):
    def __init__(self, db_path_fn, settings_fn, refresh_tree_fn, parent=None):
        super().__init__(parent)
        self._get_db_path = db_path_fn
        self._get_settings = settings_fn
        self._refresh_tree = refresh_tree_fn
        self._current_pos_id = None
        self._current_fen = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.placeholder = QLabel("Select a position from the list to view details.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.placeholder)

        self.detail_widget = QWidget()
        self.detail_widget.setVisible(False)
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setSpacing(10)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        # Editable title
        self.title_edit = QLineEdit()
        self.title_edit.setStyleSheet(
            "font-size: 17px; font-weight: bold; border: none; "
            "border-bottom: 2px solid #3a7bd5; border-radius: 0; padding: 2px 0;"
        )
        self.title_edit.setPlaceholderText("Position title…")
        self.title_edit.editingFinished.connect(self._on_title_saved)
        detail_layout.addWidget(self.title_edit)

        # Board SVG
        self.board_widget = QSvgWidget()
        self.board_widget.setFixedSize(280, 280)
        detail_layout.addWidget(self.board_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        # FEN
        fen_group = QGroupBox("FEN")
        fen_l = QVBoxLayout(fen_group)
        self.fen_label = QLabel()
        self.fen_label.setWordWrap(True)
        self.fen_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.fen_label.setStyleSheet("font-size: 11px; color: #555;")
        fen_l.addWidget(self.fen_label)
        detail_layout.addWidget(fen_group)

        # Ideas
        ideas_group = QGroupBox("Key Ideas")
        ideas_l = QVBoxLayout(ideas_group)
        self.ideas_edit = QTextEdit()
        self.ideas_edit.setFixedHeight(90)
        self.ideas_edit.setPlaceholderText("e.g. exploit weak d5 square…")
        self.ideas_edit.focusOutEvent = self._ideas_focus_out
        ideas_l.addWidget(self.ideas_edit)
        detail_layout.addWidget(ideas_group)

        # Date
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #888; font-size: 11px;")
        detail_layout.addWidget(self.date_label)

        # Action bar
        action_bar = QHBoxLayout()
        self.play_btn = QPushButton("▶  Play on Chessiverse")
        self.play_btn.setFixedHeight(34)
        self.play_btn.clicked.connect(self._on_play)
        action_bar.addWidget(self.play_btn)

        self.import_pgn_btn = QPushButton("⬇  Import PGN")
        self.import_pgn_btn.setFixedHeight(34)
        self.import_pgn_btn.clicked.connect(self._on_import_pgn)
        action_bar.addWidget(self.import_pgn_btn)
        action_bar.addStretch()
        detail_layout.addLayout(action_bar)

        # Stats bar
        stats_group = QGroupBox("Overall Stats")
        stats_l = QVBoxLayout(stats_group)
        self.stats_bar = StatsBarWidget()
        stats_l.addWidget(self.stats_bar)
        detail_layout.addWidget(stats_group)

        # Tier stats
        tier_group = QGroupBox("Stats by Rating Tier")
        tier_l = QVBoxLayout(tier_group)
        self.tier_stats = TierStatsWidget()
        tier_l.addWidget(self.tier_stats)
        detail_layout.addWidget(tier_group)

        # Playstyle stats
        playstyle_group = QGroupBox("Stats by Playstyle")
        playstyle_l = QVBoxLayout(playstyle_group)
        self.playstyle_stats = PlaystyleStatsWidget()
        playstyle_l.addWidget(self.playstyle_stats)
        detail_layout.addWidget(playstyle_group)

        # Game history
        games_group = QGroupBox("Games")
        games_l = QVBoxLayout(games_group)
        self.game_history = GameHistoryWidget()
        self.game_history.set_providers(db_path_fn, settings_fn)
        self.game_history.set_reload_fn(self._reload_games)
        games_l.addWidget(self.game_history)
        detail_layout.addWidget(games_group)

        detail_layout.addStretch()
        layout.addWidget(self.detail_widget)
        layout.addStretch()

    def show_position(self, row):
        self.placeholder.setVisible(False)
        self.detail_widget.setVisible(True)
        self._current_pos_id = row["id"]
        self._current_fen = row["fen"]

        self.title_edit.setText(row["title"] or "")
        self.fen_label.setText(row["fen"])
        self.ideas_edit.blockSignals(True)
        self.ideas_edit.setPlainText(row["ideas"] or "")
        self.ideas_edit.blockSignals(False)
        self.date_label.setText(f"Added: {row['date_added']}")

        svg_bytes = render_board_svg(row["fen"], size=280)
        if svg_bytes:
            self.board_widget.load(QByteArray(svg_bytes))
            self.board_widget.setVisible(True)
        else:
            self.board_widget.setVisible(False)

        self._reload_games()

    def _reload_games(self):
        if self._current_pos_id is None:
            return
        db_path = self._get_db_path()
        s = self._get_settings()
        games = db_get_games(db_path, self._current_pos_id)
        self.game_history.load_games(games)
        stats = db_get_stats(db_path, self._current_pos_id,
                             s.get("upper_threshold_cp", 500),
                             s.get("lower_threshold_cp", -200))
        self.stats_bar.update_stats(stats)
        playstyle_data = db_get_playstyle_stats(db_path, self._current_pos_id)
        self.playstyle_stats.update_stats(playstyle_data, n_form=s.get("form_games_shown", 5))
        tier_data = db_get_tier_stats(
            db_path, self._current_pos_id,
            s.get("player_rating", 1500),
            s.get("upper_threshold_cp", 500),
            s.get("lower_threshold_cp", -200),
            tier_upper_cutoff=s.get("tier_upper_cutoff", 400),
            tier_lower_cutoff=s.get("tier_lower_cutoff", 400),
        )
        self.tier_stats.update_tiers(tier_data)

    def _on_title_saved(self):
        if self._current_pos_id is None:
            return
        new_title = self.title_edit.text().strip()
        if not new_title:
            return
        db_update_position_title(self._get_db_path(), self._current_pos_id, new_title)
        self._refresh_tree()

    def _ideas_focus_out(self, event):
        QTextEdit.focusOutEvent(self.ideas_edit, event)
        if self._current_pos_id is None:
            return
        db_update_position_ideas(self._get_db_path(), self._current_pos_id,
                                 self.ideas_edit.toPlainText().strip())

    def _on_play(self):
        if not self._current_fen:
            return
        url = build_chessiverse_url(self._current_fen)
        if url:
            open_in_chrome(url)
        else:
            QMessageBox.warning(self, "Error", "Could not build Chessiverse URL.")

    def _on_import_pgn(self):
        if not self._current_pos_id or not self._current_fen:
            return
        dlg = ImportPgnDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        pgn_text = dlg.get_pgn()
        if not pgn_text:
            QMessageBox.warning(self, "Import PGN", "No PGN entered.")
            return

        s = self._get_settings()
        mode = s.get("engine_mode", "depth")
        depth = s["engine_depth"] if mode == "depth" else None
        time_sec = s["engine_time_sec"] if mode == "time" else None

        # Run analysis in background thread
        self._worker = AnalysisWorker(
            pgn_text, self._current_fen,
            s["engine_path"], depth, time_sec,
            s["upper_threshold_cp"], s["lower_threshold_cp"],
            username=s.get("player_username", "dab327")
        )
        self._progress_dlg = AnalysisProgressDialog(parent=self)
        self._progress_dlg.rejected.connect(self._worker.cancel)

        self._worker.progress.connect(self._progress_dlg.set_progress)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.finished.connect(self._progress_dlg.accept)
        self._worker.error.connect(self._progress_dlg.reject)

        self._worker.start()
        self._progress_dlg.exec()

    def _on_analysis_done(self, result):
        s = self._get_settings()
        if result.get("player_rating"):
            s["player_rating"] = result["player_rating"]
            save_settings(s)

        playstyle = lookup_bot_playstyle(result.get("bot_name", ""))

        game_id = db_add_game(
            self._get_db_path(), self._current_pos_id,
            result["pgn"], result["bot_name"], result["bot_rating"],
            result["result"], result["max_advantage"], result["min_eval"],
            player_rating=result.get("player_rating"),
            playstyle=playstyle
        )
        if result.get("evals"):
            db_save_evals(self._get_db_path(), game_id, result["evals"])
        self._reload_games()
        self._refresh_tree()

        graph = EvalGraphWindow(
            result.get("evals", []),
            s.get("upper_threshold_cp", 500),
            s.get("lower_threshold_cp", -200),
            result["result"],
            parent=self
        )
        graph.exec()

    def _on_analysis_error(self, msg):
        QMessageBox.critical(self, "Analysis Error", msg)

    def clear(self):
        self._current_pos_id = None
        self._current_fen = None
        self.placeholder.setVisible(True)
        self.detail_widget.setVisible(False)
        self.stats_bar.clear()
        self.tier_stats.clear()
        self.playstyle_stats.clear()


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        init_db(self.settings["db_path"])

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(1100, 700)

        self._apply_theme()
        self._build_menu()
        self._build_ui()
        self._refresh_tree()
        self._restore_window_state()

    def _apply_theme(self):
        self.setStyleSheet(get_stylesheet(self.settings.get("theme", "light")))

    def _build_menu(self):
        from PyQt6.QtGui import QKeySequence
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        add_action = file_menu.addAction("New Position…")
        add_action.setShortcut(QKeySequence("Ctrl+N"))
        add_action.triggered.connect(self.open_add_position)

        file_menu.addSeparator()

        export_action = file_menu.addAction("Export Data…")
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_data)

        import_action = file_menu.addAction("Import Data…")
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_data)

        file_menu.addSeparator()

        settings_action = file_menu.addAction("Settings…")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)

        view_menu = menubar.addMenu("&View")

        self.theme_action = view_menu.addAction("Switch to Dark Theme")
        self.theme_action.setShortcut(QKeySequence("Ctrl+D"))
        self.theme_action.triggered.connect(self._toggle_theme)
        self._update_theme_action_label()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 6, 10)
        left_layout.setSpacing(8)

        header = QLabel("Positions")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        left_layout.addWidget(header)

        btn_row = QHBoxLayout()
        self.new_btn = QPushButton("New  ▾")
        self.new_btn.setFixedWidth(90)
        self.new_btn.clicked.connect(self._show_new_menu)
        btn_row.addWidget(self.new_btn)
        btn_row.addStretch()
        left_layout.addLayout(btn_row)

        self.tree = PositionTree(left)
        left_layout.addWidget(self.tree)
        self.tree.currentItemChanged.connect(self._on_item_selected)

        splitter.addWidget(left)

        self.detail_panel = PositionDetailPanel(
            db_path_fn=lambda: self.settings["db_path"],
            settings_fn=lambda: self.settings,
            refresh_tree_fn=self._refresh_tree,
            parent=self,
        )
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        sp = self.settings.get("splitter_pos", 320)
        splitter.setSizes([sp, max(100, 1100 - sp)])
        self.splitter = splitter
        self.setCentralWidget(splitter)

    def _refresh_tree(self):
        # Remember current selection
        current = self.tree.currentItem()
        current_pos_id = current.data(0, ROLE_POS_ID) if (current and current.type() == POSITION_ITEM_TYPE) else None

        self.tree.blockSignals(True)
        self.tree.clear()
        db_path = self.settings["db_path"]
        n = self.settings.get("form_games_shown", 5)

        for row in db_get_positions(db_path, folder_id=None):
            self._make_position_item(row, parent=self.tree, n=n)

        for folder in db_get_folders(db_path, parent_id=None):
            self._make_folder_item(folder, parent=self.tree, db_path=db_path, n=n)

        self.tree.blockSignals(False)

        # Restore selection if possible
        if current_pos_id:
            self._reselect_position(current_pos_id)

    def _reselect_position(self, pos_id):
        def _search(parent_item):
            count = parent_item.childCount() if parent_item else self.tree.topLevelItemCount()
            for i in range(count):
                item = parent_item.child(i) if parent_item else self.tree.topLevelItem(i)
                if item.type() == POSITION_ITEM_TYPE and item.data(0, ROLE_POS_ID) == pos_id:
                    self.tree.blockSignals(True)
                    self.tree.setCurrentItem(item)
                    self.tree.blockSignals(False)
                    return True
                if _search(item):
                    return True
            return False
        _search(None)

    def _make_folder_item(self, folder, parent, db_path, n):
        item = QTreeWidgetItem(parent, type=FOLDER_ITEM_TYPE)
        item.setText(0, f"📁  {folder['name']}")
        item.setData(0, ROLE_FOLDER_ID, folder["id"])
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        )
        item.setExpanded(True)
        for row in db_get_positions(db_path, folder_id=folder["id"]):
            self._make_position_item(row, parent=item, n=n)
        for subfolder in db_get_folders(db_path, parent_id=folder["id"]):
            self._make_folder_item(subfolder, parent=item, db_path=db_path, n=n)
        return item

    def _make_position_item(self, row, parent, n=5):
        item = QTreeWidgetItem(parent, type=POSITION_ITEM_TYPE)
        side = fen_side(row["fen"])
        title = row["title"] or "(untitled)"
        form = db_get_form(self.settings["db_path"], row["id"], n)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        h = QHBoxLayout(container)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(6)

        h.addWidget(make_side_indicator(side))

        lbl = QLabel(title)
        lbl.setObjectName(f"pos_label_{row['id']}")
        lbl.setStyleSheet("background: transparent;")
        h.addWidget(lbl)

        h.addStretch()

        # Form circles
        for result in form:
            circle = FormCircle(result)
            h.addWidget(circle)

        item.setData(0, ROLE_POS_ID, row["id"])
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsDragEnabled
        )
        item.setSizeHint(0, QSize(260, 32))
        self.tree.setItemWidget(item, 0, container)
        return item

    def _on_item_selected(self, current, previous):
        if current is None or current.type() != POSITION_ITEM_TYPE:
            self.detail_panel.clear()
            return
        pos_id = current.data(0, ROLE_POS_ID)
        row = db_get_position(self.settings["db_path"], pos_id)
        if row:
            self.detail_panel.show_position(row)

    def add_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name.strip():
            db_add_folder(self.settings["db_path"], name.strip())
            self._refresh_tree()

    def rename_folder(self, folder_item):
        folder_id = folder_item.data(0, ROLE_FOLDER_ID)
        old_name = folder_item.text(0).replace("📁  ", "")
        name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=old_name)
        if ok and name.strip() and name.strip() != old_name:
            db_rename_folder(self.settings["db_path"], folder_id, name.strip())
            self._refresh_tree()

    def delete_folder(self, folder_item):
        folder_id = folder_item.data(0, ROLE_FOLDER_ID)
        name = folder_item.text(0).replace("📁  ", "")
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Delete \"{name}\" and all subfolders? Positions will move to the top level.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db_delete_folder(self.settings["db_path"], folder_id)
            self._refresh_tree()

    def move_position_to_folder(self, position_id, folder_id):
        db_move_position_to_folder(self.settings["db_path"], position_id, folder_id)
        self._refresh_tree()

    def move_folder_to_parent(self, folder_id, parent_id):
        db_move_folder_to_parent(self.settings["db_path"], folder_id, parent_id)
        self._refresh_tree()

    def _show_new_menu(self):
        menu = QMenu(self)
        menu.addAction("Position").triggered.connect(self.open_add_position)
        menu.addAction("Folder").triggered.connect(self.add_folder)
        btn = self.new_btn
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _restore_window_state(self):
        x = self.settings.get("window_x", 100)
        y = self.settings.get("window_y", 100)
        w = self.settings.get("window_w", 1200)
        h = self.settings.get("window_h", 750)
        self.setGeometry(x, y, w, h)

    def _save_window_state(self):
        geo = self.geometry()
        self.settings["window_x"] = geo.x()
        self.settings["window_y"] = geo.y()
        self.settings["window_w"] = geo.width()
        self.settings["window_h"] = geo.height()
        sizes = self.splitter.sizes()
        if sizes:
            self.settings["splitter_pos"] = sizes[0]
        save_settings(self.settings)

    def closeEvent(self, event):
        self._save_window_state()
        event.accept()

    def _toggle_theme(self):
        current = self.settings.get("theme", "light")
        self.settings["theme"] = "dark" if current == "light" else "light"
        save_settings(self.settings)
        self._apply_theme()
        self._update_theme_action_label()

    def _update_theme_action_label(self):
        current = self.settings.get("theme", "light")
        self.theme_action.setText(
            "Switch to Light Theme" if current == "dark" else "Switch to Dark Theme"
        )

    def edit_position(self, item):
        pos_id = item.data(0, ROLE_POS_ID)
        row = db_get_position(self.settings["db_path"], pos_id)
        if not row:
            return
        dlg = AddPositionDialog(
            parent=self,
            prefill={"title": row["title"], "fen": row["fen"], "ideas": row["ideas"] or ""}
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db_update_position(self.settings["db_path"], pos_id,
                               data["title"], data["fen"], data["ideas"])
            self._refresh_tree()
            # Refresh detail panel if this position is selected
            if self.tree.currentItem() == item:
                updated = db_get_position(self.settings["db_path"], pos_id)
                if updated:
                    self.detail_panel.show_position(updated)

    def delete_position(self, item):
        pos_id = item.data(0, ROLE_POS_ID)
        row = db_get_position(self.settings["db_path"], pos_id)
        if not row:
            return
        reply = QMessageBox.question(
            self, "Delete Position",
            "Delete '" + row['title'] + "' and all its games? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db_delete_position(self.settings["db_path"], pos_id)
            self.detail_panel.clear()
            self._refresh_tree()

    def play_selected_position(self):
        item = self.tree.currentItem()
        if not item or item.type() != POSITION_ITEM_TYPE:
            return
        pos_id = item.data(0, ROLE_POS_ID)
        row = db_get_position(self.settings["db_path"], pos_id)
        if row:
            url = build_chessiverse_url(row["fen"])
            if url:
                open_in_chrome(url)

    def export_data(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "grinder_export.grinder",
            "GRINDER Files (*.grinder)"
        )
        if not path:
            return
        try:
            data = db_export(self.settings["db_path"])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            QMessageBox.information(self, "Export", f"Data exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def import_data(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "GRINDER Files (*.grinder)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "Import Data",
            "This will replace ALL existing positions and games. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            db_import(self.settings["db_path"], data)
            self.detail_panel.clear()
            self._refresh_tree()
            QMessageBox.information(self, "Import", "Data imported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def open_add_position(self):
        dlg = AddPositionDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db_add_position(
                self.settings["db_path"],
                data["title"], data["fen"],
                data["ideas"], data["strategies"],
            )
            self._refresh_tree()

    def open_settings(self):
        dlg = SettingsDialog(self.settings, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_settings = dlg.get_settings()
            save_settings(new_settings)
            self.settings = new_settings
            self._apply_theme()
            self._refresh_tree()
            QMessageBox.information(self, "Settings", "Settings saved.")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
