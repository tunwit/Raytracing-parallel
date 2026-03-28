# a simple integrator class
# A ray is hit and then get the color.
# It is the rendering equation solver.
import RT_utility as rtu
import RT_ray as rtr
import RT_material as rtm
import math

class Integrator():
    def __init__(self, bDlight=True, bSkyBG=False, roulette=True) -> None:
        self.bool_direct_lighting = bDlight
        self.bool_sky_background = bSkyBG
        self.roulette = roulette

    def compute_scattering(self, rGen_ray, scene, maxDepth):
        if maxDepth <= 0:
            return rtu.Color()
    
        found_hit = scene.find_intersection(
            rGen_ray,
            rtu.Interval(0.000001, rtu.infinity_number)
        )

        if found_hit == True:
            hinfo = scene.getHitList()
            hmat = hinfo.getMaterial()
            sinfo = hmat.scattering(rGen_ray, hinfo)

            # if no scattering (It is a light source)
            if sinfo is None:
                return hmat.emitting()

            Le = rtu.Color()

            # direct lighting
            if self.bool_direct_lighting :
                eps = 1e-5
                
                for light in scene.point_light_list:
                    if rtu.random_double() > 0.5:
                        continue
                    surface_point = hinfo.getP()

                    # old style: compute vector to light
                    tolight_vec = light.center - surface_point
                    max_distance = tolight_vec.len()
                    if max_distance <= eps:
                        continue

                    # normalize for correct NdotL
                    tolight_dir = tolight_vec / max_distance

                    # old style shadow ray, but stop before the light sphere a bit
                    light_radius = getattr(light, 'radius', 0.0)
                    shadow_max = max_distance - light_radius - eps
                    if shadow_max <= eps:
                        shadow_max = max_distance

                    tolight_ray = rtr.Ray(surface_point, tolight_dir, rGen_ray.getTime())
                    occlusion_hit = scene.find_occlusion(
                        tolight_ray,
                        rtu.Interval(0.000001, shadow_max)
                    )

                    if not occlusion_hit:
                        Le_BRDF = hmat.BRDF(rGen_ray, tolight_ray, hinfo)

                        NdotLe = rtu.Vec3.dot_product(hinfo.getNormal(), tolight_dir)
                        if NdotLe < 1e-06:
                            NdotLe = 0.0

                        light_mat = light.material

                        # spotlight path
                        if hasattr(light_mat, 'direct_radiance'):
                            direct_L_i = light_mat.direct_radiance(light.center, surface_point)
                        else:
                            # old behavior for normal light
                            direct_L_i = light_mat.emitting()

                        Le = Le + (Le_BRDF * direct_L_i * NdotLe)

            throughput = sinfo.attenuation_color

            # keep old roulette behavior
            if self.roulette and maxDepth <= 2:
                p = min(0.95, max(throughput.r(), throughput.g(), throughput.b()))
                if rtu.random_double() > p:
                    return Le
                throughput = throughput / p

            L_i = self.compute_scattering(sinfo.scattered_ray, scene, maxDepth - 1)
            return Le + (throughput * L_i)

        if self.bool_sky_background:
            return scene.get_sky_background_color(rGen_ray)
        return scene.getBackgroundColor()

