import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from cv_bridge import CvBridge

from traffic_light_msgs.msg import PolygonPoints, PolygonPoint
from std_msgs.msg import Int32MultiArray


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
        self.declare_parameter('image_topic', '/camera_1/image_detections')
        self.declare_parameter('count_topic', '/traffic_counter/counts')
        self.declare_parameter('debug_topic', '/traffic_counter/debug')
        self.declare_parameter('config_path', '/tmp/polygon_config.json')

        self.detection_topic = self.get_parameter('detection_topic').value
        self.polygon_topic = self.get_parameter('polygon_topic').value
        self.image_topic = self.get_parameter('image_topic').value
        self.count_topic = self.get_parameter('count_topic').value
        self.debug_topic = self.get_parameter('debug_topic').value
        self.config_path = self.get_parameter('config_path').value

        # Bridge
        self.bridge = CvBridge()

        # Polygon points storage
        self.polygon_points = []

        # Count storage
        self.vehicle_count = 0
        self.person_count = 0

        # Vehicle classes (from YOLO)
        self.VEHICLE_CLASSES = {'car', 'truck', 'bus', 'motorcycle', 'bicycle', 'boat'}
        self.PERSON_CLASSES = {'person'}

        # Publishers
        self.count_pub = self.create_publisher(Int32MultiArray, self.count_topic, 10)
        self.debug_pub = self.create_publisher(Image, self.debug_topic, 10)

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

        # Debug image subscriber (optional)
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        # Current frame for debug display
        self.current_frame = None

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

        polygon_np = np.array(
                        self.polygon_points,
                        dtype=np.int32
                    )

        result = cv2.pointPolygonTest(
            polygon_np,
            (float(x), float(y)),
            False
        )

        self.get_logger().info(f"Polygon: {polygon_np}")

        return result >= 0

    def detection_callback(self, msg: Detection2DArray):
        """Callback for receiving detections"""
        vehicle_count = 0
        person_count = 0

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
                    vehicle_count += 1
                elif cls in self.PERSON_CLASSES:
                    person_count += 1

        self.vehicle_count = vehicle_count
        self.person_count = person_count

        # Publish counts
        counts_msg = Int32MultiArray()
        counts_msg.data = [vehicle_count, person_count]
        self.count_pub.publish(counts_msg)

        self.get_logger().debug(f"Counts: {vehicle_count} vehicles, {person_count} persons")

    def image_callback(self, msg: Image):
        """Callback for receiving debug images"""
        try:
            self.current_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")

    def draw_debug_frame(self):
        """Draw debug frame with polygon and counts"""
        if self.current_frame is None:
            return None

        frame = self.current_frame.copy()
        height, width = frame.shape[:2]

        # Draw polygon
        if len(self.polygon_points) >= 3:
            points = [(int(x), int(y)) for x, y in self.polygon_points]
            for i in range(len(points)):
                next_i = (i + 1) % len(points)
                cv2.line(frame, points[i], points[next_i], (0, 255, 0), 2)
            cv2.polylines(frame, [np.array(points)], True, (0, 255, 0), 2)

        # Draw counts
        cv2.putText(frame, f"Vehicles: {self.vehicle_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Persons: {self.person_count}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        return frame

    def timer_callback(self):
        """Timer callback to publish debug frame"""
        if self.current_frame is not None:
            debug_frame = self.draw_debug_frame()
            if debug_frame is not None:
                self.debug_pub.publish(self.bridge.cv2_to_imgmsg(debug_frame, encoding="bgr8"))


def main():
    rclpy.init()
    node = TrafficCounter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()