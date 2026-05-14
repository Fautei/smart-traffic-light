from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    
    # Camera node
    camera_node_1 = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node_1',
        parameters=[{
            'rtsp_url': "assets/TL1.MOV",#LaunchConfiguration('gstreamer_pipeline'),
            'calibration_file': "/home/maxim/Desktop/calibration_1.yml", #LaunchConfiguration('calibration_file'),
            'frame_id': 'camera',
            'camera_name': 'traffic_light_camera_1',
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_1/image_raw'),
            ('/camera/camera_info', '/camera_1/camera_info'),
        ]
    )
    
    # Object detector node
    object_detector_node_1 = Node(
        package='traffic_light_core',
        executable='object_detector',
        name='object_detector_1',
        parameters=[{
            'model_path': "assets/models/yolo26s.pt", #LaunchConfiguration('model_config'),
            'confidence_threshold': 0.35, #LaunchConfiguration('confidence_threshold'),
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_1/image_raw'),
            ('/camera/image_detections', '/camera_1/image_detections'),
            ('/detections', '/detections_1'),
        ]
    )

    # Traffic counter node
    traffic_counter_node_1 = Node(
        package='traffic_light_core',
        executable='traffic_counter',
        name='traffic_counter_1',
        parameters=[{
            'detection_topic': '/detections_1',
            'polygon_topic': '/polygon_config/polygon_1',
            'count_topic': '/traffic_counter_1/counts',
            'config_path': '/tmp/polygon_config_1.json',
            'lidar_topic': '/lidar_1/scan',
            'ir_topic': '/ir_sensor_1/data',
            'ultrasonic_topic': '/ultrasonic_sensor_1/data',
        }],
        output='screen',
        remappings=[
            ('/detections_1', '/detections_1'),
        ]
    )

    # Camera node
    camera_node_2 = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node_2',
        parameters=[{
            'rtsp_url': "assets/TL2.MOV",#LaunchConfiguration('gstreamer_pipeline'),
            'calibration_file': "/home/maxim/Desktop/calibration_1.yml", #LaunchConfiguration('calibration_file'),
            'frame_id': 'camera',
            'camera_name': 'traffic_light_camera',
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_2/image_raw'),
            ('/camera/camera_info', '/camera_2/camera_info'),
        ]
    )
    
    # Object detector node
    object_detector_node_2 = Node(
        package='traffic_light_core',
        executable='object_detector',
        name='object_detector_2',
        parameters=[{
            'model_path': "assets/models/yolo26s.pt", #LaunchConfiguration('model_config'),
            'confidence_threshold': 0.35, #LaunchConfiguration('confidence_threshold'),
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_2/image_raw'),
            ('/camera/image_detections', '/camera_2/image_detections'),
            ('/detections', '/detections_2'),
        ]
    )

    # Traffic counter node
    traffic_counter_node_2 = Node(
        package='traffic_light_core',
        executable='traffic_counter',
        name='traffic_counter_2',
        parameters=[{
            'detection_topic': '/detections_2',
            'polygon_topic': '/polygon_config/polygon_2',
            'count_topic': '/traffic_counter_2/counts',
            'config_path': '/tmp/polygon_config_2.json',
            'lidar_topic': '/lidar_2/scan',
            'ir_topic': '/ir_sensor_2/data',
            'ultrasonic_topic': '/ultrasonic_sensor_2/data',
        }],
         output='screen',
         remappings=[
             ('/detections_1', '/detections_2'),
         ]
     )

    # Lidar sensor nodes for traffic_counter_1
    lidar_sensor_node_1 = Node(
        package='traffic_light_core',
        executable='lidar_sensor',
        name='lidar_sensor_1',
        output='screen',
        parameters=[{
            'topic_name': '/lidar_1/scan',
        }]
    )

    ir_sensor_node_1 = Node(
        package='traffic_light_core',
        executable='ir_sensor',
        name='ir_sensor_1',
        output='screen',
        parameters=[{
            'topic_name': '/ir_sensor_1/data',
        }]
    )

    ultrasonic_sensor_node_1 = Node(
        package='traffic_light_core',
        executable='ultrasonic_sensor',
        name='ultrasonic_sensor_1',
        output='screen',
        parameters=[{
            'topic_name': '/ultrasonic_sensor_1/data',
        }]
    )

    # Lidar sensor nodes for traffic_counter_2
    lidar_sensor_node_2 = Node(
        package='traffic_light_core',
        executable='lidar_sensor',
        name='lidar_sensor_2',
        output='screen',
        parameters=[{
            'topic_name': '/lidar_2/scan',
        }]
    )

    ir_sensor_node_2 = Node(
        package='traffic_light_core',
        executable='ir_sensor',
        name='ir_sensor_2',
        output='screen',
        parameters=[{
            'topic_name': '/ir_sensor_2/data',
        }]
    )

    ultrasonic_sensor_node_2 = Node(
        package='traffic_light_core',
        executable='ultrasonic_sensor',
        name='ultrasonic_sensor_2',
        output='screen',
        parameters=[{
            'topic_name': '/ultrasonic_sensor_2/data',
        }]
    )

    # Traffic light logic node
    traffic_light_logic_node = Node(
        package='traffic_light_core',
        executable='traffic_light_logic',
        name='traffic_light_logic',
        output='screen',
        remappings=[
            ('/detections', '/detections_1'),
        ]
    )
    
    # Traffic light indicator node (GUI)
    traffic_light_indicator_node_1 = Node(
        package='traffic_light_core',
        executable='traffic_light_indicator',
        name='traffic_light_indicator_1',
        output='screen',
        parameters=[{
            'tl_topic': '/traffic_light_1/state'
        }],
    )

    # Traffic light indicator node (GUI)
    traffic_light_indicator_node_2 = Node(
        package='traffic_light_core',
        executable='traffic_light_indicator',
        name='traffic_light_indicator_2',
        output='screen',
        parameters=[{
            'tl_topic': '/traffic_light_2/state'
        }],
    )

    # Polygon configurator node
    polygon_configurator_node_1 = Node(
        package='traffic_light_core',
        executable='polygon_configurator',
        name='polygon_configurator_1',
        output='screen',
        parameters=[{
            'image_topic': '/camera_1/image_raw',
            'polygon_topic': '/polygon_config/polygon_1'
        }],
    )

    polygon_configurator_node_2 = Node(
        package='traffic_light_core',
        executable='polygon_configurator',
        name='polygon_configurator_2',
        output='screen',
        parameters=[{
            'image_topic': '/camera_2/image_raw',
            'polygon_topic': '/polygon_config/polygon_2'
        }],
    )

    # Status visualizer node
    status_visualizer_node_1 = Node(
        package='traffic_light_core',
        executable='status_visualizer',
        name='status_visualizer_1',
        parameters=[{
            'detection_topic': '/detections_1',
            'count_topic': '/traffic_counter_1/counts',
            'image_topic': '/camera_1/image_raw',
            'polygon_topic': '/polygon_config/polygon_1'
        }],
        output='screen',
        remappings=[
            ('/detections_1', '/detections_1'),
        ]
    )

    status_visualizer_node_2 = Node(
        package='traffic_light_core',
        executable='status_visualizer',
        name='status_visualizer_2',
        parameters=[{
            'detection_topic': '/detections_2',
            'count_topic': '/traffic_counter_2/counts',
            'image_topic': '/camera_2/image_raw',
            'polygon_topic': '/polygon_config/polygon_2'
        }],
        output='screen',
        remappings=[
            ('/detections_1', '/detections_2'),
        ]
    )

    # Create launch description
    return LaunchDescription([
        camera_node_1,
        object_detector_node_1,
        traffic_counter_node_1,
        camera_node_2,
        object_detector_node_2,
        traffic_counter_node_2,

        polygon_configurator_node_1,
        status_visualizer_node_1,

        polygon_configurator_node_2,
        status_visualizer_node_2,

        traffic_light_logic_node,
        traffic_light_indicator_node_1,
        traffic_light_indicator_node_2,

        lidar_sensor_node_1,
        ir_sensor_node_1,
        ultrasonic_sensor_node_1,
        lidar_sensor_node_2,
        ir_sensor_node_2,
        ultrasonic_sensor_node_2,
    ])
