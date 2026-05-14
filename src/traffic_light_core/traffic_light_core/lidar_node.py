import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2


class LidarNode(Node):
    """
    Lidar Node
    Publishes empty lidar scan data for testing purposes.
    """

    def __init__(self):
        super().__init__('lidar_sensor')

        # Declare parameters
        self.declare_parameter('topic_name', '/lidar/scan')
        self.topic_name = self.get_parameter('topic_name').value

        self.publisher_ = self.create_publisher(PointCloud2, self.topic_name, 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz
        self.get_logger().info(f"Lidar Sensor initialized with topic {self.topic_name}")

    def timer_callback(self):
        msg = PointCloud2()
        msg.header.frame_id = 'lidar_link'
        msg.height = 1
        msg.width = 0
        msg.is_dense = True
        msg.point_step = 0
        msg.row_step = 0
        msg.data = []
        self.publisher_.publish(msg)
        self.get_logger().debug(f"Published empty lidar scan to {self.topic_name}")


def main():
    rclpy.init()
    node = LidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()