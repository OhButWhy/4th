import sys
import time
import cv2
import threading
import queue
import argparse
from datetime import datetime
from pathlib import Path
import logging


class Sensor:
    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")


class SensorX(Sensor):
    '''SensorX'''

    def __init__(self, delay: float):
        self.delay = delay
        self.data = 0

    def get(self) -> int:
        time.sleep(self.delay)
        self.data += 1
        return self.data


class SensorCam(Sensor):
    def __init__(self, camera_name, resolution):
        self.camera = cv2.VideoCapture(camera_name, cv2.CAP_DSHOW)
        if not self.camera.isOpened():
            logging.error(f"Не удалось открыть камеру {camera_name}")
            raise RuntimeError(f"Не удалось открыть камеру {camera_name}")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    def get(self):
        ret, img = self.camera.read()
        if not ret:
            logging.critical(
                "Камера перестала выдавать кадры (возможно, отключена)")
            sys.exit(1)
        return img if ret else None

    def __del__(self):
        self.camera.release()


class WindowImage():
    def __init__(self, fps):
        # self.a = 1
        self.fps = fps

    def show(self, image):
        cv2.imshow('img', image)
        k = cv2.waitKey(1000//self.fps) & 0xff
        if k == ord('q'):
            return True
        return False

    def __del__(self):
        cv2.destroyAllWindows()


def worker(que, sensor, stop_event):
    while not stop_event.is_set():
        item = sensor.get()
        if item is not None:
            try:
                que.get_nowait()
            except queue.Empty:
                pass
            que.put(item)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("camera_path", type=str)
    parser.add_argument("--resolution", type=str, default="640x480")
    parser.add_argument("--fps", type=int, default=30)
    return parser.parse_args()


def mainn(que_cam, stop_event, fps):
    # i = 0
    first = 0
    zero = 0
    second = 0

    window = WindowImage(fps)
    last_frame = None

    while not stop_event.is_set():
        try:
            frame = que_cam.get_nowait()
            if frame is not None:
                last_frame = frame
        except queue.Empty:
            pass

        try:
            first = que1.get_nowait()
        except queue.Empty:
            pass

        try:
            second = que2.get_nowait()
        except queue.Empty:
            pass

        try:
            zero = que0.get_nowait()
        except queue.Empty:
            pass

        # cv2.imshow('img', cmra)
        if last_frame is not None:
            img = last_frame.copy()
            cv2.putText(img, f"{zero}, {first}, {second}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            if window.show(img):
                stop_event.set()
                break

        # print(zero, first, second)
        # i += 1

    print("end")


if __name__ == "__main__":
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    args = parse_args()
    camera_path = args.camera_path
    if camera_path.isdigit():
        camera_path = int(camera_path)
    fps = int(args.fps)
    resolution = args.resolution
    resolution = tuple(map(int, resolution.split('x')))

    stop = threading.Event()

    que_cam = queue.Queue(maxsize=1)
    que0 = queue.Queue(maxsize=1)
    que1 = queue.Queue(maxsize=1)
    que2 = queue.Queue(maxsize=1)

    sensor0 = SensorX(0.01)
    sensor1 = SensorX(0.1)
    sensor2 = SensorX(1)
    try:
        my_camera = SensorCam(camera_path, resolution)
    except RuntimeError as e:
        logging.error(f"Ошибка при инициализации камеры: {e}")
        sys.exit(1)

    threading.Thread(target=worker, args=(
        que_cam, my_camera,  stop)).start()
    threading.Thread(target=worker, args=(que0, sensor0,  stop)).start()
    threading.Thread(target=worker, args=(que1, sensor1,  stop)).start()
    threading.Thread(target=worker, args=(que2, sensor2,  stop)).start()
    main_thread = threading.Thread(
        target=mainn, args=(que_cam,  stop, fps))
    main_thread.start()
    main_thread.join()
    stop.set()
