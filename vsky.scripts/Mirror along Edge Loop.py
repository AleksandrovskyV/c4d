"""

Mirror along Edge Loop

Author: Viktor Aleksandrovsky & Google AI
Written & Tested for Maxon Cinema 4D R23

Description-US:Mirrors mesh points...|just like Symmetrize from new C4D |               But... works for me in R23

"""

import c4d

SCRIPT_NAME = "Mirror along Edge Loop"

class MessageDialogCustom(c4d.gui.GeDialog):
    """Unified modal dialog with custom title for strict errors (OK button only)."""
    def __init__(self, title, text):
        super(MessageDialogCustom, self).__init__()
        self.title = title
        self.text = text

    def CreateLayout(self):
        self.SetTitle(self.title)
        panel_width = 500
        self.AddStaticText(-1, c4d.BFH_SCALEFIT, name="")

        lines = self.text.split('\n')
        for i, line in enumerate(lines):
            if not line.strip():
                self.AddStaticText(1000+i, c4d.BFH_SCALEFIT, panel_width, 2, name="")
                continue

            self.AddStaticText(3000+i, c4d.BFH_LEFT, panel_width, 10, name="       " + line)

        self.AddStaticText(200, c4d.BFH_SCALEFIT, panel_width, 8, name="")

        self.GroupBegin(2000, c4d.BFH_CENTER, 2, 1)
        self.AddButton(c4d.IDC_OK, c4d.BFH_CENTER, 180, 18, name="OK")
        self.GroupEnd()

        self.GroupEnd()
        return True

    def Command(self, id, msg):
        if id == c4d.IDC_OK:
            self.Close()
        return True

class DirectionDialog(c4d.gui.GeDialog):
    """Unified UI holding side selection buttons and the conditional force-align layout switcher."""
    BUTTON_LEFT = 1001
    BUTTON_RIGHT = 1002
    CHECKBOX_ALIGN = 1003

    def __init__(self, show_alignment_warning=False):
        super(DirectionDialog, self).__init__()
        self.show_warning = show_alignment_warning
        self.result = None
        self.force_align = False

    def CreateLayout(self):
        self.SetTitle(SCRIPT_NAME)

        # Main vertical container
        self.GroupBegin(id=0, flags=c4d.BFH_SCALEFIT, cols=1, title="")
        self.GroupBorderSpace(20, 15, 20, 15)

        # Inject the alignment warning and the checkbox dynamically if loop points are skewed
        if self.show_warning:
            self.AddStaticText(id=2001, flags=c4d.BFH_LEFT, initw=0, inith=0,
                               name="Warning: Points on selected seam-loop not aligned with the section plane.")
            self.GroupSpace(0, 4)
            self.AddCheckbox(id=self.CHECKBOX_ALIGN, flags=c4d.BFH_LEFT, initw=0, inith=0,
                             name="Force-align?")
            self.SetBool(self.CHECKBOX_ALIGN, True) # Checked by default
            self.GroupSpace(0, 12)

        # Side selection execution buttons
        self.GroupBegin(id=1, flags=c4d.BFH_CENTER, cols=2, title="")
        self.AddButton(id=self.BUTTON_LEFT, flags=c4d.BFH_CENTER, initw=120, inith=16, name="Left >")
        self.AddButton(id=self.BUTTON_RIGHT, flags=c4d.BFH_CENTER, initw=120, inith=16, name="Right <")
        self.GroupEnd()

        self.GroupEnd()
        return True

    def Command(self, id, msg):
        if self.show_warning:
            self.force_align = self.GetBool(self.CHECKBOX_ALIGN)

        if id == self.BUTTON_LEFT:
            self.result = "left_to_right"
            self.Close()
        elif id == self.BUTTON_RIGHT:
            self.result = "right_to_left"
            self.Close()
        return True


def get_edge_points(obj, edge_idx):
    """Retrieves the two point indices forming a specific edge."""
    poly_idx = edge_idx // 4
    edge_num = edge_idx % 4
    poly = obj.GetPolygon(poly_idx)
    if edge_num == 0:   return poly.a, poly.b
    elif edge_num == 1: return poly.b, poly.c
    elif edge_num == 2: return poly.c, poly.d if poly.c != poly.d else poly.a
    else:               return poly.d if poly.c != poly.d else poly.c, poly.a
    
