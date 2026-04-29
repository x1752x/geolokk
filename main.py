from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from concurrent.futures import ThreadPoolExecutor

import asyncio
import psycopg2
import yaml
import threading
import json
import time
import asyncpg

from GaussianNoiseGenerator import *
from BerlageImpulse import *
from Sensor import *
from SensorCluster import *

with open("config.yaml", 'r') as config_file:
    config = yaml.safe_load(config_file)

impulse_cluster = SensorCluster([Sensor(coords, id) for id, coords in config['impulse_cluster'].items()])
for id, coords in config['impulse_source'].items():
    impulse_source = NoiseSource(coords, id)

def impulse_generator(stop_event: threading.Event):
    connection = psycopg2.connect(dbname=config["database"], 
                    user=config["user"], 
                    password=config["password"], 
                    host=config["host"],
                    port=config["port"])
    cursor = connection.cursor()

    while not stop_event.is_set():
        if False not in [sensor.next_event == -1 for sensor in impulse_cluster.sensors]:
            impulse_cluster.record(impulse_source)
        data = impulse_cluster.generate_once()
        json_data = json.dumps(data)
        cursor.execute("INSERT INTO cluster_responses (response) VALUES (%s);", (json_data,))
        cursor.execute("""
            DELETE FROM cluster_responses
            WHERE id IN (
                SELECT id FROM cluster_responses
                ORDER BY id ASC
                LIMIT (SELECT GREATEST(0, count(*) - 2000) FROM cluster_responses)
            )
        """)
        connection.commit()
        time.sleep(0.007)

    cursor.close()
    connection.close()

vehicle_cluster = SensorCluster.from_traces(config['vehicle_cluster'])

def vehicle_generator(stop_event: threading.Event):
    connection = psycopg2.connect(dbname=config["database"], 
                    user=config["user"], 
                    password=config["password"], 
                    host=config["host"],
                    port=config["port"])
    cursor = connection.cursor()

    while not stop_event.is_set():
        data = vehicle_cluster.generate_once()
        json_data = json.dumps(data)
        cursor.execute("INSERT INTO vehicle_responses (response) VALUES (%s);", (json_data,))
        cursor.execute("""
            DELETE FROM vehicle_responses
            WHERE id IN (
                SELECT id FROM vehicle_responses
                ORDER BY id ASC
                LIMIT (SELECT GREATEST(0, count(*) - 2000) FROM vehicle_responses)
            )
        """)
        connection.commit()
        time.sleep(0.007)

    cursor.close()
    connection.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    impulse_generator_stop = threading.Event()
    impulse_generator_thread = threading.Thread(target = impulse_generator, args=(impulse_generator_stop,), daemon=True)
    
    vehicle_generator_stop = threading.Event()
    vehicle_generator_thread = threading.Thread(target = vehicle_generator, args=(vehicle_generator_stop,), daemon = True)

    if config['impulse_active']:
        print("IMPULSE GENERATOR THREAD STARTING...")
        impulse_generator_thread.start()

    if config['vehicle_active']:
        print("VEHICLE GENERATOR THREAD STARTING...")
        vehicle_generator_thread.start()

    yield

    impulse_generator_stop.set()
    vehicle_generator_stop.set()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/impulse', response_class = HTMLResponse)
def impulse(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = 'impulse.jinja',
        context = {
            "cluster": impulse_cluster,
            "source": impulse_source
        }
    )

@app.websocket("/stream/impulse")
async def stream_impulse(*, ws: WebSocket):
    await ws.accept()
    
    conn = await asyncpg.connect(
        user=config['user'],
        password=config['password'],
        host=config['host'],
        database=config['database'],
        port=config['port']
    )
    
    queue = asyncio.Queue()

    async def callback(conn, pid, channel, payload):
        await queue.put(payload)

    await conn.add_listener('new_response_channel', callback)

    try:
        while True:
            payload = await queue.get()
            await ws.send_text(payload)
    except WebSocketDisconnect:
        pass
    finally:
        await conn.remove_listener('new_response_channel', callback)
        await conn.close()

@app.get('/vehicle', response_class = HTMLResponse)
def vehicle(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = 'vehicle.jinja',
        context = {
            "cluster": vehicle_cluster
        }
    )

@app.websocket("/stream/vehicle")
async def stream_vehicle(*, ws: WebSocket):
    await ws.accept()
    
    conn = await asyncpg.connect(
        user=config['user'],
        password=config['password'],
        host=config['host'],
        database=config['database'],
        port=config['port']
    )
    
    queue = asyncio.Queue()

    async def callback(conn, pid, channel, payload):
        await queue.put(payload)

    await conn.add_listener('new_vehicle_response_channel', callback)

    try:
        while True:
            payload = await queue.get()
            await ws.send_text(payload)
    except WebSocketDisconnect:
        pass
    finally:
        await conn.remove_listener('new_vehicle_response_channel', callback)
        await conn.close()