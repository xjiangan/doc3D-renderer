'''
Code for rendering the groundtruths of Doc3D dataset 
https://www3.cs.stonybrook.edu/~cvl/projects/dewarpnet/storage/paper.pdf (ICCV 2019)

This code renders the gts needed for the DewarpNet training (image, uv, 3D coordinates) 
and saves the .blend files. The .blend files can be later used 
to render other gts (normal, depth, checkerboard, albedo). 
Each .blend file takes ~2.5MB set the save_blend_file flag to False if you don't need.

Written by: Sagnik Das and Ke Ma
Stony Brook University, New York
December 2018

Updated for blender 2.8 by Jiang Xudong
HKUST
July 2020
'''
import glob
import json
import sys
import csv
import bpy
import bmesh
import random
import math
from mathutils import Vector, Euler
import os
import string
from bpy_extras.object_utils import world_to_camera_view
import argparse
import hashlib
from bpy import ops,context



def reset_blend():
    bpy.ops.wm.read_factory_settings()  # ...
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)  # ...

    # only worry about data in the startup scene
    for bpy_data_iter in (
            bpy.data.meshes,
            bpy.data.lights,
            bpy.data.images,
            bpy.data.materials
    ):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data, do_unlink=True)


def isVisible(mesh, cam):
    bm = bmesh.new()  # create an empty BMesh
    bm.from_mesh(mesh.data)
    cam_direction = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    cam_pos = cam.location
    # print(cam_direction)
    mat_world = mesh.matrix_world
    ct1 = 0
    ct2 = 0
    for v in bm.verts:
        co_ndc = world_to_camera_view(bpy.context.scene, cam, mat_world @ v.co)
        nm_ndc = cam_direction.angle(v.normal)
        # v1 = v.co - cam_pos
        # nm_ndc = v1.angle(v.normal)
        if (co_ndc.x < 0.03 or co_ndc.x > 0.97 or co_ndc.y < 0.03 or co_ndc.y > 0.97):
            bm.free()
            print('out of view')
            return False
        # normal may be in two directions
        if nm_ndc < math.radians(120):
            ct1 += 1
        if nm_ndc > math.radians(60):
            ct2 += 1
    if min(ct1, ct2) / 1000000. > 0.03:
        bm.free()
        print('ct1: {}, ct2: {}\n'.format(ct1, ct2))
        return False
    bm.free()
    return True


def select_object(ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    ob.select_set(state=True)
    bpy.context.view_layer.objects.active = ob


def prepare_scene():
    reset_blend()

    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = config["numSamples"]
    scene.cycles.use_square_samples = False
    scene.display_settings.display_device = 'sRGB'
    if random.random() > 0.5:
        bpy.data.scenes['Scene'].view_settings.view_transform = 'Filmic'
    else:
        bpy.data.scenes['Scene'].view_settings.view_transform = 'Standard'


def prepare_rendersettings():
    bpy.ops.object.select_all(action='DESELECT')  # ...
    bpy.data.scenes['Scene'].cycles.device = config["device"]
    if config["device"]=="GPU" :
        cprefs = bpy.context.preferences.addons['cycles'].preferences
        print("previous compute device is "+cprefs.compute_device_type)
		# Attempt to set GPU device types if available
        for compute_device_type in ('CUDA', 'OPENCL', 'NONE'):
            try:
                cprefs.compute_device_type = compute_device_type
                print("compute device is "+cprefs.compute_device_type)
                break
            except TypeError:
                pass

		#Enable all CPU and GPU devices
        for device in cprefs.devices:
            device.use = True
    bpy.data.scenes['Scene'].render.resolution_x = config["resolution_x"]
    bpy.data.scenes['Scene'].render.resolution_y = config["resolution_y"]
    bpy.data.scenes['Scene'].render.resolution_percentage = config["resolution_percentage"]


def position_object(mesh_name):
    mesh = bpy.data.objects[mesh_name]
    select_object(mesh)
    # mesh.rotation_euler = [0.0, 0.0, 0.0]
    return mesh





def hdrLighting(envp, envstr):
    world = bpy.data.worlds['World']
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    bg_node = wnodes['Background']
    # hdr lighting

    # remove old node
    for node in wnodes:
        if node.type in ['OUTPUT_WORLD', 'BACKGROUND']:
            continue
        else:
            wnodes.remove(node)

    # hdr world lighting

    texcoord = wnodes.new(type='ShaderNodeTexCoord')
    mapping = wnodes.new(type='ShaderNodeMapping')
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, random.uniform(0, 6.28))
    wlinks.new(texcoord.outputs[0], mapping.inputs[0])
    envnode = wnodes.new(type='ShaderNodeTexEnvironment')
    wlinks.new(mapping.outputs[0], envnode.inputs[0])
    envnode.image = bpy.data.images.load(os.path.abspath(envp))
    bg_node.inputs[1].default_value = random.uniform(0.4 * envstr, 0.6 * envstr)
    wlinks.new(envnode.outputs[0], bg_node.inputs[0])

