import logging


class Config:
    def __init__(self, input_value=None):
        self.input = input_value
        self.output = 'output'
        self.detector_weights = 'models/yolov8x_person_face.pt'
        self.checkpoint = 'models/mivolo_imbd.pth.tar'
        self.with_persons = True
        self.disable_faces = False
        self.draw = True
        self.device = 'cpu'


LOG_LEVEL_HASH = {
    "critical": logging.CRITICAL,
    "fatal": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG
}

LOG_LEVEL = "critical"

logging_level = LOG_LEVEL_HASH[LOG_LEVEL]
