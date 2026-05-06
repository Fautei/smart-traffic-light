from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    # Declare launch arguments
    node_id_arg = DeclareLaunchArgument(
        'node_id',
        default_value='0',
        description='ID of this traffic light node (0 or 1)'
    )
    
    gstreamer_pipeline_arg = DeclareLaunchArgument(
        'gstreamer_pipeline',
        default_value='',
        description='GStreamer pipeline for camera input'
    )
    
    camera_info_url_arg = DeclareLaunchArgument(
        'camera_info_url',
        default_value='',
        description='Camera info URL (file://path/to/calibration.yaml)'
    )
    
    calibration_file_arg = DeclareLaunchArgument(
        'calibration_file',
        default_value='',
        description='Path to camera calibration YAML file'
    )
    
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='',
        description='Path to YOLO model file'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Confidence threshold for object detection'
    )
    
    wait_time_clear_arg = DeclareLaunchArgument(
        'wait_time_clear',
        default_value='5.0',
        description='Time to wait for vehicles to clear (seconds)'
    )
    
    wait_time_green_arg = DeclareLaunchArgument(
        'wait_time_green',
        default_value='3.0',
        description='Time to wait before switching to green (seconds)'
    )
    
    max_wait_time_arg = DeclareLaunchArgument(
        'max_wait_time',
        default_value='30.0',
        description='Max time to wait for road to clear (seconds)'
    )
    
    debug_draw_arg = DeclareLaunchArgument(
        'debug_draw',
        default_value='false',
        description='Enable debug visualization'
    )
    
    # Camera node
    camera_node = Node(
        package='video_io',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'gstreamer_pipeline': LaunchConfiguration('gstreamer_pipeline'),
            'camera_info_url': LaunchConfiguration('camera_info_url'),
            'calibration_file': LaunchConfiguration('calibration_file'),
            'frame_id': 'camera',
            'camera_name': 'traffic_light_camera',
        }],
        output='screen'
    )
    
    # Object detector node
    object_detector_node = Node(
        package='traaffic_light_core',
        executable='object_detector',
        name='object_detector',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'classes_to_detect': ['car', 'truck', 'bus'],
            'publish_detections': True,
            'draw_detections': False,
        }],
        output='screen',
        remappings=[
            ('/camera/image_raw', '/camera/image_raw'),
        ]
    )
    
    # Traffic light logic node
    traffic_light_logic_node = Node(
        package='traaffic_light_core',
        executable='traffic_light_logic',
        name='traffic_light_logic',
        parameters=[{
            'node_id': LaunchConfiguration('node_id'),
            'wait_time_clear': LaunchConfiguration('wait_time_clear'),
            'wait_time_green': LaunchConfiguration('wait_time_green'),
            'max_wait_time': LaunchConfiguration('max_wait_time'),
            'detection_topic': '/detections',
            'light_state_topic': '/traffic_light/state',
            'light_command_topic': '/traffic_light/command',
            'peer_light_topic': '/traffic_light/peer',
            'debug_draw': LaunchConfiguration('debug_draw'),
        }],
        output='screen'
    )
    
    # Create launch description
    return LaunchDescription([
        node_id_arg,
        gstreamer_pipeline_arg,
        camera_info_url_arg,
        calibration_file_arg,
        model_path_arg,
        confidence_threshold_arg,
        wait_time_clear_arg,
        wait_time_green_arg,
        max_wait_time_arg,
        debug_draw_arg,
        camera_node,
        object_detector_node,
        traffic_light_logic_node,
    ])