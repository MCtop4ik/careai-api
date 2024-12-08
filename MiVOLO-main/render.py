import io
import logging
import os
import urllib.request
import numpy as np

import cv2
from mivolo.predictor import Predictor
from timm.utils import setup_default_logging

from mivolo.config.config_render import Config, logging_level

_logger = logging.getLogger("inference")
_logger.setLevel(logging_level)
_predictor = Predictor(Config(), verbose=True)


def get_parser(link):
	return Config(link)


def get_image_stream(link):
	with urllib.request.urlopen(link) as url:
		stream = io.BytesIO(url.read())
	return stream
	
def start_finding_gender_age_from_file(file_path):
	data = None
	img = None
	if os.path.exists(file_path):
		img = cv2.imread(file_path)
	else:
		raise ValueError('Image file not found')
	if img is not None:
		data = _predictor.recognize(img)
	return data


def start_finding_gender_age(link):
	try:
		parser = get_parser(link)
		args = parser

		os.makedirs(args.output, exist_ok=True)

		stream = get_image_stream(link)
		buff = np.fromstring(stream.getvalue(), dtype=np.uint8)
		stream.close()
	
		img = cv2.imdecode(buff, cv2.IMREAD_ANYCOLOR)
		data = None
		if img is not None:
			data = _predictor.recognize(img)
		else:
			_logger.error(f"{link} => cannot get image")
		return data
	except ValueError:
		_logger.error(f"{link} => Axes dont match")
		return None

# if __name__ == "__main__":
#     main()
def find_area(obj):
	x1, y1, x2, y2 = obj
	return abs(x1 - x2) * abs(y1 - y2)

def age_filter(obj):
	MIN_AGE = 12

	if obj["age"] is not None:
		return obj["age"] > MIN_AGE
	else:
		return True

if __name__ == "__main__":
    import sys
    link = str(sys.argv[1])
    result = start_finding_gender_age(link)
    if result is not None:
        first_person = result[0]
        result = list(filter(age_filter, result))
        if len(result) == 0:
            result = [first_person]

        k = 0.55
        areas = list(map(lambda obj: self.find_area(obj["coordinates"]), result))
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
        print(answer)
        if answer is not None:
            print(rf"Success detect face with mivolo {answer}")
