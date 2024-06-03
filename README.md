# rabbitmq-chatmessage-example
Example application using RabbitMQ to stream text to a browser via a FastAPI server, without the browser having direct access to RabbitMQ. Note - this is not using the streams plugin, it just creates a temporary queue for each message and produces and consumes from it on word at a time.

This is just basic proof of concept, exploring RabbitMQ. Further thought should be given to concurrent requests and how they should be handled. In the case of this application we are creating a unique response queue for each requests that gets automatically deleted after 10 minutes by RabbitMQ.

A Python Rest API using FastAPI app (`app.py`) is exposed for a simple static webpage `static/index.html` to invoke.

The Web UI sends a text message to the rest API `/start` and gets back a UUID for its chat id (`chat_id`) and a generated chat title (`chat_title`). 

It then makes a call to `"/start/{chat_id}` with its message to send. It generates a UUID `message_id` and sends a message containing the information to the `requests_queue`

The web UI then creates a stream on `/stream/{chat_id}/{message_id}` which consumes messages as they come in on the unique queue creates for the message.

`producer.py` is listening on `request_queue`, it gets the text payload, splits the words up and ends them back on `response_queue_{message_id}` for the `/stream/{chat_id}/{message_id}` method to consume and return.

## Running the Example
* Start RabbitMQ by running the included docker-compose.yml. Ensure RabbitMQ is running. `docker-compose up -d`


* Open a terminal to run the RabbitMQ Consumer/Producer:
  * Go to the directory you have the project checked out.
  * Create a Python Virtual Environment called venv `python -m venv venv`
  * Activate the virtual environment `source venv/bin/activate`
  * Install the necessary Python libraries `pip install -r requirements.txt`
  * Start the producer `python producer.py`
  * You should see `Waiting for messages. To exit press CTRL+C` returned. This is now connected on RabbitMQ.


* Open another terminal to run the FastAPI Server:
  * Go to the directory you have the project checked out.
  * Create a Python Virtual Environment called venv `python -m venv venv`
  * Activate the virtual environment `source venv/bin/activate`
  * Start FastAPI server listening on port 8080 `uvicorn app:app --reload --host 0.0.0.0 --port 8080`
  * You should see
  ```
  INFO:     Will watch for changes in these directories: ['/github/rabbitmq-streaming-example']
  INFO:     Uvicorn running on  http://0.0.0.0:8080 (Press CTRL+C to quit)
  INFO:     Started reloader process [21314] using WatchFiles
  INFO:     Started server process [21318]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  ```

* Open the Web Client: Open `http://localhost:8080/static` in a web browser and send a message to see the text stream in action!

### Docker Compose
The `docker-compose.yml` included in this project starts up RabbitMQ to use in the application. The `rabbitmq.conf` is loaded into the RabbitMQ and can be used to customise RabbitMQ further.

To start the services defined in the `docker-compose.yml` file, run the following command in your terminal:
`docker-compose up -d`. This command will start the RabbitMQ container and run it in detached mode.

The following ports are exposed on localhost
* `5672:5672` for the AMQP protocol.
* `15672:15672` for the management UI.
