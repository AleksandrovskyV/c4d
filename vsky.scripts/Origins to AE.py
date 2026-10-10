"""

Export Origins to After Effects

Author: Viktor Aleksandrovsky & Google AI & ChatGPT
Written & Tested for Maxon Cinema 4D R23
A swift kick from Sergio Gorleone

Description-US:Export selected as 2D layers to .jsx ae-script file|
Version: 0.3

"""

import c4d, os, sys, re
from c4d import storage
import codecs
IS_PY3 = sys.version_info >= (3, 0)

DEF_FILENAME="ae_origins"
UNIFORM_SCALE = 1.0
PANEL = None

def safe_open_json(path, mode='r'):
    #cyrillic safe and python 2\3
    if IS_PY3:
        return open(path, mode, encoding='utf-8')
    else:
        return codecs.open(path, mode, encoding='utf-8')

def ortho_cam_helper(proj, cam_matrix):
    print("current projection id:", proj)
    V = c4d.Vector

    ortho_presets = {
        c4d.Ptop:    (V(1, 0, 0),  V(0, 0, 1),  V(0, -1, 0)),
        c4d.Pbottom: (V(1, 0, 0),  V(0, 0, -1), V(0, 1, 0)),

        c4d.Pfront:  (V(1, 0, 0),  V(0, 1, 0),  V(0, 0, 1)),
        c4d.Pback:   (V(-1, 0, 0), V(0, 1, 0),  V(0, 0, -1)),

        c4d.Pleft:   (V(0, 0, 1),  V(0, 1, 0),  V(-1, 0, 0)),
        c4d.Pright:  (V(0, 0, -1), V(0, 1, 0),  V(1, 0, 0)),
    }

    if proj in ortho_presets:
        ortho_matrix = c4d.Matrix()
        ortho_matrix.v1, ortho_matrix.v2, ortho_matrix.v3 = ortho_presets[proj]
        return True, ortho_matrix

    elif proj == c4d.Pperspective:
        return False, _get_fitted_matrix(cam_matrix)

    return False, c4d.Matrix()

def walk_hierarchy(first_obj):
    """Итеративный обход всей сцены (вниз и вбок)"""
    if not first_obj: return
    stack = [(first_obj, True)]
    while stack:
        obj, allow_next = stack.pop()
        yield obj
        if obj.GetDown():
            stack.append((obj.GetDown(), True))
        if obj.GetNext() and allow_next:
            stack.append((obj.GetNext(), True))


def walk_selected_hierarchy(selected_objects):
    """Итеративный обход только выделенных веток"""
    if not selected_objects: return
    stack = [(obj, False) for obj in reversed(selected_objects)]
    while stack:
        obj, allow_next = stack.pop()
        yield obj
        if obj.GetDown():
            stack.append((obj.GetDown(), True))
        if obj.GetNext() and allow_next:
            stack.append((obj.GetNext(), True))


def get_objects():
    doc = c4d.documents.GetActiveDocument()
    selected = doc.GetActiveObjects(0)

    if selected:
        raw_stream = walk_selected_hierarchy(selected)
    else:
        raw_stream = walk_hierarchy(doc.GetFirstObject())

    colobjects = []
    seen_guids = set()

    for obj in raw_stream:
        if not obj: continue

        if obj.IsInstanceOf(c4d.Onull) or obj.IsInstanceOf(c4d.Opolygon):
            guid = obj.GetGUID()

            if guid not in seen_guids:
                seen_guids.add(guid)
                colobjects.append(obj)

    return colobjects


def _clean_layer_name(name):
    value = "".join(c for c in name if c.isalpha() or c.isdigit() or c in " _-").strip()
    return value or "layer"


def _hex_color(obj):
    try:
        color = obj[c4d.ID_BASEOBJECT_COLOR]
        values = [max(0, min(255, int(round(float(v) * 255.0))))
                  for v in (color.x, color.y, color.z)]
        return "#{:02x}{:02x}{:02x}".format(*values)
    except Exception:
        return "#b0b0b0"


def _jsx_string(value):
    import json
    return json.dumps(value, ensure_ascii=False)


def _get_render_resolution(doc):
    data = doc.GetActiveRenderData().GetData()
    return max(int(data.GetInt32(c4d.RDATA_XRES)), 1), max(int(data.GetInt32(c4d.RDATA_YRES)), 1)


def _camera_focal_aperture(camera):
    try: focal = float(camera[c4d.CAMERA_FOCUS])
    except Exception: focal = 36.0
    try: aperture = float(camera[c4d.CAMERAOBJECT_APERTURE])
    except Exception: aperture = 36.0
    return (focal if focal > 0 else 36.0), (aperture if aperture > 0 else 36.0)