def pointLight():
    world = bpy.data.worlds['World']
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    bg_node = wnodes['Background']
    bg_node.inputs[1].default_value = 0

    d = random.uniform(3, 5)
    litpos = Vector(config["litpos"])
    eul = Euler((0, 0, 0), 'XYZ')
    eul.rotate_axis('Z', config["litEulerZ"])
    eul.rotate_axis('X', config["litEulerX"])
    litpos.rotate(eul)

    bpy.ops.object.add(type='LIGHT', location=litpos)
    lamp = bpy.data.lights[0]
    lamp.use_nodes = True
    nodes = lamp.node_tree.nodes
    links = lamp.node_tree.links
    for node in nodes:
        if node.type == 'OUTPUT':
            output_node = node
        elif node.type == 'EMISSION':
            lamp_node = node
    strngth = config["litStr"]
    lamp_node.inputs[1].default_value = strngth
    # Change warmness of light to simulate more natural lighting
    bbody = nodes.new(type='ShaderNodeBlackbody')
    color_temp = config["litColorTemp"]
    bbody.inputs[0].default_value = color_temp
    links.new(bbody.outputs[0], lamp_node.inputs[0])


    ## Area Lighting


# def areaLighting():
#     bpy.ops.object.lamp_add(type='AREA')
#     lamp=bpy.data.objects[bpy.data.lights[0].name]
#     select_object(lamp)
#     lamp.location=(0,0,10)
#     xt=random.uniform(-7.0,7.0)
#     yt=random.uniform(-7.0,7.0)
#     zt=random.uniform(-2.0,2.0)
#     bpy.ops.transform.translate( value=(xt,yt,zt))
#     bpy.ops.object.constraint_add(type='DAMPED_TRACK')
#     # bpy.data.objects[0].constraints['Damped Track'].target=bpy.data.objects['Empty']
#     lamp.constraints['Damped Track'].track_axis='TRACK_NEGATIVE_Z'
#     lamp=bpy.data.lights[bpy.data.lights[0].name]
#     lamp.shape='RECTANGLE'
#     size_x=random.uniform(10,12)
#     size_y=random.uniform(1,3)
#     lamp.size=size_x
#     lamp.size_y=size_y
#     lamp.use_nodes=True
#     nodes=lamp.node_tree.nodes
#     links=lamp.node_tree.links
#     for node in nodes:
#         if node.type=='OUTPUT':
#             output_node=node
#         elif node.type=='EMISSION':
#             lamp_node=node
#     strngth=random.uniform(500,600)
#     lamp_node.inputs[1].default_value=strngth
#
#     #Change warmness of light to simulate more natural lighting
#     bbody=nodes.new(type='ShaderNodeBlackbody')
#     color_temp=random.uniform(4000,9500)
#     bbody.inputs[0].default_value=color_temp
#     links.new(bbody.outputs[0],lamp_node.inputs[0])
#
#     world=bpy.data.worlds['World']
#     world.use_nodes = True
#     wnodes=world.node_tree.nodes
#     wlinks=world.node_tree.links


