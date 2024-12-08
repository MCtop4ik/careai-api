import argparse
import json
from json.decoder import JSONDecodeError
import logging
import os
import sys
import pika
import time
import cv2
import urllib.error

import ultralytics
import yaml
from pika.exceptions import AMQPError, ChannelError, ReentrancyError, \
	StreamLostError, AMQPHeartbeatTimeout, ConnectionClosedByBroker, ChannelWrongStateError, ConnectionClosed, \
	ConnectionBlockedTimeout
from render import start_finding_gender_age_from_file
from render import start_finding_gender_age
import timm

LOGGER = logging.getLogger(__name__)
timm.data.config._logger.setLevel(logging.CRITICAL)
timm.models._helpers._logger.setLevel(logging.CRITICAL)
ultralytics.yolo.engine.predictor.LOGGER.setLevel(logging.CRITICAL)
ultralytics.yolo.engine.validator.LOGGER.setLevel(logging.CRITICAL)

LOGGING_FORMAT_STRING = (
	"${asctime}|${levelname}|${name}|PID ${process}|TID ${thread}|${message}"
)

LOG_LEVEL_MAP = {
	"critical": logging.CRITICAL,
	"fatal": logging.CRITICAL,
	"error": logging.ERROR,
	"warning": logging.WARNING,
	"warn": logging.WARNING,
	"info": logging.INFO,
	"debug": logging.DEBUG
}


class Configuration:
	def __init__(self, raw_config, parser_type):
		self._config = raw_config
		self._parser_type = parser_type

	@property
	def rabbitmq(self):
		return self._config[self._parser_type]["rmq"]

	@property
	def infrastructure(self):
		return self._config["infrastructure"]

	@property
	def settings(self):
		return self._config["settings"]


class FaceDataPublisher:
	def __init__(self, config, to_exchange):
		self._config = config
		self._cnx = None
		self._channel = None
		self._to_exchange = to_exchange

		self._reset_channel()

	def _reset_channel(self):
		self.close()
		self._cnx = _create_rabbitmq_connection(self._config)
		self._channel = self._cnx.channel()

	def close(self):
		if self._channel is not None and self._channel.is_open:
			self._channel.close()
		if self._cnx is not None and self._cnx.is_open:
			self._cnx.close()

	def publish_message(self, payload):
		try:
			self._publish(payload)
		except (StreamLostError, ConnectionClosedByBroker, ChannelWrongStateError, ConnectionClosed,
				ConnectionBlockedTimeout):
			LOGGER.info(
				"Publishing channel is closed. Reopening connection and channel..."
			)

			self._reset_channel()
			self._publish(payload)

	def _publish(self, payload):
		body = json.dumps(payload)  # , default=default_serialize
		self._channel.basic_publish(
			exchange=self._to_exchange,
			routing_key="",
			body=body,
			properties=pika.BasicProperties(
				delivery_mode=2,  # make message persistent
			),
		)


