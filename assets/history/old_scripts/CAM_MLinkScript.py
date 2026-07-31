"""
CAM_MLinkScript

Author: Viktor Aleksandrovsky & ChatGPT
Version: 1.0.0
Name-US: CAM_MLinkScript
Description-US: Creates a top-level duplicate Active Cam and...
optionally adds an Xpresso setup with an Extend value for sensor-based render scaling.

Written for Maxon Cinema 4D R20+
Tested on R23
Python version: 3.7.7+

Usage:
1. Quickly duplicates the active camera to the top level. Useful when working with nested or heavy rigs,
especially for baking or using scripts that require a standalone camera.
2. Adds a custom Xpresso setup with an Extend parameter that increases the render area while preserving the camera's focal length.
This works in conjunction with an extended render setting and is useful for expanding the frame in post-production (e.g., in After Effects).

Change log:
1.0.5 (22.05.2025) - Initial version with camera duplication, Extend setup, and Xpresso rig generation.
"""

# Libraries
import c4d
import math
from c4d import gui

# Functions

def PrintNodePorts(node):
    print("Node ports: {} (ID: {node.GetType()})".format(node.GetName(), node.GetName()))
    for port in node.GetInPorts() + node.GetOutPorts():
        print("[{}] Name: {port.GetName()}, ID: {port.GetDescID()}".format('IN ' if port.GetIsInput() else 'OUT', 'IN ' if port.GetIsInput() else 'OUT'))

def FindDescIDByPortName(node, port_name):
    for port in node.GetInPorts() + node.GetOutPorts():
        if port.GetName() == port_name:
            return port.GetDescID()
    raise RuntimeError("Port with name '{}' not found.".format(port_name, port_name))

def AddUserData(obj, name, dtype, default_val=0.0):
    bc = c4d.GetCustomDatatypeDefault(dtype)
    bc[c4d.DESC_NAME] = name

    if dtype == c4d.DTYPE_LONG:
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_LONG

    element = obj.AddUserData(bc)
    obj[element] = default_val
    return element

def GetSceneCamera(doc):
    bd = doc.GetActiveBaseDraw()
    return bd.GetSceneCamera(doc) if bd else None

def GetLastObject(op):
    while op and op.GetNext():
        op = op.GetNext()
    return op

def GetAllObjects(op, result=None):
    if result is None:
        result = []
    while op:
        result.append(op)
        GetAllObjects(op.GetDown(), result)
        op = op.GetNext()
    return result

def GetUserDataDescIdByName(tag, name):
    for descid, bc in tag.GetUserDataContainer():
        if bc[c4d.DESC_NAME] == name:
            return descid
    raise RuntimeError("UserData '{}' not found.".format(name, name))

