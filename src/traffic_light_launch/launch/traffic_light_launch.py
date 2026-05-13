from launch import LaunchDescription
from launch_ros.actions import Node



def generate_launch_description():
    
    # Camera node
    camera_node_1 = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node_1',
        parameters=[{
            'rtsp_url': "assets/output.mp4",#LaunchConfiguration('gstreamer_pipeline'),
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
            'confidence_threshold': 0.5, #LaunchConfiguration('confidence_threshold'),
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_1/image_raw'),
            ('/camera/image_detections', '/camera_1/image_detections'),
            ('/detections', '/detections_1'),
        ]
    )
    
    # # Traffic light logic node
    # traffic_light_logic_node_1 = Node(
    #     package='traffic_light_core',
    #     executable='traffic_light_logic',
    #     name='traffic_light_logic_1',
    #     parameters=[{
    #         'detection_topic': '/detections',
    #     }],
    #     output='screen',
    #     remappings=[
    #         ('/detections', '/detections_1'),
    #     ]
    # )

    #     # Camera node
    # camera_node_2 = Node(
    #     package='video_io',
    #     executable='camera_node',
    #     name='camera_node_2',
    #     parameters=[{
    #         'rtsp_url': "rtsp://admin:daguza123@192.168.1.11",#LaunchConfiguration('gstreamer_pipeline'),
    #         'calibration_file': "/home/maxim/Desktop/calibration_1.yml", #LaunchConfiguration('calibration_file'),
    #         'frame_id': 'camera',
    #         'camera_name': 'traffic_light_camera',
    #     }],
    #     output='screen',
    #     remappings=[
    #         ('/camera/image_raw', '/camera_2/image_raw'),
    #         ('/camera/camera_info', '/camera_2/camera_info'),
    #     ]
    # )
    
    # # Object detector node
    # object_detector_node_2 = Node(
    #     package='traffic_light_core',
    #     executable='object_detector',
    #     name='object_detector_2',
    #     parameters=[{
    #         'model_path': "assets/models/yolo26s.pt", #LaunchConfiguration('model_config'),
    #         'confidence_threshold': 0.5, #LaunchConfiguration('confidence_threshold'),
    #     }],
    #     output='screen',
    #     remappings=[
    #         ('/camera/image_raw', '/camera_2/image_raw'),
    #         ('/camera/image_detections', '/camera_2/image_detections'),
    #         ('/detections', '/detections_2'),
    #     ]
    # )
    
    # # Traffic light logic node
    # traffic_light_logic_node_2 = Node(
    #     package='traffic_light_core',
    #     executable='traffic_light_logic',
    #     name='traffic_light_logic_2',
    #     parameters=[{
    #         'detection_topic': '/detections',
    #     }],
    #     output='screen',
    #     remappings=[
    #         ('/detections', '/detections_2'),
    #     ]
    # )
    
    # Polygon configurator node
    polygon_configurator_node = Node(
        package='traffic_light_core',
        executable='polygon_configurator',
        name='polygon_configurator',
        output='screen'
    )
    
    # Traffic counter node
    traffic_counter_node = Node(
        package='traffic_light_core',
        executable='traffic_counter',
        name='traffic_counter',
        parameters=[{
            'detection_topic': '/detections_1',
            'polygon_topic': '/polygon_config/polygon',
            'image_topic': '/camera_1/image_detections',
            'count_topic': '/traffic_counter/counts',
            'debug_topic': '/traffic_counter/debug',
        }],
        output='screen',
        remappings=[
            ('/detections_1', '/detections_1'),
        ]
    )
    
    # # Status visualizer node
    status_visualizer_node = Node(
        package='traffic_light_core',
        executable='status_visualizer',
        name='status_visualizer',
        parameters=[{
            'detection_topic': '/detections_1',
            'polygon_topic': '/polygon_config/polygon',
            'image_topic': '/camera_1/image_detections',
            'count_topic': '/traffic_counter/counts',
        }],
        output='screen',
        remappings=[
            ('/detections_1', '/detections_1'),
        ]
    )

    # Create launch description
    return LaunchDescription([
        camera_node_1,
        object_detector_node_1,
        # traffic_light_logic_node_1,
        polygon_configurator_node,
        traffic_counter_node,
        status_visualizer_node,

        # camera_node_2,
        # object_detector_node_2,
        # traffic_light_logic_node_2,
    ])