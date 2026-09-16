"""

SVG from Splines

Author: Viktor Aleksandrovsky & Google AI & ChatGPT
Written & Tested for Maxon Cinema 4D R19+ (R26 safe)
A swift kick from Sergio Gorleone

Description-US:Export splines as SVG file  |


"""

import c4d, os, sys
from c4d import storage
import codecs

IS_PY3 = sys.version_info >= (3, 0)
print("is", IS_PY3)


# C4D SplineType:
# 0 SPLINETYPE_LINEAR  -Linear
# 1 SPLINETYPE_CUBIC   -Cubic
# 2 SPLINETYPE_AKIMA   -Akima
# 3 SPLINETYPE_BSPLINE -B-Spline
# 4 SPLINETYPE_BEZIER  -Bezier


def safe_open_json(path, mode='r'):
    #cyrillic safe and python 2\3
    if IS_PY3:
        return open(path, mode, encoding='utf-8')
    else: 
        return codecs.open(path, mode, encoding='utf-8')

def _distance_sq(a, b):
    d = a - b
    return d.x * d.x + d.y * d.y + d.z * d.z


def _wrap_t(t):
    return t % 1.0


def _get_spline_point(op, t, segment, closed):
    if closed:
        t = _wrap_t(t)
    else:
        t = max(0.0, min(1.0, t))

    return op.GetSplinePoint(t, segment)


def _get_spline_derivative(op, t, segment, closed):
    # Get the derivative of the actual C4D spline.
    # This is more reliable for SVG export than treating vl/vr
    # from GetTangent() as if they were SVG control points.

    eps = 0.00001

    if closed:
        p0 = _get_spline_point(op, t - eps, segment, True)
        p1 = _get_spline_point(op, t + eps, segment, True)
        return (p1 - p0) / (2.0 * eps)

    if t <= eps:
        p0 = _get_spline_point(op, t, segment, False)
        p1 = _get_spline_point(op, t + eps, segment, False)
        return (p1 - p0) / eps

    if t >= 1.0 - eps:
        p0 = _get_spline_point(op, t - eps, segment, False)
        p1 = _get_spline_point(op, t, segment, False)
        return (p1 - p0) / eps

    p0 = _get_spline_point(op, t - eps, segment, False)
    p1 = _get_spline_point(op, t + eps, segment, False)

    return (p1 - p0) / (2.0 * eps)


def _find_bspline_t(op, target, approx_t, step, segment, closed):
    # B-Spline control points are not points on the actual curve.
    # Find the point on the real B-Spline which is closest to
    # each original C4D control point.

    if closed:
        left = approx_t - step
        right = approx_t + step

        samples = 16
        best_t = approx_t
        best_dist = None

        for i in range(samples + 1):
            t = left + (right - left) * float(i) / samples
            p = _get_spline_point(op, t, segment, True)
            dist = _distance_sq(p, target)

            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_t = t

        span = (right - left) / samples

        left = best_t - span
        right = best_t + span

        for _ in range(10):
            t1 = left + (right - left) * 0.382
            t2 = left + (right - left) * 0.618

            d1 = _distance_sq(
                _get_spline_point(op, t1, segment, True),
                target
            )

            d2 = _distance_sq(
                _get_spline_point(op, t2, segment, True),
                target
            )

            if d1 < d2:
                right = t2
            else:
                left = t1

        return _wrap_t((left + right) * 0.5)

    left = max(0.0, approx_t - step)
    right = min(1.0, approx_t + step)

    samples = 16
    best_t = approx_t
    best_dist = None

    for i in range(samples + 1):
        t = left + (right - left) * float(i) / samples

        p = _get_spline_point(
            op,
            t,
            segment,
            False
        )

        dist = _distance_sq(p, target)

        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_t = t

    span = (right - left) / samples

    left = max(0.0, best_t - span)
    right = min(1.0, best_t + span)

    for _ in range(10):
        t1 = left + (right - left) * 0.382
        t2 = left + (right - left) * 0.618

        d1 = _distance_sq(
            _get_spline_point(op, t1, segment, False),
            target
        )

        d2 = _distance_sq(
            _get_spline_point(op, t2, segment, False),
            target
        )

        if d1 < d2:
            right = t2
        else:
            left = t1

    return (left + right) * 0.5


