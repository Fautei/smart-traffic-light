import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class IRNode(Node):
    """
    IR Sensor Node
    Publishes empty IR sensor data for testing purposes.
    """

    def __init__(self):
        super().__init__('ir_sensor')

        # Declare parameters
        self.declare_parameter('topic_name', '/ir_sensor/data')
        self.topic_name = self.get_parameter('topic_name').value

        self.publisher_ = self.create_publisher(Float32, self.topic_name, 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz
        self.get_logger().info(f"IR Sensor initialized with topic {self.topic_name}")

    def timer_callback(self):
        msg = Float32()
        msg.data = 0.0
        self.publisher_.publish(msg)
        self.get_logger().debug(f"Published empty IR sensor data to {self.topic_name}")


def main():
    rclpy.init()
    node = IRNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()