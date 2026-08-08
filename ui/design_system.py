"""
Centralized Design System for K Dynamics / RN Scanner Business Management System.
Light professional theme — safe for dark logos on white backgrounds.
"""

# ── Color Palette ──────────────────────────────────────────────────────────────
LIGHT_COLORS = {
    "bg_app":          "#F0F4FA",   
    "bg_card":         "#FFFFFF",   
    "bg_input":        "#F5F8FF",   
    "bg_input_focus":  "#FFFFFF",
    "primary":         "#1D4ED8",   
    "primary_hover":   "#1E40AF",
    "primary_pressed": "#1E3A8A",
    "success":         "#15803D",
    "success_hover":   "#166534",
    "danger":          "#EF4444",
    "text_primary":    "#111827",   
    "text_secondary":  "#374151",
    "text_muted":      "#6B7280",
    "text_on_primary": "#FFFFFF",
    "border":          "#D1D5DB",
    "border_focus":    "#1D4ED8",
    "border_card":     "#E5E7EB",
    "divider":         "#E5E7EB",
    "link":            "#1D4ED8",
    "link_hover":      "#1E40AF",
}

DARK_COLORS = {
    "bg_app":          "#0F172A",   # Very dark slate
    "bg_card":         "#1E293B",   # Dark slate card
    "bg_input":        "#334155",   # Input background
    "bg_input_focus":  "#475569",
    "primary":         "#3B82F6",   # Lighter blue for dark mode
    "primary_hover":   "#60A5FA",
    "primary_pressed": "#2563EB",
    "success":         "#22C55E",
    "success_hover":   "#4ADE80",
    "danger":          "#F87171",
    "text_primary":    "#F8FAFC",   # Near-white
    "text_secondary":  "#CBD5E1",
    "text_muted":      "#94A3B8",
    "text_on_primary": "#FFFFFF",
    "border":          "#475569",
    "border_focus":    "#3B82F6",
    "border_card":     "#334155",
    "divider":         "#334155",
    "link":            "#60A5FA",
    "link_hover":      "#93C5FD",
}

COLORS = {}
COLORS.update(LIGHT_COLORS) # Default

import json
from pathlib import Path
from config.settings import BASE_DIR

def get_theme_preference() -> str:
    path = BASE_DIR / "theme.json"
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f).get("theme", "light")
        except Exception:
            pass
    return "light"

def set_theme_preference(theme: str):
    path = BASE_DIR / "theme.json"
    try:
        with open(path, "w") as f:
            json.dump({"theme": theme}, f)
    except Exception:
        pass

def init_theme():
    theme = get_theme_preference()
    COLORS.clear()
    if theme == "dark":
        COLORS.update(DARK_COLORS)
    else:
        COLORS.update(LIGHT_COLORS)

# Initialize immediately when this module is imported
init_theme()

FONT = "'Segoe UI', Arial, sans-serif"

# ── Shared QSS blocks (Functions to evaluate after init_theme) ──────────────────────
def get_auth_stylesheet() -> str:
    _BASE = f"""
        QWidget {{
            font-family: {FONT};
            font-size: 13px;
            color: {COLORS['text_primary']};
            background-color: {COLORS['bg_app']};
        }}
    """

    _CARD = f"""
        QFrame#card {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border_card']};
            border-radius: 14px;
        }}
    """

    _LABEL = f"""
        QLabel {{ background: transparent; }}
    """

    _INPUT = f"""
        QLineEdit {{
            background-color: {COLORS['bg_input']};
            border: 1.5px solid {COLORS['border']};
            border-radius: 8px;
            padding: 9px 13px;
            font-size: 13px;
            color: {COLORS['text_primary']};
        }}
        QLineEdit:focus {{
            border: 1.5px solid {COLORS['border_focus']};
            background-color: {COLORS['bg_input_focus']};
        }}
    """

    _BTN_PRIMARY = f"""
        QPushButton#primary_btn {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_on_primary']};
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton#primary_btn:hover  {{ background-color: {COLORS['primary_hover']}; }}
        QPushButton#primary_btn:pressed {{ background-color: {COLORS['primary_pressed']}; }}
    """

    _BTN_SUCCESS = f"""
        QPushButton#success_btn {{
            background-color: {COLORS['success']};
            color: {COLORS['text_on_primary']};
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton#success_btn:hover  {{ background-color: {COLORS['success_hover']}; }}
    """

    _BTN_LINK = f"""
        QPushButton#link_btn {{
            background-color: transparent;
            color: {COLORS['link']};
            border: none;
            font-size: 12px;
            font-weight: 500;
            padding: 2px 4px;
        }}
        QPushButton#link_btn:hover {{ color: {COLORS['link_hover']}; }}
    """

    _BTN_OUTLINE = f"""
        QPushButton#outline_btn {{
            background-color: transparent;
            color: {COLORS['primary']};
            border: 1.5px solid {COLORS['primary']};
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton#outline_btn:hover {{
            background-color: {COLORS['primary']};
            color: #FFFFFF;
        }}
    """
    return _BASE + _CARD + _LABEL + _INPUT + _BTN_PRIMARY + _BTN_SUCCESS + _BTN_LINK + _BTN_OUTLINE
