# object class
import RT_utility as rtu
import RT_BVH as rtb
import numpy as np
import math

class Object:
    def __init__(self) -> None:
        pass

    def intersect(self, rRay, cInterval):
        pass

class Sphere(Object):
    def __init__(self, vCenter, fRadius, mMat=None) -> None:
        super().__init__()
        self.center = vCenter
        self.radius = fRadius
        self.material = mMat
        # additional parameters for motion blur
        self.moving_center = None       # where to the sphere moves to
        self.is_moving = False          # is it moving ?
        self.moving_dir = None          # moving direction

    def add_material(self, mMat):
        self.material = mMat

    def add_moving(self, vCenter):      # set an ability to move to the sphere
        self.moving_center = vCenter
        self.is_moving = True
        self.moving_dir = self.moving_center - self.center

    def move_sphere(self, fTime):       # move the sphere by time parameter
        return self.center + self.moving_dir*fTime

    def printInfo(self):
        self.center.printout()        
    
    def intersect(self, rRay, cInterval):        

        # check if the sphere is moving then move center of the sphere.
        sphere_center = self.center
        if self.is_moving:
            sphere_center = self.move_sphere(rRay.getTime())

        oc = rRay.getOrigin() - sphere_center
        a = rRay.getDirection().len_squared()
        half_b = rtu.Vec3.dot_product(oc, rRay.getDirection())
        c = oc.len_squared() - self.radius*self.radius
        discriminant = half_b*half_b - a*c 

        if discriminant < 0:
            return None
        sqrt_disc = math.sqrt(discriminant)

        root = (-half_b - sqrt_disc) / a 
        if not cInterval.surrounds(root):
            root = (-half_b + sqrt_disc) / a 
            if not cInterval.surrounds(root):
                return None
            
        hit_t = root
        hit_point = rRay.at(root)
        hit_normal = rtu.Vec3.unit_vector((hit_point - sphere_center) / self.radius)
        hinfo = rtu.Hitinfo(hit_point, hit_normal, hit_t, self.material)
        hinfo.set_face_normal(rRay, hit_normal)

        # set uv coordinates for texture mapping
        fuv = self.get_uv(hit_normal)
        hinfo.set_uv(fuv[0], fuv[1])

        return hinfo

    # return uv coordinates of the sphere at the hit point.
    def get_uv(self, vNormal):
        theta = math.acos(-vNormal.y())
        phi = math.atan2(-vNormal.z(), vNormal.x()) + math.pi

        u = phi / (2*math.pi)
        v = theta / math.pi
        return (u,v)

# Ax + By + Cz = D
class Quad(Object):
    def __init__(self, vQ, vU, vV, mMat=None) -> None:
        super().__init__()
        self.Qpoint = vQ
        self.Uvec = vU
        self.Vvec = vV
        self.material = mMat
        self.uxv = rtu.Vec3.cross_product(self.Uvec, self.Vvec)
        self.normal = rtu.Vec3.unit_vector(self.uxv)
        self.D = rtu.Vec3.dot_product(self.normal, self.Qpoint)
        self.Wvec = self.uxv / rtu.Vec3.dot_product(self.uxv, self.uxv)

    def add_material(self, mMat):
        self.material = mMat

    def intersect(self, rRay, cInterval):
        denom = rtu.Vec3.dot_product(self.normal, rRay.getDirection())
        # if parallel
        if rtu.Interval.near_zero(denom):
            return None

        # if it is hit.
        t = (self.D - rtu.Vec3.dot_product(self.normal, rRay.getOrigin())) / denom
        if not cInterval.contains(t):
            return None
        
        hit_t = t
        hit_point = rRay.at(t)
        hit_normal = self.normal

        # determine if the intersection point lies on the quad's plane.
        planar_hit = hit_point - self.Qpoint
        alpha = rtu.Vec3.dot_product(self.Wvec, rtu.Vec3.cross_product(planar_hit, self.Vvec))
        beta = rtu.Vec3.dot_product(self.Wvec, rtu.Vec3.cross_product(self.Uvec, planar_hit))
        if self.is_interior(alpha, beta) is None:
            return None

        hinfo = rtu.Hitinfo(hit_point, hit_normal, hit_t, self.material)
        hinfo.set_face_normal(rRay, hit_normal)

        # set uv coordinates for texture mapping
        hinfo.set_uv(alpha, beta)

        return hinfo
    
    def is_interior(self, fa, fb):
        delta = 0   
        if (fa<delta) or (1.0<fa) or (fb<delta) or (1.0<fb):
            return None

        return True


