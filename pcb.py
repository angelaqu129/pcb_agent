from pathlib import Path
import subprocess
import pcbnew
import wx
app = wx.App()

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

def autoroute_with_freerouting(board: pcbnew.BOARD, project_dir: Path, freerouting_jar: Path, timeout_sec: int = 300):
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

KICAD_PYTHON = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
project_path = Path("/Users/adityarao/Documents/KiCad/9.0/projects/test/")
sch_path = project_path / "test.kicad_sch"
pcb_path = project_path / "test.kicad_pcb"
freerouting_jar = Path("/Users/adityarao/code/kicad-test/freerouting-1.9.0.jar")
board = pcbnew.LoadBoard(str(pcb_path))

bounds = get_footprint_bounds(board)
print(bounds)
bounds = expand_bounds(bounds, margin_mm=3.0)
draw_edge_cuts_from_bounds(board, bounds)
autoroute_with_freerouting(board=board, project_dir=project_path, freerouting_jar=freerouting_jar)
pcbnew.SaveBoard(str(pcb_path), board)
