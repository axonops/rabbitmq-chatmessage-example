import logging
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uuid
import pika
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Get the logger for the pika package and set its level to WARNING
pika_logger = logging.getLogger('pika')
pika_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI()

# Mount the static files directory at /static
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# RabbitMQ connection parameters
rabbitmq_url = 'amqp://guest:guest@localhost:5672/%2f'
request_queue_name = 'requests_queue'
params = pika.URLParameters(rabbitmq_url)


def create_response_queue(message_id: str):
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Generate a unique queue name using UUID
        response_queue_name = generate_response_queue_name(message_id)

        channel.queue_declare(queue=response_queue_name, durable=True, auto_delete=True,
                              arguments={'x-expires': 600000})

        logger.info(f"Declared queue {response_queue_name} with TTL of 10 minute and auto delete true")

        # Close the connection
        connection.close()

        return response_queue_name

    except Exception as e:
        logger.error(f"Creation of response queue for message_id {message_id} @ {rabbitmq_url} failed: {e}")
        raise HTTPException(status_code=500, detail=f"A problem has been encountered servicing request {message_id}")


def generate_response_queue_name(message_id: str):
    return f'response_queue_{message_id}'

def send_message_to_request_queue(message_id: str, message):
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue=request_queue_name, durable=True, arguments={'x-message-ttl': 300000})

        logger.info(f"Declared queue {request_queue_name} with message TTL of 5 minute")

        channel.basic_publish(exchange='', routing_key=request_queue_name, body=json.dumps(message))

        logger.info(f"Published message for message_id {message_id} to request queue {request_queue_name}")

        # Close the connection
        connection.close()

    except Exception as e:
        logger.error(f"Error encountered publishing message for message_id {message_id} to request queue {request_queue_name} @ {rabbitmq_url} : {e}")
        raise HTTPException(status_code=503, detail=f"A problem has been sending request {message_id} for processing")


def create_requests_queue():
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue=request_queue_name, durable=True, arguments={'x-message-ttl': 300000})

        logger.info(f"Declared queue {request_queue_name} with message TTL of 5 minute")

        # Close the connection
        connection.close()

    except Exception as e:
        logger.error(f"Error encountered creating requests queue @ {rabbitmq_url} : {e}")
        exit(-2)


create_requests_queue()


@app.post("/start")
async def start_chat():
    chat_id = str(uuid.uuid1())
    chat_title = "New Chat"
    logger.info(f"Created new chat with chat_id {chat_id} and chat_title {chat_title}")
    return JSONResponse(content={"chat_id": chat_id, "chat_title": chat_title})


@app.post("/start/{chat_id}")
async def start_stream(chat_id: str, text: str = Form(...), chat_title: str = Form(...)):
    message_id = str(uuid.uuid1())
    if chat_title == "New Chat":
        chat_title = text[:100]

    logger.info(f"Created new message {message_id} with chat_id {chat_id} and chat_title {chat_title}")

    message = {"chat_id": chat_id, "chat_title": chat_title, "message_id": message_id, "text": text}
    response_queue_name = create_response_queue(message_id)
    logger.info(f"Created unique response queue {response_queue_name} for chat_id {chat_id}, chat_title {chat_title} and message_id {message_id}")
    logger.info(f"Sending message {message_id} to request_queue")
    send_message_to_request_queue(message_id, message)
    logger.info(f"Sent message to request_queue: {message}")
    return JSONResponse(content={"chat_id": chat_id, "chat_title": chat_title, "message_id": message_id})


@app.get("/stream/{chat_id}/{message_id}")
async def stream_response(chat_id: str, message_id: str):
    async def event_generator():
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ  @ {rabbitmq_url}: {e}")
            raise HTTPException(status_code=503, detail="Service Unavailable: Unable to connect to RabbitMQ")

        response_queue_name = generate_response_queue_name(message_id)

        logger.info(f"Starting listening on response_queue: {response_queue_name} for chat_id {chat_id} and message_id {message_id}")

        while True:
            try:
                method_frame, header_frame, body = channel.basic_get(queue=response_queue_name)
                if method_frame:
                    response = json.loads(body)
                    if response['message_id'] == message_id:
                        logger.info(f"Received message from response_queue: {response}")
                        yield f"data: {json.dumps(response)}\n\n"
                        channel.basic_ack(method_frame.delivery_tag)
                        if response['text'] == "^*END*^":
                            logger.info(f"Received end of stream message from response_queue: {response_queue_name}. Closing connection")
                            connection.close()
                            yield f"event: end\ndata: Stream ended\n\n"
                            break
            except Exception as e:
                logger.error(f"An error occurred listening for response on response_queue_name {response_queue_name} @ {rabbitmq_url} : {e}")
                raise HTTPException(status_code=503, detail="Internal Server Error")

            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
