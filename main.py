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

def createRoom(world):
    concreat_tex = rtt.ConcreteTexture(rtu.Color(1,1,1),2)
    concreat_mat = rtm.TextureColor(concreat_tex)
    white = rtm.Lambertian(rtu.Color(1,1,1))
    laminat_tex = rtt.ImageTexture("textures/laminate.jpg")
    laminat_mat = rtm.TextureColor(laminat_tex)

    #---- floor ----
    world.add_object(
        rto.Quad(
            rtu.Vec3(-100, 0 , -100),       # origin (shifted so center stays same)
            rtu.Vec3(200, 0, 0),           # width
            rtu.Vec3(0, 0, 200),           # depth
            laminat_mat
        )
    )

#     #---- right wall ----
#     world.add_object(
#     rto.Quad(
#         rtu.Vec3(-100, 0, -100),   # bottom-left
#         rtu.Vec3(200, 0, 0),     # width (X)
#         rtu.Vec3(0, 100, 0),     # height (Y)
#         white
#     )
# )
# #     #---- left wall ----
#     world.add_object(
#     rto.Quad(
#         rtu.Vec3(-100, 0, 100),
#         rtu.Vec3(200, 0, 0),
#         rtu.Vec3(0, 100, 0),
#         white
#         )
#     )

#     #---- back wall ----
#     world.add_object(
#     rto.Quad(
#         rtu.Vec3(100, 0, -100),
#         rtu.Vec3(0, 0, 200),
#         rtu.Vec3(0, 100, 0),
#         white
#         )
#     )

    # # #---- top wall ----
    # world.add_object(
    #     rto.Quad(
    #         rtu.Vec3(-100, 100 , -100),       # origin (shifted so center stays same)
    #         rtu.Vec3(200, 0, 0),           # width
    #         rtu.Vec3(0, 0, 200),           # depth
    #         white
    #     )
    # )

    wall_y_min = 0
    wall_y_max = 100

    window_y_min = 20
    window_y_max = 50

    window_z_min = -30
    window_z_max = 80

    x = -50


    # #---- bottom window part ----
    # world.add_object(
    # rto.Quad(
    #     rtu.Vec3(x, wall_y_min, -100),
    #     rtu.Vec3(0, 0, 200),
    #     rtu.Vec3(0, window_y_min, 0),
    #     white
    #     )
    # )

    # #---- top window part ----
    # world.add_object(
    # rto.Quad(
    #     rtu.Vec3(x, window_y_max, -100),  
    #     rtu.Vec3(0, 0, 200),              
    #     rtu.Vec3(0, wall_y_max - window_y_max, 0), 
    #     white
    #     )
    # )
    
    # #---- right window part ----
    # world.add_object(
    # rto.Quad(
    #     rtu.Vec3(x, window_y_min, -100),   # start at left side
    #     rtu.Vec3(0, 0, window_z_min - (-100)),  # width in Z
    #     rtu.Vec3(0, window_y_max - window_y_min, 0),  # height
    #     white
    #     )
    # )
    # #---- left window part ----
    # world.add_object(
    # rto.Quad(
    #     rtu.Vec3(x, window_y_min, window_z_max),  # start at right side of window
    #     rtu.Vec3(0, 0, 100 - window_z_max),       # remaining width
    #     rtu.Vec3(0, window_y_max - window_y_min, 0),
    #     white
    #     )
    # )
    

def renderTriangle():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 480  
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 10
    main_camera.max_depth = 4
    main_camera.vertical_fov = 90
    # main_camera.look_from = rtu.Vec3(7, 5, -3)
    # main_camera.look_from = rtu.Vec3(20, 200, 200)
    # main_camera.look_from = rtu.Vec3(-80, 40, -70)


    #  main_camera.look_from = rtu.Vec3(0, 40, -70)

    # main_camera.look_at = rtu.Vec3(-40,10,-10)

    main_camera.look_from = rtu.Vec3(-60, 45, -75)

    main_camera.look_at = rtu.Vec3(-35,10,-10)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)
    
    defocus_angle = 0
    focus_distance = (main_camera.look_at - main_camera.look_from).len()
    main_camera.init_camera(defocus_angle, focus_distance)

    sun_light = rtl.Diffuse_light(rtu.Color(1.0 , 0.94, 0.81),0.7)
    spotlight = rtl.SpotLight(rtu.Color(1.0 , 0.94, 0.81),rtu.Vec3(0,-1,0),30,50,1.5)

    #---- Texture ----
    tex_checker_bw = rtt.ImageTexture("textures/blueprint.jpg")

    #---- Material ----
    mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)
    lambertian_black_mat = rtm.Lambertian(rtu.Color(0,0,0))
    blinn_fabric = rtm.Blinn(rtu.Color(0,0,0),0.8,0.2,5)

    metal_mat = rtm.Metal(rtu.Color(0,0,0),0.5)
    metal_mat2 = rtm.Metal(rtu.Color(0,0,0),0.1)

    


    world = rts.Scene()
    # street_light = rttr.MeshTranformer.obj_mtl_to_mesh("model/street_with_light/tinker.obj",rtm.Phong,rtu.Vec3(-3,-0.5,0))
    # street_light.set_transform(1,rtu.Vec3(0,180,0))

    #---- Plate ----
    # world.add_object(
    #     rto.Quad(
    #         rtu.Vec3(-500, -0.5 , -500),       # origin (shifted so center stays same)
    #         rtu.Vec3(1000, 0, 0),           # width
    #         rtu.Vec3(0, 0, 1000),           # depth
    #         mat_tex_checker_bw
    #     )
    # )
    createRoom(world)
    sofa = rttr.MeshTranformer.obj_mtl_to_mesh("model/sofa/tinker.obj",blinn_fabric,rtu.Vec3(0,0,-10))
    sofa.set_transform(40,rtu.Vec3(0,90,0))
    world.add_object(sofa)

    table = rttr.MeshTranformer.obj_mtl_to_mesh("model/coffee_table/tinker.obj",metal_mat,rtu.Vec3(-40,0,-10))
    table.set_transform(25,rtu.Vec3(0,90,0))
    world.add_object(table)

    flower = rttr.MeshTranformer.obj_mtl_to_mesh("model/flower_vase/tinker.obj",lambertian_black_mat,rtu.Vec3(-70,13,-41))
    flower.set_transform(6)
    world.add_object(flower) 

    lamp = rttr.MeshTranformer.obj_mtl_to_mesh("model/lamp/tinker.obj",metal_mat2,rtu.Vec3(-40,15,-10))
    lamp.set_transform(10)
    world.add_object(lamp)

    tv = rttr.MeshTranformer.obj_mtl_to_mesh("model/tv/tinker.obj",lambertian_black_mat,rtu.Vec3( -70,0,-10))
    tv.set_transform(35,rtu.Vec3(0,90,0))
    world.add_object(tv) 

    sun = rto.Sphere(rtu.Vec3(-40,37,-10),3,sun_light)
    world.add_object(sun)

    intg = rti.Integrator(bSkyBG=False,roulette=True)

    renderer = rtren.Renderer(main_camera, intg, world)
    renderer.render(type=rtu.RenderType.JITTERED)
    renderer.write_img2png('test_1024_8.png')    

if __name__ == "__main__":
    # renderDoF()
    renderTriangle()