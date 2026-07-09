"""

MP4 Vidoc

Author: Viktor Aleksandrovsky & Google AI
Thanks: Pepluum (for save this file)
Written & Tested for Maxon Cinema 4D R23

Description-US:LMB - active setting to PV  |  +  alt     -  viewport to PV  |  +  shift  -  viewport to BG  

LMB click - default mode
- source "Render Setting" write mp4 file in Picture Viewer

LMB click with [alt] - alt mode
- pure "Viewport Renderer" in Picture Viewer

LMB click with [shift] - silent mode
- pure "Viewport Renderer" in background process (open folder on complete)

"""

import c4d, os, re
DIALOG_ID = 1000123
present_mode = False

class PreviewDialog(c4d.gui.GeDialog):
    def __init__(self, select_mode=0):
        super(PreviewDialog, self).__init__()
        self.result = None
        self.mode = select_mode

    def CreateLayout(self):
        self.SetTitle("MP4 Vidoc \\ Setting")

        panel_width = 500
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, name="")

        if self.mode == 1:
            self.AddStaticText(596, c4d.BFH_LEFT, panel_width, 10, name='       AltMode :  Viewport Renderer')
            self.AddStaticText(597, c4d.BFH_SCALEFIT, panel_width, 2, name="")

        if self.mode == 2:
            self.AddStaticText(598, c4d.BFH_LEFT, panel_width, 10, name='       SilentMode :  Viewport Renderer')
            self.AddStaticText(599, c4d.BFH_SCALEFIT, panel_width, 2, name="")

        self.AddStaticText(600, c4d.BFH_LEFT, panel_width, 10, name='       Path :      .\\mp4_previews\\preview_#.mp4')
        self.AddStaticText(601, c4d.BFH_LEFT, panel_width, 10, name='       Alright ?')

        alt_space = 8 if (self.mode != 0) else 2

        self.AddStaticText(200, c4d.BFH_SCALEFIT, panel_width, alt_space, name="")
        self.GroupBegin(2000, c4d.BFH_CENTER, 2, 1)
        self.AddButton(1001, c4d.BFH_LEFT, 180, 20, name="Yes")
        self.AddButton(1002, c4d.BFH_LEFT, 180, 20, name="Custom")
        self.GroupEnd()
        self.AddStaticText(201, c4d.BFH_SCALEFIT, panel_width, 6, name="")

        return True

    def Command(self, id, msg):
        if id == 1001:
            self.result = "yes"
            self.Close()
        elif id == 1002:
            self.result = "custom"
            self.Close()
        return True

