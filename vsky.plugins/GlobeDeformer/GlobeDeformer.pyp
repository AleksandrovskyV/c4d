"""
Globe Deformer

Author: Viktor Aleksandrovsky & Google
Written & Tested for Maxon Cinema 4D R19
"""

import c4d
import math
PLUGIN_ID = 1063489 

# ========================================================
# Добавить refresh кнопку (чтобы можно было обновить ирерахию при перемещении деформера)
# Добавить Width\Height как режим альтернативный bbox + сделать в unlock по toggling
# Убрать пропись значений width\height при добавлении деформера в иерархию
# Добавить Draw Guide Map
# Добавить матрицу трансформации (чтобы можно было перемещать)
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
            "min_x": 999999999.0, "min_y": 999999999.0, "min_z": 999999999.0,
            "max_x": -999999999.0, "max_y": -999999999.0, "max_z": -999999999.0,
            "has_geometry": False
        }

        def walk(obj):
            if obj is None: return

            if obj.IsInstanceOf(c4d.Opolygon) or obj.IsInstanceOf(c4d.Ospline) or (obj.GetType() == 5138):
                rad = obj.GetRad()
                mp = obj.GetMp() 
                
                if rad.x > 0.0 or rad.y > 0.0 or rad.z > 0.0:
                    bounds["has_geometry"] = True
                    m_op = obj.GetMg()
                    op_to_mod = ~mod_mg * m_op
                    
                    p1 = op_to_mod * (mp + c4d.Vector(-rad.x, -rad.y, -rad.z))
                    p2 = op_to_mod * (mp + c4d.Vector(rad.x, rad.y, rad.z))
                    
                    # Расширяем общие границы составной карты
                    bounds["min_x"] = min(bounds["min_x"], p1.x, p2.x)
                    bounds["min_y"] = min(bounds["min_y"], p1.y, p2.y)
                    bounds["min_z"] = min(bounds["min_z"], p1.z, p2.z)
                    
                    bounds["max_x"] = max(bounds["max_x"], p1.x, p2.x)
                    bounds["max_y"] = max(bounds["max_y"], p1.y, p2.y)
                    bounds["max_z"] = max(bounds["max_z"], p1.z, p2.z)

            child = obj.GetDown()
            while child:
                walk(child)
                child = child.GetNext()

        walk(root_obj)

        if not bounds["has_geometry"]:
            return None

        w_size = bounds["max_x"] - bounds["min_x"]
        h_size = bounds["max_y"] - bounds["min_y"]
        d_size = bounds["max_z"] - bounds["min_z"]
        
        hierarchy_size = c4d.Vector(w_size, h_size, d_size)
        center = c4d.Vector(
            (bounds["min_x"] + bounds["max_x"]) * 0.5,
            (bounds["min_y"] + bounds["max_y"]) * 0.5,
            (bounds["min_z"] + bounds["max_z"]) * 0.5
        )
        
        return hierarchy_size, center

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

        parent = mod.GetUp()
        bbox_data = None
        if parent:
            bbox_data = self.CalculateHierarchyBBox(parent, mod_mg)

        if bbox_data:
            hierarchy_size, center = bbox_data
            axis_mode = data.GetLong(1000)
            
            if axis_mode == 0:   w_size, h_size = float(hierarchy_size.x), float(hierarchy_size.y)
            elif axis_mode == 1: w_size, h_size = float(hierarchy_size.x), float(hierarchy_size.z)
            else:                w_size, h_size = float(hierarchy_size.z), float(hierarchy_size.y)
                
            #data.SetFloat(1020, w_size)
            #data.SetFloat(1021, h_size)
        else:
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
            if parent and bbox_data:
                hierarchy_size, center = bbox_data
                axis_mode = data.GetLong(1000)
                if axis_mode == 0:
                    w_size = float(hierarchy_size.x)
                elif axis_mode == 1:
                    w_size = float(hierarchy_size.x)
                else:
                    w_size = float(hierarchy_size.z)
            else:
                w_size = data.GetFloat(1020)
                center = c4d.Vector(0.0)

            if w_size <= 0.0: w_size = 1.0

            for i in range(len(points)):
                p = to_mod_space * points[i]

                if main_mode == 2:
                    # MODE 2: МЕРКАТОР (1:1 КВАДРАТ) В EQUIDISTANT (2:1) ---
                    v_merc = (p.y - center.y) / w_size
                    v_clamped = max(-0.499, min(0.499, v_merc))
                    
                    # Прямая функция Гудермана
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