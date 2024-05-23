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
params = pika.URLParameters(rabbitmq_url)
connection = pika.BlockingConnection(params)
channel = connection.channel()

channel.queue_declare(queue='request_queue', durable=True)
channel.queue_declare(queue='response_queue', durable=True)

def generate_random_text():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def callback(ch, method, properties, body):
    request = json.loads(body)
    request_id = request['request_id']
    text = request['text']
    logger.info(f"Processing request: {request}")
    for word in text.split():
        response = {"request_id": request_id, "text": word}
        channel.basic_publish(exchange='', routing_key='response_queue', body=json.dumps(response))
        logger.info(f"Sent word to response_queue: {response}")
        time.sleep(1)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='request_queue', on_message_callback=callback)

logger.info('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()