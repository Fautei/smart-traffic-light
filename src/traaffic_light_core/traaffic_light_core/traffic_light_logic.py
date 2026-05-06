"""
Traffic light logic node using standard ROS2 message types.
Coordinates two traffic lights on a single-lane road during repair work.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import time
from enum import Enum, auto
from typing import Optional
from datetime import datetime
import threading


class TrafficLightState(Enum):
    """States of the traffic light system"""
    GREEN = auto()      # Current light is green (allowing traffic)
    YELLOW = auto()     # Current light is yellow (warning)
    RED = auto()        # Current light is red (stop)
    WAITING_CLEAR = auto()  # Waiting for road to clear before switching


class TrafficLightStateMsg(String):
    """ROS2 message type for traffic light state"""
    pass


class TrafficLightLogic(Node):
    """
    Main logic node for smart traffic light system.
    Coordinates two traffic lights on a single-lane road during repair work.
    Uses standard ROS2 message types (Int32 for light state, String for peer communication).
    """
    
    def __init__(self):
        super().__init__('traffic_light_logic')
        
        # Declare parameters
        self.declare_parameter('node_id', 0)  # 0 or 1 - identifies which light this is
        self.declare_parameter('wait_time_clear', 5.0)  # Time to wait for vehicles to clear (seconds)
        self.declare_parameter('wait_time_green', 3.0)  # Time to wait before switching to green (seconds)
        self.declare_parameter('max_wait_time', 30.0)   # Max time to wait for road to clear (seconds)
        self.declare_parameter('detection_topic', '/detections')
        self.declare_parameter('light_state_topic', '/traffic_light/state')
        self.declare_parameter('light_command_topic', '/traffic_light/command')
        self.declare_parameter('peer_light_topic', '/traffic_light/peer')
        self.declare_parameter('debug_draw', False)
        
        # Get parameters
        self.node_id = self.get_parameter('node_id').get_parameter_value().integer_value
        
        # Validate node_id
        if self.node_id not in [0, 1]:
            self.get_logger().error(f"node_id must be 0 or 1, got {self.node_id}")
            rclpy.shutdown()
            return
        
        # State machine
        self.current_state = TrafficLightState.GREEN
        self.state_start_time = self.get_clock().now()
        self.traffic_light_state = 2  # Start with green (0=red, 1=yellow, 2=green)
        
        # Vehicle detection tracking
        self.last_vehicle_detection_time = None
        self.vehicles_in_frame = False
        
        # Peer communication
        self.peer_light_state = 0  # 0=red, 1=yellow, 2=green
        self.peer_last_seen = self.get_clock().now()
        
        # Timers
        self.wait_time_clear = self.get_parameter('wait_time_clear').get_parameter_value().double_value
        self.wait_time_green = self.get_parameter('wait_time_green').get_parameter_value().double_value
        self.max_wait_time = self.get_parameter('max_wait_time').get_parameter_value().double_value
        
        # Publishers - each node has unique topics based on node_id
        self.light_state_pub = self.create_publisher(Int32, self.get_parameter('light_state_topic').get_parameter_value().string_value, 10)
        self.light_command_pub = self.create_publisher(String, self.get_parameter('light_command_topic').get_parameter_value().string_value, 10)
        # Publish to peer's topic (node 0 publishes to /traffic_light/peer_1, node 1 publishes to /traffic_light/peer_0)
        self.peer_light_pub = self.create_publisher(String, f'/traffic_light/peer_{1 - self.node_id}', 10)
        
        # Subscribers - subscribe to peer's published topic
        self.detection_sub = self.create_subscription(
            String,
            self.get_parameter('detection_topic').get_parameter_value().string_value,
            self.detection_callback,
            10)
        
        self.peer_light_sub = self.create_subscription(
            String,
            f'/traffic_light/peer_{1 - self.node_id}',
            self.peer_light_callback,
            10)
        
        # State machine timer
        self.timer = self.create_timer(0.1, self.state_machine_loop)
        
        self.get_logger().info(f'Traffic light logic initialized (node_id={self.node_id})')
        self.get_logger().info(f'Initial state: GREEN (light={self.traffic_light_state})')
    
    def detection_callback(self, msg: String):
        """Process detection messages - expects JSON with detections array"""
        try:
            import json
            data = json.loads(msg.data)
            detections = data.get('detections', [])
            
            # Check if any vehicle is detected
            has_vehicle = False
            for det in detections:
                cls = det.get('class', '').lower()
                if cls in ['car', 'truck', 'bus', 'motorcycle']:
                    has_vehicle = True
                    break
            
            self.vehicles_in_frame = has_vehicle
            
            if has_vehicle:
                self.last_vehicle_detection_time = self.get_clock().now()
                
        except Exception as e:
            self.get_logger().error(f"Error processing detection: {e}")
    
    def peer_light_callback(self, msg: String):
        """Process peer light state messages - expects JSON with light_state field"""
        try:
            import json
            data = json.loads(msg.data)
            self.peer_light_state = data.get('light_state', 0)
            self.peer_last_seen = self.get_clock().now()
            
        except Exception as e:
            self.get_logger().error(f"Error processing peer light state: {e}")
    
    def state_machine_loop(self):
        """Main state machine loop"""
        now = self.get_clock().now()
        elapsed = (now - self.state_start_time).nanoseconds / 1e9
        
        # Check if peer communication is still active
        peer_timeout = (now - self.peer_last_seen).nanoseconds / 1e9
        if peer_timeout > 5.0:
            self.get_logger().warn(f"Peer light communication timeout ({peer_timeout:.1f}s)")
        
        # Process state transitions
        if self.current_state == TrafficLightState.GREEN:
            # Wait for vehicle to approach
            if self.vehicles_in_frame:
                self.get_logger().info("Vehicle detected - initiating state transition")
                self.transition_to_yellow()
                
        elif self.current_state == TrafficLightState.YELLOW:
            # Wait for road to clear
            if not self.vehicles_in_frame:
                if elapsed >= self.wait_time_clear:
                    self.transition_to_red()
            elif elapsed >= self.max_wait_time:
                self.get_logger().warn("Max wait time exceeded - forcing transition")
                self.transition_to_red()
                
        elif self.current_state == TrafficLightState.RED:
            # Wait for other light to turn green
            if self.peer_light_state == 2:  # Other light is green
                if elapsed >= self.wait_time_green:
                    self.transition_to_green()
                    
        elif self.current_state == TrafficLightState.WAITING_CLEAR:
            # Wait for road to clear
            if not self.vehicles_in_frame:
                if elapsed >= self.wait_time_clear:
                    self.transition_to_red()
            elif elapsed >= self.max_wait_time:
                self.get_logger().warn("Max wait time exceeded - forcing transition")
                self.transition_to_red()
    
    def transition_to_yellow(self):
        """Transition to yellow state"""
        self.get_logger().info("Transitioning to YELLOW")
        self.current_state = TrafficLightState.YELLOW
        self.state_start_time = self.get_clock().now()
        self.traffic_light_state = 1
        self.publish_light_state()
        self.broadcast_light_state()
    
    def transition_to_red(self):
        """Transition to red state"""
        self.get_logger().info("Transitioning to RED")
        self.current_state = TrafficLightState.RED
        self.state_start_time = self.get_clock().now()
        self.traffic_light_state = 0
        self.publish_light_state()
        self.broadcast_light_state()
    
    def transition_to_green(self):
        """Transition to green state"""
        self.get_logger().info("Transitioning to GREEN")
        self.current_state = TrafficLightState.GREEN
        self.state_start_time = self.get_clock().now()
        self.traffic_light_state = 2
        self.publish_light_state()
        self.broadcast_light_state()
    
    def publish_light_state(self):
        """Publish current light state using Int32 message"""
        msg = Int32()
        msg.data = self.traffic_light_state
        self.light_state_pub.publish(msg)
        
        # Log state
        state_names = {0: 'RED', 1: 'YELLOW', 2: 'GREEN'}
        self.get_logger().debug(f"Published light state: {state_names.get(self.traffic_light_state, 'UNKNOWN')}")
    
    def broadcast_light_state(self):
        """Broadcast light state to peer using JSON String message"""
        import json
        data = {
            'node_id': self.node_id,
            'light_state': self.traffic_light_state,
            'timestamp': self.get_clock().now().nanoseconds
        }
        
        msg = String()
        msg.data = json.dumps(data)
        self.peer_light_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TrafficLightLogic()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()