
import os
import sys
from pathlib import Path

import numpy as np
from ast import literal_eval
from PIL import Image

# Celery
from celery import shared_task
# Celery-progress
from celery_progress.backend import ProgressRecorder

from time import sleep


def pil_to_image(pil_image, img_path, name='NewImage'):
    import bpy
    '''
    PIL image pixels is 2D array of byte tuple (when mode is 'RGB', 'RGBA') or byte (when mode is 'L')
    bpy image pixels is flat array of normalized values in RGBA order
    '''
    cwd = os.getcwd()

    # setup PIL image conversion
    width = pil_image.width
    height = pil_image.height
    byte_to_normalized = 1.0 / 255.0
    # create new image
    bpy_image = bpy.data.images.new(name, width=width, height=height)
    bpy.data.images[name].filepath_raw = img_path
    bpy.data.images[name].file_format = 'PNG'

    # convert Image 'L' to 'RGBA', normalize then flatten
    bpy_image.pixels[:] = (np.asarray(pil_image.convert(
        'RGBA'), dtype=np.float32) * byte_to_normalized).ravel()
    bpy.data.images[name].save()
    print("BPY image Saved")

    return bpy_image


@shared_task(bind=True)
def blenderScript(self, pixelData):
    numStep = 9
    currStep = 0
    print('Task started')
    progress_recorder = ProgressRecorder(self)

    # Create heightmap image
    pixelData = np.array(literal_eval(pixelData))
    pixelData = np.interp(
        pixelData, (pixelData.min(), pixelData.max()), (0, 255))

    PIL_img = Image.fromarray(np.uint8(pixelData * 255), 'L')

    # Blender changes
    import bpy
    import bmesh

    # get local path
    cwd = os.getcwd()

    # load blend file
    bpy.ops.wm.open_mainfile(filepath="blender/test2.blend")
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="load blend file")

    # set directory paths
    StlPath = cwd+"/media/STLs/testy3.stl"
    print(StlPath)

    # create plane
    bpy.ops.mesh.primitive_plane_add()
    so = bpy.context.active_object
    objects = bpy.data.objects
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="create plane")

    # create bmesh
    me = bpy.context.object.data
    bm = bmesh.new()
    bm.from_mesh(me)
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="create bmesh")

    # subdivide
    bmesh.ops.subdivide_edges(bm,
                              edges=bm.edges,
                              cuts=200,
                              use_grid_fill=True,
                              )

    bm.to_mesh(me)
    bm.free()
    #   progress
    currStep += 1
    progress_recorder.set_progress(currStep, numStep, description="subdivide")

    # heightmap texture
    #HeightmapPath = "D:\Documents\school\BP2\heightMaps\C1.tif"

    #img = bpy.data.images.load(HeightmapPath)

    tex = bpy.data.textures.new("heightmapTex", 'IMAGE')
    img_path = cwd + "/media/img/testy.png"
    bpy_img = pil_to_image(PIL_img, img_path, "heighmapImg")
    bpy_img = bpy.data.images.load(img_path)
    print(bpy_img)
    tex.image = bpy_img
    print(tex)
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="heightmap texture")

    # displace modifier
    displace = so.modifiers.new("displace", 'DISPLACE')
    displace.texture = bpy.data.textures['heightmapTex']
    displace.strength = 1

    so.modifiers["displace"]
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="displace modifier")

    # solidify modifier
    solidify = so.modifiers.new("solidify", 'SOLIDIFY')
    solidify.thickness = 0.2

    so.modifiers["solidify"]
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="solidify modifier")

    # Boolean modifier
    boolean = so.modifiers.new("boolean", 'BOOLEAN')
    booleanObject = objects['CircleBoolean']
    boolean.object = booleanObject
    boolean.operation = 'INTERSECT'
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="Boolean modifier")

    # export STL
    #StlPath = 'D:/Documents/Shop/Software/Python/STLs/test2.stl'
    bpy.ops.export_mesh.stl(
        filepath=StlPath, use_mesh_modifiers=True, use_selection=True)
    #   progress
    currStep += 1
    progress_recorder.set_progress(currStep, numStep, description="export STL")

    # sleep(0.5)
    print('End')

    return 'Task Complete'