def randCam(mesh):
    bpy.ops.object.select_all(action='DESELECT')
    camera = bpy.data.objects['Camera']

    # sample camera config until find a valid one
    id = 0
    vid = False
    # focal length
    bpy.data.cameras['Camera'].lens = random.randint(25, 35)
    # cam position
    d = random.uniform(2.3, 3.3)
    campos = Vector((0, d, 0))
    eul = Euler((0, 0, 0), 'XYZ')
    eul.rotate_axis('Z', random.uniform(0, 3.1415))
    eul.rotate_axis('X', random.uniform(math.radians(60), math.radians(120)))

    campos.rotate(eul)
    camera.location = campos

    while id < 50:
        # look at pos
        st = (d - 2.3) / 1.0 * 0.2 + 0.3
        lookat = Vector((random.uniform(-st, st), random.uniform(-st, st), 0))
        eul = Euler((0, 0, 0), 'XYZ')

        eul.rotate_axis('X', math.atan2(lookat.y - campos.y, campos.z))
        eul.rotate_axis('Y', math.atan2(campos.x - lookat.x, campos.z))
        st = (d - 2.3) / 1.0 * 15 + 5.
        eul.rotate_axis('Z', random.uniform(math.radians(-90 - st), math.radians(-90 + st)))

        camera.rotation_euler = eul
        bpy.context.view_layer.update()

        if isVisible(mesh, camera):
            vid = True
            break

        id += 1
    return vid

def reset_camera(mesh):
    bpy.ops.object.select_all(action='DESELECT')
    camera = bpy.data.objects['Camera']

    # sample camera config until find a valid one
    # id = 0
    # vid = False
    # focal length
    bpy.data.cameras['Camera'].lens = config["camLens"]
    # cam position
    # d = random.uniform(2.3, 3.3)
    # eul = Euler((0, 0, 0), 'XYZ')
    # eul.rotate_axis('Z', random.uniform(0, 3.1415))
    # eul.rotate_axis('X', random.uniform(math.radians(60), math.radians(120)))

    # campos.rotate(eul)
    camera.location = Vector(config["campos"])
    camera.rotation_euler = Vector(config["camEul"])
    # while id < 50:
    #     # look at pos
    #     st = (d - 2.3) / 1.0 * 0.2 + 0.3
    #     lookat = Vector((random.uniform(-st, st), random.uniform(-st, st), 0))
    #     eul = Euler((0, 0, 0), 'XYZ')
    #
    #     eul.rotate_axis('X', math.atan2(lookat.y - campos.y, campos.z))
    #     eul.rotate_axis('Y', math.atan2(campos.x - lookat.x, campos.z))
    #     st = (d - 2.3) / 1.0 * 15 + 5.
    #     eul.rotate_axis('Z', random.uniform(math.radians(-90 - st), math.radians(-90 + st)))
    #
    #     camera.rotation_euler = eul
    #     bpy.context.view_layer.update()
    #
    #     if isVisible(mesh, camera):
    #         vid = True
    #         break
    #
    #     id += 1
    return True

def page_texturing(obj, texpath):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.material_slot_add()
    mat = bpy.data.materials.new('Material.001')
    mat.use_nodes = True
    obj.material_slots[0].material = mat
    nodes = mat.node_tree.nodes
    # clear default nodes
    for n in nodes:
        nodes.remove(n)
    out_node = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf_node = nodes.new(type='ShaderNodeBsdfDiffuse')
    texture_node = nodes.new(type='ShaderNodeTexImage')

    texture_node.image = bpy.data.images.load(os.path.abspath(texpath) )

    links = mat.node_tree.links
    links.new(bsdf_node.outputs[0], out_node.inputs[0])
    links.new(texture_node.outputs[0], bsdf_node.inputs[0])

    bsdf_node.inputs[0].show_expanded = True
    texture_node.extension = 'EXTEND'
    texturecoord_node = nodes.new(type='ShaderNodeTexCoord')
    links.new(texture_node.inputs[0], texturecoord_node.outputs[2])


# def get_image(objpath, texpath):
#     bpy.context.scene.use_nodes = True
#     tree = bpy.context.scene.node_tree
#     links = tree.links

#     # clear default nodes
#     for n in tree.nodes:
#         tree.nodes.remove(n)

#     # create input render layer node
#     render_layers = tree.nodes.new('CompositorNodeRLayers')
#     file_output_node_0 = tree.nodes.new("CompositorNodeOutputFile")
#     file_output_node_0.base_path = path_to_output_images

#     # change output image name to obj file name + texture name + random three
#     # characters (upper lower alphabet and digits)
#     id_name = objpath.split('/')[-1][:-4] + '-' + texpath.split('/')[-1][:-4] + '-' + \
#         ''.join(random.sample(string.ascii_letters + string.digits, 3))

#     file_output_node_0.file_slots[0].path = id_name

#     links.new(render_layers.outputs[0], file_output_node_0.inputs[0])
#     return id_name