def _get_bezier_data(op,spline_type,segment,seg_points,seg_closed):
    point_count = len(seg_points)

    if point_count < 2:
        return [], [], []

    # Parameter position of the original spline points.
    #
    # Open:
    #   0 -------- 1
    #
    # Closed:
    #   0 ---- last
    #   \________/
    #
    # B-Spline is handled separately below because its control
    # points do not lie on the resulting curve.

    if seg_closed:
        natural_ts = [
            float(i) / float(point_count)
            for i in range(point_count)
        ]
    else:
        natural_ts = [
            float(i) / float(point_count - 1)
            for i in range(point_count)
        ]

    actual_ts = []
    anchors = []

    for i in range(point_count):
        target = seg_points[i]

        if spline_type == c4d.SPLINETYPE_BSPLINE:
            step = 1.0 / float(point_count)

            t = _find_bspline_t(
                op,
                target,
                natural_ts[i],
                step,
                segment,
                seg_closed
            )

            # Keep B-Spline anchors ordered.
            if actual_ts and not seg_closed:
                min_t = actual_ts[-1] + 0.000001

                if t < min_t:
                    t = min_t

            actual_ts.append(t)

            anchors.append(
                _get_spline_point(
                    op,
                    t,
                    segment,
                    seg_closed
                )
            )

        else:
            t = natural_ts[i]

            actual_ts.append(t)

            anchors.append(
                _get_spline_point(
                    op,
                    t,
                    segment,
                    seg_closed
                )
            )

    # For a CLOSED B-Spline the parameters returned by
    # _find_bspline_t() are wrapped to [0, 1). Around the seam this can
    # produce a sequence such as:
    #
    #     0.97, 0.24, 0.49, 0.74
    #
    # These are in the correct geometric order, but a direct subtraction
    # makes the FIRST interval look like -0.73. The caller then falls back
    # to 1 / point_count, which gives the first Bezier handle the wrong
    # length.
    #
    # Unwrap the parameters ONCE, preserving the original projected
    # positions. The actual spline evaluation still wraps t internally.
    # This changes only the interval lengths; it does not approximate or
    # replace the B-Spline curve.
    if (
        spline_type == c4d.SPLINETYPE_BSPLINE
        and seg_closed
        and len(actual_ts) > 1
    ):
        unwrapped_ts = [actual_ts[0]]

        for t in actual_ts[1:]:
            while t <= unwrapped_ts[-1]:
                t += 1.0
            unwrapped_ts.append(t)

        actual_ts = unwrapped_ts

    derivatives = []

    for t in actual_ts:
        derivatives.append(
            _get_spline_derivative(
                op,
                t,
                segment,
                seg_closed
            )
        )

    return anchors, derivatives, actual_ts


def _append_bezier(path,p0,p1,d0,d1,dt,matrix,transform_pt):
    # Cubic Bezier derivative:
    #
    # B'(0) = 3 * (C1 - P0)
    # B'(1) = 3 * (P1 - C2)
    #
    # Therefore:
    #
    # C1 = P0 + B'(0) * dt / 3
    # C2 = P1 - B'(1) * dt / 3

    cp1 = p0 + d0 * (dt / 3.0)
    cp2 = p1 - d1 * (dt / 3.0)

    cp1 = matrix * cp1
    cp2 = matrix * cp2
    p1 = matrix * p1

    cp1_x, cp1_y = transform_pt(cp1)
    cp2_x, cp2_y = transform_pt(cp2)
    p1_x, p1_y = transform_pt(p1)

    #path += (f"C "f"{cp1_x:.4f} {cp1_y:.4f} "f"{cp2_x:.4f} {cp2_y:.4f} "f"{p1_x:.4f} {p1_y:.4f} ")
    path += "C {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} ".format(
        cp1_x, cp1_y, cp2_x, cp2_y, p1_x, p1_y
    )


    return path


