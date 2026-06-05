from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.viz import (ACCENTS, CARD_DPI, CARD_IN, CARD_PX, PALETTE,
                        save_animation, use_headless_if_saving)

# ---- tunables -------------------------------------------------------------
N_CATS = 5             # how many cats line up / pile up
HOLD_PER_STEP = 7      # frames each push/pop is held on screen
END_HOLD = 22          # frames to hold the final state before looping

# slot geometry, in axes coords (0..1) inside each panel
SLOT_X0 = 0.15
SLOT_DX = 0.165
LANE_Y = 0.52
OUT_Y = 0.13
BOX_W, BOX_H = 0.135, 0.30
OUT_W, OUT_H = 0.10, 0.18


def build_snapshots(n):
    """Push n cats into a queue and a stack, then drain both.

    A queue serves the front (first in, first out); a stack serves the top
    (last in, first out). Same cats in, opposite order out: that single
    difference is why BFS (a queue) fans out in rings and DFS (a stack) dives.
    """
    q, qo, s, so = [], [], [], []
    snaps = [dict(q=[], qo=[], s=[], so=[], note="empty")]
    for k in range(1, n + 1):
        q.append(k)
        s.append(k)
        snaps.append(dict(q=q[:], qo=qo[:], s=s[:], so=so[:],
                          note=f"cat {k} arrives"))
    for _ in range(n):
        qo.append(q.pop(0))      # queue: leave from the front
        so.append(s.pop())       # stack: leave from the top
        snaps.append(dict(q=q[:], qo=qo[:], s=s[:], so=so[:], note="next!"))
    return snaps


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", metavar="OUT.mp4")
    args = ap.parse_args()
    use_headless_if_saving(args.save)

    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.offsetbox import AnnotationBbox, OffsetImage
    from matplotlib.patches import FancyBboxPatch, Polygon
    from PIL import Image

    colors = [ACCENTS[(k - 1) % len(ACCENTS)] for k in range(1, N_CATS + 1)]
    ink = hex_to_rgb(PALETTE["ink"])
    dark = PALETTE["bg"]
    snaps = build_snapshots(N_CATS)

    # the queue's cats are a looping gif rather than flat colour blocks
    gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "giphy.webp")
    gif = Image.open(gif_path)
    cat_frames = []
    for fi in range(getattr(gif, "n_frames", 1)):
        gif.seek(fi)
        cat_frames.append(np.asarray(gif.convert("RGBA")) / 255.0)

    fig, (axq, axs) = plt.subplots(2, 1, figsize=(CARD_IN, CARD_IN),
                                   dpi=CARD_DPI)
    fig.patch.set_facecolor(PALETTE["bg"])
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0)

    def slot_x(i):
        return SLOT_X0 + i * SLOT_DX

    def box(ax, cx, cy, w, h, label, color):
        patch = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                               boxstyle="round,pad=0.0,rounding_size=0.03",
                               linewidth=0, facecolor=color, zorder=2)
        ax.add_patch(patch)
        ax.text(cx, cy, str(label), ha="center", va="center", color=dark,
                fontsize=12, fontweight="bold", zorder=3,
                family="monospace")

    def next_marker(ax, cx):
        tri = Polygon([(cx - 0.035, LANE_Y - 0.24), (cx + 0.035, LANE_Y - 0.24),
                       (cx, LANE_Y - 0.16)], closed=True,
                      facecolor=PALETTE["hot"], linewidth=0, zorder=4)
        ax.add_patch(tri)

    def cat_image(ax, cx, cy, h, label, gframe):
        img = cat_frames[gframe % len(cat_frames)]
        zoom = h * (CARD_PX / 2) / img.shape[0]
        ab = AnnotationBbox(OffsetImage(img, zoom=zoom), (cx, cy),
                            frameon=False, pad=0, zorder=2)
        ax.add_artist(ab)
        ax.text(cx, cy + h * 0.34, str(label), ha="center", va="center",
                color=PALETTE["ink"], fontsize=10, fontweight="bold",
                family="monospace", zorder=3,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=dark)])

    def draw_panel(ax, contents, out, title, sub, exit_at,
                   use_img=False, gframe=0):
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_facecolor(PALETTE["bg"])
        ax.text(0.04, 0.90, title, ha="left", va="center", color=ink,
                fontsize=12, fontweight="bold", family="monospace")
        ax.text(0.04, 0.78, sub, ha="left", va="center",
                color=PALETTE["cyan"], fontsize=8.5, alpha=0.85,
                family="monospace")
        for i, cat in enumerate(contents):
            if use_img:
                cat_image(ax, slot_x(i), LANE_Y, BOX_H, cat, gframe)
            else:
                box(ax, slot_x(i), LANE_Y, BOX_W, BOX_H, cat, colors[cat - 1])
        if contents:
            idx = 0 if exit_at == "front" else len(contents) - 1
            next_marker(ax, slot_x(idx))
        if out:
            ax.text(0.04, OUT_Y, "out", ha="left", va="center", color=ink,
                    fontsize=8, alpha=0.7, family="monospace")
            for j, cat in enumerate(out):
                if use_img:
                    cat_image(ax, slot_x(j) + 0.06, OUT_Y, OUT_H, cat, gframe)
                else:
                    box(ax, slot_x(j) + 0.06, OUT_Y, OUT_W, OUT_H, cat,
                        colors[cat - 1])

    n_frames = len(snaps) * HOLD_PER_STEP + END_HOLD

    def render(frame):
        idx = min(frame // HOLD_PER_STEP, len(snaps) - 1)
        snap = snaps[idx]
        draw_panel(axq, snap["q"], snap["qo"],
                   "QUEUE  cats in a line",
                   "first in, first out  ·  BFS", "front",
                   use_img=True, gframe=frame)
        draw_panel(axs, snap["s"], snap["so"],
                   "STACK  cats in a pile",
                   "last in, first out  ·  DFS", "top",
                   use_img=True, gframe=frame)
        return []

    anim = FuncAnimation(fig, render, frames=n_frames, interval=60,
                         blit=False)

    if args.save:
        save_animation(anim, args.save, fps=18)
    else:
        plt.show()


if __name__ == "__main__":
    main()
