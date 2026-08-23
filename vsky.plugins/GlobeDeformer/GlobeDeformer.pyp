"""
Globe Deformer

Author: Viktor Aleksandrovsky & Google AI
Written & Tested for Maxon Cinema 4D R19

Plugin for geometry deformation based on geographic projections (Equidistant/Mercator).
In 2D Convert mode, it can transform coordinate points from Equidistant > Mercator and vice versa.

The "Deformer Strength" slider in 2D Convert mode between 0 and 100 has a slight precision error (currently working on a fix). 
However, it works fine at exact values of 0 and 100.

The code is open, so feel free to fix it yourself)
"""


import c4d, math, json, os
from c4d import bitmaps
PLUGIN_ID = 1063489 

class GlobeDeformer(c4d.plugins.ObjectData):
    
    def Init(self, node):
        data = node.GetDataInstance()
        data.SetLong(999, 0)       # Mode
        data.SetLong(1000, 0)      # Axis
        data.SetFloat(1001, 1.0)   # Size Globus
        data.SetFloat(1004, 1.0)   # Stretch to equator
        data.SetFloat(1002, 1.0)   # Power Deform
        data.SetFloat(1020, 400.0) # Width
        data.SetFloat(1021, 200.0) # Height
        data.SetBool(1023, False)  # Guide Earth
        data.SetBool(1024, False)  # Unlock Height

        # --- boox eq json ---
        #"_bbox": {
        #    "points": [
        #        [-1000.0, 500.0, 0.0], 
        #        [1000.0, 500.0, 0.0], 
        #        [-1000.0, -500.0, 0.0], 
        #        [1000.0, -500.0, 0.0]
        #    ], 
        #    "closed": false
        #}, 

        plugin_dir = os.path.dirname(__file__)
        json_path = os.path.join(plugin_dir,"res","guide_map", "equirectangular.json")

        self.cached_eq_lines = []    # cache equirectangular (2:1 )
        self.cached_merc_lines = []  # cache mercator from eq(1:1)
        self.cached_guide_lines = [] # link to current

        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    raw_data = json.load(f)
                
                for name, info in raw_data.items():
                    if name == "_bbox": continue
                        
                    points_list = info.get("points", [])
                    global_closed = info.get("closed", False)
                    segments_list = info.get("segments", [])
                    
                    count = len(points_list)
                    if count < 2: continue

                    # --- CREATE CACHE EQUIDISTANT ---
                    spline_eq = c4d.SplineObject(count, c4d.SPLINETYPE_LINEAR)
                    spline_eq.SetName(name)
                    
                    vectors_eq = [c4d.Vector(float(p[0]), float(p[1]), float(p[2])) for p in points_list]
                    spline_eq.SetAllPoints(vectors_eq)
                    spline_eq[c4d.SPLINEOBJECT_CLOSED] = global_closed
                    
                    if segments_list:
                        spline_eq.ResizeObject(count, len(segments_list))
                        for s, seg_info in enumerate(segments_list):
                            spline_eq.SetSegment(s, seg_info["cnt"], seg_info["closed"])
                    
                    spline_eq.Message(c4d.MSG_UPDATE)
                    line_eq = self.BuildLineObject(spline_eq)
                    if line_eq:
                        self.cached_eq_lines.append(line_eq)
                    
                    # --- CREATE CACHE MERCATOR ---
                    spline_merc = c4d.SplineObject(count, c4d.SPLINETYPE_LINEAR)
                    spline_merc.SetName(name + "_merc")
                    
                    vectors_merc = []
                    w_size_json = 2000.0
                    center_json = c4d.Vector(0.0)

                    for p in points_list:
                        raw_x = float(p[0])
                        raw_y = float(p[1]) 
                        raw_z = float(p[2])
                        
                        canon = False
                        
                        v_equid = (raw_y - center_json.y) / w_size_json
                        lat_rad = v_equid * (2.0 * math.pi)
                        
                        if canon:
                            lat_clamped = max(-1.48442222947, min(1.48442222947, lat_rad))
                            merc_y = 0.5 * math.log((1.0 + math.sin(lat_clamped)) / (1.0 - math.sin(lat_clamped)))
                            target_y = (merc_y / (2.0 * math.pi)) * w_size_json + center_json.y
                        else:
                            lat_sin = max(-0.9999, min(0.9999, math.sin(lat_rad)))
                            merc_y = 0.5 * math.log((1.0 + lat_sin) / (1.0 - lat_sin))
                            target_y = (merc_y / (2.0 * math.pi)) * w_size_json + center_json.y
                            
                            half_width = w_size_json * 0.5
                            max_allowed_y = center_json.y + half_width
                            min_allowed_y = center_json.y - half_width
                            
                            if target_y > max_allowed_y:
                                target_y = max_allowed_y
                            elif target_y < min_allowed_y:
                                target_y = min_allowed_y
                        
                        vectors_merc.append(c4d.Vector(raw_x, target_y, raw_z))

                        
                    spline_merc.SetAllPoints(vectors_merc)
                    spline_merc[c4d.SPLINEOBJECT_CLOSED] = global_closed
                    
                    if segments_list:
                        spline_merc.ResizeObject(count, len(segments_list))
                        for s, seg_info in enumerate(segments_list):
                            spline_merc.SetSegment(s, seg_info["cnt"], seg_info["closed"])
                    
                    spline_merc.Message(c4d.MSG_UPDATE)
                    line_merc = self.BuildLineObject(spline_merc)
                    if line_merc:
                        self.cached_merc_lines.append(line_merc)
                        
                self.cached_guide_lines = self.cached_eq_lines


            except Exception as e:
                print("GlobeDeformer: Error loading JSON map:", e)

        return True

    def lerp(self, t, a, b):
        return a + (b - a) * t

    def BuildLineObject(self, spline):
        """Вспомогательный метод. Запекает SplineObject в нативный LineObject."""
        spline_help = c4d.utils.SplineHelp()
        if spline_help.InitSplineWith(spline, c4d.SPLINEHELPFLAGS_RETAINLINEOBJECT):
            line_res = spline_help.GetLineObject()
            if line_res:
                cloned_line = line_res.GetClone()
                cloned_line[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS
                cloned_line[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0.745, 0.722, 0.949)
                return cloned_line
        return None

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

            add_object_bbox(obj)
            cache = obj.GetCache()

            if cache:
                walk_cache(cache, mod_mg)

            deform_cache = obj.GetDeformCache()

            if deform_cache and deform_cache != cache:
                walk_cache(deform_cache, mod_mg)

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

    def FitToParent(self, op):
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
        is_height_unlocked = data.GetBool(1024)

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

        if not is_height_unlocked:
            main_mode = data.GetLong(999)
            if main_mode == 1 or main_mode == 3:
                h_size = w_size
            else:
                h_size = w_size / 2.0

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



    def UpdateGuideCache(self, op, forced_mode=None):
        data = op.GetDataInstance()
        if data is None or not data.GetBool(1023): return

        if not hasattr(self, "cached_eq_lines") or not self.cached_eq_lines: return
        if not hasattr(self, "cached_merc_lines"): return

        main_mode = forced_mode if forced_mode is not None else data.GetLong(999)
        strength = data.GetFloat(1002) 

        if main_mode == 0:   # Eqidistant
            t = 0.0
        elif main_mode == 1: # Mercator
            t = 1.0
        elif main_mode == 2: 
            t = max(0.0, min(1.0, strength))
        elif main_mode == 3:
            t = 1.0 - max(0.0, min(1.0, strength))
            

        self.cached_guide_lines = []

        for idx, eq_line in enumerate(self.cached_eq_lines):
            merc_line = self.cached_merc_lines[idx]
            
            pts_eq = eq_line.GetAllPoints()
            pts_merc = merc_line.GetAllPoints()
            mixed_line = eq_line.GetClone()
            new_pts = []
            
            for i in range(len(pts_eq)):
                p_start = pts_eq[i]
                p_end = pts_merc[i]
                p_mix = p_start + (p_end - p_start) * t
                new_pts.append(p_mix)
                
            mixed_line.SetAllPoints(new_pts)
            mixed_line.Message(c4d.MSG_UPDATE)
            
            self.cached_guide_lines.append(mixed_line)



    def GetDEnabling(self, node, descid, t_data, flags, itemdesc):
        param_id = descid[0].id
        data = node.GetDataInstance()

        main_mode = data.GetLong(999)  

        if main_mode == 2 or main_mode == 3:
            if param_id == 1004 or param_id == 1001:
                return False


        if param_id == 1021:
            if data:
                if not data.GetBool(1024):
                    return False

                return True

        return True

    def Message(self, node, type, data):
        if type == c4d.MSG_MENUPREPARE:
            print("MENUPREPARE")
            self.UpdateGuideCache(node)
            c4d.EventAdd()

        if type == c4d.MSG_DESCRIPTION_COMMAND:
            if data is not None:
                desc_id = data.get("id")

                if desc_id is not None:
                    print("BUTTON:", desc_id[0].id)

                    if desc_id[0].id == 1022:
                        print("FIT TO PARENT")
                        result = self.FitToParent(node)
                        node.SetDirty(c4d.DIRTYFLAGS_DATA)
                        c4d.EventAdd()
                        return True

        return True

    def SetDParameter(self, node, id, t_data, flags):
        param_id = id[0].id
        data = node.GetDataInstance()
        main_mode = data.GetLong(999) 

        if param_id == 999: 
            print("Mode Changed to:", t_data)

            width = data.GetLong(1020) 
            if (t_data == 1 or t_data == 3) and not data.GetBool(1024):
                data.SetFloat(1021, width)
            else:
                data.SetFloat(1021, width/2)

            node.GetDataInstance().SetLong(999, t_data)
            self.UpdateGuideCache(node, t_data)
            
            node.SetDirty(c4d.DIRTYFLAGS_DATA)
            c4d.EventAdd()
            return True

        if param_id == 1020 and not data.GetBool(1024):
            print("Width Changed:", t_data)
            if main_mode == 1 or main_mode == 3:
                data.SetFloat(1021, t_data)
            else:
                data.SetFloat(1021, t_data/2)

        if param_id == 1002:
            print("Power Changed:", t_data)
            node.GetDataInstance().SetFloat(1002, float(t_data))
        
            self.UpdateGuideCache(node)
            node.SetDirty(c4d.DIRTYFLAGS_DATA)
            c4d.EventAdd()
            return True

        return True

    def Draw(self, op, drawpass, bd, bh):
        if drawpass != c4d.DRAWPASS_OBJECT: return c4d.DRAWRESULT_SKIP
        if op is None or bd is None: return c4d.DRAWRESULT_SKIP

        data = op.GetDataInstance()
        w_size = data.GetFloat(1020)
        h_size = data.GetFloat(1021)
        axis_mode = data.GetLong(1000)

        if w_size <= 0.0 or h_size <= 0.0: return c4d.DRAWRESULT_SKIP
        hw, hh = w_size * 0.5, h_size * 0.5

        # --- 1. Отрисовка внешней желтой рамки деформатора ---
        if axis_mode == 0:   bbox = [c4d.Vector(-hw, -hh, 0.0), c4d.Vector(hw, -hh, 0.0), c4d.Vector(hw, hh, 0.0), c4d.Vector(-hw, hh, 0.0)]
        elif axis_mode == 1: bbox = [c4d.Vector(-hw, 0.0, -hh), c4d.Vector(hw, 0.0, -hh), c4d.Vector(hw, 0.0, hh), c4d.Vector(-hw, 0.0, hh)]
        else:                bbox = [c4d.Vector(0.0, -hh, -hw), c4d.Vector(0.0, -hh, hw), c4d.Vector(0.0, hh, hw), c4d.Vector(0.0, hh, -hw)]
        
        # Устанавливаем матрицу деформатора
        op_matrix = op.GetMg()
        bd.SetMatrix_Matrix(op, op_matrix)

        # --- Guide Plane ---
        bd.SetPen(c4d.Vector(0.667, 0.604, 1.0), 0)
        for i in range(4): 
            bd.DrawLine(bbox[i], bbox[(i+1)%4], c4d.NOCLIP_D)

        doc = bh.GetDocument()
        help_object = c4d.plugins.BaseDrawHelp(bd, doc)

        # --- MapLines ---
        if not hasattr(self, "cached_guide_lines"): 
            self.cached_guide_lines = []

        if data.GetBool(1023) and self.cached_guide_lines:
            main_mode = data.GetLong(999) 
            strength = data.GetFloat(1002)

            if main_mode == 0:     t = 0.0 # eq 
            elif main_mode == 1:   t = 1.0 # merc
            elif main_mode == 2:   t = strength # eq > merc
            elif main_mode == 3:   t = strength # merc > eq

            sx = w_size / 2000
            sy = (h_size / self.lerp(t, 500.0, 1000.0)) * 0.5

            if main_mode == 2:
                sx = w_size * self.lerp(t, 1.0 / 2000.0, 1.0 / 4000.0)

            if main_mode == 3:
                sx = w_size / 2000
                sy = h_size / 2000

            m_scale = c4d.Matrix()

            if axis_mode == 0:   # XY
                m_scale.v1 = c4d.Vector(sx, 0.0, 0.0)
                m_scale.v2 = c4d.Vector(0.0, sy, 0.0)
                m_scale.v3 = c4d.Vector(0.0, 0.0, 1.0) 

            elif axis_mode == 1: # XZ
                m_scale.v1 = c4d.Vector(sx, 0.0, 0.0)
                m_scale.v2 = c4d.Vector(0.0, 0.0, sy)
                m_scale.v3 = c4d.Vector(0.0, 1.0, 0.0)

            elif axis_mode == 2: # ZY
                m_scale.v1 = c4d.Vector(0.0, 0.0, sx)
                m_scale.v2 = c4d.Vector(0.0, sy, 0.0)
                m_scale.v3 = c4d.Vector(1.0, 0.0, 0.0)

            final_guide_mg = op_matrix * m_scale

            for cached_line in self.cached_guide_lines:
                cached_line.SetMg(final_guide_mg)
                bd.DrawPolygonObject(help_object, cached_line, c4d.DRAWOBJECT_FORCELINES | c4d.DRAWOBJECT_USE_OBJECT_COLOR)

        return c4d.DRAWRESULT_OK

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

        # 3D GLOBE (MODE 0 and 1)
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
                    latitude = v * math.pi
                else:
                    v_clamped = max(-0.49, min(0.49, v))
                    latitude = 2.0 * math.atan(math.exp(v_clamped * math.pi)) - (math.pi / 2.0) 

                latitude = latitude * lat_scale
                new_x = RADIUS * math.cos(latitude) * math.sin(longitude)
                new_y = RADIUS * math.sin(latitude)
                new_z = RADIUS * math.cos(latitude) * math.cos(longitude)

                sphere_pos = c4d.Vector(new_x + center.x, new_y + center.y, new_z + center.z)
                
                p_deformed = p + (sphere_pos - p) * strength
                points[i] = to_op_space * p_deformed

        # MAP CONVERT (MODE 2 and 3)
        else:
            axis_mode = data.GetLong(1000)
            w_size = data.GetFloat(1020)

            if w_size <= 0.0:
                w_size = 1.0

            for i in range(len(points)):
                p = to_mod_space * points[i]
                start_y = p.y

                if main_mode == 2:
                    # EQUIDISTANT (2:1) > MERCATOR (1:1) ---
                    canon = False;
                    v_equid = (p.y - center.y) / w_size
                    lat_rad = v_equid * (2.0 * math.pi)
                    
                    if canon: # sin distortion Mercator (Web Mercator)
                        # clamp on 85.051129° (canonical ~)
                        lat_clamped = max(-1.48442222947, min(1.48442222947, lat_rad))
                        merc_y = 0.5 * math.log((1.0 + math.sin(lat_clamped)) / (1.0 - math.sin(lat_clamped)))
                        target_y = (merc_y / (2.0 * math.pi)) * w_size + center.y
                    
                    else: # Hard Clamp Fix
                        lat_sin = max(-0.9999, min(0.9999, math.sin(lat_rad)))
                        merc_y = 0.5 * math.log((1.0 + lat_sin) / (1.0 - lat_sin))
                        target_y = (merc_y / (2.0 * math.pi)) * w_size + center.y

                        half_width = w_size * 0.5
                        max_allowed_y = center.y + half_width
                        min_allowed_y = center.y - half_width

                        if target_y > max_allowed_y:
                            target_y = max_allowed_y
                        elif target_y < min_allowed_y:
                            target_y = min_allowed_y

                elif main_mode == 3:
                    # MERCATOR (1:1) > EQUIDISTANT (2:1) ---
                    v_merc = (p.y - center.y) / w_size
                    v_clamped = max(-0.499, min(0.499, v_merc))
                    
                    # function Гудермана ?
                    latitude = 2.0 * math.atan(math.exp(v_clamped * (2.0 * math.pi))) - (math.pi / 2.0)
                    target_y = (latitude / (2.0 * math.pi)) * w_size + center.y
                    

                # Morph from Strength
                if main_mode == 2:
                    scale_x = self.lerp(strength, 1.0, 0.5)
                    p.x = center.x + (p.x - center.x) * scale_x
                    compressed_y = (target_y - center.y) * 0.5 + center.y
                    p.y = self.lerp(strength, start_y, compressed_y)
                else:
                    p.y = p.y + (target_y - p.y) * strength

                points[i] = to_op_space * p

        op.SetAllPoints(points)
        op.Message(c4d.MSG_UPDATE)
        return True

if __name__ == "__main__":
    path, fn = os.path.split(__file__)
    bmp = bitmaps.BaseBitmap() # thanks vonc!
    bmp.InitWith(os.path.join(path, "res", "Globe Deformer.tif"))

    c4d.plugins.RegisterObjectPlugin(
        id=PLUGIN_ID,
        str="Globe Deformer",
        g=GlobeDeformer,
        description="GlobeDeformer",
        icon=bmp,
        info=c4d.OBJECT_MODIFIER
    )