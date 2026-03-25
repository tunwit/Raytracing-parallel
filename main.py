import RT_utility as rtu
import RT_camera as rtc
import RT_renderer as rtren
import RT_material as rtm
import RT_scene as rts
import RT_object as rto
import RT_integrator as rti
import RT_light as rtl
import RT_texture as rtt

def renderDoF():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 3840
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 100
    main_camera.max_depth = 5
    main_camera.vertical_fov = 60
    main_camera.look_from = rtu.Vec3(-2, 2, 1)
    main_camera.look_at = rtu.Vec3(0, 0, -1)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)

    aperture = 1.0
    defocus_angle = 2.0
    focus_distance = 5.0
    main_camera.init_camera(defocus_angle, focus_distance,aperture)
    # add objects to the scene

    tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))

    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)

    mat_blinn1 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.8), 0.5, 0.2, 8)
    mat_blinn2 = rtm.Blinn(rtu.Color(0.4, 0.5, 0.4), 0.5, 0.6, 8)
    mat_blinn3 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.4), 0.5, 0.2, 8)


    world = rts.Scene()
    world.add_object(rto.Sphere(rtu.Vec3(   0,-100.5,-1),  100, mat_tex_checker_bw))
    world.add_object(rto.Sphere(rtu.Vec3(-1.0,   0.0,-1),  0.5, mat_blinn1))    # left
    world.add_object(rto.Sphere(rtu.Vec3(   0,   0.0,-1),  0.5, mat_blinn2))    # center
    world.add_object(rto.Sphere(rtu.Vec3( 1.0,   0.0,-1),  0.5, mat_blinn3))    # right

    intg = rti.Integrator(bSkyBG=True)

    renderer = rtren.Renderer(main_camera, intg, world)
    renderer.render(type=rtu.RenderType.JITTERED)
    renderer.write_img2png('week10_aperture_jittered_DoF.png')    

def renderMoving():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 480 
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 100
    main_camera.max_depth = 5
    main_camera.vertical_fov = 60
    main_camera.look_from = rtu.Vec3(-2, 2, 1)
    main_camera.look_at = rtu.Vec3(0, 0, -1)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)

    defocus_angle = 0.0
    focus_distance = 5.0
    main_camera.init_camera(defocus_angle, focus_distance)
    # add objects to the scene

    tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))

    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)

    mat_blinn1 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.8), 0.5, 0.2, 8)
    mat_blinn2 = rtm.Blinn(rtu.Color(0.4, 0.5, 0.4), 0.5, 0.6, 8)
    mat_blinn3 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.4), 0.5, 0.2, 8)


    sph_left = rto.Sphere(rtu.Vec3(-1.0,   0.0,-1),  0.5, mat_blinn1)
    sph_left.add_moving(rtu.Vec3(-1.0,   0.0,-1) + rtu.Vec3(0.0, 0.5,0.0))

    world = rts.Scene()
    world.add_object(rto.Sphere(rtu.Vec3(   0,-100.5,-1),  100, mat_tex_checker_bw))
    world.add_object(sph_left)    # left
    world.add_object(rto.Sphere(rtu.Vec3(   0,   0.0,-1),  0.5, mat_blinn2))    # center
    world.add_object(rto.Sphere(rtu.Vec3( 1.0,   0.0,-1),  0.5, mat_blinn3))    # right

    intg = rti.Integrator(bSkyBG=True)

    renderer = rtren.Renderer(main_camera, intg, world)
    renderer.render(type=rtu.RenderType.JITTERED)
    renderer.write_img2png('week10_moving_jitter.png')    

def renderTriangle():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 480  
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel =  50
    main_camera.max_depth = 5
    main_camera.vertical_fov = 60
    main_camera.look_from = rtu.Vec3(2, 2, 2)
    main_camera.look_at   = rtu.Vec3(0, 0, 0)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)
    
    defocus_angle = 0.0
    focus_distance = 5.0
    main_camera.init_camera(defocus_angle, focus_distance)

    tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))
    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)

    tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))

    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)

    mat_blinn1 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.8), 0.5, 0.2, 8)
    mat_blinn2 = rtm.Blinn(rtu.Color(0.4, 0.5, 0.4), 0.5, 0.6, 8)
    mat_blinn3 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.4), 0.5, 0.2, 8)
    mirror = rtm.Mirror(rtu.Color(1, 1, 1))
    dialectict = rtm.Dielectric(rtu.Color(1.0, 1.0, 1.0), 1.0)



    sph_left = rto.Sphere(rtu.Vec3(-1.0,   0.0,-1),  0.5, mat_blinn1)
    # sph_left.add_moving(rtu.Vec3(-1.0,   0.0,-1) + rtu.Vec3(0.0, 0.5,0.0))

    world = rts.Scene()
    mesh = rtu.MeshTranformer.stl_to_mesh("House Mk7 v30 Door Front.stl",mat_blinn2,rtu.Vec3(-1.5,0.5,0.5))
    mesh.setScaleAndRotation(1,rtu.Vec3(-90,90,0))
    world.add_object(rto.Sphere(rtu.Vec3(   0,-100.5,-1),  100, mat_blinn1))
    world.add_object(sph_left)    # left
    world.add_object(rto.Sphere(rtu.Vec3(   0,   0.0,-1),  0.7, mirror))    # center
    world.add_object(rto.Sphere(rtu.Vec3( 1.0,   0.0,-1),  0.5, dialectict))    # right
    world.add_object(mesh)


    intg = rti.Integrator(bSkyBG=True)

    renderer = rtren.Renderer(main_camera, intg, world)
    renderer.render(type=rtu.RenderType.JITTERED)
    renderer.write_img2png('testMesh.png')    


if __name__ == "__main__":
    # renderDoF()
    renderTriangle()