class ParentCamDialog(gui.GeDialog):

    ID_CHECK_XPRESSO = 1000
    ID_EXTEND_VALUE = 1001
    ID_DEL_RIG = 1002
    ID_CHECK_SOURCE_RES = 1003
    ID_CHECK_EXTEND_RES = 1004
    ID_OK = 2000
    ID_CANCEL = 2001

    def CreateLayout(self):

        self.SetTitle("CAM_MLink with Extend Value")
        
        # Informational header block
        self.GroupBegin(9000, c4d.BFH_SCALEFIT, 1, 3)
        self.AddStaticText(9001, c4d.BFH_LEFT, 0, 0, name=" ")
        self.AddStaticText(9002, c4d.BFH_LEFT, 0, 0, name=" Create copy ActiveCam based on CamMorph Tag")
        self.AddStaticText(9004, c4d.BFH_LEFT, 0, 0, name=" --------------------------  ")
        self.GroupEnd()




          # disable edit

        # Checkbox + text + value
        self.GroupBegin(5000, c4d.BFH_SCALEFIT, cols=3)
        self.AddCheckbox(self.ID_CHECK_XPRESSO, c4d.BFH_LEFT, 300, 12, name="Add xpTag with Extend Value")
        self.AddStaticText(-1, c4d.BFH_LEFT, 2, 12)  # spacing between checkbox and input field
        self.AddEditNumberArrows(self.ID_EXTEND_VALUE, c4d.BFH_LEFT, 60)
        self.GroupEnd()
        self.AddStaticText(9005, c4d.BFH_LEFT, 0, 0, name="⚠️ Create copy active RenderSetting w _Extnd mark")
        # Separator
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, name="")

        self.AddCheckbox(self.ID_DEL_RIG, c4d.BFH_LEFT, 400, 12, name="Delete Cam & Extend Render Settings")

        # Separator
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, name="")

        # Individual checkboxes
        self.AddCheckbox(self.ID_CHECK_SOURCE_RES, c4d.BFH_LEFT, 480, 12, name="Add [Origin Resolution] in XpressoTagParams")
        self.AddCheckbox(self.ID_CHECK_EXTEND_RES, c4d.BFH_LEFT, 480, 12, name="Add [Extend Resolution] in XpressoTagParams")

         # Separator
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, name="")

        #  OK and Cancel buttons
        self.GroupBegin(6000, c4d.BFH_CENTER, cols=2)
        self.AddButton(self.ID_OK, c4d.BFH_SCALE, name="OK")
        self.AddButton(self.ID_CANCEL, c4d.BFH_SCALE, name="Cancel")
        self.GroupEnd()

        return True

    def GetValues(self):
        return {
            "add_xpresso": self.GetBool(self.ID_CHECK_XPRESSO),
            "del_rig": self.GetBool(self.ID_DEL_RIG),
            "extend_value": self.GetInt32(self.ID_EXTEND_VALUE),
            "origin_res_checked": self.GetBool(self.ID_CHECK_SOURCE_RES),
            "extend_res_checked": self.GetBool(self.ID_CHECK_EXTEND_RES)
        }

    def Command(self, id, msg):
        if id == self.ID_EXTEND_VALUE:
            self.SetInt32(self.ID_EXTEND_VALUE, max(0, min(1000000, self.GetInt32(self.ID_EXTEND_VALUE))))

        if id == self.ID_OK:
            self.values = self.GetValues()
            self.Close()
        elif id == self.ID_CANCEL:
            self.Close()
        return True

def RemoveCameraRig(doc):
    doc.StartUndo()

    # Delete objects with name CAM_MLinkScript_
    def delete_objects_by_name(name):
        obj = doc.GetFirstObject()
        while obj:
            next_obj = obj.GetNext()  # Сохраняем следующий объект до удаления
            if obj.GetName() == name:
                doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                obj.Remove()
            obj = next_obj

    delete_objects_by_name("CAM_MLinkScript_")

    # Delete Render Settings with suffix _MLINK_EXTND
    rd = doc.GetFirstRenderData()
    while rd:
        next_rd = rd.GetNext()  # Сохраняем следующий перед возможным удалением
        if rd.GetName().endswith("_MLINK_EXTND"):
            doc.AddUndo(c4d.UNDOTYPE_DELETE, rd)
            rd.Remove()
        rd = next_rd

    doc.EndUndo()
    c4d.EventAdd()
    c4d.gui.MessageDialog("AllRigs & \nRender Settings with _EXTND\nSuccessfully deleted!!")