class FaceAgent:
	def __init__(self, configuration: Configuration):
		self._configuration = configuration

		self._connection = None
		self._channel = None
		if self._configuration.settings['face_images_predownload']:
			self._from_queue = self._configuration.infrastructure["face_agent_files_queue"]
		else:
			self._from_queue = self._configuration.infrastructure["face_queue"]
		self._to_exchange = self._configuration.infrastructure["export_exchange"]

		self._publisher = FaceDataPublisher(self._configuration.rabbitmq, self._to_exchange)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, trace):
		self._publisher.close()

	def _init_connection_and_channel(self):
		self._connection = _create_rabbitmq_connection(self._configuration.rabbitmq)
		self._channel = self._connection.channel()

	def _close_connection_and_channel(self):
		if self._channel is not None and self._channel.is_open:
			self._channel.stop_consuming()
			self._channel.close()

		if self._connection is not None and self._connection.is_open:
			self._connection.close()

	def run_forever(self):
		self._close_connection_and_channel()
		self._init_connection_and_channel()
		channel = self._channel

		# Allowing fair dispatch for all workers
		channel.basic_qos(prefetch_count=1)

		channel.basic_consume(
			queue=self._from_queue,
			on_message_callback=self._on_message_received_callback,
		)

		LOGGER.info("Service is ready to consume incoming messages")

		try:
			channel.start_consuming()
		except (
				AMQPHeartbeatTimeout, StreamLostError, ConnectionClosedByBroker, ChannelWrongStateError,
				ConnectionClosed,
				ConnectionBlockedTimeout):
			LOGGER.warning(
				"Channel start_consuming connection lost error", exc_info=True
			)
			time.sleep(5)
			LOGGER.info("Trying reconnect after connection fail.")
			self.run_forever()

	def _on_message_received_callback(self, channel, method, properties, body):
		# Message confirmation details: https://www.rabbitmq.com/confirms.html

		LOGGER.debug("New price message received: %s", body)

		try:
			message = json.loads(body)
			self._try_process_new_message_body(message)

		except (JSONDecodeError, TypeError, ValueError) as e:
			if "Image file not found" in str(e):
				channel.basic_ack(delivery_tag=method.delivery_tag)
				LOGGER.error(f"Unknown image url {message}")
			else: 
				channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
				LOGGER.error(
					"Invalid JSON '%s' obtained from the input queue", body, exc_info=True
				)			
		except (AMQPError, ChannelError, ReentrancyError):
			channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
			LOGGER.error(
				"Error during sending a message '%s' to output queue",
				body,
				exc_info=True,
			)
		except cv2.error as e:
			channel.basic_ack(delivery_tag=method.delivery_tag)
			if self._configuration.settings['face_images_predownload']:
				os.remove(message['file_path'])
			LOGGER.error("cv2.error")
		except urllib.error.HTTPError:
			channel.basic_ack(delivery_tag=method.delivery_tag)
			if self._configuration.settings['face_images_predownload']:
				os.remove(message['file_path'])
			LOGGER.error("urllib.error.HTTPError")
		except Exception as e:
			if "Name or service not known" in str(e):
				channel.basic_ack(delivery_tag=method.delivery_tag)
				if self._configuration.settings['face_images_predownload']:
					os.remove(message['file_path'])
				LOGGER.error("Unknown image url")
			else:
				channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
				LOGGER.error(
					f"Unknown error, but backtrace {e}",
					body,
					exc_info=True,
				)
				time.sleep(5)
		else:
			channel.basic_ack(delivery_tag=method.delivery_tag)
			if self._configuration.settings['face_images_predownload']:
				os.remove(message['file_path'])

			LOGGER.debug("Message '%s' is processed successfully", body)

	@staticmethod
	def find_area(obj):
		x1, y1, x2, y2 = obj
		return abs(x1 - x2) * abs(y1 - y2)

	@staticmethod
	def age_filter(obj):
		MIN_AGE = 16.4

		if obj["age"] is not None:
			return obj["age"] > MIN_AGE
		else:
			return True

	def _try_process_new_message_body(self, message):
		user_id = message['user_id']
		if self._configuration.settings['face_images_predownload']:
			file_path = message['file_path']
			d = start_finding_gender_age_from_file(file_path)
		else:
			img_url = message['profile_pic_url_hd']
			if img_url == None:
				return True
			d = start_finding_gender_age(img_url)
		LOGGER.debug(d)
		if d is not None:
			first_person = d[0]

			d = list(filter(self.age_filter, d))
			if len(d) == 0:
				d = [first_person]

			k = 0.55
			areas = list(map(lambda obj: self.find_area(obj["coordinates"]), d))
			max_area = max(areas)
			min_area = max_area * k
			new_areas = list(filter(lambda coordinates: coordinates[1] >= min_area, list(enumerate(areas))))
			predictor_data = []
			for index, area in new_areas:
				predictor_data.append(d[index])
			answer = {
				"gender": list(set(map(lambda person: person["gender"], predictor_data))),
				"age": list(map(lambda person: int(person["age"]), predictor_data))
			}
			if answer is not None:
				LOGGER.info(f"Success detect face with mivolo {answer}")
				self._send_message_to_output_queue(user_id, answer['age'], answer['gender'])

	def _send_message_to_output_queue(self, user_id, age, gender):
		data = {
			'user_id': user_id,
			'age': age,
			'gender': gender
		}

		export_msg = {
			'data': data,
			'type': 'face_recognition'
		}

		self._publisher.publish_message(export_msg)
		LOGGER.debug("Notification for the message '%s' was successfully sent", export_msg)


def _set_log_level(loglevel):
	try:
		LOGGER.setLevel(LOG_LEVEL_MAP[loglevel])
	except:
		LOGGER.setLevel(logging.WARNING)
	finally:
		logging.basicConfig(style="$", format=LOGGING_FORMAT_STRING)


def _create_rabbitmq_connection(config):
	config_copy = {**config}
	config_copy['virtual_host'] = config_copy['vhost']

	crd = {
		'username': config['username'],
		'password': config['password'],
	}

	credentials = pika.PlainCredentials(**crd)
	config_copy.pop("username")
	config_copy.pop("password")
	config_copy.pop("vhost")

	return pika.BlockingConnection(
		pika.ConnectionParameters(credentials=credentials, **config_copy)
	)


def read_parameters_from_cli_arguments():
	parser = argparse.ArgumentParser(description="face recognition agent CLI")
	parser.add_argument(
		"-c",
		"--config",
		help="path to configuration file",
		required=True,
		dest="configuration_filename",
	)
	parser.add_argument(
		"-l",
		"--loglevel",
		help="log level",
		required=True,
		dest="log_level",
	)
	parser.add_argument(
		"-t",
		"--parsertype",
		help="parser type",
		required=True,
		dest="parser_type",
	)

	return parser.parse_args()


def read_configuration_from_file(filename: str, parser_type) -> Configuration:
	with open(filename, 'r') as f:
		valuesYaml = yaml.load(f, Loader=yaml.FullLoader)

	return Configuration(valuesYaml, parser_type)


def exit(status_code: int):
	# Borrowed from here: https://www.rabbitmq.com/tutorials/tutorial-one-python.html
	try:
		sys.exit(status_code)
	except SystemExit:
		os._exit(status_code)


def start_service(configuration: Configuration):
	with FaceAgent(configuration) as service:
		service.run_forever()


def main():
	cli_parameters = read_parameters_from_cli_arguments()
	configuration_filename = cli_parameters.configuration_filename
	_set_log_level(cli_parameters.log_level)

	LOGGER.info("Reading configuration from file '%s'", configuration_filename)
	try:
		configuration = read_configuration_from_file(configuration_filename, cli_parameters.parser_type)
	except:
		LOGGER.critical(
			"Something went wrong with reading configuration file '%s'",
			configuration_filename,
			exc_info=True,
		)
		exit(1)

	LOGGER.info("Starting service...")
	try:
		start_service(configuration)
	except KeyboardInterrupt:
		LOGGER.warning("Interrupted by user")
		exit(0)
	except:
		LOGGER.critical("Unhandled exception has happened", exc_info=True)
		exit(1)


if __name__ == "__main__":
	main()
