"""
Matrix Preserve

Author: Viktor Aleksandrovsky & Google
Written & Tested for Maxon Cinema 4D R23
"""

import c4d

CUBE_SIZE = 10
HIDE_MATRIX = 1

class OptionsDialog(c4d.gui.GeDialog):
    ID_CHECKBOX = 1001
    ID_BUTTON = 1002

    def __init__(self):
        super(OptionsDialog, self).__init__()
        self.one_mesh_value = True

    def CreateLayout(self):
        self.SetTitle("Matrix Preserve")

        self.AddCheckbox(self.ID_CHECKBOX, c4d.BFH_LEFT, initw=150, inith=10, name="One Mesh (with VertexColor)")
        self.SetBool(self.ID_CHECKBOX, True)
        self.AddButton(self.ID_BUTTON, c4d.BFH_CENTER, initw=100, inith=15, name="Preserve!")

        return True

    def Command(self, id, msg):
        if id == self.ID_BUTTON:
            self.one_mesh_value = self.GetBool(self.ID_CHECKBOX)
            self.Close()
            run_generator(self.one_mesh_value)
        return True

def run_generator(one_mesh_active):
    matrix_obj = doc.GetActiveObject()

    if not matrix_obj or matrix_obj.GetType() != 1018545:
        c4d.gui.MessageDialog("Select Matrix Object")
        return

    mo_data = c4d.modules.mograph.GeGetMoData(matrix_obj)
    if not mo_data:
        c4d.gui.MessageDialog("Fail get MoData.")
        return

    matrices = mo_data.GetArray(c4d.MODATA_MATRIX)
    colors = mo_data.GetArray(c4d.MODATA_COLOR)

    if not matrices:
        c4d.gui.MessageDialog("matrix without data")
        return

    doc.StartUndo()

    temp_doc = c4d.documents.BaseDocument() if one_mesh_active else None

    connect_obj = None
    parent_null = None

    if one_mesh_active:
        connect_obj = c4d.BaseObject(c4d.Oconnector)
        connect_obj[c4d.CONNECTOBJECT_WELD] = False
        temp_doc.InsertObject(connect_obj)
    else:
        parent_null = c4d.BaseObject(c4d.Onull)
        parent_null.SetName(f"{matrix_obj.GetName()} Preserve")
        doc.InsertObject(parent_null)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, parent_null)

    for i, matrix in enumerate(matrices):
        cube = c4d.BaseObject(c4d.Ocube)
        cube.SetName(f"Cube_{i}")
        cube[c4d.PRIM_CUBE_LEN] = c4d.Vector(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE)
        cube.SetMg(matrix_obj.GetMg() * matrix)

        if colors and i < len(colors):
            cube[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS
            cube[c4d.ID_BASEOBJECT_COLOR] = colors[i]

        if one_mesh_active:
            cube.InsertUnderLast(connect_obj)
        else:
            cube.InsertUnderLast(parent_null)
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, cube)

    if one_mesh_active and connect_obj:
        join_res = c4d.utils.SendModelingCommand(
            command=c4d.MCOMMAND_MAKEEDITABLE,
            list=[connect_obj],
            mode=c4d.MODELINGCOMMANDMODE_ALL,
            doc=temp_doc
        )

        if join_res and isinstance(join_res, list) and join_res:
            final_mesh = join_res[0]
            final_mesh.SetName(f"{matrix_obj.GetName()} Mesh")

            phong_tag = final_mesh.GetTag(c4d.Tphong)
            if phong_tag:
                phong_tag[c4d.PHONGTAG_PHONG_ANGLELIMIT] = True
                phong_tag[c4d.PHONGTAG_PHONG_ANGLE] = c4d.utils.Rad(40)

            if colors:
                point_count = final_mesh.GetPointCount()
                if point_count > 0:
                    vc_tag = c4d.VertexColorTag(point_count)
                    if vc_tag:
                        data_handle = vc_tag.GetDataAddressW()

                        for i in range(len(matrices)):
                            color_vector = colors[i] if i < len(colors) else c4d.Vector(1, 1, 1)

                            start_pt = i * 8
                            end_pt = start_pt + 8

                            for pt_idx in range(start_pt, min(end_pt, point_count)):
                                c4d.VertexColorTag.SetColor(data_handle, None, None, pt_idx, color_vector)

                        final_mesh.InsertTag(vc_tag)
                        doc.AddUndo(c4d.UNDOTYPE_NEW, vc_tag)
                        final_mesh.Message(c4d.MSG_UPDATE)

            doc.InsertObject(final_mesh)
            doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, final_mesh)
            temp_doc.Flush()

    if HIDE_MATRIX:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, matrix_obj)
        matrix_obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = c4d.OBJECT_OFF
        matrix_obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = c4d.OBJECT_OFF

    doc.EndUndo()
    c4d.EventAdd()

def main():
    dialog = OptionsDialog()
    dialog.Open(c4d.DLG_TYPE_MODAL, defaultw=220, defaulth=80)

if __name__ == '__main__':
    main()