def color_wc_material(obj, mat_name):
    # Remove lamp
    for lamp in bpy.data.lights:
        bpy.data.lights.remove(lamp, do_unlink=True)

    select_object(obj)
    # Add a new material
    bpy.data.materials.new(mat_name)
    obj.material_slots[0].material = bpy.data.materials[mat_name]
    mat = bpy.data.materials[mat_name]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # clear default nodes
    for n in nodes:
        nodes.remove(n)

    # Add an material output node
    mat_node = nodes.new(type='ShaderNodeOutputMaterial')
    # Add an emission node
    em_node = nodes.new(type='ShaderNodeEmission')
    # Add a geometry node
    geo_node = nodes.new(type='ShaderNodeNewGeometry')

    # Connect each other
    tree = mat.node_tree
    links = tree.links
    links.new(geo_node.outputs[0], em_node.inputs[0])
    links.new(em_node.outputs[0], mat_node.inputs[0])


def get_albedo_img(img_name):
    scene=bpy.data.scenes['Scene']
    bpy.context.view_layer.use_pass_diffuse_color = True
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # create input render layer node
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    file_output_node = tree.nodes.new('CompositorNodeOutputFile')
    comp_node = tree.nodes.new('CompositorNodeComposite')

    # file_output_node_0.format.file_format = 'OPEN_EXR'
    out_path=path_to_output_alb
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    
    file_output_node.base_path = out_path
    file_output_node.file_slots[0].path = img_name
    links.new(render_layers.outputs["DiffCol"], file_output_node.inputs[0])
    links.new(render_layers.outputs["DiffCol"], comp_node.inputs[0])


def get_worldcoord_img(img_name):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # create input render layer node
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    file_output_node_0 = tree.nodes.new("CompositorNodeOutputFile")
    file_output_node_0.format.file_format = 'OPEN_EXR'
    file_output_node_0.base_path = path_to_output_wc
    file_output_node_0.file_slots[0].path = img_name

    links.new(render_layers.outputs[0], file_output_node_0.inputs[0])


def prepare_no_env_render():
    # Remove lamp
    for lamp in bpy.data.lights:
        bpy.data.lights.remove(lamp, do_unlink=True)

    world = bpy.data.worlds['World']
    world.use_nodes = True
    links = world.node_tree.links
    # clear default nodes
    for l in links:
        links.remove(l)

    scene = bpy.data.scenes['Scene']
    scene.cycles.samples = 1
    scene.cycles.use_square_samples = True
    scene.view_settings.view_transform = 'Standard'




def render_pass(obj, objpath, texpath,envpath,confpath):
    # change output image name to obj file name + texture name + random three
    # characters (upper lower alphabet and digits)
    scene = bpy.data.scenes['Scene']
    bpy.context.view_layer.use_pass_uv = True
    # bpy.context.view_layer.use_pass_diffuse_color = True
    #scene.render.layers['RenderLayer'].use_pass_uv=True
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # create input render layer node
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    file_output_node_img = tree.nodes.new('CompositorNodeOutputFile')
    file_output_node_img.format.file_format = 'PNG'
    file_output_node_img.base_path = path_to_output_images
    file_output_node_img.file_slots[0].path = fn+'-#'
    imglk = links.new(render_layers.outputs["Image"], file_output_node_img.inputs[0])
    # scene.cycles.samples = 128
    bpy.ops.render.render(write_still=False)

    # save_blend_file
    if config["saveBlendFile"]:
        bpy.ops.wm.save_mainfile(filepath=path_to_output_blends + fn + '.blend')

    if config["renderOthers"]:
        # prepare to render without environment
        prepare_no_env_render()

        # remove img link
        links.remove(imglk)

        # render
        file_output_node_uv = tree.nodes.new('CompositorNodeOutputFile')
        file_output_node_uv.format.file_format = 'OPEN_EXR'
        file_output_node_uv.base_path = path_to_output_uv
        file_output_node_uv.file_slots[0].path = fn+"-#"
        uvlk = links.new(render_layers.outputs["UV"], file_output_node_uv.inputs[0])
        scene.cycles.samples = 1
        bpy.ops.render.render(write_still=False)
        page_texturing(obj,'./recon_tex/chess48.png')

        get_albedo_img(fn+"-#")
        bpy.context.scene.camera = bpy.data.objects['Camera']
        bpy.data.scenes['Scene'].render.image_settings.color_depth='8'
        bpy.data.scenes['Scene'].render.image_settings.color_mode='RGB'
        # bpy.data.scenes['Scene'].render.image_settings.file_format='OPEN_EXR'
        bpy.data.scenes['Scene'].render.image_settings.compression=0
        bpy.ops.render.render(write_still=False)

        # render world coordinates
        color_wc_material(obj,'wcColor')
        get_worldcoord_img(fn+"-#")
        bpy.ops.render.render(write_still=False)

    camera = bpy.data.objects['Camera']
    print(camera.location)
    print(camera.rotation_euler)

