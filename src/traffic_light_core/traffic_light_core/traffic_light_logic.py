import json
from enum import Enum, auto
import time
from collections import deque

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32, String
from vision_msgs.msg import Detection2DArray

from traffic_light_msgs.msg import TrafficLightState, VehicleCounts


class TrafficLightStateEnum(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()


class TrafficLightLogic(Node):
    """
    Traffic light logic controller with dynamic timing based on traffic counters.
    Controls two traffic lights in opposite phases.
    """

    VEHICLE_CLASSES = {
        'car',
        'truck',
        'bus',
        'motorcycle'
    }

    # Base phase durations in seconds
    GREEN_DURATION_MIN = 10
    GREEN_DURATION_MAX = 60
    GREEN_DURATION_BASE = 30
    YELLOW_DURATION = 5
    RED_DURATION = 30

    # Ratio for green light allocation between two directions
    # If direction 1 has 3x more traffic, it gets 75% of green time
    DIRECTION_RATIO_WEIGHT = 0.5  # Base weight for balanced allocation

    def __init__(self):
        super().__init__('traffic_light_logic')

        # Phase state: 0=GREEN, 1=YELLOW, 2=RED
        self.phase_state = 0
        self.phase_start_time = time.time()

        # Current light states for both traffic lights (0=RED, 1=YELLOW, 2=GREEN)
        self.traffic_light_1_state = 0  # RED
        self.traffic_light_2_state = 2  # GREEN (opposite phase)

        # Traffic counters data storage
        # Use deque to store recent counts for smoothing
        self.counter_data_1 = {
            'timestamps': deque(maxlen=1000),
            'counts': deque(maxlen=1000),
            'total_vehicles': 0,
            'last_update': 0.0
        }
        self.counter_data_2 = {
            'timestamps': deque(maxlen=1000),
            'counts': deque(maxlen=1000),
            'total_vehicles': 0,
            'last_update': 0.0
        }

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

        # Subscribers for traffic counters
        self.counter1_sub = self.create_subscription(
            VehicleCounts,
            '/traffic_counter_1/counts',
            self.counter1_callback,
            10
        )
        self.counter2_sub = self.create_subscription(
            VehicleCounts,
            '/traffic_counter_2/counts',
            self.counter2_callback,
            10
        )

        # Timer for updating traffic light states
        self.timer = self.create_timer(1.0, self.update_timer_callback)

        self.get_logger().info('Traffic light logic initialized')
        self.get_logger().info('Subscribed to traffic counters: /traffic_counter_1/counts, /traffic_counter_2/counts')

    def counter1_callback(self, msg: VehicleCounts):
        """Callback for traffic counter 1."""
        total = sum(msg.counts)
        self.counter_data_1['total_vehicles'] =total
        self.counter_data_1['last_update'] = time.time()
        self.counter_data_1['counts'].append(total)
        self.counter_data_1['timestamps'].append(time.time())
        #self.get_logger().debug(f'Traffic Counter 1: {total} vehicles')

    def counter2_callback(self, msg: VehicleCounts):
        """Callback for traffic counter 2."""
        total = sum(msg.counts)
        self.counter_data_2['total_vehicles'] = total
        self.counter_data_2['last_update'] = time.time()
        self.counter_data_2['counts'].append(total)
        self.counter_data_2['timestamps'].append(time.time())
        #self.get_logger().debug(f'Traffic Counter 2: {total} vehicles')

    def get_smoothed_traffic(self, counter_data):
        """Get smoothed traffic count using moving average."""
        return sum(counter_data['counts']) / max(len(counter_data['counts']), 1000)

    def calculate_green_duration(self, direction1_traffic, direction2_traffic):
        """
        Calculate green light duration for each direction based on traffic ratio.
        
        Returns (duration_for_direction_1, duration_for_direction_2)
        """
        # Total traffic
        total_traffic = direction1_traffic + direction2_traffic
        
        if total_traffic == 0:
            # No traffic - use base duration
            return self.GREEN_DURATION_BASE, self.GREEN_DURATION_BASE

        # Calculate ratio
        if direction2_traffic == 0:
            ratio = 1.0  # Avoid division by zero
        else:
            ratio = direction1_traffic / direction2_traffic

        # Calculate green time allocation
        # If ratio = 1 (equal traffic), each gets 50%
        # If ratio = 3 (direction 1 has 3x traffic), direction 1 gets 75%
        if ratio >= 1:
            direction1_share = ratio / (1 + ratio)
            direction2_share = 1.0 / (1 + ratio)
        else:
            direction1_share = 1.0 / (1 + (1/ratio))
            direction2_share = (1/ratio) / (1 + (1/ratio))

        # Apply to base duration with min/max limits
        duration1 = max(
            self.GREEN_DURATION_MIN,
            min(self.GREEN_DURATION_MAX, self.GREEN_DURATION_BASE * direction1_share)
        )
        duration2 = max(
            self.GREEN_DURATION_MIN,
            min(self.GREEN_DURATION_MAX, self.GREEN_DURATION_BASE * direction2_share)
        )

        return round(duration1, 1), round(duration2, 1)

    def update_timer_callback(self):
        """
        Update traffic light states based on time and traffic.
        Lights operate in opposite phases.
        """
        current_time = time.time()
        elapsed = current_time - self.phase_start_time

        # Get smoothed traffic counts
        traffic_1 = self.get_smoothed_traffic(self.counter_data_1)
        traffic_2 = self.get_smoothed_traffic(self.counter_data_2)

        # Log traffic information periodically
        if int(current_time) % 10 == 0:
            self.get_logger().debug(
                f'Traffic: TL1={traffic_1:.1f} veh, TL2={traffic_2:.1f} veh'
            )

        # Calculate green durations based on traffic
        green_duration_1, green_duration_2 = self.calculate_green_duration(traffic_1, traffic_2)

        # Determine current green duration based on which direction is green
        if self.phase_state == 0:  # GREEN phase
            # Direction 1 is green (traffic_light_1=GREEN, traffic_light_2=RED)
            current_green_duration = green_duration_1
        else:
            # Direction 2 is green (traffic_light_1=RED, traffic_light_2=GREEN)
            current_green_duration = green_duration_2

        if self.phase_state == 0:  # GREEN
            if elapsed >= current_green_duration:
                self.phase_state = 1  # Switch to YELLOW
                self.phase_start_time = current_time
                self.get_logger().debug(
                    f'Phase changed: GREEN -> YELLOW (direction 1 green: {green_duration_1:.1f}s, direction 2: {green_duration_2:.1f}s)'
                )
        elif self.phase_state == 1:  # YELLOW
            if elapsed >= self.YELLOW_DURATION:
                self.phase_state = 2  # Switch to RED
                self.phase_start_time = current_time
                self.get_logger().debug('Phase changed: YELLOW -> RED')
        elif self.phase_state == 2:  # RED
            if elapsed >= self.RED_DURATION:
                self.phase_state = 0  # Switch to GREEN
                self.phase_start_time = current_time
                self.get_logger().debug(
                    f'Phase changed: RED -> GREEN (direction 1 green: {green_duration_1:.1f}s, direction 2: {green_duration_2:.1f}s)'
                )

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
            f'Traffic Light 2: {self._state_to_str(self.traffic_light_2_state)}, '
            f'Traffic Ratio: {green_duration_1:.1f}/{green_duration_2:.1f}'
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