def CreateMorphCamera(doc):
    # Create MorphCam Section ----

    doc.StartUndo()
    active_cam = GetSceneCamera(doc)
    if not active_cam or active_cam.GetType() != c4d.Ocamera:
        c4d.gui.MessageDialog("Active Cam Not found")
        return

    temp_cam = c4d.BaseObject(c4d.Ocamera)
    temp_cam.SetName("CamBakeTemp")
    doc.AddUndo(c4d.UNDOTYPE_NEW, temp_cam)

    last = GetLastObject(doc.GetFirstObject())
    if last:
        temp_cam.InsertAfter(last)
    else:
        doc.InsertObject(temp_cam)

    c4d.EventAdd()

    active_cam.SetBit(c4d.BIT_ACTIVE)
    temp_cam.SetBit(c4d.BIT_ACTIVE)

    objects_before = GetAllObjects(doc.GetFirstObject())

    c4d.CallCommand(1027745)
    c4d.EventAdd()

    objects_after = GetAllObjects(doc.GetFirstObject())
    new_objects = [obj for obj in objects_after if obj not in objects_before]

    morph_cam = None
    morph_null = None

    for obj in new_objects:
        if obj.GetType() == c4d.Onull and "Camera Morph Setup" in obj.GetName():
            morph_null = obj
            child = obj.GetDown()
            if child and child.GetType() == c4d.Ocamera:
                morph_cam = child
                break

    if morph_cam:
        morph_cam.Remove()
        doc.InsertObject(morph_cam)
        morph_cam.SetName("CAM_MLinkScript_")
        c4d.EventAdd()

        if morph_null:
            doc.AddUndo(c4d.UNDOTYPE_DELETE, morph_null)
            morph_null.Remove()

    if temp_cam:
        doc.AddUndo(c4d.UNDOTYPE_DELETE, temp_cam)
        temp_cam.Remove()

    if morph_cam:
        morph_tag = morph_cam.GetTag(c4d.Tmorphcam)
        if morph_tag:
            bc = morph_tag.GetDataInstance()
            bc.SetBool(100202, False)

    doc.EndUndo()
    c4d.EventAdd()
    doc.SetActiveObject(morph_cam, c4d.SELECTION_NEW)

    bd = doc.GetActiveBaseDraw()
    bd.SetSceneCamera(morph_cam)
    c4d.EventAdd()

