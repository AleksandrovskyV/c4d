import c4d, json, os

def main():
    project_path = doc.GetDocumentPath()
    file_path = os.path.join(project_path, "equirectangular.json")

    if not os.path.exists(file_path):
        c4d.gui.MessageDialog("File 'equirectangular.json' not found!")
        return

    try:
        with open(file_path, "r") as f:
            map_data = json.load(f)
    except Exception as e:
        c4d.gui.MessageDialog("Error read JSON: " + str(e))
        return

    root_null = c4d.BaseObject(c4d.Onull)
    root_null.SetName("IMPORTED_MAP_FINAL_CHECK")
    doc.InsertObject(root_null)

    for name, info in map_data.items():
        points_list = info.get("points", [])
        global_closed = info.get("closed", False)
        segments_list = info.get("segments", [])
        
        count = len(points_list)
        if count < 2:
            continue

        spline = c4d.SplineObject(count, c4d.SPLINETYPE_LINEAR)
        spline.SetName(name)
        
        vectors = [c4d.Vector(float(p[0]), float(p[1]), float(p[2])) for p in points_list]
        spline.SetAllPoints(vectors)
        spline[c4d.SPLINEOBJECT_CLOSED] = global_closed
        
        if segments_list:
            spline.ResizeObject(count, len(segments_list))
            for s, seg_info in enumerate(segments_list):
                spline.SetSegment(s, seg_info["cnt"], seg_info["closed"])
        
        spline.InsertUnderLast(root_null)
        spline.Message(c4d.MSG_UPDATE)

    c4d.EventAdd()
    c4d.gui.MessageDialog("Import Complete")

if __name__=='__main__':
    main()
