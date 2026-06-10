"""
Fillet Plane

Author: Viktor Aleksandrovsky & Google
Written for Maxon Cinema 4D R23
Tested on R23
"""

import c4d
GENERATOR_CODE = """import c4d
import math

def main():
    # --- 1. User Data Retrieval ---
    extend = op[c4d.ID_USERDATA, 3]

    width = op[c4d.ID_USERDATA, 1] - extend * 2.0
    height = op[c4d.ID_USERDATA, 2] - extend * 2.0

    raw_corner = op[c4d.ID_USERDATA, 4]
    raw_grid_size = op[c4d.ID_USERDATA, 5]

    use_manual_sub = op[c4d.ID_USERDATA, 7]
    raw_sub_x = op[c4d.ID_USERDATA, 8]
    raw_sub_y = op[c4d.ID_USERDATA, 9]


    flip_normals = op[c4d.ID_USERDATA, 10]

    use_extrude = op[c4d.ID_USERDATA, 12]
    thickness = op[c4d.ID_USERDATA, 13]

    phong_value = 23.0

    if width is None or width < 1.0: width = 200.0
    if height is None or height < 1.0: height = 200.0
    if extend is None: extend = 100.0

    if raw_corner is None or raw_corner < 1:
        raw_corner = 1
    corner_sub = int(raw_corner) + 2

    if use_manual_sub == 1 or use_manual_sub is True:
        if raw_sub_x is None or int(raw_sub_x) < 1: sub_x = 1
        else: sub_x = int(raw_sub_x)

        if raw_sub_y is None or int(raw_sub_y) < 1: sub_y = 1
        else: sub_y = int(raw_sub_y)
    else:
        if raw_grid_size is None:
            grid_size = 20.0
        else:
            grid_size = float(raw_grid_size)

        if grid_size <= 0.0:
            sub_x = 1
            sub_y = 1
        else:
            sub_x = max(1, int(width / grid_size))
            sub_y = max(1, int(height / grid_size))

    all_points = []
    all_polygons = []

    w_step = width / sub_x
    h_step = height / sub_y

    left_inner = -width / 2.0
    right_inner = width / 2.0
    bottom_inner = -height / 2.0
    top_inner = height / 2.0

    nx = sub_x + 3
    ny = sub_y + 3

    for y in range(ny):
        if y == 0:
            z_pos = bottom_inner - extend
        elif y == ny - 1:
            z_pos = top_inner + extend
        else:
            z_pos = bottom_inner + (y - 1) * h_step

        for x in range(nx):
            if x == 0:
                x_pos = left_inner - extend
            elif x == nx - 1:
                x_pos = right_inner + extend
            else:
                x_pos = left_inner + (x - 1) * w_step

            all_points.append(c4d.Vector(x_pos, 0, z_pos))

    idx_bl_center = 1 * nx + 1
    idx_br_center = 1 * nx + (nx - 2)
    idx_tl_center = (ny - 2) * nx + 1
    idx_tr_center = (ny - 2) * nx + (nx - 2)

    pt_bl_start = 0 * nx + 1
    pt_bl_end = 1 * nx + 0

    pt_br_start = 1 * nx + (nx - 1)
    pt_br_end = 0 * nx + (nx - 2)

    pt_tr_start = (ny - 1) * nx + (nx - 2)
    pt_tr_end = (ny - 2) * nx + (nx - 1)

    pt_tl_start = (ny - 2) * nx + 0
    pt_tl_end = (ny - 1) * nx + 1

    def generate_arc_points(center_pt, start_angle, end_angle, count, corner_type):
        arc_indices = []

        if count == 3:
            if corner_type == "BL":
                corner_pos = c4d.Vector(left_inner - extend, 0, bottom_inner - extend)
            elif corner_type == "BR":
                corner_pos = c4d.Vector(right_inner + extend, 0, bottom_inner - extend)
            elif corner_type == "TR":
                corner_pos = c4d.Vector(right_inner + extend, 0, top_inner + extend)
            elif corner_type == "TL":
                corner_pos = c4d.Vector(left_inner - extend, 0, top_inner + extend)

            all_points.append(corner_pos)
            arc_indices.append(len(all_points) - 1)
            return arc_indices

        for i in range(1, count - 1):
            t = float(i) / (count - 1)
            angle = start_angle + t * (end_angle - start_angle)
            rad = math.radians(angle)

            x = center_pt.x + extend * math.cos(rad)
            z = center_pt.z + extend * math.sin(rad)

            all_points.append(c4d.Vector(x, 0, z))
            arc_indices.append(len(all_points) - 1)
        return arc_indices

    bl_arc = generate_arc_points(all_points[idx_bl_center], 180, 270, corner_sub, "BL")
    br_arc = generate_arc_points(all_points[idx_br_center], 270, 360, corner_sub, "BR")
    tr_arc = generate_arc_points(all_points[idx_tr_center], 360, 450, corner_sub, "TR")
    tl_arc = generate_arc_points(all_points[idx_tl_center], 90, 180, corner_sub, "TL")

    for y in range(ny - 1):
        for x in range(nx - 1):
            if x == 0 and y == 0: continue
            if x == nx - 2 and y == 0: continue
            if x == nx - 2 and y == ny - 2: continue
            if x == 0 and y == ny - 2: continue

            a = y * nx + x
            b = a + 1
            c = (y + 1) * nx + x + 1
            d = c - 1

            if flip_normals:
                all_polygons.append(c4d.CPolygon(d, c, b, a))
            else:
                all_polygons.append(c4d.CPolygon(a, b, c, d))

    bl_poly_points = [idx_bl_center, pt_bl_end] + bl_arc + [pt_bl_start]
    br_poly_points = [idx_br_center, pt_br_end] + br_arc + [pt_br_start]
    tr_poly_points = [idx_tr_center, pt_tr_end] + tr_arc + [pt_tr_start]
    tl_poly_points = [idx_tl_center, pt_tl_end] + tl_arc + [pt_tl_start]

    all_corner_poly_indices = []

    def build_triangulated_corner_polys(pt_list):
        center = pt_list[0] # ИСПРАВЛЕНО: Берем индекс первой точки, а не весь массив
        for i in range(1, len(pt_list) - 1):
            p1 = pt_list[i]
            p2 = pt_list[i+1]

            if flip_normals:
                poly = c4d.CPolygon(p2, p1, center, center)
            else:
                poly = c4d.CPolygon(center, p1, p2, p2)

            all_polygons.append(poly)
            all_corner_poly_indices.append(len(all_polygons) - 1)

    build_triangulated_corner_polys(bl_poly_points)
    build_triangulated_corner_polys(br_poly_points)
    build_triangulated_corner_polys(tr_poly_points)
    build_triangulated_corner_polys(tl_poly_points)

    top_vertex_count = len(all_points)
    top_poly_count = len(all_polygons)

    if use_extrude and thickness > 0.0:
        for i in range(top_vertex_count):
            top_pt = all_points[i]
            all_points.append(c4d.Vector(top_pt.x, top_pt.y - thickness, top_pt.z))

        for i in range(top_poly_count):
            poly = all_polygons[i]
            a_bot = poly.a + top_vertex_count
            b_bot = poly.b + top_vertex_count
            c_bot = poly.c + top_vertex_count
            d_bot = poly.d + top_vertex_count

            all_polygons.append(c4d.CPolygon(a_bot, b_bot, c_bot, d_bot))


        outer_loop = []

        for x in range(1, nx - 1):
            outer_loop.append(0 * nx + x)
        outer_loop.extend(br_arc)
        for y in range(1, ny - 1):
            outer_loop.append(y * nx + (nx - 1))
        outer_loop.extend(tr_arc)
        for x in range(nx - 2, 0, -1):
            outer_loop.append((ny - 1) * nx + x)
        outer_loop.extend(tl_arc)
        for y in range(ny - 2, 0, -1):
            outer_loop.append(y * nx + 0)
        outer_loop.extend(bl_arc)

        for i in range(len(outer_loop)):
            t1 = outer_loop[i]
            t2 = outer_loop[0] if i == len(outer_loop) - 1 else outer_loop[i+1]

            b1 = t1 + top_vertex_count
            b2 = t2 + top_vertex_count

            all_polygons.append(c4d.CPolygon(t1, t2, b2, b1))


    mesh = c4d.PolygonObject(pcnt=len(all_points), vcnt=len(all_polygons))
    if not mesh: return None

    mesh.SetAllPoints(all_points)

    for i, poly in enumerate(all_polygons):
        mesh.SetPolygon(i, poly)

    mesh.Message(c4d.MSG_UPDATE)
    current_doc = op.GetDocument() if 'op' in globals() else c4d.documents.GetActiveDocument()

    poly_selection = mesh.GetPolygonS()
    poly_selection.DeselectAll()

    for poly_idx in all_corner_poly_indices:
        poly_selection.Select(poly_idx)

    if use_extrude and thickness > 0.0:
        for poly_idx in all_corner_poly_indices:
            poly_selection.Select(poly_idx + top_poly_count)

    settings = c4d.BaseContainer()
    c4d.utils.SendModelingCommand(
        command=c4d.MCOMMAND_MELT,
        list=[mesh],
        mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
        bc=settings,
        doc=current_doc
    )

    c4d.utils.SendModelingCommand(
        command=c4d.MCOMMAND_ALIGNNORMALS,
        list=[mesh],
        mode=c4d.MODELINGCOMMANDMODE_ALL,
        doc=current_doc
    )

    # --- 7. Default Phong Tag Initialization ---
    phong_tag = mesh.MakeTag(c4d.Tphong)
    if phong_tag:
        phong_tag[c4d.PHONGTAG_PHONG_ANGLELIMIT] = True
        phong_tag[c4d.PHONGTAG_PHONG_ANGLE] = c4d.utils.DegToRad(phong_value)

    mesh.Message(c4d.MSG_UPDATE)
    return mesh
"""

