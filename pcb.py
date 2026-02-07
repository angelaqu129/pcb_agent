"This is for PCB layout work"
import pcbnew
import wx
app = wx.App(False)

KICAD_PYTHON = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
project_path = "/Users/adityarao/Documents/KiCad/9.0/projects/test/"
sch_path = project_path + "test.kicad_sch"
pcb_path = project_path + "test.kicad_pcb"
board = pcbnew.LoadBoard(pcb_path)
fp = board.FindFootprintByReference("R1")
fp.SetPos(pcbnew.VECTOR2I_MM(500, 500))
pcbnew.SaveBoard(pcb_path, board)

# use freerouting for auto routing
