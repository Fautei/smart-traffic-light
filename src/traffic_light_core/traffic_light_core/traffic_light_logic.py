import json
from enum import Enum, auto

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32, String
from vision_msgs.msg import Detection2DArray


class TrafficLightState(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()


class TrafficLightLogic(Node):

    VEHICLE_CLASSES = {
        'car',
        'truck',
        'bus',
        'motorcycle'
    }

    def __init__(self):
        super().__init__('traffic_light_logic')

        self.declare_parameter('detection_topic', '/detections')

        self.create_subscription(
            Detection2DArray,
            self.get_parameter(
                'detection_topic'
            ).get_parameter_value().string_value,
            self.detection_callback,
            10
        )

    def detection_callback(self, msg):
        count = 0
        for det in msg.detections:
            if len(det.results) == 0:
                continue

            cls = det.results[0].hypothesis.class_id
            if cls in self.VEHICLE_CLASSES:
                count += 1

        self.vehicle_count = count

        if count > 0:
            self.last_vehicle_time = self.get_clock().now()
            self.get_logger().info(f"Detected vehicle")
        




def main(args=None):
    rclpy.init(args=args)
    node = TrafficLightLogic()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()