def CreateXpresso(doc,obj,ex_val,oe,ee):
    # Add XpressoTag with ExtendValue

    orig_exp_on = oe;
    ext_exp_on = ee;

    morph_cam = obj;
    c4d.StatusSetText("Create Xpresso Tag...")
    doc.StartUndo()

    xpresso_tag = c4d.BaseTag(c4d.Texpresso)
    xpresso_tag.SetName("xCalc_Sensor")
    morph_cam.InsertTag(xpresso_tag)
    doc.AddUndo(c4d.UNDOTYPE_NEW, xpresso_tag)

    extend_id = AddUserData(xpresso_tag, "Extend", c4d.DTYPE_LONG, 0)
    source_rs_id = AddUserData(xpresso_tag, "Source_RenderSetting", c4d.DTYPE_BASELISTLINK, None)
    extend_rs_id = AddUserData(xpresso_tag, "Extend_RenderSetting", c4d.DTYPE_BASELISTLINK, None)

    #Add Origin Resolution [Add Origin]
    if orig_exp_on:
        source_w_id = AddUserData(xpresso_tag, "Original Width", c4d.DTYPE_REAL, 0)
        source_h_id = AddUserData(xpresso_tag, "Original Height", c4d.DTYPE_REAL, 0)

    #Add Extend Resolution  [Add Extend]
    if ext_exp_on:
        extend_w_id = AddUserData(xpresso_tag, "Extend Width", c4d.DTYPE_REAL, 0)
        extend_h_id = AddUserData(xpresso_tag, "Extend Height", c4d.DTYPE_REAL, 0)

    active_rs = doc.GetActiveRenderData()
    if active_rs:
        xpresso_tag[source_rs_id] = active_rs
    else:
        c4d.gui.MessageDialog("Cannot get active RenderSetting")

    render_data = doc.GetActiveRenderData()

    #Create RenderSettings with _extend
    new_render_data = render_data.GetClone()
    new_render_data.SetName(render_data.GetName() + "_MLINK_EXTND")
    new_render_data[c4d.RDATA_LOCKRATIO] = True
    doc.InsertRenderData(new_render_data)
    doc.SetActiveRenderData(new_render_data)

    xpresso_tag[extend_rs_id] = doc.GetActiveRenderData()

    #UserInput
    xpresso_tag[extend_id] = ex_val

    doc.EndUndo()
    c4d.EventAdd()

    try:
        rs_id = GetUserDataDescIdByName(xpresso_tag, "Source_RenderSetting")
        ext_id = GetUserDataDescIdByName(xpresso_tag, "Extend")
    except RuntimeError as e:
        c4d.gui.MessageDialog(str(e))
        return

    nodemaster = xpresso_tag.GetNodeMaster()
    root = nodemaster.GetRoot()

    morph_tag = morph_cam.GetTag(c4d.Tmorphcam)

    morph_node = nodemaster.CreateNode(root, c4d.ID_OPERATOR_OBJECT, x=100, y=140)
    morph_node[c4d.GV_OBJECT_OBJECT_ID] = morph_tag
    desc_id = c4d.DescID(c4d.DescLevel(100009, c4d.DTYPE_BASELISTLINK, 1027743))
    morph_out = morph_node.AddPort(c4d.GV_PORT_OUTPUT, desc_id)

    tag_node = nodemaster.CreateNode(root, c4d.ID_OPERATOR_OBJECT, x=100, y=250)
    tag_node[c4d.GV_OBJECT_OBJECT_ID] = xpresso_tag

    rs_out = tag_node.AddPort(c4d.GV_PORT_OUTPUT, rs_id)
    rs_out.SetName("Source_RenderSetting")
    ext_out = tag_node.AddPort(c4d.GV_PORT_OUTPUT, ext_id)
    ext_out.SetName("Extend")

    py_node = nodemaster.CreateNode(root, 1022471, x=300, y=200)
    py_node[c4d.GV_PYTHON_CODE] = """
import math
import c4d

def main():
    global eSensor, eWidth, eHeight,sWidth,sHeight
    width = rendSetting[c4d.RDATA_XRES]
    height = rendSetting[c4d.RDATA_YRES]
    sensorIn = sensor[c4d.CAMERAOBJECT_APERTURE]

    if height == 0:
        new_sensor = sensorIn
    else:
        new_height = height + extendValue
        new_width = round(new_height * width / height)
        d0 = math.hypot(width, height)
        d1 = math.hypot(new_width, new_height)
        new_sensor = sensorIn * (d1 / d0)

    eSensor = round(new_sensor, 4)
    sWidth = width;
    sHeight = height;
    eWidth = new_width
    eHeight = new_height

"""
    for port in py_node.GetInPorts():
        py_node.RemovePort(port)

    port_out = py_node.GetOutPort(0)
    port_out.SetName("eSensor")

    longId = c4d.DescID(c4d.DescLevel(c4d.IN_LONG, c4d.ID_GV_DATA_TYPE_INTEGER,1022471))
    linkId = c4d.DescID(c4d.DescLevel(c4d.IN_LINK, c4d.DTYPE_BASELISTLINK,1022471))
    realIdOut = c4d.DescID(c4d.DescLevel(c4d.OUT_REAL, c4d.ID_GV_DATA_TYPE_REAL,1022471))

    port_sensor = py_node.AddPort(c4d.GV_PORT_INPUT, linkId)
    port_sensor.SetName("sensor")
    port_rendsetting = py_node.AddPort(c4d.GV_PORT_INPUT, linkId)
    port_rendsetting.SetName("rendSetting")
    port_extend = py_node.AddPort(c4d.GV_PORT_INPUT, longId)
    port_extend.SetName("extendValue")

    #Add Origin Resolution [Add Origin]
    port_or_width_ex = py_node.AddPort(c4d.GV_PORT_OUTPUT, realIdOut)
    port_or_width_ex.SetName("sWidth")
    port_or_height_ex = py_node.AddPort(c4d.GV_PORT_OUTPUT, realIdOut)
    port_or_height_ex.SetName("sHeight")

    #Add Extend Resolution [Add Extend]
    port_width_ex = py_node.AddPort(c4d.GV_PORT_OUTPUT, realIdOut)
    port_width_ex.SetName("eWidth")
    port_height_ex = py_node.AddPort(c4d.GV_PORT_OUTPUT, realIdOut)
    port_height_ex.SetName("eHeight")

    cam_node = nodemaster.CreateNode(root, c4d.ID_OPERATOR_OBJECT, x=500, y=140)
    cam_node[c4d.GV_OBJECT_OBJECT_ID] = morph_cam
    sensor_in = cam_node.AddPort(c4d.GV_PORT_INPUT, c4d.DescID(c4d.DescLevel(c4d.CAMERAOBJECT_APERTURE, c4d.DTYPE_REAL, c4d.Ocamera)))
    sensor_in.SetName("Sensor Size (Film Gate)")

    # Create Render Settings node
    ID_OPERATOR_RENDERS = 400001000
    GV_RENDERS_RENDATA = 1000
    GV_RENDERS_PARAMETER = 1001

    render_node = nodemaster.CreateNode(root, ID_OPERATOR_RENDERS, x=500, y=350)
    new_render_data = doc.GetActiveRenderData()
    render_node[GV_RENDERS_RENDATA] = new_render_data

    desc_id_width = c4d.DescID(c4d.DescLevel(c4d.RDATA_XRES, c4d.DTYPE_REAL, 0))
    desc_id_height = c4d.DescID(c4d.DescLevel(c4d.RDATA_YRES, c4d.DTYPE_REAL, 0))

    port_wdth = render_node.AddPort(c4d.GV_PORT_INPUT, desc_id_width)
    port_hgth = render_node.AddPort(c4d.GV_PORT_INPUT, desc_id_height)

    # only if one of the options [Add Origin]  или [Add Extend] включена
    if orig_exp_on or ext_exp_on:

        tag_node_exp = nodemaster.CreateNode(root, c4d.ID_OPERATOR_OBJECT, x=500, y=220)
        tag_node_exp[c4d.GV_OBJECT_OBJECT_ID] = xpresso_tag

        if orig_exp_on:
            orig_w_id = GetUserDataDescIdByName(xpresso_tag, "Original Width")
            orig_h_id = GetUserDataDescIdByName(xpresso_tag, "Original Height")

            orig_w_out = tag_node_exp.AddPort(c4d.GV_PORT_INPUT, orig_w_id)
            orig_w_out.SetName("Original Width")
            orig_h_out = tag_node_exp.AddPort(c4d.GV_PORT_INPUT, orig_h_id)
            orig_h_out.SetName("Original Height")

        if ext_exp_on:
            ext_w_id = GetUserDataDescIdByName(xpresso_tag, "Extend Width")
            ext_h_id = GetUserDataDescIdByName(xpresso_tag, "Extend Height")

            ext_w_out = tag_node_exp.AddPort(c4d.GV_PORT_INPUT, ext_w_id)
            ext_w_out.SetName("Extend Width")
            ext_h_out = tag_node_exp.AddPort(c4d.GV_PORT_INPUT, ext_h_id)
            ext_h_out.SetName("Extend Height")

    # Add General Connection
    morph_out.Connect(port_sensor)
    rs_out.Connect(port_rendsetting)
    ext_out.Connect(port_extend)
    port_out.Connect(sensor_in)

    port_width_ex.Connect(port_wdth)
    port_height_ex.Connect(port_hgth)

    # Add connection with extend resolution, [Add Extend] checkbox
    if ext_exp_on:
        port_width_ex.Connect(ext_w_out)
        port_height_ex.Connect(ext_h_out)

    # Add connection with extend resolution, [Add Origin] checkbox
    if orig_exp_on:
        port_or_width_ex.Connect(orig_w_out)
        port_or_height_ex.Connect(orig_h_out)

    c4d.EventAdd()
    c4d.gui.MessageDialog("CAM_MLinkScript_ with XTag added!")


if __name__ == '__main__':
    doc = c4d.documents.GetActiveDocument()

    dlg = ParentCamDialog()
    dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=320, defaulth=220)
    c4d.EventAdd()

    user_values = dlg.values

    delete_rig = user_values["del_rig"]

    if delete_rig:
        RemoveCameraRig(doc)


    if not delete_rig:
        CreateMorphCamera(doc)
        cam = GetSceneCamera(doc)

        tag = user_values["add_xpresso"]

        if tag:
            ex_val = user_values["extend_value"]
            orig = user_values["origin_res_checked"]
            extd = user_values["extend_res_checked"]
            CreateXpresso(doc,cam,ex_val,orig,extd)

