import numpy as np
from PIL import Image as im
import math
import RT_pbar
import multiprocessing as mp
from datetime import datetime
from RT_utility import RenderType
from concurrent.futures import ThreadPoolExecutor

MAX_CPU = int(mp.cpu_count())

_worker_camera = None
_worker_integrator = None
_worker_scene = None
_worker_sqrt_spp = None

def init_worker(camera, integrator, scene, sqrt_spp=None):
    global _worker_camera, _worker_integrator, _worker_scene, _worker_sqrt_spp,_active_worker
    _worker_camera = camera
    _worker_integrator = integrator
    _worker_scene = scene
    _worker_sqrt_spp = sqrt_spp
    print(f"[Worker PID {mp.current_process().pid}] initialized")


def generate_tiles(width, height, tile_size):
    tiles = []
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            x1 = min(x + tile_size, width)
            y1 = min(y + tile_size, height)
            tiles.append((x, x1, y, y1))
    return tiles


def compute_tile(tile):
    x0, x1, y0, y1 = tile
    width, height = x1 - x0, y1 - y0
    tile_data = np.zeros((height, width, 3), dtype=np.float32)

    for j in range(y0, y1):
        for i in range(x0, x1):
            r = g = b = 0.0
            for spp in range(_worker_camera.samples_per_pixel):
                ray = _worker_camera.get_ray(i, j)
                sample = _worker_integrator.compute_scattering(
                    ray, _worker_scene, _worker_camera.max_depth
                )
                r += sample.r()
                g += sample.g()
                b += sample.b()

            tile_data[j - y0, i - x0, 0] = r
            tile_data[j - y0, i - x0, 1] = g
            tile_data[j - y0, i - x0, 2] = b

    return x0, y0, tile_data


def compute_tile_jittered(tile):
    x0, x1, y0, y1 = tile
    width, height = x1 - x0, y1 - y0
    tile_data = np.zeros((height, width, 3), dtype=np.float32)
    total_samples = _worker_sqrt_spp * _worker_sqrt_spp

    for j in range(y0, y1):
        for i in range(x0, x1):
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

            tile_data[j - y0, i - x0, 0] = r / total_samples
            tile_data[j - y0, i - x0, 1] = g / total_samples
            tile_data[j - y0, i - x0, 2] = b / total_samples

    return x0, y0, tile_data



def compute_tile_jittered_adaptive(tile):
    x0, x1, y0, y1 = tile
    width, height = x1 - x0, y1 - y0
    tile_data = np.zeros((height, width, 3), dtype=np.float32)

    # --- PRO SETTINGS ---
    MIN_SAMPLES = 32      # Need a decent baseline for stats to be accurate
    MAX_SAMPLES = _worker_sqrt_spp * _worker_sqrt_spp
    BATCH_SIZE = 32       # Larger batches are more efficient for the CPU
    MAX_ERROR = 0.02    # 2% relative error allowed (adjust this for quality)
    
    for j in range(y0, y1):
        for i in range(x0, x1):
            sum_r = sum_g = sum_b = 0.0
            sum_lum = 0.0
            sum_lum_sq = 0.0
            count = 0
            
            while count < MAX_SAMPLES:
                for _ in range(BATCH_SIZE):
                    if count >= MAX_SAMPLES: break

                    ray = _worker_camera.get_jittered_stratified_ray(i, j,count)
                    sample = _worker_integrator.compute_scattering(
                        ray, _worker_scene, _worker_camera.max_depth
                    )
                    
                    s_r, s_g, s_b = sample.r(), sample.g(), sample.b()
                    sum_r += s_r
                    sum_g += s_g
                    sum_b += s_b

                    # Stats based on luminance
                    lum = 0.2126 * s_r + 0.7152 * s_g + 0.0722 * s_b
                    sum_lum += lum
                    sum_lum_sq += lum * lum
                    count += 1
                
                if count >= MIN_SAMPLES:
                    mean_lum = sum_lum / count

                    # If the pixel is pure black
                    if mean_lum < 0.0001: 
                        break
                    variance = max(0, (sum_lum_sq / count) - (mean_lum ** 2))
                    stdev = math.sqrt(variance)
                    
                    # 1.96 is the Z-score for 95%
                    interval_width = 1.96 * (stdev / math.sqrt(count))

                    # STOP if the error is small RELATIVE to the brightness
                    if interval_width < (MAX_ERROR * mean_lum):
                        break
            
            tile_data[j - y0, i - x0, 0] = sum_r / count
            tile_data[j - y0, i - x0, 1] = sum_g / count
            tile_data[j - y0, i - x0, 2] = sum_b / count

    return x0, y0, tile_data
    
class Renderer:
    def __init__(self, cCamera, iIntegrator, sScene) -> None:
        self.camera = cCamera
        self.integrator = iIntegrator
        self.scene = sScene

    def _get_compute_function(self, t: RenderType):
        if t == RenderType.JITTERED:
            sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))
            return sqrt_spp, compute_tile_jittered_adaptive
        return None, compute_tile

    def render(self, type: RenderType = RenderType.NORMAL):
        self.scene.find_lights()
        tile_size = self._compute_adaptive_tile_size(
            self.camera.img_width, self.camera.img_height, self.camera.samples_per_pixel
        )
        tile_size= 8
        
        tiles = generate_tiles(self.camera.img_width, self.camera.img_height, tile_size)
        avg_pixel_work = self.camera.samples_per_pixel
        base_chunksize = max(1, len(tiles) // (2 * MAX_CPU))
        chunksize = max(1, int(base_chunksize / math.sqrt(avg_pixel_work)))
        chunksize = 1
        sqrt, func = self._get_compute_function(type)

        print(f"Initializing Multi-core Render...")
        print(
            f"Cores: {MAX_CPU} | Tile Size: {tile_size} | "
            f"Tiles: {len(tiles)} | Chunksize: {chunksize}"
        )

        with mp.Pool(
            MAX_CPU,
            initializer=init_worker,
            initargs=(self.camera, self.integrator, self.scene, sqrt),
        ) as pool:
            renderbar = RT_pbar.start_animated_marker(len(tiles))
            for idx, (x0, y0, tile_data) in enumerate(
                pool.imap_unordered(func, tiles, chunksize=chunksize), start=1
            ):
                self.camera.write_tile_to_film(x0, y0, tile_data)
                renderbar.update(idx,recent=datetime.now().strftime("%H:%M %S"))
            renderbar.finish()

    def _compute_adaptive_tile_size(self, width, height, spp, adaptive=False):
        if adaptive:
            return 8  # 🔥 sweet spot (try 8–32 depending on scene)

        base_pixel_count = 1024  
        workload_factor = math.sqrt(spp)
        target_tile_area = max(256, base_pixel_count / workload_factor)

        side = math.sqrt(target_tile_area)
        tile_size = 2**int(math.log2(side) + 0.5)

        return int(max(8, min(tile_size, 256)))

    def write_img2png(self, strPng_filename):
        png_film = self.camera.film * 255
        data = im.fromarray(png_film.astype(np.uint8))
        data.save(strPng_filename)