def add_user_data(obj, name, data_type, default_val):
    bc = c4d.GetCustomDatatypeDefault(data_type)
    bc[c4d.DESC_NAME] = name
    bc[c4d.DESC_SHORT_NAME] = name

    if data_type == c4d.DTYPE_REAL:
        bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_METER
        bc[c4d.DESC_STEP] = 1.0
        # Превращаем все float поля в слайдеры по умолчанию
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER
    elif data_type == c4d.DTYPE_LONG:
        bc[c4d.DESC_STEP] = 1
        # Превращаем все int поля в слайдеры по умолчанию
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_LONGSLIDER
    elif data_type == c4d.DTYPE_SEPARATOR:
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_SEPARATOR
        if name == "":
            bc[c4d.DESC_SEPARATORLINE] = True

    # --- Настройка лимитов под конкретные параметры ---
    if name == "Width" or name == "Height":
        bc[c4d.DESC_MIN] = 0.001
        bc[c4d.DESC_MINEX] = True # limit min [on]
        bc[c4d.DESC_MAX] = 10000000.0
        bc[c4d.DESC_MAXEX] = True # limit max [on]
        bc[c4d.DESC_MAXSLIDER] = 600.0 # slider max [on]

    elif name == "Round":
        bc[c4d.DESC_MIN] = 1.0
        bc[c4d.DESC_MINEX] = True
        bc[c4d.DESC_MAX] = 1000.0
        bc[c4d.DESC_MAXEX] = True
        bc[c4d.DESC_MAXSLIDER] = 79.0

    elif name == "Round Segments":
        bc[c4d.DESC_MIN] = 1
        bc[c4d.DESC_MINEX] = True
        bc[c4d.DESC_MAX] = 24
        bc[c4d.DESC_MAXEX] = True
        bc[c4d.DESC_MAXSLIDER] = 8

    elif name == "Grid Size":
        bc[c4d.DESC_MIN] = 0.0
        bc[c4d.DESC_MINEX] = True
        bc[c4d.DESC_MAX] = 1000.0
        bc[c4d.DESC_MAXEX] = True
        bc[c4d.DESC_MAXSLIDER] = 160.0

    elif name == "Width Segments" or name == "Height Segments":
        bc[c4d.DESC_MIN] = 0
        bc[c4d.DESC_MINEX] = True
        bc[c4d.DESC_MAX] = 100
        bc[c4d.DESC_MAXEX] = True

    elif name == "Thickness":
        bc[c4d.DESC_STEP] = 0.1 # Step 0.1
        bc[c4d.DESC_MIN] = 0.0
        bc[c4d.DESC_MINEX] = True
        bc[c4d.DESC_MAX] = 10000000.0
        bc[c4d.DESC_MAXEX] = True
        bc[c4d.DESC_MAXSLIDER] = 60.0

    element = obj.AddUserData(bc)
    if default_val is not None:
        obj[element] = default_val
    return element

