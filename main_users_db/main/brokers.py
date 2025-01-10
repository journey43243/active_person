import os
import pika
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

class RabbitMQSettings:


    broker_user = os.environ.get("RABBITMQ_DEFAULT_USER")
    broker_pass = os.environ.get("RABBITMQ_DEFAULT_PASS")
    credential = {"username": broker_user, "password": broker_pass}
    credentials = pika.PlainCredentials(**credential)
    parameters = pika.ConnectionParameters(host='rabittmq', port='5672', credentials=credentials)
    connection = pika.BlockingConnection(parameters)

class CelerySettings:

    app = Celery('celery', broker=f'amqp://{RabbitMQSettings.broker_user}:{RabbitMQSettings.broker_pass}@rabittmq:5672')

