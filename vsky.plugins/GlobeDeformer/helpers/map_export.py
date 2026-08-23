import c4d
import json
import os

def collect_splines(obj, splines_list):
    while obj:
        if obj.IsInstanceOf(c4d.Ospline):
            splines_list.append(obj)
        if obj.GetDown():
            collect_splines(obj.GetDown(), splines_list)
        obj = obj.GetNext()

def main():
    root = doc.GetActiveObject()
    if not root:
        c4d.gui.MessageDialog("Выделите оригинальный Null-объект вашей карты!")
        return

    all_splines = []
    collect_splines(root, all_splines)

    map_data = {}
    counter = 0

    for spline in all_splines:
        local_points = spline.GetAllPoints()
        if not local_points:
            continue
            
        mg = spline.GetMg()
        seg_count = spline.GetSegmentCount()
        global_closed = bool(spline[c4d.SPLINEOBJECT_CLOSED])
        
        # Переводим ВСЕ точки сплайна в мировые координаты
        world_points = []
        for p in local_points:
            wp = mg * p
            world_points.append([round(wp.x, 4), round(wp.y, 4), round(wp.z, 4)])
        
        # Собираем данные о внутренних сегментах C4D
        segments_data = []
        if seg_count > 0:
            for s in range(seg_count):
                seg_info = spline.GetSegment(s)
                segments_data.append({
                    "cnt": int(seg_info["cnt"]),
                    "closed": bool(seg_info["closed"])
                })

        unique_name = "{}_{}".format(spline.GetName(), counter)
        counter += 1
        
        map_data[unique_name] = {
            "closed": global_closed,
            "points": world_points,
            "segments": segments_data # Сохраняем родную структуру сегментов C4D
        }

    desktop_path = os.path.expanduser("~/Desktop")
    file_path = os.path.join(desktop_path, "equirectangular.json")

    with open(file_path, "w") as f:
        json.dump(map_data, f, indent=4)

    c4d.gui.MessageDialog("Успешно! Структурный JSON сохранен на Рабочий стол.")

if __name__=='__main__':
    main()