def calculate_seam_matrix(seam_points, points):
    """Constructs a localized transformation matrix using the seam loop layout."""
    seam_list = list(seam_points)
    center = c4d.Vector(0.0)
    for p in seam_list:
        center += points[p]
    center /= float(len(seam_list))

    if len(seam_list) < 3:
        mat = c4d.Matrix()
        mat.off = center
        return mat

    p_start = points[seam_list[0]]
    p_mid = points[seam_list[len(seam_list) // 2]]

    v_z = (p_mid - p_start).GetNormalized()
    v_y = (p_start - center).GetNormalized()
    v_x = v_y.Cross(v_z).GetNormalized()
    v_y = v_z.Cross(v_x).GetNormalized()

    mat = c4d.Matrix()
    mat.off = center
    mat.v1 = v_x
    mat.v2 = v_y
    mat.v3 = v_z
    return mat

def count_side_polygons(start_poly, seam_edges_set, polys, nbr):
    """Performs a pure topological flood fill to count polygons on one side."""
    visited = {start_poly}
    queue = [start_poly]
    
    while queue:
        curr_poly = queue.pop(0)
        p = polys[curr_poly]
        pts = [p.a, p.b, p.c, p.d]
        sides = 4 if p.c != p.d else 3
        
        for i in range(sides):
            if (curr_poly * 4 + i) in seam_edges_set:
                continue
                
            neighbor = nbr.GetNeighbor(pts[i], pts[(i + 1) % sides], curr_poly)
            if neighbor != -1 and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                
    return len(visited)
    
def main():
    obj = doc.GetActiveObject()
    if not obj or not obj.CheckType(c4d.Opolygon):
        err_dlg = (SCRIPT_NAME, "Selection Error: Please select a valid polygon mesh object!")
        err_dlg.Open(c4d.DLG_TYPE_MessageDialogCustomMODAL_RESIZEABLE, defaultw=380, defaulth=120)
        return

    edge_selection = obj.GetEdgeS()
    if edge_selection.GetCount() == 0:
        err_dlg = MessageDialogCustom(SCRIPT_NAME, "Error: Please select the base symmetrical edge-loop!", is_question=False)
        err_dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=380, defaulth=120)
        return

    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)

    points = obj.GetAllPoints()
    polys = obj.GetAllPolygons()

    nbr = c4d.utils.Neighbor()
    nbr.Init(obj)

    seam_edges = []
    seam_points = set()

    sel_elements = edge_selection.GetAll(obj.GetPolygonCount() * 4)
    for idx, selected in enumerate(sel_elements):
        if selected:
            seam_edges.append(idx)
            p1, p2 = get_edge_points(obj, idx)
            seam_points.add(p1)
            seam_points.add(p2)

    seam_matrix = calculate_seam_matrix(seam_points, points)
    inv_seam_matrix = ~seam_matrix 

    flat_tolerance = 0.01
    show_alignment_warning = False

    for p in seam_points:
        local_pos = inv_seam_matrix * points[p]
        if abs(local_pos.x) > flat_tolerance:
            show_alignment_warning = True
            break

    # 6. TOPOLOGY PROCESSING: Determine starter graph pairs
    start_edge = seam_edges[0]
    poly_a_idx = start_edge // 4
    root_a, root_b = get_edge_points(obj, start_edge)
    poly_b_idx = nbr.GetNeighbor(root_a, root_b, poly_a_idx)

    if poly_b_idx == -1:
        err_dlg = MessageDialogCustom(SCRIPT_NAME, "Error: The base seam lacks a valid topological neighbor layout. Aborting.")
        err_dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=380, defaulth=120)
        return

    center_a = (points[polys[poly_a_idx].a] + points[polys[poly_a_idx].b] + points[polys[poly_a_idx].c]) / 3.0
    local_center_a = inv_seam_matrix * center_a

    if local_center_a.x > 0:
        left_start_poly, right_start_poly = poly_a_idx, poly_b_idx
    else:
        left_start_poly, right_start_poly = poly_b_idx, poly_a_idx

    # Pure topological Flood Fill side counts
    seam_edges_set = set(seam_edges)
    
    left_poly_count = count_side_polygons(left_start_poly, seam_edges_set, polys, nbr)
    right_poly_count = count_side_polygons(right_start_poly, seam_edges_set, polys, nbr)

    if left_poly_count != right_poly_count:
        warn_text = (
            f"Polygon count mismatch between sides\n"
            f"They must be identical to execute :)\n\n"
            f"Left: {left_poly_count}   |   Right: {right_poly_count}"
        )


        warn_dlg = MessageDialogCustom(SCRIPT_NAME, warn_text)
        warn_dlg.Open(c4d.DLG_TYPE_MODAL, defaultw=380, defaulth=140)
        return

    # Trigger unified UI window holding selection buttons
    dlg = DirectionDialog(show_alignment_warning)
    dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=340, defaulth=100)
    if dlg.result is None:
        return

    # Force alignment switcher state handle
    if dlg.force_align:
        for p in seam_points:
            local_pos = inv_seam_matrix * points[p]
            local_pos.x = 0.0
            points[p] = seam_matrix * local_pos

    start_edge = seam_edges[0]
    poly_a_idx = start_edge // 4
    root_a, root_b = get_edge_points(obj, start_edge)
    poly_b_idx = nbr.GetNeighbor(root_a, root_b, poly_a_idx)

    if poly_b_idx == -1:
        err_dlg = MessageDialogCustom(SCRIPT_NAME, "Error: The base seam lacks a valid topological neighbor layout. Aborting.")
        err_dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=380, defaulth=120)
        return

    center_a = (points[polys[poly_a_idx].a] + points[polys[poly_a_idx].b] + points[polys[poly_a_idx].c]) / 3.0
    local_center_a = inv_seam_matrix * center_a

    if local_center_a.x > 0:
        left_start_poly, right_start_poly = poly_a_idx, poly_b_idx
    else:
        left_start_poly, right_start_poly = poly_b_idx, poly_a_idx

    topology_map = {}
    poly_queue = [(left_start_poly, right_start_poly)]
    visited_polys = {left_start_poly, right_start_poly}

    for p in seam_points:
        topology_map[p] = p


    while poly_queue:
        l_poly_idx, r_poly_idx = poly_queue.pop(0)

        l_poly = polys[l_poly_idx]
        r_poly = polys[r_poly_idx]

        l_pts = [l_poly.a, l_poly.b, l_poly.c, l_poly.d]
        r_pts = [r_poly.a, r_poly.b, r_poly.c, r_poly.d]

        known_l_pt = None
        known_r_pt = None

        for lp in l_pts:
            if lp in topology_map:
                known_l_pt = lp
                known_r_pt = topology_map[lp]
                break

        if known_l_pt is None:
            continue

        l_offset = l_pts.index(known_l_pt)
        r_offset = r_pts.index(known_r_pt)

        is_quad = (l_poly.c != l_poly.d)
        sides_count = 4 if is_quad else 3

        for i in range(sides_count):
            idx_l_curr = (l_offset + i) % sides_count
            idx_l_next = (l_offset + i + 1) % sides_count

            idx_r_curr = (r_offset - i) % sides_count
            idx_r_next = (r_offset - i - 1) % sides_count

            l_curr = l_pts[idx_l_curr]
            l_next = l_pts[idx_l_next]

            r_curr = r_pts[idx_r_curr]
            r_next = r_pts[idx_r_next]

            if l_curr not in topology_map:
                topology_map[l_curr] = r_curr

            next_l_poly = nbr.GetNeighbor(l_curr, l_next, l_poly_idx)
            next_r_poly = nbr.GetNeighbor(r_curr, r_next, r_poly_idx)

            if next_l_poly != -1 and next_r_poly != -1:
                if next_l_poly not in visited_polys and next_r_poly not in visited_polys:
                    visited_polys.add(next_l_poly)
                    visited_polys.add(next_r_poly)
                    poly_queue.append((next_l_poly, next_r_poly))

    # Safe coordinate transfer using immutable donor array
    points_donor_backup = list(points)

    for left_id, right_id in topology_map.items():
        if left_id == right_id:
            continue

        if dlg.result == "left_to_right":
            src_pos = inv_seam_matrix * points_donor_backup[left_id]
            target_local_pos = c4d.Vector(-src_pos.x, src_pos.y, src_pos.z)
            points[right_id] = seam_matrix * target_local_pos
        else:
            src_pos = inv_seam_matrix * points_donor_backup[right_id]
            target_local_pos = c4d.Vector(-src_pos.x, src_pos.y, src_pos.z)
            points[left_id] = seam_matrix * target_local_pos

    for p in seam_points:
        local_pos = inv_seam_matrix * points[p]
        local_pos.x = 0.0
        points[p] = seam_matrix * local_pos

    obj.SetAllPoints(points)
    obj.Message(c4d.MSG_UPDATE)
    doc.EndUndo()
    c4d.EventAdd()

if __name__ == '__main__':
    main()