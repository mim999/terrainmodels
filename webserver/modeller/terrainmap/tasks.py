
import os


import sys
from pathlib import Path

# Celery
from celery import shared_task
# Celery-progress
from celery_progress.backend import ProgressRecorder

from time import sleep


@shared_task(bind=True)
def blenderScript(self):
    numStep = 9
    currStep = 0
    print('Task started')
    progress_recorder = ProgressRecorder(self)

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
    HeightmapPath = cwd+"/blender/Heightmaps/A1.tif"
    StlPath = cwd+"/terrainmap/static/terrainmap/STLs/testy3.stl"
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

    img = bpy.data.images.load(HeightmapPath)

    tex = bpy.data.textures.new("heightmap", 'IMAGE')
    tex.image = img
    #   progress
    currStep += 1
    progress_recorder.set_progress(
        currStep, numStep, description="heightmap texture")

    # displace modifier
    displace = so.modifiers.new("displace", 'DISPLACE')
    displace.texture = bpy.data.textures['heightmap']
    displace.strength = 0.05

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
