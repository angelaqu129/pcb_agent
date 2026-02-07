from pathlib import Path
import json
import subprocess
import pcbnew
import wx
app = wx.App()


def place_footprints_from_schematic(board: pcbnew.BOARD, llm_output1: dict):
    """
    Place each footprint at the same position and rotation as in the schematic.
    llm_output1["symbols"] entries have ref_des and at: { x, y, rot } (mm and degrees).
    """
    ref_to_fp = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for sym in llm_output1.get("symbols", []):
        ref_des = sym.get("ref_des")
        at = sym.get("at")
        if not ref_des or not at:
            continue
        fp = ref_to_fp.get(ref_des)
        if fp is None:
            continue
        x_mm, y_mm = at.get("x", 0), at.get("y", 0)
        rot_deg = at.get("rot", 0)
        x_iu = pcbnew.FromMM(x_mm)
        y_iu = pcbnew.FromMM(y_mm)
        fp.SetPosition(pcbnew.VECTOR2I(int(x_iu), int(y_iu)))
        fp.SetOrientationDegrees(rot_deg)
    print("Placed footprints from schematic.")


def get_footprint_bounds(board: pcbnew.BOARD):
    min_x = min_y = None
    max_x = max_y = None

    for fp in board.GetFootprints():
        bbox = fp.GetBoundingBox()  # EDA_RECT in board coords

        if min_x is None:
            min_x = bbox.GetLeft()
            min_y = bbox.GetTop()
            max_x = bbox.GetRight()
            max_y = bbox.GetBottom()
        else:
            min_x = min(min_x, bbox.GetLeft())
            min_y = min(min_y, bbox.GetTop())
            max_x = max(max_x, bbox.GetRight())
            max_y = max(max_y, bbox.GetBottom())

    if min_x is None:
        raise RuntimeError("No footprints found on board")

    return min_x, min_y, max_x, max_y

def _rect_min_distance(left1, top1, right1, bottom1, left2, top2, right2, bottom2):
    """Minimum distance between two axis-aligned rectangles. 0 if overlapping."""
    gap_x = max(0, max(left1 - right2, left2 - right1))
    gap_y = max(0, max(top1 - bottom2, top2 - bottom1))
    if gap_x > 0 and gap_y > 0:
        return (gap_x ** 2 + gap_y ** 2) ** 0.5
    return max(gap_x, gap_y)


def relayout_footprints_min_spacing(board: pcbnew.BOARD, min_spacing_mm: float, max_iters: int = 50):
    """
    Re-position footprints so there is at least min_spacing_mm between every pair.
    Uses iterative separation: pairs closer than min_spacing are pushed apart.
    """
    min_spacing = pcbnew.FromMM(min_spacing_mm)
    footprints = list(board.GetFootprints())
    if len(footprints) < 2:
        return

    for _ in range(max_iters):
        moved = False
        for i in range(len(footprints)):
            for j in range(i + 1, len(footprints)):
                fp_i, fp_j = footprints[i], footprints[j]
                bbox_i = fp_i.GetBoundingBox()
                bbox_j = fp_j.GetBoundingBox()
                l1, t1 = bbox_i.GetLeft(), bbox_i.GetTop()
                r1, b1 = bbox_i.GetRight(), bbox_i.GetBottom()
                l2, t2 = bbox_j.GetLeft(), bbox_j.GetTop()
                r2, b2 = bbox_j.GetRight(), bbox_j.GetBottom()

                dist = _rect_min_distance(l1, t1, r1, b1, l2, t2, r2, b2)
                if dist >= min_spacing:
                    continue

                # Push apart along line between centers
                cx1 = (l1 + r1) // 2
                cy1 = (t1 + b1) // 2
                cx2 = (l2 + r2) // 2
                cy2 = (t2 + b2) // 2
                dx = cx1 - cx2
                dy = cy1 - cy2
                d = (dx * dx + dy * dy) ** 0.5
                if d <= 0:
                    d = 1
                    dx, dy = 1, 0
                push = min_spacing - dist
                ux = dx / d
                uy = dy / d
                half = push / 2

                pos_i = fp_i.GetPosition()
                pos_j = fp_j.GetPosition()
                fp_i.SetPosition(
                    pcbnew.VECTOR2I(
                        int(pos_i.x + half * ux),
                        int(pos_i.y + half * uy),
                    )
                )
                fp_j.SetPosition(
                    pcbnew.VECTOR2I(
                        int(pos_j.x - half * ux),
                        int(pos_j.y - half * uy),
                    )
                )
                moved = True
        if not moved:
            break
    print("Relayout with min spacing done.")


def expand_bounds(bounds, margin_mm: float):
    margin = pcbnew.FromMM(margin_mm)
    min_x, min_y, max_x, max_y = bounds
    return (min_x - margin, min_y - margin, max_x + margin, max_y + margin,)

def draw_edge_cuts_from_bounds(board: pcbnew.BOARD, bounds):
    min_x, min_y, max_x, max_y = bounds

    def line(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(x1, y1))
        s.SetEnd(pcbnew.VECTOR2I(x2, y2))
        board.Add(s)

    line(min_x, min_y, max_x, min_y)
    line(max_x, min_y, max_x, max_y)
    line(max_x, max_y, min_x, max_y)
    line(min_x, max_y, min_x, min_y)

def autoroute_with_freerouting(board: pcbnew.BOARD, project_dir: Path, timeout_sec: int = 300):
    dsn_path = project_dir / "board.dsn"
    ses_path = project_dir / "board.ses"

    pcbnew.ExportSpecctraDSN(board, str(dsn_path))

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_dir}:/work",
        "freerouting",
        "-de", "/work/board.dsn",
        "-do", "/work/board.ses",
        "-dr", "auto",
        "-mp", "8"
    ]

    print("Running freerouting...")
    result = subprocess.run(
        cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Freerouting failed")

    # 3. Import routes
    pcbnew.ImportSpecctraSES(board, str(ses_path))

    print("Routing imported successfully")


def main(project_path_str: str, llm_output1_path_arg: str | None = None):
    """Main function to process PCB layout. If llm_output1_path_arg is set and exists, place footprints from schematic; else relayout with min spacing."""
    project_path = Path(project_path_str)
    print("project_path:", project_path)
    # Find .kicad_pcb file in directory
    pcb_files = list(project_path.glob("*.kicad_pcb"))
    print(pcb_files)
    if not pcb_files:
        raise FileNotFoundError(f"No .kicad_pcb file found in {project_path}")
    
    pcb_path = pcb_files[0]
    print(f"Found PCB file: {pcb_path}")
    board = pcbnew.LoadBoard(str(pcb_path))

    llm_output1_path = llm_output1_path_arg if llm_output1_path_arg else None
    if llm_output1_path and Path(llm_output1_path).exists():
        with open(llm_output1_path, "r", encoding="utf-8") as f:
            llm_output1 = json.load(f)
        place_footprints_from_schematic(board, llm_output1)
    else:
        relayout_footprints_min_spacing(board, min_spacing_mm=2.0)

    bounds = get_footprint_bounds(board)
    print(bounds)
    bounds = expand_bounds(bounds, margin_mm=3.0)
    draw_edge_cuts_from_bounds(board, bounds)
    autoroute_with_freerouting(board=board, project_dir=project_path)
    pcbnew.SaveBoard(str(pcb_path), board)

if __name__ == "__main__":
    import sys
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    llm_output1_path = sys.argv[2] if len(sys.argv) > 2 else None
    main(project_path, llm_output1_path)
