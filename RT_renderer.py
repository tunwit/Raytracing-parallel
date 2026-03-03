# renderer class

import RT_utility as rtu
import numpy as np
from PIL import Image as im
import math
import RT_pbar
import multiprocessing as mp
import time

_worker_camera = None
_worker_integrator = None
_worker_scene = None
_worker_sqrt_spp = None

def init_worker(camera, integrator, scene, sqrt_spp=None):
    global _worker_camera
    global _worker_integrator
    global _worker_scene
    global _worker_sqrt_spp

    _worker_camera = camera
    _worker_integrator = integrator
    _worker_scene = scene
    _worker_sqrt_spp = sqrt_spp

def render_row(j):
    row_colors = []
    for i in range(_worker_camera.img_width):
        r = g = b = 0.0
        
        for spp in range(_worker_camera.samples_per_pixel):
            
            ray = _worker_camera.get_ray(i, j)
            sample = _worker_integrator.compute_scattering(
                ray, _worker_scene, _worker_camera.max_depth
            )
            r += sample.r()
            g += sample.g()
            b += sample.b()
        row_colors.append(rtu.Color(r, g, b))
    return j, row_colors


def render_row_jittered(j):
    row_colors = []

    for i in range(_worker_camera.img_width):
        r = g = b = 0.0

        for s_j in range(_worker_sqrt_spp):
            for s_i in range(_worker_sqrt_spp):
                ray = _worker_camera.get_jittered_ray(i, j, s_i, s_j)
                sample = _worker_integrator.compute_scattering(
                    ray, _worker_scene, _worker_camera.max_depth
                )
                r += sample.r()
                g += sample.g()
                b += sample.b()

        row_colors.append(rtu.Color(r, g, b))

    return j, row_colors

def render_tile(tile):
    x0, x1, y0, y1 = tile

    tile_pixels = []

    for j in range(y0, y1):
        for i in range(x0, x1):

            pixel_color = rtu.Color(0, 0, 0)

            for spp in range(_worker_camera.samples_per_pixel):
                ray = _worker_camera.get_ray(i, j)
                pixel_color += _worker_integrator.compute_scattering(
                    ray, _worker_scene, _worker_camera.max_depth
                )

            tile_pixels.append((i, j, pixel_color))

    return tile_pixels


def render_tile_jittered(tile):
    x0, x1, y0, y1 = tile

    tile_pixels = []

    for j in range(y0, y1):
        for i in range(x0, x1):

            pixel_color = rtu.Color(0, 0, 0)

            for s_j in range(_worker_sqrt_spp):
                for s_i in range(_worker_sqrt_spp):
                    ray = _worker_camera.get_jittered_ray(i, j, s_i, s_j)
                    pixel_color += _worker_integrator.compute_scattering(
                        ray, _worker_scene, _worker_camera.max_depth
                    )

            tile_pixels.append((i, j, pixel_color))

    return tile_pixels

class Renderer():

    def __init__(self, cCamera, iIntegrator, sScene) -> None:
        self.camera = cCamera
        self.integrator = iIntegrator
        self.scene = sScene
        pass


    def render(self):
        # gather lights to the light list
        self.scene.find_lights()

        with mp.Pool(mp.cpu_count(),
                     initializer=init_worker,
                     initargs=(self.camera, self.integrator, self.scene)) as pool:

            renderbar = RT_pbar.start_animated_marker(self.camera.img_height*self.camera.img_width)
            k = 0
                    
            for j, row in pool.imap_unordered(render_row,range(self.camera.img_height)):
                for i, pixel_color in enumerate(row):
                    self.camera.write_to_film(i, j, pixel_color)
                k += self.camera.img_width
                renderbar.update(k)
            
            renderbar.finish()

    def render_jittered(self):
        # gather lights to the light list
        self.scene.find_lights()
        renderbar = RT_pbar.start_animated_marker(self.camera.img_height*self.camera.img_width)
        k = 0
        sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))
                
        with mp.Pool(mp.cpu_count(),
                     initializer=init_worker,
                     initargs=(self.camera, self.integrator, self.scene,sqrt_spp)) as pool:

            renderbar = RT_pbar.start_animated_marker(self.camera.img_height*self.camera.img_width)
            k = 0
                    
            for j, row in pool.imap_unordered(render_row_jittered,range(self.camera.img_height)):
                for i, pixel_color in enumerate(row):
                    self.camera.write_to_film(i, j, pixel_color)
                k += self.camera.img_width
                renderbar.update(k)
            
            renderbar.finish()
        

    def write_img2png(self, strPng_filename):
        png_film = self.camera.film * 255
        data = im.fromarray(png_film.astype(np.uint8))
        data.save(strPng_filename)

