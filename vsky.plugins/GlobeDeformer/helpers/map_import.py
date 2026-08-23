import c4d
import json
import os

def main():
    desktop_path = os.path.expanduser("~/Desktop")
    file_path = os.path.join(desktop_path, "equirectangular.json")

    if not os.path.exists(file_path):
        c4d.gui.MessageDialog("Файл 'equirectangular.json' не найден!")
        return

    try:
        with open(file_path, "r") as f:
            map_data = json.load(f)
    except Exception as e:
        c4d.gui.MessageDialog("Ошибка чтения JSON: " + str(e))
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

        # Создаем ОДИН сплайн, как в оригинале
        spline = c4d.SplineObject(count, c4d.SPLINETYPE_LINEAR)
        spline.SetName(name)
        
        # Заполняем его точки
        vectors = [c4d.Vector(float(p[0]), float(p[1]), float(p[2])) for p in points_list]
        spline.SetAllPoints(vectors)
        spline[c4d.SPLINEOBJECT_CLOSED] = global_closed
        
        # Если у оригинального сплайна были сегменты, восстанавливаем их в ядре C4D
        if segments_list:
            spline.ResizeObject(count, len(segments_list))
            for s, seg_info in enumerate(segments_list):
                spline.SetSegment(s, seg_info["cnt"], seg_info["closed"])
        
        spline.InsertUnderLast(root_null)
        spline.Message(c4d.MSG_UPDATE)

    c4d.EventAdd()
    c4d.gui.MessageDialog("Импорт структуры завершен!")

if __name__=='__main__':
    main()
