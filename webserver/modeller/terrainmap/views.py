from django.shortcuts import render
from django.http import HttpResponse

import os


import sys
from pathlib import Path

# Create your views here.


def index(request):
    return render(request, 'terrainmap/index.html')


# blender -b test2.blend --python Scripts/Topo.py -o //Renders/img -f 1 -- C1.tif test1.stl
def blender(request):
    print("testing bpy")
    blenderScript()
    return render(request, 'terrainmap/rendered.html')


def rendertest(request):
    return render(request, 'terrainmap/rendered.html')


def blenderScript():
    import bpy
    import bmesh

    # get local path
    cwd = os.getcwd()

    # load blend file
    bpy.ops.wm.open_mainfile(filepath="blender/test2.blend")

    # set directory paths
    HeightmapPath = cwd+"/blender/Heightmaps/A1.tif"
    StlPath = cwd+"/terrainmap/static/terrainmap/STLs/testy3.stl"
    print(StlPath)

    # create plane
    bpy.ops.mesh.primitive_plane_add()
    so = bpy.context.active_object
    objects = bpy.data.objects

    # create bmesh
    me = bpy.context.object.data
    bm = bmesh.new()
    bm.from_mesh(me)

    # subdivide
    bmesh.ops.subdivide_edges(bm,
                              edges=bm.edges,
                              cuts=200,
                              use_grid_fill=True,
                              )

    bm.to_mesh(me)
    bm.free()

    # heightmap texture
    #HeightmapPath = "D:\Documents\school\BP2\heightMaps\C1.tif"

    img = bpy.data.images.load(HeightmapPath)

    tex = bpy.data.textures.new("heightmap", 'IMAGE')
    tex.image = img

    # displace modifier
    displace = so.modifiers.new("displace", 'DISPLACE')
    displace.texture = bpy.data.textures['heightmap']
    displace.strength = 0.05

    so.modifiers["displace"]

    # solidify modifier
    solidify = so.modifiers.new("solidify", 'SOLIDIFY')
    solidify.thickness = 0.2

    so.modifiers["solidify"]

    # Boolean modifier
    boolean = so.modifiers.new("boolean", 'BOOLEAN')
    booleanObject = objects['CircleBoolean']
    boolean.object = booleanObject
    boolean.operation = 'INTERSECT'

    # export STL
    #StlPath = 'D:/Documents/Shop/Software/Python/STLs/test2.stl'

    bpy.ops.export_mesh.stl(
        filepath=StlPath, use_mesh_modifiers=True, use_selection=True)
