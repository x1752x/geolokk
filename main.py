from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

import asyncio

from GaussianNoiseGenerator import *
from BerlageImpulse import *
from Sensor import *
from SensorCluster import *

app = FastAPI()
templates = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

cluster = SensorCluster([
    Sensor([0, 0],  0),
    Sensor([0, 600],  1),
    Sensor([0, 1200],  2),
    Sensor([0, -600], 3),
    Sensor([0, -1200], 4),
    Sensor([600, 0],  5),
    Sensor([1200, 0],  6),
    Sensor([-600, 0], 7),
    Sensor([-1200, 0], 8),
    Sensor([-1800, 0], 9),
    Sensor([1800, 0], 10),
    Sensor([0, -1800], 11),
    Sensor([0, 1800],  12),
])

source = NoiseSource([-600, 600], 0)

@app.get('/', response_class = HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = 'index.jinja',
        context = {
            "cluster": cluster,
            "source": source
        }
    )

@app.websocket("/noise")
async def noise(*, ws: WebSocket):
    cluster = SensorCluster([
        Sensor([0, 0],  0),
        Sensor([0, 600],  1),
        Sensor([0, 1200],  2),
        Sensor([0, -600], 3),
        Sensor([0, -1200], 4),
        Sensor([600, 0],  5),
        Sensor([1200, 0],  6),
        Sensor([-600, 0], 7),
        Sensor([-1200, 0], 8),
        Sensor([-1800, 0], 9),
        Sensor([1800, 0], 10),
        Sensor([0, -1800], 11),
        Sensor([0, 1800],  12),
    ])

    source = NoiseSource([-600, 600], 0)

    await ws.accept()
    try:
        while True:
            if cluster.get(10).next_event == -1 and cluster.get(11).next_event == -1:
                cluster.record(source)
            data = cluster.generate_once()
            
            await ws.send_json(data)
            await asyncio.sleep(0.01)
            
    except WebSocketDisconnect:
        pass
