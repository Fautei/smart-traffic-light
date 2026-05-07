from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    
    # Camera node
    camera_node_1 = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node_1',
        parameters=[{
            'rtsp_url': "rtsp://admin:daguza123@192.168.1.10",#LaunchConfiguration('gstreamer_pipeline'),
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
        package='traaffic_light_core',
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
    
    # Traffic light logic node
    traffic_light_logic_node_1 = Node(
        package='traaffic_light_core',
        executable='traffic_light_logic',
        name='traffic_light_logic_1',
        parameters=[{
            'detection_topic': '/detections',
        }],
        output='screen',
        remappings=[
            ('/detections', '/detections_1'),
        ]
    )

        # Camera node
    camera_node_2 = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node_2',
        parameters=[{
            'rtsp_url': "rtsp://admin:daguza123@192.168.1.10",#LaunchConfiguration('gstreamer_pipeline'),
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
        package='traaffic_light_core',
        executable='object_detector',
        name='object_detector_2',
        parameters=[{
            'model_path': "assets/models/yolo26s.pt", #LaunchConfiguration('model_config'),
            'confidence_threshold': 0.5, #LaunchConfiguration('confidence_threshold'),
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera_2/image_raw'),
            ('/camera/image_detections', '/camera_2/image_detections'),
            ('/detections', '/detections_2'),
        ]
    )
    
    # Traffic light logic node
    traffic_light_logic_node_2 = Node(
        package='traaffic_light_core',
        executable='traffic_light_logic',
        name='traffic_light_logic_2',
        parameters=[{
            'detection_topic': '/detections',
        }],
        output='screen',
        remappings=[
            ('/detections', '/detections_2'),
        ]
    )
    
    # Create launch description
    return LaunchDescription([
        camera_node_1,
        object_detector_node_1,
        traffic_light_logic_node_1,

        camera_node_2,
        object_detector_node_2,
        traffic_light_logic_node_2,
    ])