def get_next_index(directory, base_name, ext):
    if not os.path.exists(directory):
        return 1

    max_index = 0
    pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(ext)}$", re.IGNORECASE)

    try:
        for filename in os.listdir(directory):
            match = pattern.match(filename)
            if match:
                current_index = int(match.group(1))
                if current_index > max_index:
                    max_index = current_index
    except Exception:
        pass

    return max_index + 1

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return

    is_alt_pressed = False
    is_shift_pressed = False
    state = c4d.BaseContainer()

    if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_ALT, state):
        if state[c4d.BFM_INPUT_QUALIFIER] & c4d.QUALIFIER_ALT:
            is_alt_pressed = True

    if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_SHIFT, state):
        if state[c4d.BFM_INPUT_QUALIFIER] & c4d.QUALIFIER_SHIFT:
            is_shift_pressed = True

    target_setting_name = "mp4_preview"
    uniq_setting_name = "mp4_preview_temp"
    original_rdata = doc.GetActiveRenderData()
    root_rdata = doc.GetFirstRenderData()
    preview_rdata = None

    while root_rdata:
        if root_rdata.GetName() == target_setting_name:
            preview_rdata = root_rdata
            break
        root_rdata = root_rdata.GetNext()

    # silent render flag
    should_hide_pv = False
    if is_shift_pressed and preview_rdata is not None:
        should_hide_pv = True

    # create template render setting
    if not preview_rdata:

        mode_selection = 1 if (is_alt_pressed) else 0

        if is_shift_pressed:
            mode_selection = 2

        dialog = PreviewDialog(mode_selection)

        my_height = 150 if (is_alt_pressed or is_shift_pressed) else 100

        if not present_mode:
            dialog.Open(c4d.DLG_TYPE_MODAL, DIALOG_ID, defaultw=300, defaulth=100)
        else:
            dialog.Open(c4d.DLG_TYPE_MODAL, DIALOG_ID, xpos=130, ypos=290, defaultw=300, defaulth=my_height)

        if not dialog.result:
            return

        project_path = doc.GetDocumentPath()

        # copy source render settings and change preview and format params
        preview_rdata = original_rdata.GetClone()
        preview_rdata.SetName(target_setting_name)
        preview_rdata[c4d.RDATA_FORMAT] = c4d.FILTER_MOVIE # Format MP4
        preview_rdata[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_PREVIEWRANGE # Preview Range

        # Logic Path
        if dialog.result == "yes" and not project_path:
            c4d.gui.MessageDialog("untitled.c4d need set folder, sorry...")
            dialog.result = "custom"

        if dialog.result == "yes" and not project_path:
            c4d.gui.MessageDialog("project path undefined. Switching to custom setup.")
            dialog.result = "custom"

        if dialog.result == "yes":
            folder_path = os.path.join(project_path, "mp4_previews")
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            preview_rdata[c4d.RDATA_PATH] = os.path.join(folder_path, "preview")

        if dialog.result == "custom":
            custom_path = c4d.storage.SaveDialog(title="set mp4 preview folder", force_suffix="mp4")
            if not custom_path:
                return

            path_without_ext, _ = os.path.splitext(custom_path)
            preview_rdata[c4d.RDATA_PATH] = path_without_ext

        # send to end list
        last_rdata = doc.GetFirstRenderData()
        if last_rdata:
            while last_rdata.GetNext():
                last_rdata = last_rdata.GetNext()

            preview_rdata.InsertAfter(last_rdata)
        else:
            doc.InsertRenderData(preview_rdata)


    # TEMP RENDER SETTINGS
    render_target_rdata = preview_rdata

    if is_alt_pressed or is_shift_pressed:
        render_target_rdata = preview_rdata.GetClone()
        render_target_rdata.SetName(uniq_setting_name)
        render_target_rdata[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE

        vp = render_target_rdata.GetFirstVideoPost()
        viewport_vp = None
        while vp:
            if vp.GetType() == c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE:
                viewport_vp = vp
                break
            vp = vp.GetNext()

        if not viewport_vp:
            viewport_vp = c4d.documents.BaseVideoPost(c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE)
            if viewport_vp:
                render_target_rdata.InsertVideoPostLast(viewport_vp)

        if viewport_vp:
            viewport_vp[c4d.VP_PREVIEWHARDWARE_ONLY_GEOMETRY] = True
            command_data = {"id": c4d.DescID(c4d.DescLevel(c4d.VP_PREVIEWHARDWARE_COPY_VP_EFFECTS))}
            viewport_vp.Message(c4d.MSG_DESCRIPTION_COMMAND, command_data)

        doc.InsertRenderData(render_target_rdata)

    doc.SetActiveRenderData(render_target_rdata)
    full_path = render_target_rdata[c4d.RDATA_PATH]

    if not full_path:
        c4d.gui.MessageDialog(f"Save path in '{target_setting_name}' - empty!")
        doc.SetActiveRenderData(original_rdata)
        if is_alt_pressed or is_shift_pressed:
            render_target_rdata.Remove()
        return

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    base_name = re.sub(r'_\d+$', '', filename)
    ext = ".mp4"
    next_counter = get_next_index(directory, base_name, ext)
    render_target_rdata[c4d.RDATA_PATH] = os.path.join(directory, f"{base_name}_{next_counter}")

    # Select Rendering Pipeline
    if should_hide_pv:
        print("[MP4Vidoc] - Silent Render")

        active_bd = doc.GetActiveBaseDraw()
        active_camera = None
        if active_bd:
            active_camera = active_bd.GetSceneCamera(doc)
            if not active_camera:
                active_camera = active_bd.GetEditorCamera()

        unique_stage_name = "vidoc_temp_stage"
        stage_obj = c4d.BaseObject(c4d.Ostage)
        if stage_obj:
            stage_obj.SetName(unique_stage_name)
            doc.InsertObject(stage_obj)

            if active_camera:
                stage_obj[c4d.STAGEOBJECT_CLINK] = active_camera

        render_data_container = render_target_rdata.GetData()
        xres = int(render_data_container[c4d.RDATA_XRES])
        yres = int(render_data_container[c4d.RDATA_YRES])
        bmp = c4d.bitmaps.BaseBitmap()
        bmp.Init(xres, yres)
        render_flags = c4d.RENDERFLAGS_EXTERNAL

        import threading
        import time

        render_state = {
            "is_active": True,
            "progress": 0
        }

        def render_progress_hook(progress, progress_type):
            render_state["progress"] = int(progress * 100)

        def bg_render_worker():
            found_stage = doc.SearchObject(unique_stage_name)
            if found_stage:
                found_stage.Remove()
                c4d.EventAdd()

            found_uniq_rdata = doc.GetFirstRenderData()
            while found_uniq_rdata:
                if found_uniq_rdata.GetName() == uniq_setting_name:
                    found_uniq_rdata.Remove()
                    break
                found_uniq_rdata = found_uniq_rdata.GetNext()

            print("[MP4Vidoc] Render Started...")

            c4d.documents.RenderDocument(
                doc,
                render_data_container,
                bmp,
                render_flags,
                prog=render_progress_hook,
                wprog=None
            )

            print(f"[MP4Vidoc] {base_name}_{next_counter}{ext} - on disk!")
            c4d.EventAdd()

            if os.path.exists(directory):
                c4d.storage.ShowInFinder(directory)

            # Status Bar
            time.sleep(1.5)
            render_state["is_active"] = False

        def status_spammer_worker():
            while render_state["is_active"]:
                current_pct = render_state["progress"]
                #c4d.StatusSetBar(current_pct)
                c4d.StatusSetText(f"[MP4Vidoc] Rendering: {current_pct}%")
                time.sleep(0.025) 

            
            #c4d.StatusSetBar(100)
            c4d.StatusSetText("[MP4Vidoc] Render Complete!")
            
            time.sleep(5)
            c4d.StatusClear()

            
        # BG Render
        render_thread = threading.Thread(target=bg_render_worker)
        render_thread.daemon = True
        render_thread.start()

        # TextSpamer
        status_thread = threading.Thread(target=status_spammer_worker)
        status_thread.daemon = True
        status_thread.start()

        c4d.EventAdd()

    else:
        # default render (without shift)
        print("[MP4Vidoc] - Render to Picture Viewer")
        c4d.EventAdd()
        c4d.CallCommand(12099)

        # remove temp (if alt-mode)
        if is_alt_pressed:
            found_uniq_rdata = doc.GetFirstRenderData()
            while found_uniq_rdata:
                if found_uniq_rdata.GetName() == uniq_setting_name:
                    found_uniq_rdata.Remove()
                    break
                found_uniq_rdata = found_uniq_rdata.GetNext()

    # reback Source Render Settings
    doc.SetActiveRenderData(original_rdata)
    c4d.EventAdd()

if __name__ == '__main__':
    main()