def createBook(wdh,r,k1,k2):
    for bpy_data_iter in (
        bpy.data.meshes,
        bpy.data.lights,
        bpy.data.images,
        bpy.data.materials,
        bpy.data.curves
):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data, do_unlink=True)

    ops.curve.primitive_bezier_curve_add(radius=2*r,enter_editmode=True)
    ops.curve.subdivide()
    curve=context.active_object
    bez_points = curve.data.splines[0].bezier_points
    bez_points[0].handle_right_type="FREE"
    bez_points[0].handle_left.y=0
    bez_points[0].handle_right.y=0
    bez_points[0].handle_right.x=-r
   
    bez_points[1].handle_right_type="FREE"
    bez_points[1].handle_left_type="FREE"
    bez_points[1].co=Vector((0,0,0))
    bez_points[1].handle_left=Vector((-0.5*r,-0.5*k1*r,0))
    bez_points[1].handle_right=Vector((0.5*r,-0.5*k2*r,0))


    curve.data.resolution_u=100
    curve.data.extrude=wdh*curve.data.splines[0].calc_length()*0.5

    ops.object.mode_set(mode='OBJECT')

    ops.object.convert(target='MESH')
    ops.transform.rotate(value=math.pi/2,orient_axis='Y')
    ops.transform.rotate(value=-math.pi/2,orient_axis='X')


    # if not os.path.exists(args.out):
    #     os.makedirs(args.out)
    # fn='{:.2f}-{:.2f}-{:.2f}-{:.2f}.obj'.format(wdh,r,k1,k2)
    # fPath = os.path.abspath(os.path.join(args.out, fn))
    # if args.overwirte or not os.path.exists(fPath):
    #     ops.export_scene.obj(filepath=fPath)
    #     print("---output:"+fPath+"---")
    # else:
    #     print("exists")

def render_img( texpath,objpath,envpath,confpath):
    prepare_scene()
    prepare_rendersettings()
    if args.generate:
        image=bpy.data.images.load(os.path.abspath(texpath) )
        wdh=image.size[1]/image.size[0]
        createBook(wdh,0.5,random.uniform(0.1,1.7),random.uniform(0.1,1.7))
    else:
    	bpy.ops.import_scene.obj(filepath=os.path.abspath(objpath))
    mesh_name=bpy.data.meshes[0].name
    mesh=position_object(mesh_name)
    if config["lighting"]=='hdr':
        hdrLighting(envpath,config["hdrStr"])
    elif config["lighting"]=='point':
        pointLight()

    if(config["randCam"]):
    	v=randCam(mesh)
    else:
    	v = reset_camera(mesh)
    
    if not v:
        return 1
    else:
        #add texture
        page_texturing(mesh, texpath)
        render_pass(mesh, objpath, texpath,envpath,confpath)
