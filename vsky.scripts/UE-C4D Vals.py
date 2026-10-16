"""

Description-US:Calc pos, rot between C4D><UE|
Written & Tested for Maxon Cinema 4D R23

Authors: MaxonSDK & Viktor Aleksandrovsky & Google_AI?
With a swift roll from Valdram Arispoga...

"""

import c4d, re, math
ON_MATRIX = False
def convert_matrix_logic(mode, data):
    if mode == "c4dtoue":
        mydata=convert_logic("c4dtoue",data)
    else:
        mydata=convert_logic("uetoc4d",data)

    return mydata

def convert_logic(mode, data):
    # mode:  "c4dtoue" or "uetoc4d"
    res = {"px": 0.0, "py": 0.0, "pz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}

    if mode == "c4dtoue": # res UE DATA from C4D

        res["px"] =  data["px"]
        res["py"] =  -data["pz"]
        res["pz"] =  data["py"]

        # Rotation # Source HPB > XZY > Mapping to Unreal
        rad_x = c4d.utils.Rad(data["rx"])
        rad_y = c4d.utils.Rad(data["ry"])
        rad_z = c4d.utils.Rad(data["rz"])

        angles_rad = c4d.Vector(rad_x,rad_y,rad_z)
        rot_matrix = c4d.utils.HPBToMatrix(angles_rad, order=c4d.ROTATIONORDER_DEFAULT )
        converted_rad = c4d.utils.MatrixToHPB(rot_matrix, order= c4d.ROTATIONORDER_XZYGLOBAL )

        res["rx"] =  c4d.utils.Deg(converted_rad.x)
        
        res["ry"] = -c4d.utils.Deg(converted_rad.z)
        res["rz"] = -c4d.utils.Deg(converted_rad.y)

    else: # == 2: res C4D from UE DATA
        res["px"] =  data["px"]

        res["py"] =  data["pz"]
        res["pz"] =  -data["py"]

        # Rotation # Source XYZ > UE_COR > XYZ > HPB 
        x_deg = data["rx"]

        z_deg = -data["ry"]
        y_deg = -data["rz"]
        
        angles_rad = c4d.Vector(
            c4d.utils.Rad(x_deg),
            c4d.utils.Rad(y_deg),
            c4d.utils.Rad(z_deg)
        )
        print(x_deg,y_deg, z_deg)
        rot_matrix = c4d.utils.HPBToMatrix(angles_rad, order=c4d.ROTATIONORDER_XZYGLOBAL)
        converted_rad = c4d.utils.MatrixToHPB(rot_matrix, order=c4d.ROTATIONORDER_DEFAULT)

        res["rx"] = c4d.utils.Deg(converted_rad.x)
        res["ry"] = c4d.utils.Deg(converted_rad.y)
        res["rz"] = c4d.utils.Deg(converted_rad.z)

    # Cutting value *symbols,
    for key in res:
        res[key] = round(res[key], 8)

    return res

PANEL = None
class OptionsDialog(c4d.gui.GeDialog):

    ID_TO_UE_BTN = 501
    ID_TO_CD_BTN = 502

    ID_CD_PX = 1001
    ID_CD_PY = 1002
    ID_CD_PZ = 1003
    ID_CD_RX = 1004
    ID_CD_RY = 1005
    ID_CD_RZ = 1006

    ID_UE_PX = 1101
    ID_UE_PY = 1102
    ID_UE_PZ = 1103
    ID_UE_RX = 1104
    ID_UE_RY = 1105
    ID_UE_RZ = 1106

    def __init__(self):
        super(OptionsDialog, self).__init__()

        self.c4d_data = {
            "px": 0.0,"py": 0.0,"pz": 0.0,
            "rx": 0.0,"ry": 0.0,"rz": 0.0,
        }

        self.ue_data = {
            "px": 0.0,"py": 0.0,"pz": 0.0,
            "rx": 0.0,"ry": 0.0,"rz": 0.0,
        }

    def CreateLayout(self):
        self.SetTitle("c4d-ue-values")

        # globe start
        self.GroupBegin(2000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupSpace(0, 0)
        self.GroupBorderSpace(14, 14, 14, 14)


        #self.GroupBegin(2001, c4d.BFH_SCALEFIT, cols=3, rows=1)
        #self.AddStaticText(-1, c4d.BFH_SCALEFIT, 0, 0, name="")
        #self.AddStaticText(-1, c4d.BFH_CENTER, 0, 0, name="Values Convert")
        #self.AddStaticText(-1, c4d.BFH_SCALEFIT, 0, 0, name="")
        #self.GroupEnd()

        # main start
        self.GroupBegin(2002, c4d.BFH_SCALEFIT, cols=3, rows=1)
        self.GroupSpace(12, 0)

        # 1
        ws = 280

        self.GroupBegin(2003, c4d.BFH_SCALEFIT, cols=1, rows=5)

        self.GroupBegin(2004, c4d.BFH_SCALEFIT, cols=3, rows=0)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Cinema 4D")
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, 0, 0, name="")
        self.AddButton(self.ID_TO_UE_BTN, c4d.BFH_RIGHT, initw=32, name=" > ")
        self.GroupEnd()

        self.AddSeparatorH(inith=1)

        self.GroupBegin(2005, c4d.BFH_SCALEFIT, cols=2, rows=6)
        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="P . X  ")

        self.AddEditNumberArrows(self.ID_CD_PX, c4d.BFH_SCALEFIT, initw=ws)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="P . Y  ")
        self.AddEditNumberArrows(self.ID_CD_PY, c4d.BFH_SCALEFIT, initw=ws)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="P . Z  ")
        self.AddEditNumberArrows(self.ID_CD_PZ, c4d.BFH_SCALEFIT, initw=ws)
        self.GroupEnd()

        self.AddSeparatorH(inith=1)
        self.GroupBegin(2006, c4d.BFH_SCALEFIT, cols=2, rows=6)
        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 0)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="R . H  ")
        self.AddEditNumberArrows(self.ID_CD_RX, c4d.BFH_SCALEFIT, initw=ws)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="R . P  ")
        self.AddEditNumberArrows(self.ID_CD_RY, c4d.BFH_SCALEFIT, initw=ws)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="R . B  ")
        self.AddEditNumberArrows(self.ID_CD_RZ, c4d.BFH_SCALEFIT, initw=ws)
        self.GroupEnd()

        self.GroupEnd()


        # 2
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)


        # 3
        wsu = 64
        self.GroupBegin(2007, c4d.BFV_SCALEFIT, cols=1, rows=4)

        self.GroupBegin(2008, c4d.BFH_SCALEFIT, cols=3, rows=0)
        self.AddButton(self.ID_TO_CD_BTN, c4d.BFH_LEFT, initw=32,  name=" < ")
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="  ")
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Unreal Engine")
        self.GroupEnd()

        self.AddSeparatorH(inith=1)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Location")

        self.GroupBegin(2009, c4d.BFH_SCALEFIT, cols=6, rows=0)
        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 5)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="X ")
        self.AddEditNumberArrows(self.ID_UE_PX, c4d.BFH_SCALEFIT, initw=wsu)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="   Y ")
        self.AddEditNumberArrows(self.ID_UE_PY, c4d.BFH_SCALEFIT, initw=wsu)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="   Z ")
        self.AddEditNumberArrows(self.ID_UE_PZ, c4d.BFH_SCALEFIT, initw=wsu)
        self.GroupEnd()

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="")
        self.AddSeparatorH(inith=1)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Rotation")

        self.GroupBegin(2010, c4d.BFH_SCALEFIT, cols=6, rows=0)
        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="X ")
        self.AddEditNumberArrows(self.ID_UE_RX, c4d.BFH_SCALEFIT, initw=wsu)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="   Y ")
        self.AddEditNumberArrows(self.ID_UE_RY, c4d.BFH_SCALEFIT, initw=wsu)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="   Z ")
        self.AddEditNumberArrows(self.ID_UE_RZ, c4d.BFH_SCALEFIT, initw=wsu)

        self.GroupEnd()

        self.AddStaticText(-1, c4d.BFH_SCALEFIT, 0, 0, name="")


        self.GroupEnd()

        # main end
        self.GroupEnd()


        # globe close
        self.GroupEnd()

        return True


    def fill_vals_data(self, mode=0): # 0-both, 1-ue, 2-c4d
        datasets = []
        if mode == 0 or mode == 2:
            datasets.append((1000, self.c4d_data))
        if mode == 0 or mode == 1:
            datasets.append((1100, self.ue_data))

        axes = ["x", "y", "z"]

        for base_id, data in datasets:
            # 2. Pos (PX, PY, PZ)
            for i, axis in enumerate(axes, start=1):
                field_id = base_id + i
                val = data.get("p{}".format(axis), 0.0)
                self.SetFloat(field_id, val, step=0.1, format=c4d.FORMAT_FLOAT)

            # 2. Angles (RX, RY, RZ) -> offset +4, +5, +6
            step_one_degree = c4d.utils.Rad(1.0)
            for i, axis in enumerate(axes, start=4):
                field_id = base_id + i
                val = data.get("r{}".format(axis), 0.0)
                rad_val = c4d.utils.Rad(val)
                self.SetFloat(field_id, rad_val, step=step_one_degree, format=c4d.FORMAT_DEGREE)

    def read_vals_from_gui(self):
        datasets = [
            (1000, self.c4d_data),
            (1100, self.ue_data)
        ]

        axes = ["x", "y", "z"]

        for base_id, data in datasets:
            for i, axis in enumerate(axes, start=1):
                field_id = base_id + i
                data["p{}".format(axis)] = self.GetFloat(field_id)

            for i, axis in enumerate(axes, start=4):
                field_id = base_id + i
                rad_val = self.GetFloat(field_id)
                data["r{}".format(axis)] = c4d.utils.Deg(rad_val)


    def InitValues(self):
        self.fill_vals_data(0)
        return True

    def Command(self, id, msg):
        if id == self.ID_TO_UE_BTN or id == self.ID_TO_CD_BTN:

            if id == self.ID_TO_UE_BTN:
                self.read_vals_from_gui()

                if ON_MATRIX:
                    self.ue_data = convert_matrix_logic("c4dtoue", self.c4d_data) # 1 c4d-to-ue, 2 ue-to-c4d
                else:
                    self.ue_data = convert_logic("c4dtoue", self.c4d_data) # 1 c4d-to-ue, 2 ue-to-c4d


                self.fill_vals_data(1)

            elif id == self.ID_TO_CD_BTN:
                self.read_vals_from_gui()

                if ON_MATRIX:
                    self.c4d_data = convert_matrix_logic("uetoc4d", self.ue_data) # 1 c4d-to-ue, 2 ue-to-c4d
                else:
                    self.c4d_data = convert_logic("uetoc4d", self.ue_data) # 1 c4d-to-ue, 2 ue-to-c4d

                self.fill_vals_data(2)

            return True

        return True


def main():
    global PANEL
    PANEL = OptionsDialog()
    PANEL.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=100, defaulth=40)

if __name__ == '__main__':
    main()