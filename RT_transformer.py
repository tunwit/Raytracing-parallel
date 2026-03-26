from stl import mesh as stlmesh
import pywavefront
import RT_object as rto
import RT_utility as rtu
import multiprocessing as mp
import RT_material as rtm
import copy

class MeshTranformer():
    @staticmethod
    def stl_to_mesh(filepath, material, pos):
        stl_data = stlmesh.Mesh.from_file(filepath)

        min_v = rtu.Vec3(float('inf'), float('inf'), float('inf'))
        max_v = rtu.Vec3(float('-inf'), float('-inf'), float('-inf'))

        # Compute bounds
        for tri in stl_data.vectors:
            for v in tri:
                vec = rtu.Vec3(*v)
                min_v = rtu.Vec3(
                    min(min_v.x(), vec.x()),
                    min(min_v.y(), vec.y()),
                    min(min_v.z(), vec.z())
                )
                max_v = rtu.Vec3(
                    max(max_v.x(), vec.x()),
                    max(max_v.y(), vec.y()),
                    max(max_v.z(), vec.z())
                )

        extent = max_v - min_v
        max_dim = max(extent.x(), extent.y(), extent.z())
        scale = 2.0 / max_dim
        center = (min_v + max_v) * 0.5

        # Z becomes Y after rotate_x, so use Z extent for height
        half_height = (extent.z() * scale) / 2

        args_list = [(tri, center, scale, material, pos, half_height) for tri in stl_data.vectors]

        with mp.Pool(processes=mp.cpu_count()) as pool:
            triangles = pool.map(MeshTranformer._transform_triangle, args_list)

        print(f"Finish Transform {filepath} to mesh with {len(triangles)} triangle(s)")
        return rto.Mesh(triangles)

    @staticmethod
    def obj_mtl_to_mesh(objPath, mat, pos):
        obj = pywavefront.Wavefront(
            objPath,
            strict=False,
            collect_faces=True
        )
        min_v = rtu.Vec3(float('inf'), float('inf'), float('inf'))
        max_v = rtu.Vec3(float('-inf'), float('-inf'), float('-inf'))

        all_triangles = []

        for mesh in obj.meshes.values():
            for material in mesh.materials:

                verts = material.vertices
                stride = material.vertex_size

                for i in range(0, len(verts), stride * 3):

                    v1 = rtu.Vec3(*verts[i:i+3])
                    v2 = rtu.Vec3(*verts[i+stride:i+stride+3])
                    v3 = rtu.Vec3(*verts[i+2*stride:i+2*stride+3])

                    tri = [v1, v2, v3]
                    all_triangles.append((tri, material))

                    for v in tri:
                        min_v = rtu.Vec3(
                            min(min_v.x(), v.x()),
                            min(min_v.y(), v.y()),
                            min(min_v.z(), v.z())
                        )
                        max_v = rtu.Vec3(
                            max(max_v.x(), v.x()),
                            max(max_v.y(), v.y()),
                            max(max_v.z(), v.z())
                        )

        extent = max_v - min_v
        max_dim = max(extent.x(), extent.y(), extent.z())
        scale = 2.0 / max_dim
        center = (min_v + max_v) * 0.5

        # Z becomes Y after rotate_x, so use Z extent for height
        half_height = (extent.z() * scale) / 2

        args_list = []

        for tri, material in all_triangles:
            color = material.diffuse[:3] if material.diffuse else (0, 0, 0)
            try:
                cp_mat = copy.deepcopy(mat)
                cp_mat.color_albedo = rtu.Color(color[0], color[1], color[2])
            except Exception as e:
                print(e)
                cp_mat = rtm.Lambertian(rtu.Color(color[0], color[1], color[2]))
                
            args_list.append((tri, center, scale, cp_mat, pos, half_height))

        with mp.Pool(processes=mp.cpu_count()) as pool:
            triangles = pool.map(MeshTranformer._transform_triangle, args_list)

        print(f"Finish Transform {objPath} to mesh with {len(triangles)} triangle(s)")
        return rto.Mesh(triangles,pos=pos)

    @staticmethod
    def _transform_triangle(args):
        tri, center, scale, material, pos, half_height = args

        v0 = (rtu.Vec3(*tri[0]) - center) * scale
        v1 = (rtu.Vec3(*tri[1]) - center) * scale
        v2 = (rtu.Vec3(*tri[2]) - center) * scale

        def rotate_x(v):
            return rtu.Vec3(v.x(), v.z(), v.y())

        v0 = rotate_x(v0) + pos
        v1 = rotate_x(v1) + pos
        v2 = rotate_x(v2) + pos

        return rto.Triangle(v0, v1, v2, material)
    
    
