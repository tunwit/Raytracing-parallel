# a simple integrator class
# A ray is hit and then get the color.
# It is the rendering equation solver.
import RT_utility as rtu
import RT_ray as rtr
import RT_material as rtm
import math

class Integrator():
    def __init__(self, bDlight=True, bSkyBG=False,roulette=True) -> None:
        self.bool_direct_lighting = bDlight
        self.bool_sky_background = bSkyBG
        self.roulette = roulette
        pass

    def compute_scattering(self, rGen_ray, scene, maxDepth):
        if maxDepth <= 0:
            return rtu.Color()
    
        # if the generated ray hits an object
        found_hit = scene.find_intersection(rGen_ray, rtu.Interval(0.000001, rtu.infinity_number))
        if found_hit == True:
            # get the hit info
            hinfo = scene.getHitList()
            # get the material of the object
            hmat = hinfo.getMaterial()
            # compute scattering
            sinfo = hmat.scattering(rGen_ray, hinfo)
            # if no scattering (It is a light source)
            if sinfo is None:
                # return Le
                return hmat.emitting()


            Le = rtu.Color()
            # if direct lighting is enabled
            if self.bool_direct_lighting:
                eps = 1e-5

                # for each point light
                for light in scene.point_light_list:
                    surface_point = hinfo.getP()
                    surface_normal = hinfo.getNormal()

                    tolight_vec = light.center - surface_point
                    light_distance = tolight_vec.len()
                    if light_distance <= eps:
                        continue

                    light_dir = rtu.Vec3.unit_vector(tolight_vec)

                    NdotLe = rtu.Vec3.dot_product(surface_normal, light_dir)
                    if NdotLe <= eps:
                        continue

                    # ยิง shadow ray จากผิวออกไปนิด เพื่อกัน self-intersection
                    light_radius = getattr(light, 'radius', 0.0)
                    shadow_max = light_distance - light_radius - eps
                    if shadow_max <= eps:
                        shadow_max = light_distance - eps
                    if shadow_max <= eps:
                        continue

                    tolight_ray = rtr.Ray(surface_point + surface_normal * eps, light_dir, rGen_ray.getTime())
                    occlusion_hit = scene.find_occlusion(tolight_ray, rtu.Interval(eps, shadow_max))

                    if not occlusion_hit:
                        Le_BRDF = hmat.BRDF(rGen_ray, tolight_ray, hinfo)

                        light_mat = light.material
                        if hasattr(light_mat, 'direct_radiance'):
                            direct_L_i = light_mat.direct_radiance(light.center, surface_point)
                        else:
                            direct_L_i = light_mat.emitting()

                        Le = Le + (Le_BRDF * direct_L_i * NdotLe)

            # return the color
            # Le*attennuation_color upto the point before reflection models otherwise it is not correct.
            L_i = rtu.Color()
            throughput = sinfo.attenuation_color
            if self.roulette and maxDepth <= 7:
                p = min(0.95, max(throughput.r(), throughput.g(), throughput.b()))
                if rtu.random_double() > p:
                    return Le
                throughput = throughput / p

            L_i = self.compute_scattering(sinfo.scattered_ray, scene, maxDepth - 1)
            return Le + (throughput * L_i)

        if self.bool_sky_background:
            return scene.get_sky_background_color(rGen_ray)
        return scene.getBackgroundColor()

