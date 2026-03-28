import RT_utility as rtu
import RT_material as rtm
import math

class Light(rtm.Material):
    def __init__(self) -> None:
        super().__init__()

    def scattering(self, rRayIn, hHinfo):
        return None

    def emitting(self):
        return rtu.Color(0,0,0)

    def is_light(self):
        return True


class Diffuse_light(Light):
    def __init__(self, cAlbedo, intensity=1.0, linear=0.0, quadratic=0.0) -> None:
        super().__init__()
        self.light_color = cAlbedo
        self.intensity = intensity
        self.linear = linear
        self.quadratic = quadratic

    def scattering(self, rRayIn, hHinfo):
        return None

    def emitting(self):
        return self.light_color

    def direct_radiance(self, light_pos, surface_point):
        to_point = surface_point - light_pos
        dist = to_point.len()
        if dist <= 1e-8:
            return rtu.Color()

        atten = 1.0 / (1.0 + self.linear * dist + self.quadratic * dist * dist)
        return self.light_color * self.intensity * atten


class SpotLight(Diffuse_light):
    def __init__(self, cAlbedo, direction, inner_deg, outer_deg,
                 intensity=1.0, linear=0.0, quadratic=0.0) -> None:
        super().__init__(cAlbedo, intensity, linear, quadratic)

        self.direction = rtu.Vec3.unit_vector(direction)

        if inner_deg > outer_deg:
            inner_deg, outer_deg = outer_deg, inner_deg

        self.inner_cos = math.cos(math.radians(inner_deg))
        self.outer_cos = math.cos(math.radians(outer_deg))

    def direct_radiance(self, light_pos, surface_point):
        to_point = surface_point - light_pos
        dist = to_point.len()
        if dist <= 1e-8:
            return rtu.Color()

        L = rtu.Vec3.unit_vector(to_point)
        theta = rtu.Vec3.dot_product(self.direction, L)

        if theta <= self.outer_cos:
            return rtu.Color()

        if theta >= self.inner_cos:
            spot = 1.0
        else:
            t = (theta - self.outer_cos) / max(self.inner_cos - self.outer_cos, 1e-8)
            spot = t * t * (3.0 - 2.0 * t)

        atten = 1.0 / (1.0 + self.linear * dist + self.quadratic * dist * dist)
        return self.light_color * self.intensity * atten * spot