def main():
    py_gen = c4d.BaseObject(1023866)
    if not py_gen:
        print("Не удалось создать Python Generator")
        return

    py_gen.SetName("f_plane")
    py_gen[c4d.OPYTHON_CODE] = GENERATOR_CODE

    add_user_data(py_gen, "Width", c4d.DTYPE_REAL, 400.0)
    add_user_data(py_gen, "Height", c4d.DTYPE_REAL, 300.0)
    add_user_data(py_gen, "Round", c4d.DTYPE_REAL, 40.0)
    add_user_data(py_gen, "Round Segments", c4d.DTYPE_LONG, 2)
    add_user_data(py_gen, "Grid Size", c4d.DTYPE_REAL, 60.0)

    add_user_data(py_gen, "", c4d.DTYPE_SEPARATOR, None)

    add_user_data(py_gen, "Use Manual Segment", c4d.DTYPE_BOOL, False)
    add_user_data(py_gen, "Width Segments", c4d.DTYPE_LONG, 6)
    add_user_data(py_gen, "Height Segments", c4d.DTYPE_LONG, 6)
    add_user_data(py_gen, "Flip Normals", c4d.DTYPE_BOOL, False)

    add_user_data(py_gen, "Extrude", c4d.DTYPE_SEPARATOR, None)

    add_user_data(py_gen, "Push it", c4d.DTYPE_BOOL, False)
    add_user_data(py_gen, "Thickness", c4d.DTYPE_REAL, 8.0)

    active_doc = c4d.documents.GetActiveDocument()
    active_doc.InsertObject(py_gen)

    bevel = c4d.BaseObject(431000028)
    if bevel:
        bevel.SetName("depth_fillet")
        bevel[c4d.O_BEVEL_RADIUS] = 2.0
        bevel[c4d.O_BEVEL_SUB] = 1
        bevel[c4d.O_BEVEL_LIMIT] = True
        
        bevel.InsertUnder(py_gen)


    active_doc.SetActiveObject(py_gen, c4d.SELECTION_NEW)
    c4d.EventAdd()

if __name__ == '__main__':
    main()