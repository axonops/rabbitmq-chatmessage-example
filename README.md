# rabbitmq-streaming-example
IN PROGRESS - NOT FINISHED

Example application using RabbitMQ and Sockets to stream text to a browser without the browser having direct access to RabbitMQ


## Docker Compose
The `docker-compose.yml` included in this project starts up RabbitMQ to use in the application. The `rabbitmq.conf` is loaded into the RabbitMQ and can be used to customise RabbitMQ further.

To start the services defined in the `docker-compose.yml` file, run the following command in your terminal:
`docker-compose up -d`. This command will start the RabbitMQ container with the Streams feature enabled and run it in detached mode.

The following ports are exposed on localhost
* `5672:5672` for the AMQP protocol.
* `15672:15672` for the management UI.
* `5552:5552` for the Stream protocol.