def _get_fitted_matrix(matrix):
    """Снэпим векторы к ближайшим округленным значениям"""
    fitted_matrix = c4d.Matrix()
    vectors = [matrix.v1, matrix.v2, matrix.v3]
    fitted_vectors = []
    
    for v in vectors:
        fv = c4d.Vector(0, 0, 0)

        if abs(v.x) >= 0.5:
            fv.x = 1.0 if v.x > 0 else -1.0
        elif abs(v.y) >= 0.5:
            fv.y = 1.0 if v.y > 0 else -1.0
        elif abs(v.z) >= 0.5:
            fv.z = 1.0 if v.z > 0 else -1.0
            
        fitted_vectors.append(fv)
        
    fitted_matrix.v1 = fitted_vectors[0]
    fitted_matrix.v2 = fitted_vectors[1]
    fitted_matrix.v3 = fitted_vectors[2]
    fitted_matrix.off = c4d.Vector(0, 0, 0) 
    
    return fitted_matrix



""" напоминалка
if proj == c4d.Pfront:
    ortho_matrix = c4d.Matrix() 
    ortho_matrix.v1 = c4d.Vector(1, 0, 0)
    ortho_matrix.v2 = c4d.Vector(0, 1, 0)
    ortho_matrix.v3 = c4d.Vector(0, 0, 1)
"""

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


