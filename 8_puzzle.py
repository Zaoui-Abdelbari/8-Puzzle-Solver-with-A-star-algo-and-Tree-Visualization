"""
8-Puzzle Solver — Modern UI Redesign v2
A* Search with Manhattan Distance Heuristic

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  HEADER  (title + subtitle + dark mode toggle)          │
  ├──────────────┬──────────────────┬───────────────────────┤
  │  LEFT PANEL  │  CENTER PANEL    │  RIGHT PANEL          │
  │  · Input     │  · Solution View │  · Tree Canvas        │
  │  · Presets   │  · Navigation    │  · Zoom/Pan           │
  │  · Settings  │  · Statistics    │  · Legend             │
  │  · Actions   │                  │                       │
  ├──────────────┴──────────────────┴───────────────────────┤
  │  STATUS BAR                                             │
  └─────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, messagebox
import heapq
from itertools import count
import threading

# ═══════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════

C = {
    # Backgrounds
    "app":          "#EEF2F7",
    "panel":        "#FFFFFF",
    "header":       "#1C2B4A",
    "canvas_bg":    "#F5F8FC",
    "section_hdr":  "#F0F4FA",
    "tile":         "#FFFFFF",
    "tile_empty":   "#E2EAF4",
    "tile_moved":   "#FFF3CD",

    # Borders
    "border":       "#D4DCE8",
    "focus":        "#3B82F6",

    # Text
    "t_primary":    "#1C2B4A",
    "t_secondary":  "#5A6E8A",
    "t_muted":      "#8FA0B4",
    "t_white":      "#FFFFFF",
    "t_head_sub":   "#8FA0B4",

    # Buttons
    "btn_solve":    "#2563EB",
    "btn_refresh":  "#F1F5F9",
    "btn_nav":      "#F1F5F9",
    "btn_play":     "#16A34A",
    "btn_pause":    "#DC2626",

    # Presets
    "easy_bg":      "#DCFCE7",  "easy_fg":   "#166534",
    "med_bg":       "#FEF9C3",  "med_fg":    "#854D0E",
    "hard_bg":      "#FEE2E2",  "hard_fg":   "#991B1B",

    # Tree nodes
    "n_unexp_f":    "#FFF7ED",  "n_unexp_o": "#F97316",
    "n_exp_f":      "#EFF6FF",  "n_exp_o":   "#3B82F6",
    "n_sol_f":      "#DCFCE7",  "n_sol_o":   "#16A34A",
    "e_sol":        "#16A34A",
    "e_exp":        "#93C5FD",
    "e_norm":       "#CBD5E1",

    # Status
    "s_idle":       "#8FA0B4",
    "s_solving":    "#D97706",
    "s_ok":         "#16A34A",
    "s_err":        "#DC2626",
}

# Direction visuals
ARROWS = {"RIGHT":"→","LEFT":"←","DOWN":"↓","UP":"↑","START":"●"}
ARROW_C = {"RIGHT":"#3B82F6","LEFT":"#8B5CF6","DOWN":"#F59E0B","UP":"#10B981","START":"#94A3B8"}


# ═══════════════════════════════════════════════════════════════
#  ALGORITHM  (unchanged from original)
# ═══════════════════════════════════════════════════════════════

class Puzzle:
    def __init__(self, start_board, goal_board):
        self.start_board = start_board
        self.goal_board  = goal_board
        self.board_size  = len(start_board)
        self.tree_data   = []

    def is_goal(self, state):
        return state == self.goal_board

    def get_successors(self, state):
        def swap(s, i1, j1, i2, j2):
            sl = [list(r) for r in s]
            sl[i1][j1], sl[i2][j2] = sl[i2][j2], sl[i1][j1]
            return tuple(tuple(r) for r in sl)

        zero_r = zero_c = -1
        for r in range(self.board_size):
            for c in range(self.board_size):
                if state[r][c] == 0:
                    zero_r, zero_c = r, c; break
            if zero_r != -1: break

        result = []
        for (dr,dc), name in zip([(0,1),(0,-1),(1,0),(-1,0)],
                                  ["RIGHT","LEFT","DOWN","UP"]):
            nr, nc = zero_r+dr, zero_c+dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                result.append((swap(state, zero_r, zero_c, nr, nc), name))
        return result

    def manhattan_distance(self, state):
        dist = 0
        gpos = {self.goal_board[r][c]:(r,c)
                for r in range(self.board_size)
                for c in range(self.board_size)}
        for r in range(self.board_size):
            for c in range(self.board_size):
                v = state[r][c]
                if v != 0:
                    tr, tc = gpos[v]
                    dist += abs(tr-r) + abs(tc-c)
        return dist

    def solve(self, max_nodes=1000):
        ctr = count()
        open_set, entry_finder = [], {}
        came_from, move_from = {}, {}
        self.tree_data = []
        nid = 0; s2id = {}

        h0 = self.manhattan_distance(self.start_board)
        s2id[self.start_board] = nid
        self.tree_data.append({'id':nid,'state':self.start_board,'parent_id':None,
                               'g':0,'h':h0,'f':h0,'move':"START",'expanded':False})
        nid += 1

        e0 = (h0, next(ctr), self.start_board, 0, None)
        heapq.heappush(open_set, e0); entry_finder[self.start_board] = e0

        closed = set(); processed = 0

        while open_set and processed < max_nodes:
            f, _, cur, g, _ = heapq.heappop(open_set)
            processed += 1
            cid = s2id[cur]
            for nd in self.tree_data:
                if nd['id'] == cid: nd['expanded'] = True; break

            if self.is_goal(cur):
                path = []
                c = cur
                while c:
                    path.append((c, move_from.get(c,"START")))
                    c = came_from.get(c)
                return path[::-1], processed, self.tree_data

            if cur in closed: continue
            closed.add(cur)

            for suc, mv in self.get_successors(cur):
                if suc in closed: continue
                tg = g+1
                if suc not in entry_finder or tg < entry_finder[suc][3]:
                    came_from[suc] = cur; move_from[suc] = mv
                    hs = self.manhattan_distance(suc); fs = tg+hs
                    if suc not in s2id:
                        s2id[suc] = nid
                        self.tree_data.append({'id':nid,'state':suc,'parent_id':cid,
                                               'g':tg,'h':hs,'f':fs,'move':mv,'expanded':False})
                        nid += 1
                    ne = (fs, next(ctr), suc, tg, cur)
                    heapq.heappush(open_set, ne); entry_finder[suc] = ne

        return None, processed, self.tree_data


# ═══════════════════════════════════════════════════════════════
#  TREE VISUALIZATION
# ═══════════════════════════════════════════════════════════════

class TreeVisualization:
    def __init__(self, canvas, tree_data):
        self.canvas    = canvas
        self.tree_data = tree_data
        self.node_r    = 32
        self.h_gap     = 500
        self.nodes     = {}
        self.edges     = []
        self.compact   = False
        self._tip_win  = None

    def clear(self):
        self.canvas.delete("all")
        self.nodes = {}; self.edges = []
        self._hide_tip()

    def _calc_positions(self, show_all, max_depth, max_width):
        if not self.tree_data: return {}, {}
        root = next((n for n in self.tree_data if n['parent_id'] is None), None)
        if not root: return {}, {}

        # Build adjacency
        tree = {}
        for nd in self.tree_data:
            nid, pid = nd['id'], nd['parent_id']
            if nid not in tree: tree[nid] = {'nd':nd,'children':[]}
            if pid is not None:
                if pid not in tree: tree[pid] = {'nd':None,'children':[]}
                if show_all or nd.get('expanded', False):
                    tree[pid]['children'].append(nid)

        # BFS depths
        depths = {root['id']:0}; q = [(root['id'],0)]; max_d = 0
        while q:
            nid, d = q.pop(0); max_d = max(max_d, d)
            for cid in tree.get(nid,{}).get('children',[]):
                if cid not in depths:
                    depths[cid] = d+1; q.append((cid,d+1))

        by_d = {}
        for nid, d in depths.items(): by_d.setdefault(d,[]).append(nid)

        disp_max = max_d if max_depth is None else min(max_depth, max_d)
        if show_all: disp_max = max_d

        positions = {}
        for d in range(disp_max+1):
            if d not in by_d: continue
            at_d = by_d[d]
            if max_width and not show_all: at_d = at_d[:max_width]
            n = len(at_d)
            ch = max(self.canvas.winfo_height(), 500)
            for i, nid in enumerate(at_d):
                x = d * self.h_gap + 60
                y = (i+1) * ch / (n+1) if n > 1 else ch/2
                positions[nid] = (x, y)
        return positions, tree

    def draw_tree(self, sol_ids=None, show_all=False, max_depth=None, max_width=None):
        self.clear()
        if not self.tree_data: return
        positions, tree = self._calc_positions(show_all, max_depth, max_width)
        if not positions: return

        sol = set(sol_ids or [])

        # Edges
        for nd in self.tree_data:
            nid, pid = nd['id'], nd['parent_id']
            if pid is not None and nid in positions and pid in positions:
                x1,y1 = positions[pid]; x2,y2 = positions[nid]
                in_sol = nid in sol and pid in sol
                if in_sol:       col,w = C["e_sol"], 2.5
                elif nd.get('expanded'): col,w = C["e_exp"], 1.5
                else:            col,w = C["e_norm"], 1.0
                self.edges.append(
                    self.canvas.create_line(x1,y1,x2,y2,fill=col,width=w))

        # Nodes
        for nd in self.tree_data:
            nid = nd['id']
            if nid not in positions: continue
            x, y = positions[nid]
            in_sol = nid in sol

            if in_sol:           fill,out,ow = C["n_sol_f"],C["n_sol_o"],2.5
            elif nd.get('expanded'): fill,out,ow = C["n_exp_f"],C["n_exp_o"],2.0
            else:                fill,out,ow = C["n_unexp_f"],C["n_unexp_o"],1.5

            r = self.node_r
            circ = self.canvas.create_oval(x-r,y-r,x+r,y+r,fill=fill,outline=out,width=ow)

            if self.compact:
                body = "".join(str(v) if v!=0 else "_" for row in nd['state'] for v in row)
                fs = 7
            else:
                body = "\n".join(" ".join(str(v) if v!=0 else "_" for v in row) for row in nd['state'])
                body += f"\nf={nd['f']} g={nd['g']} h={nd['h']}"
                fs = 7 if in_sol else 6

            txt = self.canvas.create_text(x,y,text=body,font=("Courier",fs))
            self.nodes[nid] = {'circle':circ,'text':txt,'nd':nd}

            for item in (circ, txt):
                self.canvas.tag_bind(item,"<Enter>",lambda e,n=nd:self._show_tip(e,n))
                self.canvas.tag_bind(item,"<Leave>",lambda e:self._hide_tip())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show_tip(self, event, nd):
        self._hide_tip()
        state_str = "\n".join("  ".join(str(v) if v!=0 else " " for v in row) for row in nd['state'])
        info = f"Move: {nd['move']}\nf={nd['f']}  g={nd['g']}  h={nd['h']}\nExpanded: {'Yes' if nd.get('expanded') else 'No'}\n\n{state_str}"
        rx = self.canvas.winfo_rootx() + event.x + 16
        ry = self.canvas.winfo_rooty() + event.y - 8
        self._tip_win = tk.Toplevel(self.canvas)
        self._tip_win.wm_overrideredirect(True)
        self._tip_win.wm_geometry(f"+{rx}+{ry}")
        tk.Label(self._tip_win, text=info, justify=tk.LEFT,
                 bg="#1E293B", fg="#F1F5F9", font=("Courier",9),
                 padx=8, pady=6, relief="flat").pack()

    def _hide_tip(self):
        if self._tip_win:
            try: self._tip_win.destroy()
            except: pass
            self._tip_win = None


# ═══════════════════════════════════════════════════════════════
#  MAIN GUI
# ═══════════════════════════════════════════════════════════════

class PuzzleGUI:
    def __init__(self, root):
        self.root = root
        root.title("8-Puzzle Solver")
        root.geometry("1400x840")
        root.minsize(1100, 700)
        root.configure(bg=C["app"])

        # State
        self.puzzle              = None
        self.tree_vis            = None
        self.solution_path       = []
        self.current_step        = 0
        self.tree_data           = []
        self.sol_node_ids        = []
        self._autoplay_job       = None
        self._solving            = False
        self._prev_state         = None
        self.scale_factor        = 1.0

        self._build_ui()
        self.load_preset("easy")

    # ───────────────────────────────────────────────────────────
    #  TOP-LEVEL LAYOUT
    # ───────────────────────────────────────────────────────────

    def _build_ui(self):
        self._make_header()

        body = tk.Frame(self.root, bg=C["app"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6,0))

        # Three columns
        self._make_left(body)
        self._make_center(body)
        self._make_right(body)

        self._make_statusbar()
        self._bind_keys()

    # ───────────────────────────────────────────────────────────
    #  HEADER
    # ───────────────────────────────────────────────────────────

    def _make_header(self):
        hdr = tk.Frame(self.root, bg=C["header"], height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="8-Puzzle Solver",
                 bg=C["header"], fg=C["t_white"],
                 font=("Segoe UI",15,"bold")).pack(side=tk.LEFT, padx=18, pady=10)
        tk.Label(hdr, text="A* Search  ·  Manhattan Distance Heuristic",
                 bg=C["header"], fg=C["t_head_sub"],
                 font=("Segoe UI",9)).pack(side=tk.LEFT, pady=(14,0))

        self._kbd_lbl = tk.Label(hdr,
            text="Keyboard: ← → navigate  |  Space = play/pause  |  Home/End = first/last",
            bg=C["header"], fg="#5A6E8A", font=("Segoe UI",8))
        self._kbd_lbl.pack(side=tk.RIGHT, padx=18)

    # ───────────────────────────────────────────────────────────
    #  LEFT PANEL  (fixed 300 px)
    # ───────────────────────────────────────────────────────────

    def _make_left(self, parent):
        left = tk.Frame(parent, bg=C["panel"], width=300,
                        highlightbackground=C["border"], highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8), pady=4)
        left.pack_propagate(False)

        self._section_puzzle_input(left)
        self._section_presets(left)
        self._section_settings(left)
        self._section_actions(left)

    # ── Puzzle Input ──────────────────────────────────────────

    def _section_puzzle_input(self, parent):
        sec = self._section(parent, "Puzzle Input")

        grids = tk.Frame(sec, bg=C["panel"])
        grids.pack(fill=tk.X, pady=(4,6))

        self.start_entries = self._grid_widget(grids, "Start State")
        self.goal_entries  = self._grid_widget(grids, "Goal State")

        # String inputs
        self._str_input_row(sec, "Start:", "start")
        self._str_input_row(sec, "Goal:", "goal")

    def _grid_widget(self, parent, title):
        col = tk.Frame(parent, bg=C["panel"])
        col.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Label(col, text=title, bg=C["panel"], fg=C["t_secondary"],
                 font=("Segoe UI",8,"bold")).pack(pady=(0,4))
        gf = tk.Frame(col, bg=C["panel"])
        gf.pack()
        entries = []
        for r in range(3):
            row = []
            for c in range(3):
                e = tk.Entry(gf, width=3, font=("Segoe UI",13,"bold"),
                             justify="center", bg=C["tile"], fg=C["t_primary"],
                             relief="flat",
                             highlightthickness=1,
                             highlightbackground=C["border"],
                             highlightcolor=C["focus"],
                             insertbackground=C["t_primary"])
                e.grid(row=r, column=c, padx=2, pady=2, ipady=5)
                e.bind("<FocusIn>",  lambda ev: ev.widget.configure(highlightbackground=C["focus"]))
                e.bind("<FocusOut>", lambda ev: ev.widget.configure(highlightbackground=C["border"]))
                row.append(e)
            entries.append(row)
        return entries

    def _str_input_row(self, parent, label, kind):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill=tk.X, pady=2, padx=2)
        tk.Label(row, text=label, bg=C["panel"], fg=C["t_secondary"],
                 font=("Segoe UI",8), width=5, anchor="w").pack(side=tk.LEFT)
        entry = tk.Entry(row, width=11, font=("Courier",9),
                         bg=C["tile"], fg=C["t_primary"],
                         relief="flat",
                         highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["focus"],
                         insertbackground=C["t_primary"])
        entry.pack(side=tk.LEFT, padx=4, ipady=2)
        self._btn(row, "Apply", lambda k=kind: self.apply_str(k),
                  bg="#E8EEF6", fg=C["t_primary"], padx=6).pack(side=tk.LEFT)
        if kind == "start": self.start_str_entry = entry
        else:               self.goal_str_entry  = entry

    # ── Presets ───────────────────────────────────────────────

    def _section_presets(self, parent):
        sec = self._section(parent, "Quick Presets")
        row = tk.Frame(sec, bg=C["panel"])
        row.pack(fill=tk.X, pady=4)
        specs = [("Easy","easy",C["easy_bg"],C["easy_fg"]),
                 ("Medium","medium",C["med_bg"],C["med_fg"]),
                 ("Hard","hard",C["hard_bg"],C["hard_fg"])]
        for lbl, diff, bg, fg in specs:
            self._btn(row, lbl, lambda d=diff: self.load_preset(d),
                      bg=bg, fg=fg, padx=14, pady=5).pack(side=tk.LEFT, padx=3)

    # ── Settings ──────────────────────────────────────────────

    def _section_settings(self, parent):
        sec = self._section(parent, "Solver Settings")

        self.max_nodes_var = tk.IntVar(value=1000)
        self.depth_var     = tk.IntVar(value=5)
        self.width_var     = tk.IntVar(value=8)

        self._slider_row(sec, "Max Nodes", self.max_nodes_var, 100, 20000, 1000,
                         fmt=lambda v: f"{int(v):,}")
        self._slider_row(sec, "Tree Depth", self.depth_var, 1, 15, 5,
                         fmt=lambda v: str(int(v)))
        self._slider_row(sec, "Tree Width", self.width_var, 2, 24, 8,
                         fmt=lambda v: str(int(v)))

        chk_f = tk.Frame(sec, bg=C["panel"])
        chk_f.pack(fill=tk.X, pady=(4,0))

        self.show_all_var  = tk.BooleanVar(value=True)
        self.compact_var   = tk.BooleanVar(value=False)
        self._checkbox(chk_f, "Show all processed nodes", self.show_all_var)
        self._checkbox(chk_f, "Compact node labels",      self.compact_var)

    def _slider_row(self, parent, label, var, lo, hi, default, fmt):
        f = tk.Frame(parent, bg=C["panel"])
        f.pack(fill=tk.X, pady=3)
        tk.Label(f, text=label, bg=C["panel"], fg=C["t_secondary"],
                 font=("Segoe UI",8), width=11, anchor="w").pack(side=tk.LEFT)
        val_lbl = tk.Label(f, text=fmt(default), bg=C["panel"],
                           fg=C["t_primary"], font=("Segoe UI",8,"bold"), width=7)
        val_lbl.pack(side=tk.RIGHT)
        ttk.Scale(f, from_=lo, to=hi, variable=var, orient="horizontal",
                  command=lambda v, lbl=val_lbl, fn=fmt: lbl.configure(text=fn(float(v)))
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

    def _checkbox(self, parent, text, var):
        tk.Checkbutton(parent, text=text, variable=var,
                       bg=C["panel"], fg=C["t_secondary"],
                       activebackground=C["panel"],
                       selectcolor=C["panel"],
                       font=("Segoe UI",8)).pack(anchor="w", pady=1)

    # ── Action buttons ────────────────────────────────────────

    def _section_actions(self, parent):
        f = tk.Frame(parent, bg=C["panel"])
        f.pack(fill=tk.X, padx=10, pady=10)
        self.solve_btn = self._btn(f, "▶  Solve Puzzle", self.solve_puzzle,
                                   bg=C["btn_solve"], fg="#FFFFFF",
                                   padx=14, pady=7,
                                   font=("Segoe UI",10,"bold"))
        self.solve_btn.pack(fill=tk.X, pady=(0,4))

        self.refresh_btn = self._btn(f, "⟳  Refresh Tree", self.refresh_tree,
                                     bg=C["btn_refresh"], fg=C["t_secondary"],
                                     padx=14, pady=6, state=tk.DISABLED)
        self.refresh_btn.pack(fill=tk.X)

    # ───────────────────────────────────────────────────────────
    #  CENTER PANEL  (fixed 360 px) — tabbed: Solver | A* Guide
    # ───────────────────────────────────────────────────────────

    def _make_center(self, parent):
        mid = tk.Frame(parent, bg=C["panel"], width=360,
                       highlightbackground=C["border"], highlightthickness=1)
        mid.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8), pady=4)
        mid.pack_propagate(False)

        # Tab styles
        style = ttk.Style()
        style.configure("Center.TNotebook",     background=C["panel"], borderwidth=0)
        style.configure("Center.TNotebook.Tab", font=("Segoe UI",9,"bold"),
                        padding=[10,5], background=C["section_hdr"],
                        foreground=C["t_secondary"])
        style.map("Center.TNotebook.Tab",
                  background=[("selected", C["btn_solve"])],
                  foreground=[("selected", "#FFFFFF")])

        nb = ttk.Notebook(mid, style="Center.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1 — Solver
        tab_solver = tk.Frame(nb, bg=C["panel"])
        nb.add(tab_solver, text="  \U0001f9e9 Solver  ")
        self._section_solution_viewer(tab_solver)
        self._section_stats(tab_solver)

        # Tab 2 — A* Explanation
        tab_astar = tk.Frame(nb, bg=C["panel"])
        nb.add(tab_astar, text="  \U0001f4d6 A* Guide  ")
        self._section_astar_guide(tab_astar)

    # ── Solution Viewer ───────────────────────────────────────

    def _section_solution_viewer(self, parent):
        sec = self._section(parent, "Solution Viewer")

        # Tile grid
        tiles_outer = tk.Frame(sec, bg=C["panel"])
        tiles_outer.pack(pady=10)
        self.tile_labels = []
        for r in range(3):
            row_tiles = []
            for c in range(3):
                lbl = tk.Label(tiles_outer, text="", width=3, height=1,
                               font=("Segoe UI",22,"bold"),
                               bg=C["tile"], fg=C["t_primary"],
                               relief="flat",
                               highlightthickness=1,
                               highlightbackground=C["border"])
                lbl.grid(row=r, column=c, padx=3, pady=3, ipady=12, ipadx=10)
                row_tiles.append(lbl)
            self.tile_labels.append(row_tiles)

        # Step + move info
        info = tk.Frame(sec, bg=C["panel"])
        info.pack(pady=(0,6))
        self.step_lbl = tk.Label(info, text="Step  — / —", bg=C["panel"],
                                  fg=C["t_secondary"], font=("Segoe UI",10,"bold"))
        self.step_lbl.pack(side=tk.LEFT, padx=8)
        self.move_lbl = tk.Label(info, text="—", bg=C["panel"],
                                  fg=C["t_primary"], font=("Segoe UI",13,"bold"))
        self.move_lbl.pack(side=tk.LEFT)

        # Navigation row
        nav = tk.Frame(sec, bg=C["panel"])
        nav.pack(pady=4)

        btns = [
            ("⏮", self._go_first,  C["btn_nav"], C["t_secondary"],  8),
            ("◀",  self.prev_step,  C["btn_nav"], C["t_secondary"], 10),
            ("▶ Play", self.toggle_play, C["btn_play"], "#FFFFFF",   10),
            ("▶",  self.next_step,  C["btn_nav"], C["t_secondary"], 10),
            ("⏭", self._go_last,   C["btn_nav"], C["t_secondary"],  8),
        ]
        self.nav_btns = {}
        keys = ["first","prev","play","next","last"]
        for (txt, cmd, bg, fg, px), key in zip(btns, keys):
            b = self._btn(nav, txt, cmd, bg=bg, fg=fg, padx=px, pady=5, state=tk.DISABLED)
            b.pack(side=tk.LEFT, padx=2)
            self.nav_btns[key] = b

        # Speed control
        spd = tk.Frame(sec, bg=C["panel"])
        spd.pack(pady=(6,2), fill=tk.X, padx=12)
        tk.Label(spd, text="Speed:", bg=C["panel"], fg=C["t_secondary"],
                 font=("Segoe UI",8)).pack(side=tk.LEFT)
        self.speed_lbl = tk.Label(spd, text="Normal", bg=C["panel"],
                                   fg=C["t_primary"], font=("Segoe UI",8,"bold"), width=6)
        self.speed_lbl.pack(side=tk.RIGHT)
        self.speed_var = tk.IntVar(value=600)

        def _upd(v):
            ms = int(float(v))
            self.speed_lbl.configure(text="Fast" if ms<300 else "Slow" if ms>900 else "Normal")

        ttk.Scale(spd, from_=100, to=1500, variable=self.speed_var,
                  orient="horizontal", command=_upd
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

    # ── Statistics ────────────────────────────────────────────

    def _section_stats(self, parent):
        sec = self._section(parent, "Statistics")
        self.stats_lbl = tk.Label(sec, text="Nodes Processed: —\nSolution Steps: —",
                                   bg=C["panel"], fg=C["t_secondary"],
                                   font=("Segoe UI",9), justify="left", anchor="w")
        self.stats_lbl.pack(anchor="w", pady=4)

    # ── A* Algorithm Guide ────────────────────────────────────

    def _section_astar_guide(self, parent):
        """Scrollable A* / 8-Puzzle explanation panel."""

        outer = tk.Frame(parent, bg=C["panel"])
        outer.pack(fill=tk.BOTH, expand=True)

        vscroll = tk.Scrollbar(outer, orient=tk.VERTICAL)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        cv = tk.Canvas(outer, bg=C["panel"], highlightthickness=0,
                       yscrollcommand=vscroll.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll.config(command=cv.yview)

        inner = tk.Frame(cv, bg=C["panel"])
        win = cv.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            cv.configure(scrollregion=cv.bbox("all"))
            cv.itemconfig(win, width=cv.winfo_width())
        inner.bind("<Configure>", _resize)
        cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(-1*(e.delta//120), "units"))
        cv.bind("<Button-4>",   lambda e: cv.yview_scroll(-1, "units"))
        cv.bind("<Button-5>",   lambda e: cv.yview_scroll( 1, "units"))

        P = 12

        def heading(text, size=10, color=None):
            color = color or C["btn_solve"]
            tk.Label(inner, text=text, bg=C["panel"], fg=color,
                     font=("Segoe UI", size, "bold"),
                     anchor="w", wraplength=310, justify="left",
                     padx=P).pack(fill=tk.X, pady=(10, 2))

        def body(text):
            tk.Label(inner, text=text, bg=C["panel"], fg=C["t_secondary"],
                     font=("Segoe UI", 8),
                     anchor="w", wraplength=310, justify="left",
                     padx=P).pack(fill=tk.X, pady=(0, 4))

        def divider():
            tk.Frame(inner, bg=C["border"], height=1).pack(fill=tk.X, padx=P, pady=6)

        def formula_box(lines, bg="#EFF6FF", fg="#1D4ED8"):
            box = tk.Frame(inner, bg=bg, highlightbackground=fg, highlightthickness=1)
            box.pack(fill=tk.X, padx=P, pady=4)
            for line in lines:
                tk.Label(box, text=line, bg=bg, fg=fg,
                         font=("Courier", 8, "bold"),
                         anchor="w", padx=8, pady=1).pack(fill=tk.X)

        def step_box(num, title, desc, bg="#F0FDF4", fg="#166534"):
            row = tk.Frame(inner, bg=bg, highlightbackground=fg, highlightthickness=1)
            row.pack(fill=tk.X, padx=P, pady=2)
            tk.Label(row, text=f" {num} ", bg=fg, fg="#FFFFFF",
                     font=("Segoe UI", 9, "bold"), padx=5, pady=3).pack(side=tk.LEFT)
            right = tk.Frame(row, bg=bg)
            right.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
            tk.Label(right, text=title, bg=bg, fg=fg,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill=tk.X)
            tk.Label(right, text=desc, bg=bg, fg=fg,
                     font=("Segoe UI", 7), anchor="w",
                     wraplength=260, justify="left").pack(fill=tk.X)

        def info_row(label, value, val_fg=None):
            val_fg = val_fg or C["t_primary"]
            row = tk.Frame(inner, bg=C["panel"])
            row.pack(fill=tk.X, padx=P, pady=1)
            tk.Label(row, text=label, bg=C["panel"], fg=C["t_secondary"],
                     font=("Segoe UI", 8, "bold"), width=11, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=C["panel"], fg=val_fg,
                     font=("Segoe UI", 8), anchor="w",
                     wraplength=230, justify="left").pack(side=tk.LEFT)

        # ── CONTENT ──────────────────────────────────────────────

        # Banner
        banner = tk.Frame(inner, bg=C["btn_solve"])
        banner.pack(fill=tk.X)
        tk.Label(banner, text="A* Search Algorithm", bg=C["btn_solve"],
                 fg="#FFFFFF", font=("Segoe UI", 12, "bold"),
                 padx=P, pady=8, anchor="w").pack(fill=tk.X)
        tk.Label(banner, text="How this solver finds the optimal solution",
                 bg="#1D4ED8", fg="#BFDBFE",
                 font=("Segoe UI", 8), padx=P, pady=3, anchor="w").pack(fill=tk.X)

        # 1 — Problem
        heading("1.  The 8-Puzzle Problem")
        body("A 3x3 grid holds 8 numbered tiles and one blank. "
             "Slide tiles into the blank (left/right/up/down) to reach "
             "the goal configuration. The blank has 2-4 valid neighbours.")

        ex_frame = tk.Frame(inner, bg=C["panel"])
        ex_frame.pack(padx=P, pady=4)

        def mini_grid(parent, state, caption, cap_color):
            col = tk.Frame(parent, bg=C["panel"])
            col.pack(side=tk.LEFT, padx=6)
            tk.Label(col, text=caption, bg=C["panel"], fg=cap_color,
                     font=("Segoe UI", 8, "bold")).pack(pady=(0, 2))
            gf = tk.Frame(col, bg=C["panel"])
            gf.pack()
            for r in range(3):
                for c in range(3):
                    v = state[r][c]
                    bg_t = C["tile_empty"] if v == 0 else C["tile"]
                    tk.Label(gf, text=str(v) if v else "",
                             bg=bg_t, fg=C["t_primary"],
                             font=("Segoe UI", 10, "bold"),
                             width=2, height=1, relief="flat",
                             highlightthickness=1,
                             highlightbackground=C["border"]
                             ).grid(row=r, column=c, padx=1, pady=1, ipady=2)

        mini_grid(ex_frame, [[1,2,3],[4,5,0],[7,8,6]], "Start", C["t_secondary"])
        tk.Label(ex_frame, text=" → ", bg=C["panel"], fg=C["t_muted"],
                 font=("Segoe UI", 14)).pack(side=tk.LEFT)
        mini_grid(ex_frame, [[1,2,3],[4,5,6],[7,8,0]], "Goal", C["btn_solve"])

        divider()

        # 2 — State space
        heading("2.  State Space as a Graph")
        body("Each board layout is a node. Nodes are connected if one "
             "tile-slide transforms one into the other. "
             "A* searches for the shortest path from Start to Goal.")

        divider()

        # 3 — Core formula
        heading("3.  The A* Cost Function")
        body("A* always expands the node with the lowest estimated "
             "total cost f(n). It is guaranteed to be optimal when the "
             "heuristic h is admissible (never over-estimates).")

        formula_box([
            "  f(n)  =  g(n)  +  h(n)",
            "",
            "  f(n) — total estimated cost through n",
            "  g(n) — cost from Start to n (exact)",
            "  h(n) — cost from n to Goal (estimate)",
        ])

        divider()

        # 4 — Steps
        heading("4.  Algorithm Steps")

        step_box("1", "Initialise",
                 "Push Start node onto the Open (priority) queue with f = h.",
                 bg="#F0FDF4", fg="#166534")
        step_box("2", "Pick best",
                 "Pop the node with the lowest f from Open. "
                 "If it is the Goal — reconstruct and return the path.",
                 bg="#EFF6FF", fg="#1D4ED8")
        step_box("3", "Expand",
                 "Slide the blank in every valid direction to get successors. "
                 "Compute g = parent_g + 1 and h = Manhattan distance.",
                 bg="#FFF7ED", fg="#9A3412")
        step_box("4", "Update Open",
                 "Add each successor if it is new or found via a cheaper path. "
                 "Nodes already in Closed are skipped.",
                 bg="#FDF4FF", fg="#7E22CE")
        step_box("5", "Repeat",
                 "Return to Step 2. If Open empties with no goal found, "
                 "the puzzle has no solution.",
                 bg="#F0FDF4", fg="#166534")

        divider()

        # 5 — Heuristic
        heading("5.  Manhattan Distance Heuristic")
        body("For every tile count the horizontal + vertical distance "
             "to its goal position. Sum all tiles (ignore blank). "
             "This is admissible because no tile can travel fewer moves.")

        formula_box([
            "  h = SUM |row_i - goal_row_i|",
            "        + |col_i - goal_col_i|",
        ], bg="#FFF7ED", fg="#9A3412")

        body("Example: tile 6 at (1,2), goal (2,2)  -->  |1-2|+|2-2| = 1")

        divider()

        # 6 — Properties
        heading("6.  Algorithm Properties")

        info_row("Optimal?",  "Yes — with an admissible heuristic",   val_fg=C["btn_play"])
        info_row("Complete?", "Yes — always finds a solution if one exists", val_fg=C["btn_play"])
        info_row("vs Greedy", "Greedy uses only h — fast but sub-optimal", val_fg=C["t_muted"])
        info_row("vs BFS",    "BFS ignores h — optimal but much slower",    val_fg=C["t_muted"])
        info_row("Limit",     "Memory grows with Open list size",            val_fg=C["t_secondary"])

        divider()

        # 7 — Tree legend
        heading("7.  Reading the Tree (right panel)")
        body("Every circle is a board state. "
             "Hover to see f/g/h values and the full grid.")

        legend_data = [
            (C["n_unexp_f"], C["n_unexp_o"], "Generated, not yet expanded"),
            (C["n_exp_f"],   C["n_exp_o"],   "Expanded — successors generated"),
            (C["n_sol_f"],   C["n_sol_o"],   "On the optimal solution path"),
        ]
        for fill, out, desc in legend_data:
            row = tk.Frame(inner, bg=C["panel"])
            row.pack(fill=tk.X, padx=P, pady=2)
            sw = tk.Canvas(row, width=16, height=16, bg=C["panel"],
                           highlightthickness=0)
            sw.pack(side=tk.LEFT)
            sw.create_oval(1, 1, 14, 14, fill=fill, outline=out, width=2)
            tk.Label(row, text=desc, bg=C["panel"], fg=C["t_secondary"],
                     font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=6)

        divider()

        # 8 — Solvability
        heading("8.  Solvability Check")
        body("Not every arrangement can reach the goal. "
             "Count inversions in the tile sequence (blank ignored). "
             "An inversion is a pair where a larger tile comes before "
             "a smaller one in reading order.")

        formula_box([
            "  inv = # pairs (i,j): i<j & tile[i]>tile[j]",
            "",
            "  Solvable  <==>  inv is EVEN",
        ], bg="#FEE2E2", fg="#991B1B")

        # Credit
        divider()
        tk.Label(inner, text="Reference: rand-asswad.xyz/taquin",
                 bg=C["section_hdr"], fg=C["t_muted"],
                 font=("Segoe UI", 7, "italic"),
                 padx=P, pady=4).pack(fill=tk.X, padx=P)

        tk.Frame(inner, bg=C["panel"], height=20).pack()

    # ───────────────────────────────────────────────────────────
    #  RIGHT PANEL  (fills remaining space)
    # ───────────────────────────────────────────────────────────

    def _make_right(self, parent):
        right = tk.Frame(parent, bg=C["panel"],
                         highlightbackground=C["border"], highlightthickness=1)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)

        # Control bar
        ctrl = tk.Frame(right, bg=C["section_hdr"],
                        highlightbackground=C["border"], highlightthickness=1)
        ctrl.pack(fill=tk.X, padx=6, pady=6)

        tk.Label(ctrl, text="Search Tree Visualization",
                 bg=C["section_hdr"], fg=C["t_primary"],
                 font=("Segoe UI",10,"bold")).pack(side=tk.LEFT, padx=10, pady=6)

        for txt, cmd in [("Reset ⊙", self.reset_view),
                          ("－", self.zoom_out),
                          ("＋", self.zoom_in)]:
            self._btn(ctrl, txt, cmd, bg="#E8EEF6", fg=C["t_secondary"],
                      padx=10, pady=4).pack(side=tk.RIGHT, padx=3, pady=5)

        # Canvas area
        cf = tk.Frame(right, bg=C["panel"])
        cf.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0,4))

        hscroll = tk.Scrollbar(cf, orient=tk.HORIZONTAL)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        vscroll = tk.Scrollbar(cf)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(cf, bg=C["canvas_bg"],
                                xscrollcommand=hscroll.set,
                                yscrollcommand=vscroll.set,
                                highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hscroll.config(command=self.canvas.xview)
        vscroll.config(command=self.canvas.yview)

        self.canvas.bind("<ButtonPress-1>", self.pan_start)
        self.canvas.bind("<B1-Motion>",     self.pan_drag)
        self.canvas.bind("<MouseWheel>",    self.mouse_zoom)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out())

        # Legend bar
        lgd = tk.Frame(right, bg=C["section_hdr"],
                       highlightbackground=C["border"], highlightthickness=1)
        lgd.pack(fill=tk.X, padx=6, pady=(0,6))
        for lbl, fill, out in [("Unexpanded",  C["n_unexp_f"], C["n_unexp_o"]),
                                ("Expanded",    C["n_exp_f"],   C["n_exp_o"]),
                                ("Solution",    C["n_sol_f"],   C["n_sol_o"])]:
            row = tk.Frame(lgd, bg=C["section_hdr"])
            row.pack(side=tk.LEFT, padx=10, pady=4)
            sw = tk.Canvas(row, width=14, height=14, bg=C["section_hdr"],
                           highlightthickness=0)
            sw.pack(side=tk.LEFT)
            sw.create_oval(1,1,13,13, fill=fill, outline=out, width=1.5)
            tk.Label(row, text=lbl, bg=C["section_hdr"], fg=C["t_secondary"],
                     font=("Segoe UI",8)).pack(side=tk.LEFT, padx=3)
        tk.Label(lgd, text="f=g+h   g=path cost   h=Manhattan, Author = Zaoui Abdelbari",
                 bg=C["section_hdr"], fg=C["t_muted"],
                 font=("Segoe UI",7)).pack(side=tk.RIGHT, padx=10)

    # ───────────────────────────────────────────────────────────
    #  STATUS BAR
    # ───────────────────────────────────────────────────────────

    def _make_statusbar(self):
        bar = tk.Frame(self.root, bg=C["header"], height=24)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Ready — select a preset or enter a puzzle to begin.")
        self._status_lbl = tk.Label(bar, textvariable=self._status_var,
                                     bg=C["header"], fg=C["s_idle"],
                                     font=("Segoe UI",8), anchor="w")
        self._status_lbl.pack(side=tk.LEFT, padx=10)

    def _status(self, msg, color="s_idle"):
        self._status_var.set(msg)
        self._status_lbl.configure(fg=C.get(color, C["s_idle"]))

    # ───────────────────────────────────────────────────────────
    #  WIDGET FACTORY HELPERS
    # ───────────────────────────────────────────────────────────

    def _section(self, parent, title):
        """Returns inner Frame of a visually labeled section."""
        outer = tk.Frame(parent, bg=C["panel"])
        outer.pack(fill=tk.X, padx=10, pady=(8,0))

        hrow = tk.Frame(outer, bg=C["panel"])
        hrow.pack(fill=tk.X)
        tk.Label(hrow, text=title, bg=C["panel"], fg=C["t_primary"],
                 font=("Segoe UI",9,"bold")).pack(side=tk.LEFT)
        tk.Frame(outer, bg=C["border"], height=1).pack(fill=tk.X, pady=(2,6))

        inner = tk.Frame(outer, bg=C["panel"])
        inner.pack(fill=tk.X)
        return inner

    def _btn(self, parent, text, command, bg=None, fg=None,
             padx=10, pady=4, state=tk.NORMAL, font=None):
        bg   = bg   or C["btn_refresh"]
        fg   = fg   or C["t_secondary"]
        font = font or ("Segoe UI",9,"bold")
        return tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg, font=font,
                         relief="flat", cursor="hand2",
                         activebackground=bg, activeforeground=fg,
                         padx=padx, pady=pady, state=state,
                         bd=0, highlightthickness=0)

    # ───────────────────────────────────────────────────────────
    #  KEYBOARD SHORTCUTS
    # ───────────────────────────────────────────────────────────

    def _bind_keys(self):
        self.root.bind("<Right>", lambda e: self.next_step())
        self.root.bind("<Left>",  lambda e: self.prev_step())
        self.root.bind("<Home>",  lambda e: self._go_first())
        self.root.bind("<End>",   lambda e: self._go_last())
        self.root.bind("<space>", lambda e: self.toggle_play())

    # ───────────────────────────────────────────────────────────
    #  INPUT LOGIC
    # ───────────────────────────────────────────────────────────

    def apply_str(self, kind):
        entry   = self.start_str_entry if kind=="start" else self.goal_str_entry
        entries = self.start_entries   if kind=="start" else self.goal_entries
        s = entry.get().strip()
        if len(s)!=9 or not s.isdigit() or set(s)!=set("012345678"):
            entry.configure(highlightbackground=C["s_err"])
            self._status("Invalid input — must contain digits 0-8 exactly once.", "s_err")
            self.root.after(1500, lambda: entry.configure(highlightbackground=C["border"]))
            return
        entry.configure(highlightbackground=C["border"])
        for r in range(3):
            for c in range(3):
                entries[r][c].delete(0, tk.END)
                entries[r][c].insert(0, s[r*3+c])
        self._status(f"{'Start' if kind=='start' else 'Goal'} state applied from string.")

    def load_preset(self, difficulty):
        goal = [[1,2,3],[4,5,6],[7,8,0]]
        starts = {
            "easy":   [[1,2,3],[4,5,0],[7,8,6]],
            "medium": [[1,2,3],[4,0,6],[7,5,8]],
            "hard":   [[8,1,3],[4,0,2],[7,6,5]],
        }
        start = starts.get(difficulty)
        if not start: return

        for r in range(3):
            for c in range(3):
                self.start_entries[r][c].delete(0, tk.END)
                self.goal_entries[r][c].delete(0, tk.END)
                self.start_entries[r][c].insert(0, str(start[r][c]))
                self.goal_entries[r][c].insert(0, str(goal[r][c]))

        ss = ''.join(str(start[r][c]) for r in range(3) for c in range(3))
        gs = ''.join(str(goal[r][c])  for r in range(3) for c in range(3))
        self.start_str_entry.delete(0, tk.END); self.start_str_entry.insert(0, ss)
        self.goal_str_entry.delete(0, tk.END);  self.goal_str_entry.insert(0, gs)
        self._status(f"Loaded '{difficulty}' preset.")

    def _read_grid(self, entries):
        state, vals = [], set()
        for r in range(3):
            row = []
            for c in range(3):
                s = entries[r][c].get().strip()
                v = 0 if not s else int(s)
                if not (0 <= v <= 8):
                    return None, f"Value out of range at row {r+1}, col {c+1}."
                if v in vals:
                    return None, f"Duplicate value '{v}'."
                vals.add(v); row.append(v)
            state.append(tuple(row))
        if vals != set(range(9)):
            return None, "Must use all numbers 0–8 without repetition."
        return tuple(state), None

    def _flash_grid(self, entries):
        for row in entries:
            for e in row:
                e.configure(highlightbackground=C["s_err"])
        self.root.after(1800, lambda: [
            e.configure(highlightbackground=C["border"])
            for row in entries for e in row])

    # ───────────────────────────────────────────────────────────
    #  SOLVE
    # ───────────────────────────────────────────────────────────

    def solve_puzzle(self):
        if self._solving: return

        start, se = self._read_grid(self.start_entries)
        goal,  ge = self._read_grid(self.goal_entries)
        if se:
            self._flash_grid(self.start_entries)
            self._status(f"Input error: {se}", "s_err"); return
        if ge:
            self._flash_grid(self.goal_entries)
            self._status(f"Input error: {ge}", "s_err"); return

        self._solving = True
        self.solve_btn.configure(state=tk.DISABLED, text="Solving…")
        self.refresh_btn.configure(state=tk.DISABLED)
        for b in self.nav_btns.values():
            b.configure(state=tk.DISABLED)
        self._status("Solving — please wait…", "s_solving")
        self.root.update_idletasks()

        mx = int(self.max_nodes_var.get())

        def _run():
            p = Puzzle(start, goal)
            sol, nodes, tree = p.solve(mx)
            self.root.after(0, lambda: self._on_solved(p, sol, nodes, tree))

        threading.Thread(target=_run, daemon=True).start()

    def _on_solved(self, puzzle, sol, nodes, tree):
        self._solving = False
        self.solve_btn.configure(state=tk.NORMAL, text="▶  Solve Puzzle")

        if not sol:
            mx = int(self.max_nodes_var.get())
            self._status(f"No solution within {mx:,} nodes. Try increasing Max Nodes.", "s_err")
            messagebox.showinfo("No Solution",
                f"No solution found within {mx:,} nodes.\n"
                "Try increasing the Max Nodes slider.")
            return

        self.puzzle      = puzzle
        self.solution_path = sol
        self.tree_data   = tree
        self.current_step = 0
        self._prev_state = None

        self.stats_lbl.configure(
            text=f"Nodes Processed: {nodes:,}\nSolution Steps: {len(sol)}")
        self._status(f"✓ Solution found in {len(sol)} steps — {nodes:,} nodes processed.", "s_ok")

        self._update_display()
        self._update_nav()

        self.tree_vis = TreeVisualization(self.canvas, tree)
        self.tree_vis.compact = self.compact_var.get()
        sol_states = [s for s,_ in sol]
        self.sol_node_ids = [nd['id'] for nd in tree if nd['state'] in sol_states]
        self._draw_tree()
        self.refresh_btn.configure(state=tk.NORMAL)

    # ───────────────────────────────────────────────────────────
    #  SOLUTION DISPLAY
    # ───────────────────────────────────────────────────────────

    def _update_display(self):
        if not (0 <= self.current_step < len(self.solution_path)): return
        state, move = self.solution_path[self.current_step]

        for r in range(3):
            for c in range(3):
                v   = state[r][c]
                txt = str(v) if v != 0 else ""
                moved = False
                if self._prev_state and v != 0:
                    for pr in range(3):
                        for pc in range(3):
                            if self._prev_state[pr][pc]==v and (pr!=r or pc!=c):
                                moved = True
                if v == 0:      bg = C["tile_empty"]
                elif moved:     bg = C["tile_moved"]
                else:           bg = C["tile"]
                self.tile_labels[r][c].configure(text=txt, bg=bg,
                    highlightbackground=C["border"] if v!=0 else C["tile_empty"])

        self._prev_state = state
        n = len(self.solution_path)
        self.step_lbl.configure(text=f"Step  {self.current_step+1} / {n}")
        arrow = ARROWS.get(move, move)
        color = ARROW_C.get(move, C["t_primary"])
        self.move_lbl.configure(text=f"{arrow}  {move}", fg=color)

    def _update_nav(self):
        n   = len(self.solution_path)
        idx = self.current_step
        st  = tk.NORMAL if n > 0 else tk.DISABLED
        self.nav_btns["play"].configure(state=st)
        self.nav_btns["first"].configure(state=tk.NORMAL if idx>0    else tk.DISABLED)
        self.nav_btns["prev"].configure( state=tk.NORMAL if idx>0    else tk.DISABLED)
        self.nav_btns["next"].configure( state=tk.NORMAL if idx<n-1  else tk.DISABLED)
        self.nav_btns["last"].configure( state=tk.NORMAL if idx<n-1  else tk.DISABLED)

    def next_step(self):
        if self.current_step < len(self.solution_path)-1:
            self.current_step += 1
            self._update_display(); self._update_nav()

    def prev_step(self):
        if self.current_step > 0:
            self._prev_state = self.solution_path[self.current_step-2][0] if self.current_step>1 else None
            self.current_step -= 1
            self._update_display(); self._update_nav()

    def _go_first(self):
        self.current_step = 0; self._prev_state = None
        self._update_display(); self._update_nav()

    def _go_last(self):
        n = len(self.solution_path)
        if not n: return
        self.current_step = n-1
        self._prev_state = self.solution_path[n-2][0] if n>1 else None
        self._update_display(); self._update_nav()

    def toggle_play(self):
        if self._autoplay_job:
            self.root.after_cancel(self._autoplay_job)
            self._autoplay_job = None
            self.nav_btns["play"].configure(text="▶ Play", bg=C["btn_play"])
            self._status("Playback paused.")
        else:
            if self.current_step >= len(self.solution_path)-1:
                self._go_first()
            self.nav_btns["play"].configure(text="⏸ Pause", bg=C["btn_pause"])
            self._status("Playing solution…", "s_solving")
            self._autoplay_tick()

    def _autoplay_tick(self):
        if self.current_step < len(self.solution_path)-1:
            self.next_step()
            self._autoplay_job = self.root.after(int(self.speed_var.get()), self._autoplay_tick)
        else:
            self._autoplay_job = None
            self.nav_btns["play"].configure(text="▶ Play", bg=C["btn_play"])
            self._status("✓ Playback complete.", "s_ok")

    # ───────────────────────────────────────────────────────────
    #  TREE CONTROLS
    # ───────────────────────────────────────────────────────────

    def _draw_tree(self):
        if not self.tree_vis: return
        self.tree_vis.compact = self.compact_var.get()
        self.tree_vis.draw_tree(
            self.sol_node_ids,
            show_all  = self.show_all_var.get(),
            max_depth = int(self.depth_var.get()),
            max_width = int(self.width_var.get()))
        self.scale_factor = 1.0

    def refresh_tree(self):
        self._draw_tree()

    def zoom_in(self):
        if self.scale_factor < 4.0:
            self.scale_factor *= 1.25
            self.canvas.scale("all", 0, 0, 1.25, 1.25)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoom_out(self):
        if self.scale_factor > 0.25:
            self.scale_factor *= 0.8
            self.canvas.scale("all", 0, 0, 0.8, 0.8)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def reset_view(self):
        inv = 1.0 / self.scale_factor
        self.canvas.scale("all", 0, 0, inv, inv)
        self.scale_factor = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def mouse_zoom(self, event):
        if event.delta > 0: self.zoom_in()
        else: self.zoom_out()


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    try:
        style = ttk.Style(root)
        style.theme_use("clam")
    except Exception:
        pass

    app = PuzzleGUI(root)
    root.mainloop()