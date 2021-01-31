from django.shortcuts import render
from django.http import HttpResponse
from .tasks import blenderScript


# Create your views here.


def index(request):
    return render(request, 'terrainmap/index.html')


# blender -b test2.blend --python Scripts/Topo.py -o //Renders/img -f 1 -- C1.tif test1.stl
def blender(request):
    blender_task = blenderScript.delay()
    task_id = blender_task.task_id
    print(f'Celery Task ID: {task_id}')
    return render(request, 'terrainmap/rendered.html', {'task_id': task_id})
