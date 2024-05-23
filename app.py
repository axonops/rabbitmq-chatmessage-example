import logging
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uuid
import pika
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount the static files directory at /static
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# RabbitMQ connection parameters
rabbitmq_url = 'amqp://guest:guest@localhost:5672/%2f'
params = pika.URLParameters(rabbitmq_url)
connection = pika.BlockingConnection(params)
channel = connection.channel()

# Declare the queues with TTL
channel.queue_declare(queue='request_queue', durable=True, arguments={'x-message-ttl': 300000})
channel.queue_declare(queue='response_queue', durable=True, arguments={'x-message-ttl': 300000})


@app.post("/start")
async def start_stream(text: str = Form(...)):
    request_id = str(uuid.uuid4())
    message = {"request_id": request_id, "text": text}
    channel.basic_publish(exchange='', routing_key='request_queue', body=json.dumps(message))
    logger.info(f"Sent message to request_queue: {message}")
    return JSONResponse(content={"request_id": request_id})


@app.get("/stream/{request_id}")
async def stream_response(request_id: str):
    async def event_generator():
        while True:
            method_frame, header_frame, body = channel.basic_get(queue='response_queue')
            if method_frame:
                response = json.loads(body)
                if response['request_id'] == request_id:
                    logger.info(f"Received message from response_queue: {response}")
                    yield f"data: {response['text']}\n\n"
                    channel.basic_ack(method_frame.delivery_tag)
                    if response['text'] == "END":
                        yield f"event: end\ndata: Stream ended\n\n"
                        break
            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")