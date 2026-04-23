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

cluster = SensorCluster([Sensor(coords, id) for id, coords in config['cluster'].items()])
for id, coords in config['noise'].items():
    source = NoiseSource(coords, id)

def worker(stop_event: threading.Event):
    connection = psycopg2.connect(dbname=config["database"], 
                    user=config["user"], 
                    password=config["password"], 
                    host=config["host"],
                    port=config["port"])
    cursor = connection.cursor()

    while not stop_event.is_set():
        if False not in [sensor.next_event == -1 for sensor in cluster.sensors]:
            cluster.record(source)
        data = cluster.generate_once()
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = threading.Event()
    thread = threading.Thread(target = worker, args=(stop,), daemon=True)
    print("WORKER THREAD STARTING...")
    thread.start();

    yield

    stop.set()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/impulse', response_class = HTMLResponse)
def impulse(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = 'impulse.jinja',
        context = {
            "cluster": cluster,
            "source": source
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