def svg_from_spline(splines):

    usermode = "useview" # or "ortho"
    plane = "xy"

    all_global_points = []
    svg_paths_list = [] # список хранения отдельных тегов <path>

    doc = c4d.documents.GetActiveDocument()
    bd = doc.GetActiveBaseDraw()
    if bd is None:
        return ""
        
    camera = bd.GetSceneCamera(doc) or bd.GetEditorCamera()
    focal_length = camera[c4d.CAMERA_FOCUS]
    aperture = camera[c4d.CAMERAOBJECT_APERTURE]
    fov_factor = focal_length / (aperture if aperture > 0 else 36.0)

    frame = bd.GetFrame()
    width = float(frame["cr"] - frame["cl"])
    height = float(frame["cb"] - frame["ct"])
    print("frame", frame)

    cam_matrix = camera.GetMg() 
    inv_cam_matrix = ~cam_matrix
    projection = bd.GetProjection()
    
    is_orthogonal, ortho_matrix  = ortho_cam_helper(projection, cam_matrix)

    if is_orthogonal or usermode == "ortho": 
        inv_cam_matrix = ~ortho_matrix

    # -----------------------------------------------------------------

    for op in splines:
        matrix = inv_cam_matrix * op.GetMg()
        print("[DEBUG] WORKED MATRIX:", matrix)

        points = op.GetAllPoints()      
        point_count = len(points)
        if point_count == 0:
            continue
            
        try:
            spline_type = op.GetInterpolationType()
        except AttributeError:
            spline_type = op[c4d.SPLINEOBJECT_TYPE]
        
        print("[DEBUG] SPLINE_TYPE:",spline_type)

        segment_count = op.GetSegmentCount()
        segments = []

        if segment_count > 0:
            for s in range(segment_count):
                segments.append(op.GetSegment(s))
        else:
            segments.append({
                "cnt": point_count,
                "closed": op.IsClosed()
            })

        global_points = [matrix * p for p in points]
        all_global_points.extend(global_points)

        def transform_pt_base(p):
            return p.x, -p.y

        def transform_pt_prod(p):
            # Если мы в режиме перспективы, p.z — это расстояние от плоскости камеры.
            # В пространстве камеры инвертированный взгляд направлен по оси Z.
            # Делаем проверку, чтобы избежать деления на ноль, если точка позади камеры.
            if projection == c4d.Pperspective and p.z != 0:
                # Магическая формула перспективы: проецируем 3D на 2D экран
                # Чем больше p.z (глубина), тем меньше становятся X и Y
                # fov_factor * 1000 — это просто масштаб, чтобы значения не были дробью в 0.01
                scale = (fov_factor * 1000.0) / abs(p.z)
                return p.x * scale, -p.y * scale
            else:
                # Если вид ортогональный (Top/Left/Front), перспективы нет — отдаем как раньше
                return p.x, -p.y
        
        def transform_pt(p):
            if projection == c4d.Pperspective and p.z != 0:
                # ИСПРАВЛЕНО: Вместо хардкодного множителя 1000.0 мы привязываемся к viewport_height.
                # Теперь масштаб точек будет строго соответствовать экранному разрешению твоего окна!
                scale = (fov_factor * width) / abs(p.z)
                return p.x * scale, -p.y * scale
            else:
                # Для ортогональных видов (Top/Left/Front) тоже нужен нормальный коэффициент,
                # чтобы они не были микроскопическими на больших экранах.
                # Умножаем на базовый масштаб (например, 1.0 или подгоняем под зум окна через bd.GetZoom())
                #ortho_scale = height / 7000.0
                #return p.x * ortho_scale, -p.y * ortho_scale
                return p.x, -p.y

        current_start_idx = 0
        single_d_path = "" # Строка пути строго для ТЕКУЩЕГО объекта

        for segment_index, seg in enumerate(segments):
            seg_p_count = seg["cnt"]
            seg_closed = seg["closed"]

            seg_points = points[
                current_start_idx:
                current_start_idx + seg_p_count
            ]

            # ---------------------------------------------------------
            # LINEAR
            # ---------------------------------------------------------

            if spline_type == c4d.SPLINETYPE_LINEAR:

                for i in range(seg_p_count):
                    global_idx = current_start_idx + i
                    curr_pt = global_points[global_idx]

                    curr_x, curr_y = transform_pt(curr_pt)

                    if i == 0:
                        single_d_path += "M {:.4f} {:.4f} ".format(curr_x, curr_y)
                    else:
                        single_d_path += "L {:.4f} {:.4f} ".format(curr_x, curr_y)


            # ---------------------------------------------------------
            # BEZIER
            # ---------------------------------------------------------

            elif spline_type == c4d.SPLINETYPE_BEZIER:

                anchors, derivatives, actual_ts = _get_bezier_data(
                    op,
                    spline_type,
                    segment_index,
                    seg_points,
                    seg_closed
                )

                if anchors:

                    first_pt = matrix * anchors[0]
                    first_x, first_y = transform_pt(first_pt)

                    single_d_path += "M {:.4f} {:.4f} ".format(first_x, first_y)

                    for i in range(1, len(anchors)):

                        dt = actual_ts[i] - actual_ts[i - 1]

                        if dt <= 0.0:
                            dt = 1.0 / max(
                                1,
                                seg_p_count - 1
                            )

                        single_d_path = _append_bezier(
                            single_d_path,
                            anchors[i - 1],
                            anchors[i],
                            derivatives[i - 1],
                            derivatives[i],
                            dt,
                            matrix,
                            transform_pt
                        )

            # ---------------------------------------------------------
            # CUBIC / AKIMA / BSPLINE
            # ---------------------------------------------------------

            elif spline_type in (
                c4d.SPLINETYPE_CUBIC,
                c4d.SPLINETYPE_AKIMA,
                c4d.SPLINETYPE_BSPLINE
            ):

                anchors, derivatives, actual_ts = _get_bezier_data(
                    op,
                    spline_type,
                    segment_index,
                    seg_points,
                    seg_closed
                )

                if anchors:

                    first_pt = matrix * anchors[0]
                    first_x, first_y = transform_pt(first_pt)

                    single_d_path += "M {:.4f} {:.4f} ".format(first_x, first_y)

                    for i in range(1, len(anchors)):

                        dt = actual_ts[i] - actual_ts[i - 1]

                        if dt <= 0.0:
                            dt = 1.0 / max(
                                1,
                                seg_p_count - 1
                            )

                        single_d_path = _append_bezier(
                            single_d_path,
                            anchors[i - 1],
                            anchors[i],
                            derivatives[i - 1],
                            derivatives[i],
                            dt,
                            matrix,
                            transform_pt
                        )

            else:

                # Unknown spline type: keep the old safe behavior.

                for i in range(seg_p_count):
                    global_idx = current_start_idx + i
                    curr_pt = global_points[global_idx]

                    curr_x, curr_y = transform_pt(curr_pt)

                    if i == 0:
                        single_d_path += "M {:.4f} {:.4f} ".format(curr_x, curr_y)
                    else:
                        single_d_path += "L {:.4f} {:.4f} ".format(curr_x, curr_y)
            # ---------------------------------------------------------
            # CLOSED SPLINE
            # ---------------------------------------------------------

            if seg_closed and seg_p_count > 1:

                first_idx = current_start_idx
                last_idx = current_start_idx + seg_p_count - 1

                first_pt = global_points[first_idx]
                last_pt = global_points[last_idx]

                first_x, first_y = transform_pt(first_pt)

                if spline_type == c4d.SPLINETYPE_LINEAR:

                    single_d_path += "L {:.4f} {:.4f} ".format(first_x, first_y)

                elif spline_type in (
                    c4d.SPLINETYPE_BEZIER,
                    c4d.SPLINETYPE_CUBIC,
                    c4d.SPLINETYPE_AKIMA,
                    c4d.SPLINETYPE_BSPLINE
                ):

                    anchors, derivatives, actual_ts = _get_bezier_data(
                        op,
                        spline_type,
                        segment_index,
                        seg_points,
                        seg_closed
                    )

                    if len(anchors) > 1:

                        # The final interval goes from the last
                        # anchor through t=1.0 back to the first anchor.

                        # B-Spline seam PATCH:
                        #
                        # For a CLOSED B-Spline the first control point can
                        # legitimately project to a curve parameter just
                        # BEFORE t=0. _find_bspline_t() wraps that value into
                        # ~1.0. The old formula
                        #
                        #     1 - last_t + first_t
                        #
                        # then interprets ~1.0 as a full extra revolution,
                        # making the final Bezier handle fly away.
                        #
                        # What we need here is the FORWARD CYCLIC distance
                        # from the last anchor to the first anchor.
                        if spline_type == c4d.SPLINETYPE_BSPLINE:
                            # actual_ts is unwrapped above, so the final
                            # cyclic interval is simply the distance from
                            # the last parameter to the next copy of the
                            # first parameter.
                            dt = (actual_ts[0] + 1.0) - actual_ts[-1]
                        else:
                            dt = (actual_ts[0] - actual_ts[-1]) % 1.0

                        # Exact coincidence means one complete closed
                        # interval, not a zero-length interval.
                        if dt <= 0.0:
                            dt = 1.0 / float(seg_p_count)

                        single_d_path = _append_bezier(
                            single_d_path,
                            anchors[-1],
                            anchors[0],
                            derivatives[-1],
                            derivatives[0],
                            dt,
                            matrix,
                            transform_pt
                        )

                single_d_path += "Z "

            current_start_idx += seg_p_count

        # save name object (id)
        obj_name = "".join([c for c in op.GetName() if c.isalpha() or c.isdigit() or c in " _-"]).strip() or "layer"
        
        # Create <path> tag
        #path_tag = f'  <path id="{obj_name}" d="{single_d_path.strip()}" fill="#b0b0b0" fill-rule="evenodd" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        path_tag = '  <path id="{}" d="{}" fill="#b0b0b0" fill-rule="evenodd" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'.format(obj_name, single_d_path.strip())

        svg_paths_list.append(path_tag)

    if not all_global_points:
        return

    # 4. calc viewBox
    min_x = min(p.x for p in all_global_points)
    max_x = max(p.x for p in all_global_points)
    min_y = min(p.y for p in all_global_points)
    max_y = max(p.y for p in all_global_points)
    
    if projection == c4d.Pperspective:
        svg_min_x = -width / 2.0
        svg_min_y = -height / 2.0
        svg_width = width 
        svg_height = height 
    else:
        svg_min_x = min_x - 10
        svg_min_y = -max_y - 10
        svg_width = (max_x - min_x) + 20
        svg_height = (max_y - min_y) + 20

    
    # 5. create svg
    #svg_content = f'<?xml version="1.0" encoding="utf-8"?>\n'
    #svg_content += f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="{svg_min_x:.4f} {svg_min_y:.4f} {svg_width:.4f} {svg_height:.4f}" width="{svg_width:.4f}" height="{svg_height:.4f}">\n'
    #svg_content += "\n".join(svg_paths_list) + "\n"
    #svg_content += f'</svg>'
    svg_content = '<?xml version="1.0" encoding="utf-8"?>\n'
    
    svg_content += '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="' + \
                   "{:.4f}".format(svg_min_x) + " " + "{:.4f}".format(svg_min_y) + " " + \
                   "{:.4f}".format(svg_width) + " " + "{:.4f}".format(svg_height) + \
                   '" width="' + "{:.4f}".format(svg_width) + '" height="' + "{:.4f}".format(svg_height) + '">\n'
                   
    svg_content += "\n".join(svg_paths_list) + "\n"
    svg_content += '</svg>'

    print("width,height",svg_width, svg_height)

    return svg_content

