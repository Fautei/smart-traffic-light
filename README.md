# Smart Traffic Light System

ROS 2 package for a smart traffic light system designed for single-lane road repair work. The system consists of two mobile traffic lights with cameras that communicate with each other to coordinate traffic flow.

## Features

- **Dual Traffic Light Coordination**: Two traffic lights work together to manage traffic on a single-lane road during repairs
- **YOLO-based Object Detection**: Uses OpenCV DNN with YOLO for vehicle detection
- **Camera Calibration Support**: Supports camera intrinsic and extrinsic parameters
- **State Machine Logic**: Implements traffic light state transitions based on vehicle detection
- **Peer-to-Peer Communication**: Traffic lights communicate directly with each other

## System Architecture

### Nodes

1. **Camera Node** (`video_io/camera_node`)
   - Captures video stream from GStreamer pipeline
   - Publishes camera images and calibration info

2. **Object Detector Node** (`traaffic_light_core/object_detector`)
   - Uses YOLOv8 for vehicle detection
   - Publishes detection results

3. **Traffic Light Logic Node** (`traaffic_light_core/traffic_light_logic`)
   - Implements state machine for traffic light control
   - Communicates with peer traffic light

### State Machine

```
GREEN → YELLOW → RED → GREEN (cycle)
     ↑                    ↓
     └── Wait for vehicles ─┘
```

**Algorithm:**
1. Traffic light A is GREEN, Traffic light B is RED
2. When vehicle approaches RED light (B), it sends signal to GREEN light (A)
3. GREEN light (A) waits for road to clear (max N seconds)
4. GREEN light (A) turns RED
5. After delay, RED light (B) turns GREEN
6. Cycle repeats

## Installation

### Prerequisites

- ROS 2 (Humble or newer)
- Python 3.8+
- GStreamer (for camera stream)

### Build

```bash
cd ~/colcon_ws/src
git clone <this-repo>
cd ..
colcon build
source install/setup.bash
```

### Install Dependencies

```bash
pip install gdown onnx opencv-python PyYAML
```

## Usage

### Launch Pair of Traffic Lights

```bash
ros2 launch traaffic_light_launch traaffic_light_pair.launch.py \
  node_0_gstreamer_pipeline="v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! appsink" \
  node_1_gstreamer_pipeline="v4l2src device=/dev/video1 ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! appsink" \
  node_0_calibration_file="$(pwd)/config/camera_calibration.yaml" \
  node_1_calibration_file="$(pwd)/config/camera_calibration.yaml" \
  model_config="yolov8n" \
  confidence_threshold=0.5 \
  wait_time_clear=5.0 \
  wait_time_green=3.0 \
  max_wait_time=30.0
```

### Launch Single Traffic Light

```bash
ros2 launch traaffic_light_launch traaffic_light_launch.py \
  node_id=0 \
  gstreamer_pipeline="v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! appsink" \
  calibration_file="$(pwd)/config/camera_calibration.yaml" \
  model_config="yolov8n" \
  confidence_threshold=0.5
```

## Configuration Parameters

### Camera Node
- `gstreamer_pipeline`: GStreamer pipeline string
- `camera_info_url`: URL to camera calibration (file://path/to/calibration.yaml)
- `calibration_file`: Path to calibration YAML file
- `frame_id`: Frame ID for camera
- `camera_name`: Name of camera

### Object Detector
- `model_config`: YOLO model config (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
- `confidence_threshold`: Detection confidence threshold
- `nms_threshold`: Non-maximum suppression threshold
- `classes_to_detect`: List of classes to detect
- `use_cuda`: Use CUDA for inference (if available)

### Traffic Light Logic
- `node_id`: ID of this traffic light (0 or 1)
- `wait_time_clear`: Time to wait for vehicles to clear
- `wait_time_green`: Time to wait before switching to green
- `max_wait_time`: Maximum time to wait for road to clear

## Topics

### Published
- `/camera/image_raw` - Raw camera images
- `/camera/camera_info` - Camera calibration info
- `/detections` - Detection results (JSON)
- `/traffic_light/state` - Current traffic light state (0=red, 1=yellow, 2=green)
- `/traffic_light/peer_0` - Peer light state (node 0)
- `/traffic_light/peer_1` - Peer light state (node 1)

### Subscribed
- `/detections` - Detection results
- `/traffic_light/peer_0` - Peer light state (node 0)
- `/traffic_light/peer_1` - Peer light state (node 1)

## Future Work

- Add LiDAR sensor support
- Add ultrasonic sensor support
- Implement more advanced detection algorithms
- Add GUI for monitoring and configuration

## License

Apache-2.0