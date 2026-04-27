# -*- coding: utf-8 -*-
"""
Stylesheet generator — aggregates section generators into a complete QSS stylesheet.

All theme color values pass through directly to QSS:
- Hex colors (#RRGGBB) → used as-is for opaque backgrounds/text
- rgba(r,g,b,a) → used as-is for glass transparency
- Gradient values already wrapped in qlineargradient() by section templates
"""
from typing import Dict

from .sections.dock import generate_dock_stylesheet
from .sections.sidebar import generate_sidebar_stylesheet
from .sections.content import generate_content_stylesheet
from .sections.cards import generate_cards_stylesheet
from .sections.inputs import generate_inputs_stylesheet
from .sections.buttons import generate_buttons_stylesheet
from .sections.tables import generate_tables_stylesheet
from .sections.tabs import generate_tabs_stylesheet
from .sections.scrollbars import generate_scrollbars_stylesheet
from .sections.misc import generate_misc_stylesheet
from .sections.pages import generate_pages_stylesheet


def generate_stylesheet(theme: Dict[str, str]) -> str:
    """Generate a complete QSS stylesheet from a theme dictionary."""
    return "\n".join([
        generate_dock_stylesheet(theme),
        generate_sidebar_stylesheet(theme),
        generate_content_stylesheet(theme),
        generate_cards_stylesheet(theme),
        generate_inputs_stylesheet(theme),
        generate_buttons_stylesheet(theme),
        generate_tables_stylesheet(theme),
        generate_tabs_stylesheet(theme),
        generate_scrollbars_stylesheet(theme),
        generate_misc_stylesheet(theme),
        generate_pages_stylesheet(theme),
    ])