def _matrix_position_ae(matrix):
    return [round(float(matrix.off.x) * UNIFORM_SCALE, 4),
            round(float(matrix.off.y) * -UNIFORM_SCALE, 4),
            round(float(matrix.off.z) * -UNIFORM_SCALE, 4)]


def _matrix_rotation_ae(matrix):
    try:
        hpb = matrix.GetHPB()
        k = 180.0 / 3.141592653589793
        return [round(float(hpb.x) * k, 4), round(float(hpb.y) * -k, 4), round(float(hpb.z) * -k, 4)]
    except Exception:
        return [0.0, 0.0, 0.0]


def _project_c4d_point(world_pos, camera_matrix, focal, aperture, res_x, res_y):
    cam_pos = world_pos * (~camera_matrix)
    # C4D camera forward is its local +Z axis, so visible points have
    # positive camera-space Z. Houdini's source projection used -Z.
    depth = float(cam_pos.z)
    if abs(depth) < 0.0001: depth = 0.0001
    fov_factor = focal / aperture
    # Cinema 4D's camera-space axes do not map to the screen the same way as
    # the Houdini projection convention used in the source exporter. Keep the
    # screen-space result explicitly as AE [x, y] pixels; do not swap the
    # resulting pixel coordinates. Correct depth/aspect are handled here.
    xp = (float(cam_pos.x) / depth) * fov_factor
    # Match the tested Houdini exporter: vertical projection includes aspect correction.
    yp = (float(cam_pos.y) / depth) * fov_factor * (float(res_x) / float(res_y))
    screen_x = (xp + 0.5) * res_x
    screen_y = (0.5 - yp) * res_y
    return [round(screen_x, 3), round(screen_y, 3)]


def _make_jsx(data, settings):
    import json
    data_js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    template = r"""(function () {
    app.beginUndoGroup("Cinema 4D Nulls Import");
    var data = __MAIN_DATA__;
    var asTextLayer = __AS_TEXT_FLAG__;
    var as2D = __AS_2D_FLAG__;
    var pasteExpression = __AS_PASTE_EXPR_FLAG__;
    var userScaleFactor = __SCALEFACTOR__;
    var textExpression = __TEXT_EXPR__;
    var currentScale = (10 * (data.width / 1280)) * userScaleFactor;
    if (!app.project) { alert("Open or create an After Effects project first."); app.endUndoGroup(); return; }
    var comp = app.project.items.addComp(data.compName, data.width, data.height, 1.0, data.duration, data.fps);
    function setKeys(prop, values) { for (var i = 0; i < values.length; i++) prop.setValueAtTime(i / data.fps, values[i]); }
    if (data.camera) {
        var cam = comp.layers.addCamera(data.cameraName, [data.width / 2, data.height / 2]);
        cam.name = data.cameraName;
        try { cam.property("Point of Interest").expression = "transform.position"; } catch (e) {}
        setKeys(cam.property("Position"), data.camera.position);
        var rx = [], ry = [], rz = [];
        for (var c = 0; c < data.camera.rotation.length; c++) {
            rx.push(data.camera.rotation[c][0]); ry.push(data.camera.rotation[c][1]); rz.push(data.camera.rotation[c][2]);
        }
        setKeys(cam.property("X Rotation"), rx); setKeys(cam.property("Y Rotation"), ry); setKeys(cam.property("Z Rotation"), rz);
        setKeys(cam.property("Zoom"), data.camera.zoom); setKeys(cam.property("Focus Distance"), data.camera.focus);
    }
    for (var pointName in data.points) {
        if (!data.points.hasOwnProperty(pointName)) continue;
        var item = data.points[pointName], layer;
        if (asTextLayer) {
            layer = comp.layers.addText(pointName);
            if (pasteExpression && textExpression !== "") {
                try { layer.property("Source Text").expression = textExpression; } catch (e) {}
            }
            try {
                var sourceText = layer.property("Source Text"), textDoc = sourceText.value;
                textDoc.applyFill = true; textDoc.fillColor = item.colorRGB; sourceText.setValue(textDoc);
            } catch (colorError) {}
            layer.property("Scale").setValue([currentScale, currentScale]);
        } else {
            layer = comp.layers.addNull(data.duration); layer.name = pointName;
        }
        layer.threeDLayer = !as2D;
        setKeys(layer.property("Position"), item.positions);
    }
    app.endUndoGroup();
    alert("Export complete: " + data.pointCount + " null(s).");
})();"""
    replacements = {
        "__MAIN_DATA__": data_js,
        "__AS_TEXT_FLAG__": "true" if settings["asText"] else "false",
        "__AS_2D_FLAG__": "true" if settings["as2D"] else "false",
        "__AS_PASTE_EXPR_FLAG__": "true" if settings["pasteExpression"] else "false",
        "__SCALEFACTOR__": str(float(settings["scalefactor"])),
        "__TEXT_EXPR__": _jsx_string(settings.get("textExpression", "")),
    }
    for key, value in replacements.items(): template = template.replace(key, value)
    return template


