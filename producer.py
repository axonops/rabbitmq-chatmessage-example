import logging
import pika
import json
import time
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Get the logger for the pika package and set its level to WARNING
pika_logger = logging.getLogger('pika')
pika_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

rabbitmq_url = 'amqp://guest:guest@localhost:5672/%2f'
request_queue_name = 'requests_queue'

params = pika.URLParameters(rabbitmq_url)
connection = None
channel = None

try:
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=request_queue_name, durable=True, arguments={'x-message-ttl': 300000})

    logger.info(f"Declared queue {request_queue_name} with message TTL of 5 minute")

except Exception as e:
    logger.error(f"Error encountered creating connection @ {rabbitmq_url}")
    exit(-1)


def generate_response_queue_name(message_id: str):
    return f'response_queue_{message_id}'


def callback(ch, method, properties, body):
    request = json.loads(body)
    chat_id = request['chat_id']
    chat_title = request['chat_title']
    message_id = request['message_id']
    response_queue_name = generate_response_queue_name(message_id)
    channel.queue_declare(queue=response_queue_name, durable=True, auto_delete=True,
                          arguments={'x-expires': 600000})

    original_text = request['text']
    text = "This is generated on the server side. Here is your original message: " + original_text
    logger.info(f"Processing request: {request}")
    for word in text.split():
        response = {"chat_id": chat_id, "chat_title": chat_title, "message_id": message_id, "text": word}
        channel.basic_publish(exchange='', routing_key=response_queue_name, body=json.dumps(response))
        logger.info(f"Sent word to response_queue {response_queue_name} : {response}")
        time.sleep(0.1)
    # Send an "END" message to signal the end of the stream
    logger.info(f"Sending end message tag as finished")
    end_message = {"chat_id": chat_id, "chat_title": chat_title, "message_id": message_id, "text": "^*END*^"}
    channel.basic_publish(exchange='', routing_key=response_queue_name, body=json.dumps(end_message))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(queue=request_queue_name, on_message_callback=callback)

logger.info(f'Waiting for messages on {request_queue_name}. To exit press CTRL+C')
channel.start_consuming()