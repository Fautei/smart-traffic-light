import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from cv_bridge import CvBridge

from traffic_light_msgs.msg import PolygonPoints, VehicleCounts, PolygonPoint
from std_msgs.msg import Int32MultiArray, Float32
from sensor_msgs.msg import PointCloud2

class TrafficCounter(Node):
    """
    Traffic Counter Node
    
    Subscribes to detector topic and polygon topic, counts vehicles and persons
    in the configured zone, and publishes the counts.
    """

    def __init__(self):
        super().__init__('traffic_counter')

        # Parameters
        self.declare_parameter('detection_topic', '/detections_1')
        self.declare_parameter('polygon_topic', '/polygon_config/polygon')
        self.declare_parameter('count_topic', '/traffic_counter/counts')
        self.declare_parameter('config_path', '/tmp/polygon_config.json')

        self.detection_topic = self.get_parameter('detection_topic').value
        self.polygon_topic = self.get_parameter('polygon_topic').value
        self.count_topic = self.get_parameter('count_topic').value
        self.config_path = self.get_parameter('config_path').value

        # Bridge
        self.bridge = CvBridge()

        # Polygon points storage
        self.polygon_points = []

        # Vehicle classes (from YOLO)
        self.VEHICLE_CLASSES = {'car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'}

        # Publishers
        self.count_pub = self.create_publisher(VehicleCounts, self.count_topic, 10)

        # Subscribers
        self.detection_sub = self.create_subscription(
            Detection2DArray,
            self.detection_topic,
            self.detection_callback,
            10
        )

        self.polygon_sub = self.create_subscription(
            PolygonPoints,
            self.polygon_topic,
            self.polygon_callback,
            10
        )

        # Sensor stub topic subscriptions (pass - no processing)
        self.declare_parameter('lidar_topic', '/lidar/scan')
        self.declare_parameter('ir_topic', '/ir_sensor/data')
        self.declare_parameter('ultrasonic_topic', '/ultrasonic_sensor/data')

        self.lidar_topic = self.get_parameter('lidar_topic').value
        self.ir_topic = self.get_parameter('ir_topic').value
        self.ultrasonic_topic = self.get_parameter('ultrasonic_topic').value

        self.lidar_sub = self.create_subscription(
            PointCloud2,
            self.lidar_topic,
            self.lidar_callback,
            10
        )

        self.ir_sub = self.create_subscription(
            Float32,
            self.ir_topic,
            self.ir_callback,
            10
        )

        self.ultrasonic_sub = self.create_subscription(
            Float32,
            self.ultrasonic_topic,
            self.ultrasonic_callback,
            10
        )


        # Load saved polygon if exists
        self.load_polygon()

        self.get_logger().info("Traffic Counter initialized")
        self.get_logger().info(f"Subscribes to: {self.detection_topic}")
        self.get_logger().info(f"Polygon from: {self.polygon_topic}")
        self.get_logger().info(f"Publishes counts to: {self.count_topic}")

    def polygon_callback(self, msg: PolygonPoints):
        """Callback for receiving polygon configuration"""
        self.polygon_points = []
        for point in msg.points:
            self.polygon_points.append((point.x, point.y))
        self.get_logger().info(f"Received polygon with {len(self.polygon_points)} points")
        self.save_polygon()

    def lidar_callback(self, msg: PointCloud2):
        """Callback for receiving lidar data (pass - no processing)"""
        pass

    def ir_callback(self, msg: Float32):
        """Callback for receiving IR sensor data (pass - no processing)"""
        pass

    def ultrasonic_callback(self, msg: Float32):
        """Callback for receiving ultrasonic sensor data (pass - no processing)"""
        pass

    def save_polygon(self):
        """Save polygon to config file"""
        if len(self.polygon_points) > 0:
            try:
                config = {
                    'points': [{'x': float(x), 'y': float(y)} for x, y in self.polygon_points]
                }
                import json
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.get_logger().info(f"Polygon saved to {self.config_path}")
            except Exception as e:
                self.get_logger().warning(f"Failed to save polygon: {e}")

    def load_polygon(self):
        """Load polygon from config file"""
        try:
            import json
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.polygon_points = [(p['x'], p['y']) for p in config['points']]
                self.get_logger().info(f"Loaded polygon with {len(self.polygon_points)} points from {self.config_path}")
        except FileNotFoundError:
            self.get_logger().info(f"No polygon config found at {self.config_path}, waiting for configuration...")
        except Exception as e:
            self.get_logger().warning(f"Failed to load polygon: {e}")

    def is_inside_polygon(self, x, y):
        """
        Fast polygon test using OpenCV.
        """
        if not self.polygon_points:
            return False

        polygon_np = np.array(
                        self.polygon_points,
                        dtype=np.int32
                    )

        result = cv2.pointPolygonTest(
            polygon_np,
            (float(x), float(y)),
            False
        )

        return result >= 0

    def detection_callback(self, msg: Detection2DArray):
        """Callback for receiving detections"""

        counts = {n:0 for n in self.VEHICLE_CLASSES}

        for detection in msg.detections:
            if len(detection.results) == 0:
                continue

            cls = detection.results[0].hypothesis.class_id
            bbox = detection.bbox

            # Calculate center of bounding box
            cx = bbox.center.position.x
            cy = bbox.center.position.y

            # Check if center is inside polygon
            if self.is_inside_polygon(cx, cy):
                if cls in self.VEHICLE_CLASSES:
                    counts[cls] +=1




        # Publish counts
        counts_msg = VehicleCounts()
        counts_msg.polygon = [PolygonPoint(x=_x, y=_y) for _x,_y in self.polygon_points]
        counts_msg.detection_names = list(self.VEHICLE_CLASSES)
        counts_msg.counts = counts.values()
        self.count_pub.publish(counts_msg)

        self.get_logger().debug(f"Counts: {counts} ")




def main():
    rclpy.init()
    node = TrafficCounter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()