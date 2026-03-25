# object class
import RT_utility as rtu
import RT_BVH as rtb
import random
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
    def __init__(self, triangles, scale=1.0, rotation_deg=(0, 0, 0)):
        transformed_triangles = self._apply_transform(triangles, scale, rotation_deg)
        self.triangles = transformed_triangles
        self.bvh = BVHNode(transformed_triangles)

    def setScaleAndRotation(self,scale,rotation_deg):
        transformed_triangles = self._apply_transform(self.triangles,scale,rotation_deg)
        self.triangles = transformed_triangles
        self.bvh = BVHNode(transformed_triangles)

    def _apply_transform(self, triangles, scale, rotation_deg):
        rad_x = math.radians(rotation_deg[0])
        rad_y = math.radians(rotation_deg[1])
        rad_z = math.radians(rotation_deg[2])

        new_triangles = []
        for tri in triangles:
            v0_new = self._rotate_and_scale(tri.v0, scale, rad_x, rad_y, rad_z)
            v1_new = self._rotate_and_scale(tri.v1, scale, rad_x, rad_y, rad_z)
            v2_new = self._rotate_and_scale(tri.v2, scale, rad_x, rad_y, rad_z)
            
            # Create a new triangle with the same material
            new_tri = Triangle(v0_new, v1_new, v2_new, tri.material)
            new_triangles.append(new_tri)
        
        return new_triangles

    def _rotate_and_scale(self, v, s, rx, ry, rz):
        x, y, z = v.x() * s, v.y() * s, v.z() * s

        if rx != 0:
            new_y = y * math.cos(rx) - z * math.sin(rx)
            new_z = y * math.sin(rx) + z * math.cos(rx)
            y, z = new_y, new_z

        if ry != 0:
            new_x = x * math.cos(ry) + z * math.sin(ry)
            new_z = -x * math.sin(ry) + z * math.cos(ry)
            x, z = new_x, new_z

        if rz != 0:
            new_x = x * math.cos(rz) - y * math.sin(rz)
            new_y = x * math.sin(rz) + y * math.cos(rz)
            x, y = new_x, new_y

        return rtu.Vec3(x, y, z)

    def intersect(self, rRay, cInterval):
        return self.bvh.intersect(rRay, cInterval)

class BVHNode(Object):
    def __init__(self, objects):
        super().__init__()

        objects = list(objects) 

        axis = random.randint(0, 2)
        
        objects = [(obj, obj.bounding_box()) for obj in objects]
        objects.sort(key=lambda item: item[1].min[axis])
        objects = [item[0] for item in objects]
        
        n = len(objects)

        if n == 1:
            self.left = objects[0]
            self.right = None

        elif n == 2:
            self.left = objects[0]
            self.right = objects[1]

        else:
            mid = n // 2
            self.left = BVHNode(objects[:mid])
            self.right = BVHNode(objects[mid:])

        if self.right is None:
            self.box = self.left.bounding_box()
        else:
            box_left = self.left.bounding_box()
            box_right = self.right.bounding_box()
            self.box = rtu.surrounding_box(box_left, box_right)

    def intersect(self, rRay, cInterval):
        # IMPORTANT: use copy of interval
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