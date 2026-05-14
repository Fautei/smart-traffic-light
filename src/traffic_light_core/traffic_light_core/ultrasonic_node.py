import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class UltrasonicNode(Node):
    """
    Ultrasonic Sensor Node
    Publishes empty ultrasonic sensor data for testing purposes.
    """

    def __init__(self):
        super().__init__('ultrasonic_sensor')

        # Declare parameters
        self.declare_parameter('topic_name', '/ultrasonic_sensor/data')
        self.topic_name = self.get_parameter('topic_name').value

        self.publisher_ = self.create_publisher(Float32, self.topic_name, 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz
        self.get_logger().info(f"Ultrasonic Sensor initialized with topic {self.topic_name}")

    def timer_callback(self):
        msg = Float32()
        msg.data = 0.0
        self.publisher_.publish(msg)
        self.get_logger().debug(f"Published empty ultrasonic sensor data to {self.topic_name}")


def main():
    rclpy.init()
    node = UltrasonicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()