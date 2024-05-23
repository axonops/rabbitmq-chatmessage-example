# rabbitmq-streaming-example
IN PROGRESS - NOT FINISHED

Example application using RabbitMQ and Sockets to stream text to a browser without the browser having direct access to RabbitMQ

## Running the Example
* Start RabbitMQ: Ensure RabbitMQ is running.
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
* Open the Web Client: Open `index.html` in a web browser, enter some text, and click the "Start Stream" button to see the text stream in action.

### Docker Compose
The `docker-compose.yml` included in this project starts up RabbitMQ to use in the application. The `rabbitmq.conf` is loaded into the RabbitMQ and can be used to customise RabbitMQ further.

To start the services defined in the `docker-compose.yml` file, run the following command in your terminal:
`docker-compose up -d`. This command will start the RabbitMQ container with the Streams feature enabled and run it in detached mode.

The following ports are exposed on localhost
* `5672:5672` for the AMQP protocol.
* `15672:15672` for the management UI.
* `5552:5552` for the Stream protocol.