def run_main_logic(panel_data):
    """Sample nulls and camera over the selected frame range, then write JSX."""
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        c4d.gui.MessageDialog("No active Cinema 4D document.")
        return
    collected_obj = get_objects()
    if not collected_obj:
        c4d.gui.MessageDialog("Nothing objects!")
        return
    start_frame, end_frame = int(panel_data.get("startframe", 0)), int(panel_data.get("endframe", 90))
    fps = int(panel_data.get("fps", doc.GetFps()))
    if fps <= 0 or end_frame < start_frame:
        c4d.gui.MessageDialog("Invalid FPS or frame range.")
        return
    bd = doc.GetActiveBaseDraw()
    camera = None
    if bd:
        try: camera = bd.GetSceneCamera(doc) or bd.GetEditorCamera()
        except Exception: camera = None
    if camera is None:
        c4d.gui.MessageDialog("Could not find an active camera.")
        return
    try:
        width, height = _get_render_resolution(doc)
        focal, aperture = _camera_focal_aperture(camera)
        frames = list(range(start_frame, end_frame + 1))
        original_time = doc.GetTime()
        names, used = [], set()
        tracks = {}
        for obj in collected_obj:
            base = _clean_layer_name(obj.GetName())
            name, suffix = base, 1
            while name in used:
                name = "{}_{}".format(base, suffix); suffix += 1
            used.add(name); names.append(name)
            color = _hex_color(obj)
            rgb = [int(color[i:i+2], 16) / 255.0 for i in (1, 3, 5)]
            tracks[name] = {"positions": [], "color": color, "colorRGB": rgb}
        cam_pos, cam_rot, cam_zoom, cam_focus = [], [], [], []
        try:
            for frame in frames:
                # Timeline frames are defined by the Cinema 4D document FPS,
                # not necessarily by the export FPS selected in the dialog.
                doc.SetTime(c4d.BaseTime(frame, doc.GetFps()))
                # EventAdd() only refreshes the UI; force animation, expressions
                # and generators to evaluate before reading animated transforms.
                try:
                    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
                except Exception:
                    c4d.EventAdd()
                cm = camera.GetMg()
                cam_pos.append(_matrix_position_ae(cm))
                cam_rot.append(_matrix_rotation_ae(cm))
                cam_zoom.append(round(focal * width / aperture, 4))
                cam_focus.append(round(focal * UNIFORM_SCALE, 4))
                for obj, name in zip(collected_obj, names):
                    mg = obj.GetMg()
                    pos = _project_c4d_point(mg.off, cm, focal, aperture, width, height) if panel_data.get("as2D", True) else _matrix_position_ae(mg)
                    tracks[name]["positions"].append(pos)
        finally:
            doc.SetTime(original_time)
            c4d.EventAdd()
        output_path = panel_data.get("filepath", "").strip().strip('"')
        if output_path.startswith("$prj"):
            project_dir = doc.GetDocumentPath() or c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP)
            output_path = os.path.join(project_dir, output_path[4:].lstrip("/\\"))
        if not output_path:
            c4d.gui.MessageDialog("Please choose an output .jsx file.")
            return
        if not output_path.lower().endswith(".jsx"): output_path += ".jsx"
        data = {
            "pointCount": len(tracks), "fps": float(fps), "width": width, "height": height,
            "duration": float(len(frames)) / float(fps), "cameraName": camera.GetName(),
            "camera": {"position": cam_pos, "rotation": cam_rot, "zoom": cam_zoom, "focus": cam_focus},
            "points": tracks,
            "compName": os.path.splitext(os.path.basename(output_path))[0] or DEF_FILENAME,
        }
        folder = os.path.dirname(output_path)
        if folder and not os.path.isdir(folder): os.makedirs(folder)
        with safe_open_json(output_path, "w") as f: f.write(_make_jsx(data, panel_data))
        c4d.gui.MessageDialog("Successfully wrote JSX:\n{}".format(output_path))
        print("Exported {} objects, frames {}-{}, FPS {}".format(len(collected_obj), start_frame, end_frame, fps))
    except Exception as exc:
        c4d.gui.MessageDialog("Export error:\n{}".format(str(exc)))
        raise


