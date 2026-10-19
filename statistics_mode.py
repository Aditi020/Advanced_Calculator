"""Statistics panel — the ONE mode that needs more than a keypad.

A calculator display holds one expression. A dataset holds many numbers,
persistently. That's the only reason this file exists. It provides exactly
two widgets: a dataset entry box and a results strip. Stage 3 will fill it in.
"""
import customtkinter as ctk
import theme


def build_stats_strip(parent) -> dict:
    """Return the widgets so the caller can read/write later."""
    frame = ctk.CTkFrame(parent, fg_color=theme.BG2, corner_radius=theme.RADIUS)
    ctk.CTkLabel(frame, text="Dataset (comma-separated):",
                 font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED,
                 anchor="w").pack(fill="x", padx=10, pady=(6, 0))
    entry = ctk.CTkEntry(frame, font=theme.FONT_KEY,
                         fg_color=theme.BG1, text_color=theme.TEXT)
    entry.pack(fill="x", padx=8, pady=6)
    results = ctk.CTkLabel(frame, text="—", font=theme.FONT_HISTORY,
                           text_color=theme.TEXT, anchor="w", justify="left")
    results.pack(fill="x", padx=10, pady=(0, 8))
    return {"frame": frame, "entry": entry, "results": results}