def _collect_splines(obj, found_splines):
    """Рекурсивно обходит объект и всех его детей, собирая сплайны."""
    if obj is None:
        return
    
    # Если текущий объект — сплайн, добавляем в список
    if obj.IsInstanceOf(c4d.Ospline):
        found_splines.append(obj)
        
    # Идем по детям объекта
    child = obj.GetDown()
    while child:
        _collect_splines(child, found_splines)
        child = child.GetNext()

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

def get_clean_splines():
    """
    get unuq splines
    Convert param circle or Text in memory C4D.
    """
    doc = c4d.documents.GetActiveDocument()
    selected = doc.GetActiveObjects(0)
    
    if selected:
        raw_stream = walk_selected_hierarchy(selected)
    else:
        raw_stream = walk_hierarchy(doc.GetFirstObject())
        
    splines = []
    seen_guids = set()

    for obj in raw_stream:
        if not obj: continue
        
        is_real_spline = obj.IsInstanceOf(c4d.Ospline)
        is_parametric = bool(obj.GetInfo() & c4d.OBJECT_ISSPLINE) and not is_real_spline

        if is_real_spline or is_parametric:
            guid = obj.GetGUID()
            
            if guid not in seen_guids:
                seen_guids.add(guid)
                

                if is_real_spline:
                    splines.append(obj)
                
                elif is_parametric:
                    temp_doc = c4d.documents.BaseDocument()
                    temp_obj = obj.GetClone() # Берем безопасную копию
                    temp_doc.InsertObject(temp_obj)
                    
                    res = c4d.utils.SendModelingCommand(
                        command=c4d.MCOMMAND_CURRENTSTATETOOBJECT,
                        list=[temp_obj],
                        mode=c4d.MODELINGCOMMANDMODE_ALL,
                        doc=temp_doc
                    )
                    
                    if isinstance(res, list) and len(res) > 0:
                        converted_root = res[0]

                        if converted_root.IsInstanceOf(c4d.Ospline):
                            splines.append(converted_root)
                        else:
                            child = converted_root.GetDown()
                            while child:
                                if child.IsInstanceOf(c4d.Ospline):
                                    child_clone = child.GetClone()
                                    splines.append(child_clone)
                                child = child.GetNext()
                                
    return splines