if __name__ == '__main__':

	#parse argument
	parser = argparse.ArgumentParser(description='Render mesh')
	parser.add_argument('-t','--texture',help='texture path',default='tex/pp_Page_001.jpg')
	parser.add_argument('-m','--mesh',help='mesh path',default='obj/1_1.obj')
	parser.add_argument('-e','--env',help='environment path',default='env/0001.hdr')
	parser.add_argument('-c','--conf',help='configuration path',default='config.json')
	parser.add_argument('-o','--out',help='output folder name',default='1')
	parser.add_argument('-b' ,'--batch', action='store_true',
	                        help='batch render files in folder')
	parser.add_argument('-s' ,'--selectmesh', action='store_true',
	                        help='batch render 1000 meshes')
	parser.add_argument('--generate', action='store_true',
	                        help='generate mesh')
	parser.add_argument('--overwrite', action='store_true',
	                        help='overwirte')
	args, unknown = parser.parse_known_args(sys.argv[5:])
	print(args)


	try:
	    with open(args.conf, 'r', encoding='utf-8') as fs:
	        config=json.load(fs)
	        print(config)
	except IOError as e:
	    print(e)


	#prepare output directory
	path_to_output_images=os.path.abspath('./img/{}/'.format(args.out))
	path_to_output_uv = os.path.abspath('./uv/{}/'.format(args.out))
	path_to_output_wc = os.path.abspath('./wc/{}/'.format(args.out))
	path_to_output_alb =os.path.abspath('./alb/{}/'.format(args.out)) 
	path_to_output_blends=os.path.abspath('./bld/{}/'.format(args.out))

	for fd in [path_to_output_images, path_to_output_uv, path_to_output_wc,path_to_output_alb, path_to_output_blends]:
	    if not os.path.exists(fd):
	        os.makedirs(fd)

	if args.batch:
		# meshList=glob.glob(os.path.join(args.mesh,"*.obj"))
		envList=os.listdir(args.env)
		for fname in sorted(os.listdir(args.texture)):
			if '.jpg' in fname or '.JPG' in fname or '.png' in fname:
				# randMesh=os.path.join(args.mesh,random.choice(meshList) )
				randEnv=os.path.join(args.env,random.choice(envList))
				fn=fname[:-4] 
				fPath =os.path.join(os.path.abspath(path_to_output_images),fn+'-1.png')
				if not os.path.exists(fPath):
					render_img(os.path.join(args.texture,fname),"randMesh",randEnv,args.conf)
					print("---output:"+fPath+"---")
				else:
					print("exists")
	elif args.selectmesh:
		texpath='./recon_tex/chess48.png'
		for fname in sorted(os.listdir(args.mesh)):
			meshPath=os.path.join(args.mesh,fname)
			randEnv=os.path.join(args.env,random.choice(os.listdir(args.env)))
			fn=fname[:-4] 
			fPath =os.path.join(os.path.abspath(path_to_output_images),fn+'-1.png')
			if not os.path.exists(fPath):
				render_img(texpath,meshPath,randEnv,args.conf)
				print("---output:"+fPath+"---")
			else:
				print("exists")


	else:
		confHash=hashlib.md5(open(args.conf, 'rb').read()).hexdigest()
		fn=os.path.split(args.mesh)[1][:-4] +'-' + os.path.split(args.texture)[1][:-4] \
		   + '-' +  os.path.split(args.env)[1][:-4] +'-'+ confHash[0:5]
		fPath =os.path.join(os.path.abspath(path_to_output_images),fn+'-1.png')
		if args.overwrite or not os.path.exists(fPath):
			render_img(args.texture,args.mesh,args.env,args.conf)
			print("---output:"+fPath+"---")
		else:
			print("exists")


# rridx=sys.argv[-3]
# strt=int(sys.argv[-2])
# end=int(sys.argv[-1])
# blend_list = './blendlists/blendlist'+ str(rridx) +'.csv'

# if not os.path.exists(path_to_output_alb):
#     os.makedirs(path_to_output_alb)

# with open(blend_list,'r') as b:
#     blendlist = list(csv.reader(b))

# for bfile in blendlist[strt:end]:
#     bfname=bfile[0]
#     fn=bfname.split('/')[-1][:-6]
#     #load blend file 
#     bpy.ops.wm.open_mainfile(filepath=bfname)
#     prepare_rendersettings()
#     prepare_no_env_render()
#     get_albedo_img(fn)
#     render()




# id1 = int(sys.argv[-2])
# id2 = int(sys.argv[-1])
# rridx = int(sys.argv[-3])
#


#
# env_list = './envs.csv'
# tex_list = './tex.csv'
# obj_list = './objs.csv'
#
# with open(env_list, 'r') as f:
#     envlist = list(csv.reader(f))
#
# with open(tex_list, 'r') as t, open(obj_list, 'r') as m:
#     texlist = list(csv.reader(t))
#     objlist = list(csv.reader(m))
#     # print(objlist)
#     for k in range(id1, id2):
#         # print(k)
#         objpath = os.path.abspath(objlist[k][0])
#         idx = random.randint(0, len(texlist))
#         texpath = os.path.abspath(texlist[idx][0])
#         print(objpath)
#         print(texpath)
#
#         render_img(objpath, texpath)