class Triangle(Object):
    def __init__(self, v0, v1, v2, mMat=None) -> None:
        super().__init__()
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.material = mMat
        self.edge1 = self.v1 - self.v0
        self.edge2 = self.v2 - self.v0
        self.uxv = rtu.Vec3.cross_product(self.edge1, self.edge2)
        self.normal = rtu.Vec3.unit_vector(self.uxv)

    def intersect(self, rRay, cInterval):
        origin = rRay.getOrigin()
        direction = rRay.getDirection()

        h = rtu.Vec3.cross_product(direction, self.edge2)
        a = rtu.Vec3.dot_product(self.edge1, h)

        # If near zero → ray parallel to triangle
        if rtu.Interval.near_zero(a):
            return None

        f = 1.0 / a
        s = origin - self.v0

        u = f * rtu.Vec3.dot_product(s, h)
        if u < 0.0 or u > 1.0:
            return None

        q = rtu.Vec3.cross_product(s, self.edge1)
        v = f * rtu.Vec3.dot_product(direction, q)
        if v < 0.0 or (u + v) > 1.0:
            return None

        t = f * rtu.Vec3.dot_product(self.edge2, q)

        if not cInterval.surrounds(t):
            return None

        hit_point = rRay.at(t)

        hinfo = rtu.Hitinfo(hit_point, self.normal, t, self.material)
        hinfo.set_face_normal(rRay, self.normal)

        # Optional UV (using barycentric coords)
        hinfo.set_uv(u, v)

        return hinfo
    
    def bounding_box(self):
        epsilon = 1e-5

        min_v = rtu.Vec3(
            min(self.v0.x(), self.v1.x(), self.v2.x()) - epsilon,
            min(self.v0.y(), self.v1.y(), self.v2.y()) - epsilon,
            min(self.v0.z(), self.v1.z(), self.v2.z()) - epsilon
        )

        max_v = rtu.Vec3(
            max(self.v0.x(), self.v1.x(), self.v2.x()) + epsilon,
            max(self.v0.y(), self.v1.y(), self.v2.y()) + epsilon,
            max(self.v0.z(), self.v1.z(), self.v2.z()) + epsilon
        )

        return rtb.AABB(min_v, max_v)

class Mesh(Object):
    def __init__(self, triangles, scale=1.0, rotation_deg=(0, 0, 0), pos=(0, 0, 0)):
        self.base_triangles = triangles 
        
        self.scale = scale
        self.rotation_deg = rotation_deg
        self.pos = rtu.Vec3(*pos) if isinstance(pos, (tuple, list)) else pos
        self.center = self._compute_center()
        self.half_height = self._compute_half_height()

        self._update_geometry()

    def set_transform(self, scale=None, rotation_deg=None, pos=None):
        if scale is not None: self.scale = scale
        if rotation_deg is not None: self.rotation_deg = rotation_deg
        if pos is not None: 
            self.pos = rtu.Vec3(*pos) if isinstance(pos, (tuple, list)) else pos
        
        self._update_geometry()

    def _update_geometry(self):
        rad_x = math.radians(self.rotation_deg[0])
        rad_y = math.radians(self.rotation_deg[1])
        rad_z = math.radians(self.rotation_deg[2])

        new_world_triangles = []

        lift = rtu.Vec3(0, self.half_height * self.scale, 0)

        for tri in self.base_triangles:
            v0 = tri.v0 - self.center
            v1 = tri.v1 - self.center
            v2 = tri.v2 - self.center

            # apply transform
            v0 = self._apply_math(v0, self.scale, rad_x, rad_y, rad_z)
            v1 = self._apply_math(v1, self.scale, rad_x, rad_y, rad_z)
            v2 = self._apply_math(v2, self.scale, rad_x, rad_y, rad_z)

            # move back + apply lift
            v0 = v0 + self.center + lift
            v1 = v1 + self.center + lift
            v2 = v2 + self.center + lift

            new_world_triangles.append(Triangle(v0, v1, v2, tri.material))

        self.triangles = new_world_triangles
        self.bvh = BVHNode(self.triangles)

    def _compute_center(self):
        min_v = rtu.Vec3(float('inf'), float('inf'), float('inf'))
        max_v = rtu.Vec3(float('-inf'), float('-inf'), float('-inf'))

        for tri in self.base_triangles:
            for v in (tri.v0, tri.v1, tri.v2):
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

        return (min_v + max_v) * 0.5

    def _compute_half_height(self):
        min_y = float('inf')
        max_y = float('-inf')

        for tri in self.base_triangles:
            for v in (tri.v0, tri.v1, tri.v2):
                min_y = min(min_y, v.y())
                max_y = max(max_y, v.y())

        return (max_y - min_y) / 2

    def _apply_math(self, v, s, rx, ry, rz):
        x, y, z = v.x() * s, v.y() * s, v.z() * s

        if rx != 0:
            c, s_val = math.cos(rx), math.sin(rx)
            y, z = y * c - z * s_val, y * s_val + z * c
        if ry != 0:
            c, s_val = math.cos(ry), math.sin(ry)
            x, z = x * c + z * s_val, -x * s_val + z * c
        if rz != 0:
            c, s_val = math.cos(rz), math.sin(rz)
            x, y = x * c - y * s_val, x * s_val + y * c

        return rtu.Vec3(x, y, z)

    def intersect(self, rRay, cInterval):
        return self.bvh.intersect(rRay, cInterval)
    
