from car.config import load_config
from car.parts.camera import Webcam
from car.parts.datastore import DatasetHandler
from car.parts.engine import Engine
from car.parts.web.client.ai import AI
from car.parts.web.client.ui import UI

from car.vehicle import Vehicle

# Load default settings
cfg = load_config()

# Initialize the car
car = Vehicle(warm_up_seconds=cfg.WARM_UP_SECONDS)

# Add a webcam
cam = Webcam(
    pi_host=cfg.PI_HOSTNAME,
    name='camera',
    unit_test=False)
car.add(
    cam,
    outputs=['cam/image_array'],
    threaded=True)

# Add a web app / user interface accessible via laptop or phone
ui = UI(
    api=cfg.UI_API,
    name='ui',
    server_path=cfg.UI_SERVER_PATH,
    port=cfg.WEB_UI_PORT)
car.add(
    ui,
    outputs=[
        'remote_model/angle',
        'remote_model/throttle',
        'user/angle',
        'user/throttle',
        'mode',
        'recording',
        'user-brake',
        'max_throttle'
    ],
    threaded=True)
server_message = "You can now go to {host}:{port} to drive your car."
print(server_message.format(host=cfg.PI_HOSTNAME, port=cfg.WEB_UI_PORT))

# Add AI API caller
ai = AI(
    model_api=cfg.MODEL_API,
    name='ai',
    server_path=cfg.AI_SERVER_PATH,
    port=cfg.WEB_AI_PORT,
    image_scale=cfg.IMAGE_SCALE,
    crop_factor=cfg.CROP_FACTOR,
    model_directory=cfg.MODEL_PATH,
    angle_only=cfg.ANGLE_ONLY)
car.add(
    ai,
    inputs=['cam/image_array'],
    outputs=['ai/angle', 'ai/throttle'],
    threaded=True)

# Add engine
engine_inputs =[
    'user/angle',
    'user/throttle',
    'remote_model/angle',
    'remote_model/throttle',
    'local_model/angle',
    'local_model/throttle',
    'mode',
    'system-brake',
    'user-brake',
    'max_throttle']
engine = Engine(16, 18, 22, 19, 21, 23, name='engine', input_names=engine_inputs)
car.add(
    engine,
    inputs=engine_inputs,
    threaded=True)

# Add dataset to save data
recorded_inputs = [
    'cam/image_array',
    'user/angle',
    'user/throttle',
    'ai/angle',
    'ai/throttle',
    'mode',
    'system-brake',
    'user-brake',
    'ai/healthcheck',
    'max_throttle']
types = [
    'image_array',
    'float',
    'float',
    'float',
    'float',
    'str',
    'boolean',
    'boolean',
    'str',
    'float']
dh = DatasetHandler(path=cfg.DATA_PATH)
print(cfg.DATA_PATH)
dataset = dh.new_dataset_writer(inputs=recorded_inputs, types=types)
dataset.set_name('dataset')
car.add(
    dataset,
    inputs=recorded_inputs,
    run_condition='recording')

car.start(
    rate_hz=cfg.DRIVE_LOOP_HZ,
    max_loop_count=cfg.MAX_LOOPS)