class OptionsDialog(c4d.gui.GeDialog):

    ID_FILEPATH = 999
    ID_SELECT_FILEPATH_BTN = 1000

    ID_SCALE_FACTOR = 1002
    ID_FPS = 1003
    ID_FRAME_START = 1004
    ID_FRAME_END = 1005

    ID_AS_2D = 1006
    ID_AS_TEXT = 1007
    ID_PASTE_EXPRESSION = 1008
    ID_TEXT_EXPRESSION = 1009

    ID_CLOSE_BUTTON = 1010
    ID_EXPORT_BUTTON = 1011

    def __init__(self):
        super(OptionsDialog, self).__init__()

        doc = c4d.documents.GetActiveDocument()
        doc_fps = doc.GetFps() if doc else 24
        if doc:
            start_frame = doc.GetMinTime().GetFrame(doc_fps)
            end_frame = doc.GetMaxTime().GetFrame(doc_fps)
        else:
            start_frame = 1
            end_frame = 90

        self.data = {
            "filepath": "$prj/{}.jsx".format(DEF_FILENAME),
            "scalefactor": 1.0,
            "fps": doc_fps,
            "startframe": start_frame,
            "endframe": end_frame,
            "as2D": True,
            "asText": True,
            "pasteExpression": False,
            "textExpression": "thisLayer.name",
        }

    def CreateLayout(self):
        self.SetTitle("Export Origins to AE")

        self.GroupBegin(2000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupSpace(0, 10)
        self.GroupBorderSpace(14, 14, 14, 14)

        self.GroupBegin(2001, c4d.BFH_SCALEFIT, cols=1, rows=0)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Export selected as 2D layers ( text / null )")
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="* Write .jsx After Effects script file...")
        self.GroupEnd()

        self.GroupBegin(2002, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupSpace(5, 0)
        self.AddEditText(self.ID_FILEPATH, c4d.BFH_SCALEFIT, editflags=1)
        self.AddButton(self.ID_SELECT_FILEPATH_BTN, 0, name="...", initw=30)
        self.GroupEnd()

        self.GroupBegin(2003, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="Layers Scale Factor")
        self.AddEditNumberArrows(self.ID_SCALE_FACTOR, c4d.BFH_LEFT, initw=74)
        self.GroupEnd()

        self.GroupBegin(2004, c4d.BFH_SCALEFIT, cols=3, rows=1)
        self.GroupSpace(20, 0)


        self.GroupBegin(2005, c4d.BFH_SCALEFIT, cols=3, rows=1)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="With")
        self.AddEditNumberArrows(self.ID_FPS, c4d.BFH_SCALEFIT, initw=42)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name=" FPS  ")
        self.GroupEnd()

        self.GroupBegin(2006, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="   From")
        self.AddEditNumberArrows(self.ID_FRAME_START, c4d.BFH_SCALEFIT, initw=42)
        self.GroupEnd()

        self.GroupBegin(2007, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name="To")
        self.AddEditNumberArrows(self.ID_FRAME_END, c4d.BFH_SCALEFIT, initw=42)
        self.GroupEnd()


        self.GroupEnd()

        self.GroupBegin(2008, c4d.BFH_SCALEFIT, cols=4, rows=1)
        self.GroupSpace(10, 0)

        #self.AddCheckbox(self.ID_AS_2D, c4d.BFH_SCALEFIT, initw=0, inith=10, name="2D Layer")
        self.AddCheckbox(self.ID_AS_TEXT, c4d.BFH_SCALEFIT, initw=0, inith=10, name="Text Layer")
        self.AddCheckbox(self.ID_PASTE_EXPRESSION, c4d.BFH_SCALEFIT, initw=0, inith=10, name="Paste expression to Source Text?")
        self.AddStaticText(-1, c4d.BFH_LEFT, 0, 0, name=" ")
        self.GroupEnd()

        self.AddMultiLineEditText(self.ID_TEXT_EXPRESSION, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=100,
            inith=0
        )

        self.GroupBegin(2009, c4d.BFH_CENTER, cols=2, rows=1)
        #self.AddButton(self.ID_CLOSE_BUTTON, c4d.BFH_CENTER, initw=100, inith=20, name="close")
        self.AddButton(self.ID_EXPORT_BUTTON, c4d.BFH_CENTER, initw=100, inith=20, name="export")
        self.GroupEnd()

        self.GroupEnd()

        return True

    def InitValues(self):
        self.SetString(self.ID_FILEPATH, self.data["filepath"])

        self.SetFloat(
            self.ID_SCALE_FACTOR,
            self.data["scalefactor"],
            min=0.0,
            max=100.0,
            step=0.1,
            format=c4d.FORMAT_FLOAT
        )
        self.SetFloat(self.ID_FRAME_START, self.data["startframe"])
        self.SetFloat(self.ID_FRAME_END, self.data["endframe"])
        self.SetFloat(self.ID_FPS, self.data["fps"])
        self.SetBool(self.ID_AS_2D, self.data["as2D"])
        self.SetBool(self.ID_AS_TEXT, self.data["asText"])
        self.SetBool(self.ID_PASTE_EXPRESSION, self.data["pasteExpression"])
        self.SetString(self.ID_TEXT_EXPRESSION, self.data["textExpression"])

        return True

    def Command(self, id, msg):
        if id == self.ID_SELECT_FILEPATH_BTN:
            current_path = self.GetString(self.ID_FILEPATH).strip('"')

            if current_path.startswith("$prj") or not current_path:
                doc = c4d.documents.GetActiveDocument()
                target_dir = doc.GetDocumentPath() if doc else c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP)

                if not current_path:
                    base_name = "2D_nulls"
                else:
                    base_name = os.path.basename(current_path)
            else:
                target_dir = os.path.dirname(current_path)
                base_name = os.path.basename(current_path)

            if base_name.lower().endswith(".jsx"):
                base_name = base_name[:-4]

            clean_name = "".join([c for c in base_name if c.isalpha() or c.isdigit() or c in " _-"]).strip()

            filename = "{}.jsx".format(clean_name)
            filepath = os.path.join(target_dir, filename)

            if os.path.isfile(filepath):
                match = re.search(r'([_\-\s])?(\d+)$', clean_name)

                if match:
                    separator = match.group(1) if match.group(1) else "_"
                    num = int(match.group(2)) + 1
                    name_prefix = clean_name[:match.start()]

                    while True:
                        filename = "{}{}{}.jsx".format(name_prefix, separator, num)
                        if not os.path.isfile(os.path.join(target_dir, filename)):
                            break
                        num += 1
                else:
                    counter = 1
                    while True:
                        filename = "{}_{}.jsx".format(clean_name, counter)
                        if not os.path.isfile(os.path.join(target_dir, filename)):
                            break
                        counter += 1

            filepath = c4d.storage.SaveDialog(
                type=c4d.FILESELECTTYPE_ANYTHING,
                title="Save .jsx ae-script file",
                force_suffix="jsx",
                def_path=target_dir,
                def_file=filename
            )

            if filepath:
                self.SetString(self.ID_FILEPATH, filepath)
                self.data["filepath"] = filepath

            return True

        elif id == self.ID_FILEPATH:
            user_entered_path = self.GetString(self.ID_FILEPATH).strip('"')
            dir_name = os.path.dirname(user_entered_path)
            if os.path.isdir(dir_name):
                self.SetString(self.ID_FILEPATH, user_entered_path)
                self.data["filepath"] = user_entered_path
            else:
                c4d.gui.MessageDialog("Directory does not exist! Please use the '...' button.")
                self.SetString(self.ID_FILEPATH, self.data["filepath"])

            return True

        elif id == self.ID_EXPORT_BUTTON:
            self.data["filepath"] = self.GetString(self.ID_FILEPATH)

            self.data["scalefactor"] = self.GetFloat(self.ID_SCALE_FACTOR)
            self.data["startframe"] = self.GetInt32(self.ID_FRAME_START)
            self.data["endframe"] = self.GetInt32(self.ID_FRAME_END)
            self.data["fps"] = self.GetInt32(self.ID_FPS)
            self.data["as2D"] = self.GetBool(self.ID_AS_2D)
            self.data["asText"] = self.GetBool(self.ID_AS_TEXT)
            self.data["pasteExpression"] = self.GetBool(self.ID_PASTE_EXPRESSION)
            self.data["textExpression"] = self.GetString(self.ID_TEXT_EXPRESSION)


            run_main_logic(self.data)
            return True

        elif id == self.ID_CLOSE_BUTTON:
            self.Close()
            return True

        return True


def main():
    global PANEL
    PANEL = OptionsDialog()
    PANEL.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=100, defaulth=40)

if __name__ == '__main__':
    main()