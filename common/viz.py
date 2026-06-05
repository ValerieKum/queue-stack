from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Palette — matches the site's warm pink/orange theme on a near-black ground.
# ---------------------------------------------------------------------------
PALETTE = {
    "bg":      "#0d0a12",   # near-black, slight violet (matches site)
    "ink":     "#f3e9e0",   # warm off-white for sparse text
    "grid":    "#241b2e",   # faint grid / dead cells
    "pink":    "#ff5d8f",   # primary accent
    "orange":  "#ff9e57",   # secondary accent
    "hot":     "#ffd166",   # highlight / "found it" yellow
    "cool":    "#7c5cff",   # cool violet for contrast / frontier
    "cyan":    "#56d4dd",   # second cool accent
}

# A short cyclic list of accent colors for multi-agent / multi-series demos.
ACCENTS = [PALETTE["pink"], PALETTE["orange"], PALETTE["cool"],
           PALETTE["cyan"], PALETTE["hot"]]

# Card render target: small + square so it sits inside a project card.
CARD_PX = 480            # output GIF is CARD_PX x CARD_PX pixels
CARD_DPI = 100
CARD_IN = CARD_PX / CARD_DPI


def card_figure(facecolor: str | None = None):
    """A square, chrome-free figure sized for a project card.

    Returns (fig, ax) with no margins, no spines, no ticks — just the visual,
    edge to edge, on the dark theme background.
    """
    fig, ax = plt.subplots(figsize=(CARD_IN, CARD_IN), dpi=CARD_DPI)
    fig.patch.set_facecolor(facecolor or PALETTE["bg"])
    ax.set_facecolor(facecolor or PALETTE["bg"])
    _strip(ax)
    # Fill the whole figure — no wasted padding in a tiny card.
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax


def _strip(ax):
    """Remove ticks, labels and spines from an axis (chrome-free)."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.margins(0)


# Public alias so demos can strip their secondary axes too.
strip_axes = _strip


def caption(ax, text: str):
    """Tiny lower-left label so a standalone GIF is self-explanatory.

    Returns the Text artist so animated demos can update it each frame.
    """
    return ax.text(0.035, 0.04, text, transform=ax.transAxes,
                   color=PALETTE["ink"], fontsize=9, alpha=0.85,
                   ha="left", va="bottom", family="monospace")


def save_animation(anim, path: str, fps: int = 30):
    """Export a Matplotlib animation as a looping GIF (or mp4 by extension)."""
    if path.lower().endswith(".gif"):
        from matplotlib.animation import PillowWriter
        anim.save(path, writer=PillowWriter(fps=fps))
    else:
        anim.save(path, fps=fps, dpi=CARD_DPI)
    print(f"saved -> {path}")


def use_headless_if_saving(save_path: str | None):
    """Switch Matplotlib to the non-interactive Agg backend when exporting,
    so demos can render a GIF on a machine with no display."""
    if save_path:
        matplotlib.use("Agg")