def main():

    splines = get_clean_splines()
    
    if not splines:
        c4d.gui.MessageDialog("Select Splines or Hierarchy with Splines!")
        return
    
    # 2. Проверка путей и форм. имени файла
    doc_path = doc.GetDocumentPath()
    if doc_path and os.path.exists(doc_path):
        target_dir = doc_path
    else:
        target_dir = os.path.join(os.path.expanduser("~"), "Desktop")

    if len(splines) > 1:
        base_name = "splines_export"
    else:
        base_name = splines[0].GetName().strip() or "spline_export"
        
    
    clean_name = "".join([c for c in base_name if c.isalpha() or c.isdigit() or c in " _-"]).strip()
    
    filename = clean_name + ".svg"
    filepath = os.path.join(target_dir, filename)

    if os.path.isfile(filepath):
        import re
        match = re.search(r'([_\-\s])?(\d+)$', clean_name)
        
        if match:
            separator = match.group(1) if match.group(1) else "_"
            num = int(match.group(2)) + 1
            name_prefix = clean_name[:match.start()]
            
            while True:
                filename = "{}{}{}.svg".format(name_prefix, separator, num)
                if not os.path.isfile(os.path.join(target_dir, filename)):
                    break
                num += 1
        else:
            counter = 1
            while True:
                filename = "{}_{}.svg".format(clean_name, counter)
                if not os.path.isfile(os.path.join(target_dir, filename)):
                    break
                counter += 1



    user_target_filepath = storage.SaveDialog(
        type=c4d.FILESELECTTYPE_ANYTHING,
        title="Export SVG",
        def_path=target_dir,
        def_file=filename,
        force_suffix="svg"
    )

    if not user_target_filepath:
        print("User skip SaveDialog")
        return

    print("user_target_filepath: ",user_target_filepath)

    svg_content = svg_from_spline(splines)

    try:

        with safe_open_json(user_target_filepath, "w") as f:
            f.write(svg_content)
            
        c4d.gui.MessageDialog("Succes SVG write:\n{}".format(user_target_filepath))
    except Exception as e:
        c4d.gui.MessageDialog("Error saving:\n{}".format(str(e)))



if __name__ == '__main__':
    main()