"""
Globe Deformer

Author: Viktor Aleksandrovsky & Google AI
Written & Tested for Maxon Cinema 4D R19
"""

import c4d
import math
PLUGIN_ID = 1063489 
FIT_CENTER_ID = 1023

# ========================================================
# Добавить Draw Guide Map
# Добавить иконку
# ========================================================

class GlobeDeformer(c4d.plugins.ObjectData):
    
    def Init(self, node):
        data = node.GetDataInstance()
        data.SetLong(999, 0)       # Mode
        data.SetLong(1000, 0)      # Плоскость
        data.SetFloat(1020, 400.0) # Заглушки ползунков
        data.SetFloat(1021, 400.0) 
        data.SetFloat(1001, 1.0)   # Множитель размера глобуса
        data.SetFloat(1004, 1.0)   # Сжатие к экватору
        data.SetFloat(1002, 1.0)   # Сила деформации
        return True

    def CalculateHierarchyBBox(self, root_obj, mod_mg):
        bounds = {
            "min_x": 999999999.0,
            "min_y": 999999999.0,
            "min_z": 999999999.0,
            "max_x": -999999999.0,
            "max_y": -999999999.0,
            "max_z": -999999999.0,
            "has_geometry": False
        }

        def add_point(p):
            bounds["min_x"] = min(bounds["min_x"], p.x)
            bounds["min_y"] = min(bounds["min_y"], p.y)
            bounds["min_z"] = min(bounds["min_z"], p.z)

            bounds["max_x"] = max(bounds["max_x"], p.x)
            bounds["max_y"] = max(bounds["max_y"], p.y)
            bounds["max_z"] = max(bounds["max_z"], p.z)

            bounds["has_geometry"] = True

        def add_object_bbox(obj):
            rad = obj.GetRad()
            mp = obj.GetMp()

            if rad.x <= 0.0 and rad.y <= 0.0 and rad.z <= 0.0:
                return

            obj_to_mod = ~mod_mg * obj.GetMg()

            # Все 8 углов локального bounding box.
            for sx in (-1.0, 1.0):
                for sy in (-1.0, 1.0):
                    for sz in (-1.0, 1.0):
                        local_p = mp + c4d.Vector(
                            rad.x * sx,
                            rad.y * sy,
                            rad.z * sz
                        )

                        add_point(obj_to_mod * local_p)

        def walk(obj):
            if obj is None:
                return

            # Сначала пробуем сам объект.
            add_object_bbox(obj)

            # Затем его cache.
            cache = obj.GetCache()

            if cache:
                walk_cache(cache, mod_mg)

            # И deformation cache.
            deform_cache = obj.GetDeformCache()

            if deform_cache and deform_cache != cache:
                walk_cache(deform_cache, mod_mg)

            # Дети исходной иерархии.
            child = obj.GetDown()

            while child:
                walk(child)
                child = child.GetNext()

        def walk_cache(obj, matrix):
            if obj is None:
                return

            add_object_bbox(obj)

            child = obj.GetDown()

            while child:
                walk_cache(child, matrix)
                child = child.GetNext()

        walk(root_obj)

        if not bounds["has_geometry"]:
            return None

        w_size = bounds["max_x"] - bounds["min_x"]
        h_size = bounds["max_y"] - bounds["min_y"]
        d_size = bounds["max_z"] - bounds["min_z"]

        hierarchy_size = c4d.Vector(
            w_size,
            h_size,
            d_size
        )

        center = c4d.Vector(
            (bounds["min_x"] + bounds["max_x"]) * 0.5,
            (bounds["min_y"] + bounds["max_y"]) * 0.5,
            (bounds["min_z"] + bounds["max_z"]) * 0.5
        )

        return hierarchy_size, center

    def Draw(self, op, drawpass, bd, bh):
        # Рисуем guide только один раз — в Object pass.
        if drawpass != c4d.DRAWPASS_OBJECT:
            return c4d.DRAWRESULT_SKIP

        if op is None or bd is None:
            return c4d.DRAWRESULT_SKIP

        data = op.GetDataInstance()

        w_size = data.GetFloat(1020)
        h_size = data.GetFloat(1021)
        axis_mode = data.GetLong(1000)

        if w_size <= 0.0 or h_size <= 0.0:
            return c4d.DRAWRESULT_SKIP

        hw = w_size * 0.5
        hh = h_size * 0.5

        # Прямоугольник в локальной системе координат деформера.
        if axis_mode == 0:          # XY
            points = [
                c4d.Vector(-hw, -hh, 0.0),
                c4d.Vector( hw, -hh, 0.0),
                c4d.Vector( hw,  hh, 0.0),
                c4d.Vector(-hw,  hh, 0.0)
            ]

        elif axis_mode == 1:        # XZ
            points = [
                c4d.Vector(-hw, 0.0, -hh),
                c4d.Vector( hw, 0.0, -hh),
                c4d.Vector( hw, 0.0,  hh),
                c4d.Vector(-hw, 0.0,  hh)
            ]

        else:                       # ZY
            points = [
                c4d.Vector(0.0, -hh, -hw),
                c4d.Vector(0.0, -hh,  hw),
                c4d.Vector(0.0,  hh,  hw),
                c4d.Vector(0.0,  hh, -hw)
            ]

        # Локальные координаты -> координаты деформера.
        bd.SetMatrix_Matrix(op, op.GetMg())

        # Для проверки задаём заведомо заметный цвет.
        bd.SetPen(c4d.Vector(1.0, 1.0, 0.0), 0)

        bd.DrawLine(points[0], points[1], c4d.NOCLIP_D)
        bd.DrawLine(points[1], points[2], c4d.NOCLIP_D)
        bd.DrawLine(points[2], points[3], c4d.NOCLIP_D)
        bd.DrawLine(points[3], points[0], c4d.NOCLIP_D)

        return c4d.DRAWRESULT_OK

    def Message(self, node, type, data):
        if type == c4d.MSG_DESCRIPTION_COMMAND:
            if data is not None:
                desc_id = data.get("id")

                if desc_id is not None:
                    print("BUTTON:", desc_id[0].id)

                    if desc_id[0].id == 1022:
                        print("FIT TO OBJECT")

                        result = self.FitToObject(node)
                        print("FIT RESULT:", result)

                        node.SetDirty(c4d.DIRTYFLAGS_DATA)
                        c4d.EventAdd()

                        return True

        return True

    def FitToObject(self, op):
        data = op.GetDataInstance()
        target = op.GetUp()

        #print("FIT TARGET:", target)
        #print("FIT TARGET TYPE:", target.GetType() if target else None)

        if target is None:
            return False

        mod_mg = op.GetMg()
        bbox_data = self.CalculateHierarchyBBox(target, mod_mg)

        if bbox_data is None:
            return False

        hierarchy_size, center = bbox_data
        axis_mode = data.GetLong(1000)

        if axis_mode == 0:          # XY
            w_size = float(hierarchy_size.x)
            h_size = float(hierarchy_size.y)

        elif axis_mode == 1:        # XZ
            w_size = float(hierarchy_size.x)
            h_size = float(hierarchy_size.z)

        else:                       # ZY
            w_size = float(hierarchy_size.z)
            h_size = float(hierarchy_size.y)

        if w_size <= 0.0:
            w_size = 1.0

        if h_size <= 0.0:
            h_size = 1.0

        # Set Parameter
        data.SetFloat(1020, w_size)
        data.SetFloat(1021, h_size)

        # Reset Position
        new_ml = c4d.Matrix() 
        new_ml.off = c4d.Vector(0)
        op.SetMl(new_ml)

        op.SetDirty(c4d.DIRTYFLAGS_DATA | c4d.DIRTYFLAGS_MATRIX)
        c4d.EventAdd() 
        return True


    def ModifyObject(self, mod, doc, op, op_mg, mod_mg, lod, flags, thread):
        if op is None or mod is None:
            return True

        is_polygon = op.IsInstanceOf(c4d.Opolygon)
        is_spline = (op.GetType() == 5137) or op.IsInstanceOf(c4d.Ospline) or (op.GetType() == 5138)

        if not is_polygon and not is_spline:
            return True

        data = mod.GetDataInstance()
        main_mode = data.GetLong(999) 
        strength = data.GetFloat(1002)

        if strength <= 0.0: 
            return True

        points = op.GetAllPoints()
        if not points or len(points) == 0: 
            return True

        w_size = data.GetFloat(1020)
        h_size = data.GetFloat(1021)
        center = c4d.Vector(0.0)

        if w_size <= 0.0: w_size = 1.0
        if h_size <= 0.0: h_size = 1.0

        to_mod_space = ~mod_mg * op_mg
        to_op_space = ~op_mg * mod_mg

        # БЛОК 1: 3D GLOBe (MODE 0 и 1)
        if main_mode == 0 or main_mode == 1:
            axis_mode = data.GetLong(1000)
            radius_mult = data.GetFloat(1001)
            lat_scale = data.GetFloat(1004)

            RADIUS = (w_size / (2.0 * math.pi)) * radius_mult

            for i in range(len(points)):
                p = to_mod_space * points[i]
                
                if axis_mode == 0:   u, v = (p.x - center.x) / w_size, (p.y - center.y) / h_size
                elif axis_mode == 1: u, v = (p.x - center.x) / w_size, (p.z - center.z) / h_size
                else:                u, v = (p.z - center.z) / w_size, (p.y - center.y) / h_size

                longitude = u * (2.0 * math.pi)
                
                if main_mode == 0:
                    v_clamped = max(-0.49, min(0.49, v))
                    latitude = 2.0 * math.atan(math.exp(v_clamped * math.pi)) - (math.pi / 2.0)
                else:
                    latitude = v * math.pi

                latitude = latitude * lat_scale
                new_x = RADIUS * math.cos(latitude) * math.sin(longitude)
                new_y = RADIUS * math.sin(latitude)
                new_z = RADIUS * math.cos(latitude) * math.cos(longitude)

                sphere_pos = c4d.Vector(new_x + center.x, new_y + center.y, new_z + center.z)
                
                p_deformed = p + (sphere_pos - p) * strength
                points[i] = to_op_space * p_deformed

        # БЛОК 2: MAP CONVERT (MODE 2 и 3)
        else:
            axis_mode = data.GetLong(1000)
            w_size = data.GetFloat(1020)

            if w_size <= 0.0:
                w_size = 1.0

            for i in range(len(points)):
                p = to_mod_space * points[i]

                if main_mode == 2:
                    # MODE 2: МЕРКАТОР (1:1 КВАДРАТ) В EQUIDISTANT (2:1) ---
                    v_merc = (p.y - center.y) / w_size
                    v_clamped = max(-0.499, min(0.499, v_merc))
                    
                    # функция Гудермана ?
                    latitude = 2.0 * math.atan(math.exp(v_clamped * (2.0 * math.pi))) - (math.pi / 2.0)
                    target_y = (latitude / (2.0 * math.pi)) * w_size + center.y
                    
                else:
                    # MODE 3: ИЗ EQUIDISTANT (2:1) В МЕРКАТОР (1:1) ---
                    canon = False;

                    v_equid = (p.y - center.y) / w_size
                    lat_rad = v_equid * (2.0 * math.pi)
                    
                    if canon: # синусоидальая дисторсии Меркатора (Web Mercator)
                        # клэмпинг на уровне 85.051129° (канонически~)
                        lat_clamped = max(-1.48442222947, min(1.48442222947, lat_rad))
                        merc_y = 0.5 * math.log((1.0 + math.sin(lat_clamped)) / (1.0 - math.sin(lat_clamped)))
                        target_y = (merc_y / (2.0 * math.pi)) * w_size + center.y
                    
                    else: # Hard Width Fix
                        # Защищаем знаменатель от деления на ноль на полюсах панорамы, 
                        # слегка ограничивая синус оригинального lat_rad числом 0.9999
                        lat_sin = max(-0.9999, min(0.9999, math.sin(lat_rad)))
                        merc_y = 0.5 * math.log((1.0 + lat_sin) / (1.0 - lat_sin))
                        target_y = (merc_y / (2.0 * math.pi)) * w_size + center.y

                        # жесткие геометрические границы квадрата
                        half_width = w_size * 0.5
                        max_allowed_y = center.y + half_width
                        min_allowed_y = center.y - half_width

                        if target_y > max_allowed_y:
                            target_y = max_allowed_y
                        elif target_y < min_allowed_y:
                            target_y = min_allowed_y


                # Morph from Strength
                p.y = p.y + (target_y - p.y) * strength
                points[i] = to_op_space * p

        op.SetAllPoints(points)
        op.Message(c4d.MSG_UPDATE)
        return True

if __name__ == "__main__":
    c4d.plugins.RegisterObjectPlugin(
        id=PLUGIN_ID,
        str="Globe Deformer",
        g=GlobeDeformer,
        description="GlobeDeformer",
        icon=None,
        info=c4d.OBJECT_MODIFIER
    )