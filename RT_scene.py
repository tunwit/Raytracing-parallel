import RT_utility as rtu
import numpy as np
import RT_object as rto
class Scene:
    def __init__(self, cBgcolor=rtu.Color(0.01, 0.01, 0.01)) -> None:
        self.obj_list = []
        self.hit_list = None
        self.background_color = cBgcolor
        self.light_list = []
        self.point_light_list = []
        self._scene_bvh = None          # built lazily on first render

    def add_object(self, obj):
        self.obj_list.append(obj)
        self._scene_bvh = None          # invalidate cached BVH
 
    # ── BVH helpers ──────────────────────────────────────────────────────────
 
    def build_bvh(self):
        """Build a top-level BVH over every object in the scene.
        Called automatically by find_lights() → render(), but you can also
        call it manually after adding all objects.
        """
        if len(self.obj_list) == 0:
            self._scene_bvh = None
            return
        try:
            self._scene_bvh = rto.BVHNode(self.obj_list)
            print(f"[Scene] Top-level BVH built over {len(self.obj_list)} object(s).")
        except Exception as e:
            print(f"[Scene] BVH build failed ({e}), falling back to linear traversal.")
            self._scene_bvh = None
 
    # ── Intersection ─────────────────────────────────────────────────────────
 
    def find_intersection(self, vRay, cInterval):
        # Fast BVH path
        if self._scene_bvh is not None:
            hinfo = self._scene_bvh.intersect(vRay, rtu.Interval(cInterval.min_val, cInterval.max_val))
            if hinfo is not None:
                self.hit_list = hinfo
                return True
            return False
 
        # Fallback: linear traversal (used when BVH is unavailable)
        found_hit = False
        closest_tmax = cInterval.max_val
        for obj in self.obj_list:
            hinfo = obj.intersect(vRay, rtu.Interval(cInterval.min_val, closest_tmax))
            if hinfo is not None:
                closest_tmax = hinfo.getT()
                found_hit = True
                self.hit_list = hinfo
        return found_hit
 
    def find_occlusion(self, vRay, cInterval):
        interval = rtu.Interval(cInterval.min_val, cInterval.max_val)
 
        # BVH path: any hit inside the interval = occluded
        if self._scene_bvh is not None:
            hinfo = self._scene_bvh.intersect(vRay, interval)
            return hinfo is not None
 
        # Fallback linear
        number_of_hit = 0
        for obj in self.obj_list:
            if hasattr(obj, 'bvh'):
                hinfo = obj.bvh.intersect(vRay, interval)
            else:
                hinfo = obj.intersect(vRay, interval)
            if hinfo is not None:
                number_of_hit += 1
            if number_of_hit > 1:
                return True
        return False
 
    # ── Accessors ─────────────────────────────────────────────────────────────
 
    def getHitNormalAt(self, idx):
        return self.hit_list[idx].getNormal()
 
    def getHitList(self):
        return self.hit_list
 
    def getBackgroundColor(self):
        return self.background_color
 
    def get_sky_background_color(self, rGen_ray):
        unit_direction = rtu.Vec3.unit_vector(rGen_ray.getDirection())
        a = (unit_direction.y() + 1.0) * 0.5
        return rtu.Color(1, 1, 1) * (1.0 - a) + rtu.Color(0.5, 0.7, 1.0) * a
 
    # ── Light discovery ───────────────────────────────────────────────────────
 
    def find_lights(self):
        self.light_list = []
        self.point_light_list = []

        for obj in self.obj_list:
            if isinstance(obj, rto.Mesh):
                for tri in obj.triangles:
                    if tri.material and tri.material.is_light():
                        self.light_list.append(tri)
            else:
                if obj.material and obj.material.is_light():
                    self.light_list.append(obj)

        self.find_point_lights()
        self.build_bvh()

    def find_point_lights(self):
        for light in self.light_list:
            if isinstance(light, rto.Sphere):
                self.point_light_list.append(light)
