import logging
import pika
import json
import time
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

rabbitmq_url = 'amqp://guest:guest@localhost:5672/%2f'
request_queue_name = 'requests_queue'

params = pika.URLParameters(rabbitmq_url)
connection = None
channel = None

try:
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=request_queue_name, durable=True, arguments={'x-expires': 300000})

    logger.info(f"Declared queue {request_queue_name} with message TTL of 5 minute")

except Exception as e:
    logger.error(f"Error encountered creating connection @ {rabbitmq_url}")
    exit(-1)


def generate_response_queue_name(request_id: str):
    return f'response_queue_{request_id}'

def callback(ch, method, properties, body):
    request = json.loads(body)
    request_id = request['request_id']
    response_queue_name = generate_response_queue_name(request_id)
    channel.queue_declare(queue=response_queue_name, durable=True, auto_delete=True,
                          arguments={'x-expires': 600000})

    text = request['text']
    logger.info(f"Processing request: {request}")
    for word in text.split():
        response = {"request_id": request_id, "text": word}
        channel.basic_publish(exchange='', routing_key=response_queue_name, body=json.dumps(response))
        logger.info(f"Sent word to response_queue {response_queue_name} : {response}")
        time.sleep(0.1)
    # Send an "END" message to signal the end of the stream
    logger.info(f"Sending end message tag as finished")
    end_message = {"request_id": request_id, "text": "END"}
    channel.basic_publish(exchange='', routing_key=response_queue_name, body=json.dumps(end_message))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=request_queue_name, on_message_callback=callback)

logger.info(f'Waiting for messages on {request_queue_name}. To exit press CTRL+C')
channel.start_consuming()