class BVHNode(Object):
    def __init__(self, objects, max_leaf_size=2):
        super().__init__()

        objects = list(objects)
        n = len(objects)

        # Base cases
        if n == 1:
            self.left = objects[0]
            self.right = None
            self.box = objects[0].bounding_box()
            return
        elif n == 2:
            self.left = objects[0]
            self.right = objects[1]
            box_left = self.left.bounding_box()
            box_right = self.right.bounding_box()
            self.box = rtu.surrounding_box(box_left, box_right)
            return

        # Compute bounding box of all objects
        object_boxes = [(obj, obj.bounding_box()) for obj in objects]
        bbox_min = rtu.Vec3(float('inf'), float('inf'), float('inf'))
        bbox_max = rtu.Vec3(float('-inf'), float('-inf'), float('-inf'))
        for obj, box in object_boxes:
            bbox_min = rtu.Vec3(
                min(bbox_min.x(), box.min.x()),
                min(bbox_min.y(), box.min.y()),
                min(bbox_min.z(), box.min.z())
            )
            bbox_max = rtu.Vec3(
                max(bbox_max.x(), box.max.x()),
                max(bbox_max.y(), box.max.y()),
                max(bbox_max.z(), box.max.z())
            )

        # Split axis = longest axis
        extent = bbox_max - bbox_min
        axis = np.argmax([extent.x(), extent.y(), extent.z()])

        # Sort objects along the chosen axis using their bounding box centers
        object_boxes.sort(key=lambda obj_box: 0.5 * (obj_box[1].min[axis] + obj_box[1].max[axis]))
        objects = [obj for obj, _ in object_boxes]

        # Split in the middle (median)
        mid = n // 2
        left_objects = objects[:mid]
        right_objects = objects[mid:]

        # Create children recursively
        self.left = BVHNode(left_objects, max_leaf_size)
        self.right = BVHNode(right_objects, max_leaf_size)

        # Compute enclosing bounding box
        self.box = rtu.surrounding_box(self.left.bounding_box(), self.right.bounding_box())

    def intersect(self, rRay, cInterval):
        if not self.box.hit(rRay, rtu.Interval(cInterval.min_val, cInterval.max_val)):
            return None

        hit_left = self.left.intersect(rRay, cInterval)
        if hit_left:
            new_interval = rtu.Interval(cInterval.min_val, hit_left.t)
        else:
            new_interval = rtu.Interval(cInterval.min_val, cInterval.max_val)

        hit_right = None
        if self.right:
            hit_right = self.right.intersect(rRay, new_interval)

        return hit_right if hit_right else hit_left

    def bounding_box(self):
        return self.box