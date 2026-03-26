# Camera class

import RT_utility as rtu
import RT_ray as rtr

import numpy as np
import math
from PIL import Image as im

class Camera:
    def __init__(self) -> None:
        self.img_spectrum = 3
        self.aspect_ratio = 16.0/9.0
        self.img_width = 400
        self.center = rtu.Vec3()
        self.intensity = rtu.Interval(0.000, 0.999)
        self.samples_per_pixel = 10
        self.vertical_fov = 90
        self.look_from = rtu.Vec3(0, 0, -1)
        self.look_at = rtu.Vec3(0, 0, 0)
        self.vec_up = rtu.Vec3(0, 1, 0)

        self.Lens = None

        self.one_over_sqrt_spp = 1.0/math.sqrt(self.samples_per_pixel)

        self.defocus_disk_u = rtu.Vec3()
        self.defocus_disk_v = rtu.Vec3()

        self.init_camera()
        pass

    def compute_img_height(self):
        h = int(self.img_width / self.aspect_ratio)
        return  h if h > 1 else 1
    
    def init_camera(self,fDefocusAngle=0.0, fFocusDist=10.0):
        self.set_Lens(fDefocusAngle, fFocusDist)

        self.img_height = self.compute_img_height()
        self.center = self.look_from

        h = math.tan(math.radians(self.vertical_fov)/2.0)
        self.viewport_height = 2.0 * h * self.Lens.get_focus_dist()
        self.viewport_width = self.viewport_height * float(self.img_width/self.img_height)

        self.camera_frame_w = rtu.Vec3.unit_vector(self.look_from - self.look_at)
        self.camera_frame_u = rtu.Vec3.unit_vector(rtu.Vec3.cross_product(self.vec_up, self.camera_frame_w))
        self.camera_frame_v = rtu.Vec3.cross_product(self.camera_frame_w, self.camera_frame_u)

        self.viewport_u = self.camera_frame_u*self.viewport_width
        self.viewport_v = -self.camera_frame_v*self.viewport_height
        self.pixel_du = self.viewport_u / self.img_width
        self.pixel_dv = self.viewport_v / self.img_height

        self.viewport_upper_left = self.center - (self.camera_frame_w*self.Lens.get_focus_dist()) - self.viewport_u/2 - self.viewport_v/2
        self.pixel00_location = self.viewport_upper_left + (self.pixel_du+self.pixel_dv)*0.5
        self.film = np.zeros((self.img_height, self.img_width, self.img_spectrum))

        # compute defocus parameters.
        theta = math.radians(self.Lens.get_defocus_angle())
        defocus_radius = self.Lens.get_focus_dist() * math.tan(theta / 2)
        self.defocus_disk_u = self.camera_frame_u * defocus_radius
        self.defocus_disk_v = self.camera_frame_v * defocus_radius

    # call right before init_camera()
    def set_Lens(self, fDefocusAngle, fFocusDist):
        self.Lens = Thinlens(fDefocusAngle, fFocusDist)

    def write_to_film(self, widthId, heightId, cPixelColor):
        # scaling with samples_per_pixel
        scale = 1.0/self.samples_per_pixel
    
        r = cPixelColor.r()*scale
        g = cPixelColor.g()*scale
        b = cPixelColor.b()*scale

        r = rtu.linear_to_gamma(r, 2.0)
        g = rtu.linear_to_gamma(g, 2.0)
        b = rtu.linear_to_gamma(b, 2.0)

        self.film[heightId,widthId,0] = self.intensity.clamp(r)
        self.film[heightId,widthId,1] = self.intensity.clamp(g)
        self.film[heightId,widthId,2] = self.intensity.clamp(b)

    def write_tile_to_film(self, x0, y0, tile_data):
        tile_data = np.sqrt(tile_data)

        tile_data = np.clip(tile_data, 0.0, 1.0)

        h, w, _ = tile_data.shape
        self.film[y0:y0+h, x0:x0+w] = tile_data

    def get_center_ray(self, i, j):
        pixel_center = self.pixel00_location + (self.pixel_du*i) + (self.pixel_dv*j)
        ray_direction = pixel_center - self.center
        return rtr.Ray(self.center, ray_direction)

    def get_ray(self, i, j):
        pixel_center = self.pixel00_location + (self.pixel_du*i) + (self.pixel_dv*j)
        pixel_sample = pixel_center + self.random_pixel_in_square(self.pixel_du, self.pixel_dv)

        ray_origin = self.center
        if self.Lens.get_defocus_angle() > 1e-06:
            ray_origin = self.defocus_disk_sample()
        ray_direction = pixel_sample - ray_origin
        ray_time = rtu.random_double()              # an additional parameter for motion blur

        return rtr.Ray(ray_origin, ray_direction, ray_time)
    
    def get_jittered_ray(self, i, j, s_i, s_j):

        pixel_center = self.pixel00_location + (self.pixel_du*i) + (self.pixel_dv*j)
        pixel_sample = pixel_center + self.pixel_sample_square(self.pixel_du, self.pixel_dv, s_i, s_j) * 0.5

        ray_origin = self.center
        if self.Lens.get_defocus_angle() > 1e-06:
            ray_origin = self.defocus_disk_sample()
        ray_direction = pixel_sample - ray_origin
        ray_time = rtu.random_double()              # an additional parameter for motion blur

        return rtr.Ray(ray_origin, ray_direction,ray_time)

    def get_random_jittered_ray(self, i, j):

        pixel_center = self.pixel00_location + (self.pixel_du*i) + (self.pixel_dv*j)
        rd_x = rtu.random_double() - 0.5
        rd_y = rtu.random_double() - 0.5

        pixel_sample = pixel_center + (self.pixel_du * rd_x) + (self.pixel_dv * rd_y)

        ray_origin = self.center
        if self.Lens.get_defocus_angle() > 1e-06:
            ray_origin = self.defocus_disk_sample()
        ray_direction = pixel_sample - ray_origin
        ray_time = rtu.random_double()            

        return rtr.Ray(ray_origin, ray_direction,ray_time)
    
    def get_jittered_stratified_ray(self, i, j, sample_index):
        # Let's assume a 4x4 stratification grid (16 cells total)
        grid_size = 4 
        num_cells = grid_size * grid_size
        
        # Determine which cell this specific sample belongs to
        cell_idx = sample_index % num_cells
        cell_x = cell_idx % grid_size
        cell_y = cell_idx // grid_size
        
        # Calculate the boundaries of this specific cell within the pixel
        # Each cell is 1/grid_size wide/tall
        cell_width = 1.0 / grid_size
        
        # Pick a random spot ONLY within this tiny cell
        # random_double() returns 0.0 to 1.0
        stochastic_offset_x = (cell_x + rtu.random_double()) * cell_width - 0.5
        stochastic_offset_y = (cell_y + rtu.random_double()) * cell_width - 0.5
        
        # Standard ray math
        pixel_center = self.pixel00_location + (self.pixel_du * i) + (self.pixel_dv * j)
        pixel_sample = pixel_center + (self.pixel_du * stochastic_offset_x) + (self.pixel_dv * stochastic_offset_y)

        ray_origin = self.center
        if self.Lens.get_defocus_angle() > 1e-06:
            ray_origin = self.defocus_disk_sample()
            
        ray_direction = pixel_sample - ray_origin
        return rtr.Ray(ray_origin, ray_direction, rtu.random_double())

    def random_pixel_in_square(self, vDu, vDv):
        px = -0.5 + rtu.random_double()
        py = -0.5 + rtu.random_double()
        return (vDu*px) + (vDv*py)

    def pixel_sample_square(self, vDu, vDv, s_i, s_j):
        px = -0.5 + self.one_over_sqrt_spp * (s_i + rtu.random_double())
        py = -0.5 + self.one_over_sqrt_spp * (s_j + rtu.random_double())
        return (vDu * px) + (vDv * py)

    # an additional defocus method --> To move the ray orgin away from its center by defecous parameters.
    def defocus_disk_sample(self):
        pp = rtu.Vec3.random_vec3_in_unit_disk()
        du = (self.defocus_disk_u * pp.x())
        dv = (self.defocus_disk_v * pp.y())
        return self.center + du + dv


class Lens():
    def __init__(self) -> None:
        pass

class Thinlens(Lens):
    def __init__(self, fDefocusAngle=0.0, fFocusDist=10.0) -> None:
        super().__init__()

        self.defocus_angle = fDefocusAngle
        self.focus_distance = fFocusDist


    def get_focus_dist(self):
        return self.focus_distance
    def get_defocus_angle(self):
        return self.defocus_angle

    