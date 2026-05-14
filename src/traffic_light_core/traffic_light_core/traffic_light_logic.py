import json
from enum import Enum, auto
import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32, String
from vision_msgs.msg import Detection2DArray

from traffic_light_msgs.msg import TrafficLightState


class TrafficLightStateEnum(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()


class TrafficLightLogic(Node):
    """
    Traffic light logic controller with timed phases.
    Controls two traffic lights in opposite phases.
    """

    VEHICLE_CLASSES = {
        'car',
        'truck',
        'bus',
        'motorcycle'
    }

    # Phase durations in seconds
    GREEN_DURATION = 30
    YELLOW_DURATION = 5
    RED_DURATION = 30

    def __init__(self):
        super().__init__('traffic_light_logic')

        # Phase state: 0=GREEN, 1=YELLOW, 2=RED
        self.phase_state = 0
        self.phase_start_time = time.time()

        # Current light states for both traffic lights (0=RED, 1=YELLOW, 2=GREEN)
        self.traffic_light_1_state = 0  # RED
        self.traffic_light_2_state = 2  # GREEN (opposite phase)

        # Publishers for traffic light states
        self.tl1_pub = self.create_publisher(
            TrafficLightState,
            '/traffic_light_1/state',
            10
        )
        self.tl2_pub = self.create_publisher(
            TrafficLightState,
            '/traffic_light_2/state',
            10
        )

        # Timer for updating traffic light states
        self.timer = self.create_timer(1.0, self.update_timer_callback)

        self.get_logger().info('Traffic light logic initialized')

    def update_timer_callback(self):
        """
        Update traffic light states based on time.
        Lights operate in opposite phases.
        """
        current_time = time.time()
        elapsed = current_time - self.phase_start_time

        if self.phase_state == 0:  # GREEN
            if elapsed >= self.GREEN_DURATION:
                self.phase_state = 1  # Switch to YELLOW
                self.phase_start_time = current_time
                self.get_logger().info('Phase changed: GREEN -> YELLOW')
        elif self.phase_state == 1:  # YELLOW
            if elapsed >= self.YELLOW_DURATION:
                self.phase_state = 2  # Switch to RED
                self.phase_start_time = current_time
                self.get_logger().info('Phase changed: YELLOW -> RED')
        elif self.phase_state == 2:  # RED
            if elapsed >= self.RED_DURATION:
                self.phase_state = 0  # Switch to GREEN
                self.phase_start_time = current_time
                self.get_logger().info('Phase changed: RED -> GREEN')

        # Update traffic light states (opposite phases)
        if self.phase_state == 0:  # GREEN
            self.traffic_light_1_state = 2  # GREEN
            self.traffic_light_2_state = 0  # RED
        elif self.phase_state == 1:  # YELLOW
            self.traffic_light_1_state = 1  # YELLOW
            self.traffic_light_2_state = 1  # YELLOW
        elif self.phase_state == 2:  # RED
            self.traffic_light_1_state = 0  # RED
            self.traffic_light_2_state = 2  # GREEN

        # Publish states
        tl1_msg = TrafficLightState()
        tl1_msg.state = self.traffic_light_1_state
        self.tl1_pub.publish(tl1_msg)

        tl2_msg = TrafficLightState()
        tl2_msg.state = self.traffic_light_2_state
        self.tl2_pub.publish(tl2_msg)

        self.get_logger().info(
            f'Traffic Light 1: {self._state_to_str(self.traffic_light_1_state)}, '
            f'Traffic Light 2: {self._state_to_str(self.traffic_light_2_state)}'
        )

    def _state_to_str(self, state):
        """Convert state number to string."""
        states = {0: 'RED', 1: 'YELLOW', 2: 'GREEN'}
        return states.get(state, 'UNKNOWN')
        



def main(args=None):
    rclpy.init(args=args)
    node = TrafficLightLogic()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
