import bpy
import bmesh
import numpy as np


def initialize_environment():
    bpy.ops.object.select_all(action = 'DESELECT')
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")


def deselected_all():
    bpy.ops.object.select_all(action='DESELECT')


def remove_object(obj):

    deselected_all()
    obj.select = True
    bpy.ops.object.delete()


def set_parent(parent, child, vertex_parenting=False):

    deselected_all()

    parent.select = True
    child.select = True     #select the object for the 'parenting'

    bpy.context.scene.objects.active = parent    #the active object will be the parent of all selected object

    if vertex_parenting:
        bpy.ops.object.parent_set(type='VERTEX')
    else:
        bpy.ops.object.parent_set()

    deselected_all()


def import_object(path, name):

    deselected_all()

    bpy.ops.import_scene.obj(filepath=path)
    obj = bpy.context.selected_objects[0]
    obj.name = name

    return obj


def switch_origin(obj_name, max_point=True, coords=None):

    deselected_all()
    obj = bpy.data.objects[obj_name]
    obj.select = True

    mw = obj.matrix_world      # Active object's world matrix
    glob_vertex_coordinates = [mw * v.co for v in obj.data.vertices] # Global coordinates of vertices

    # Find the lowest Z value amongst the object's vertex

    if max_point:
        Z = max([co.z for co in glob_vertex_coordinates])
    else:
        Z = min([co.z for co in glob_vertex_coordinates])

    for v in obj.data.vertices:
        if (mw * v.co).z == Z:

            if coords is None:
                bpy.context.scene.cursor_location = mw * v.co
            else:

                bpy.context.scene.cursor_location = (coords[0], coords[1], (mw * v.co).z)

            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    deselected_all()

# SPLIT OBJECT:

def highest_edge(obj):

    max_idx = np.argmax([v.co.z for v in obj.data.vertices])
    obj.data.vertices[max_idx].select = True

    edges_with_max_vertex = []
    for edge in obj.data.edges:
        if edge.vertices[0] == max_idx or edge.vertices[1] == max_idx:
            edges_with_max_vertex.append(edge)

    edge_angles = []
    for edge  in edges_with_max_vertex:
        a_v = obj.data.vertices[edge.vertices[0]]
        b_v = obj.data.vertices[edge.vertices[1]]

        a_v = np.array([a_v.co.x, a_v.co.y])
        b_v = np.array([b_v.co.x, b_v.co.y])

        norm_a = np.linalg.norm(a_v)
        norm_b = np.linalg.norm(b_v)
        ab = a_v @ b_v
        angle = np.cos(ab / (norm_a * norm_b))

        edge_angles.append(angle)

    edge_idx = np.argmax(edge_angles)

    return edges_with_max_vertex[edge_idx].index


def select_edge_loop(edge):

    for loop in edge.link_loops:
       if len(loop.vert.link_edges) == 4:
            edge.select = True

    while len(loop.vert.link_edges) == 4:

        loop = loop.link_loop_prev.link_loop_radial_prev.link_loop_prev
        edge_next = loop.edge

        if edge_next.select:
            break;
        else:
            edge_next.select = True


def activate_object(obj):
    obj.select = True
    bpy.context.scene.objects.active = obj


def split_object(obj, splitted_name, choose_edge=highest_edge):

    activate_object(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    edge_id = choose_edge(obj)

    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(obj.data)   # fill it in from a Mesh

    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

    select_edge_loop(bm.edges[edge_id])

    bm.to_mesh(obj.data)
    bm.free()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.loop_to_region()
    bpy.ops.mesh.separate(type='SELECTED')

    bpy.ops.object.editmode_toggle()
    inner = bpy.context.selected_objects[0]
    inner.name = splitted_name

    bpy.ops.object.select_all(action='DESELECT')