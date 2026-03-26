import RT_utility as rtu
import RT_camera as rtc
import RT_renderer as rtren
import RT_material as rtm
import RT_scene as rts
import RT_object as rto
import RT_integrator as rti
import RT_light as rtl
import RT_texture as rtt
import RT_transformer as rttr

def renderDoF():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 3840
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 100
    main_camera.max_depth = 5
    main_camera.vertical_fov = 60
    main_camera.look_from = rtu.Vec3(-2, 2, 2)
    main_camera.look_at = rtu.Vec3(0, 0, 0)
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
    main_camera.samples_per_pixel = 10
    main_camera.max_depth = 5
    main_camera.vertical_fov = 60
    main_camera.look_from = rtu.Vec3(1, 2, -2)
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
    main_camera.samples_per_pixel =  1
    main_camera.max_depth = 10
    main_camera.vertical_fov = 60
    # main_camera.look_from = rtu.Vec3(7, 5, -3)
    main_camera.look_from = rtu.Vec3(4, 4, -4)
    main_camera.look_at = rtu.Vec3(0, 0, 0)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)
    
    defocus_angle = 0
    focus_distance = (main_camera.look_at - main_camera.look_from).len()
    main_camera.init_camera(defocus_angle, focus_distance)

    tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))
    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)


    mat_blinn1 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.8), 0.5, 0.2, 8)
    mat_blinn2 = rtm.Blinn(rtu.Color(0.4, 0.5, 0.4), 0.5, 0.6, 8)
    mat_blinn3 = rtm.Blinn(rtu.Color(0.8, 0.5, 0.4), 0.5, 0.2, 8)

    mat_red   = rtm.Lambertian(rtu.Color(1, 0, 0))  # +X
    mat_green = rtm.Lambertian(rtu.Color(0, 1, 0))  # +Y
    mat_blue  = rtm.Lambertian(rtu.Color(0, 0, 1))  # +Z

    light = rtl.Diffuse_light(rtu.Color(0.5, 0.5, 0.4))


    sph_left = rto.Sphere(rtu.Vec3(-1.0,   0.0,-1),  0.5, mat_blinn1)
    building =  rttr.MeshTranformer.obj_mtl_to_mesh("model/building/tinker.obj",rtm.Lambertian,rtu.Vec3(0,0,0))
    building.set_transform(1.5,rtu.Vec3(0,-90,0))

    car =  rttr.MeshTranformer.obj_mtl_to_mesh("model/car/tinker.obj",rtm.Lambertian,rtu.Vec3(0,0,-4))
    car.set_transform(0.4,rtu.Vec3(0,180,0))
    # car2 =  rttr.MeshTranformer.obj_mtl_to_mesh("model/car/tinker.obj",rtm.Lambertian,rtu.Vec3(0,0,6))
    # car2.set_transform(0.4,rtu.Vec3(0,180,0))

    # sph_left.add_moving(rtu.Vec3(-1.0,   0.0,-1) + rtu.Vec3(0.0, 0.5,0.0))
    # return 
    world = rts.Scene()
    street_light = rttr.MeshTranformer.obj_mtl_to_mesh("model/street_with_light/tinker.obj",rtm.Phong,rtu.Vec3(-3,-0.5,0))
    street_light.set_transform(1,rtu.Vec3(0,180,0))

    street = rttr.MeshTranformer.obj_mtl_to_mesh("model/street/tinker.obj",rtm.Phong,rtu.Vec3(1,-0.25,0))

    world.add_object(rto.Sphere(rtu.Vec3(   0,-100.5,-1),  100, mat_tex_checker_bw))
    # world.add_object(sph_left)    # left
    world.add_object(rto.Sphere(rtu.Vec3(   0.5, 5 ,0.5 ),  0.05, light))    # center
    # world.add_object(rto.Sphere(rtu.Vec3( 3,0,0),  0.5, mat_blinn1))    # right
    world.add_object(building)
    world.add_object(car)
    # world.add_object(street_light)
    world.add_object(street)



    intg = rti.Integrator(bSkyBG=False,roulette=True)

    renderer = rtren.Renderer(main_camera, intg, world)
    renderer.render(type=rtu.RenderType.JITTERED)
    renderer.write_img2png('testMesh_new.png')    


if __name__ == "__main__":
    # renderDoF()
    renderTriangle()


