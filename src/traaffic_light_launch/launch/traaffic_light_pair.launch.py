"""
Launch file for running a pair of traffic lights on a single-lane road during repair work.
This launch file starts two traffic light nodes that communicate with each other.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare launch arguments
    node_0_gstreamer_pipeline_arg = DeclareLaunchArgument(
        'node_0_gstreamer_pipeline',
        default_value='',
        description='GStreamer pipeline for camera 0 (left side)'
    )
    
    node_1_gstreamer_pipeline_arg = DeclareLaunchArgument(
        'node_1_gstreamer_pipeline',
        default_value='',
        description='GStreamer pipeline for camera 1 (right side)'
    )
    
    node_0_calibration_file_arg = DeclareLaunchArgument(
        'node_0_calibration_file',
        default_value='',
        description='Path to camera 0 calibration YAML file'
    )
    
    node_1_calibration_file_arg = DeclareLaunchArgument(
        'node_1_calibration_file',
        default_value='',
        description='Path to camera 1 calibration YAML file'
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
    
    # Traffic light 0 (node_id=0) - left side
    traffic_light_0_group = GroupAction([
        Node(
            package='video_io',
            executable='camera_node',
            name='camera_node_0',
            parameters=[{
                'gstreamer_pipeline': LaunchConfiguration('node_0_gstreamer_pipeline'),
                'calibration_file': LaunchConfiguration('node_0_calibration_file'),
                'frame_id': 'camera_0',
                'camera_name': 'traffic_light_camera_0',
            }],
            output='screen'
        ),
        
        Node(
            package='traaffic_light_core',
            executable='object_detector',
            name='object_detector_0',
            parameters=[{
                'model_path': LaunchConfiguration('model_path'),
                'confidence_threshold': LaunchConfiguration('confidence_threshold'),
                'classes_to_detect': ['car', 'truck', 'bus'],
                'publish_detections': True,
                'draw_detections': False,
            }],
            output='screen',
            remappings=[
                ('/camera/image_raw', '/camera_0/image_raw'),
            ]
        ),
        
        Node(
            package='traaffic_light_core',
            executable='traffic_light_logic',
            name='traffic_light_logic_0',
            parameters=[{
                'node_id': 0,
                'wait_time_clear': LaunchConfiguration('wait_time_clear'),
                'wait_time_green': LaunchConfiguration('wait_time_green'),
                'max_wait_time': LaunchConfiguration('max_wait_time'),
                'detection_topic': '/detections_0',
                'light_state_topic': '/traffic_light/state_0',
                'light_command_topic': '/traffic_light/command_0',
                'peer_light_topic': '/traffic_light/peer',
                'debug_draw': LaunchConfiguration('debug_draw'),
            }],
            output='screen'
        ),
    ])
    
    # Traffic light 1 (node_id=1) - right side
    traffic_light_1_group = GroupAction([
        Node(
            package='video_io',
            executable='camera_node',
            name='camera_node_1',
            parameters=[{
                'gstreamer_pipeline': LaunchConfiguration('node_1_gstreamer_pipeline'),
                'calibration_file': LaunchConfiguration('node_1_calibration_file'),
                'frame_id': 'camera_1',
                'camera_name': 'traffic_light_camera_1',
            }],
            output='screen'
        ),
        
        Node(
            package='traaffic_light_core',
            executable='object_detector',
            name='object_detector_1',
            parameters=[{
                'model_path': LaunchConfiguration('model_path'),
                'confidence_threshold': LaunchConfiguration('confidence_threshold'),
                'classes_to_detect': ['car', 'truck', 'bus'],
                'publish_detections': True,
                'draw_detections': False,
            }],
            output='screen',
            remappings=[
                ('/camera/image_raw', '/camera_1/image_raw'),
            ]
        ),
        
        Node(
            package='traaffic_light_core',
            executable='traffic_light_logic',
            name='traffic_light_logic_1',
            parameters=[{
                'node_id': 1,
                'wait_time_clear': LaunchConfiguration('wait_time_clear'),
                'wait_time_green': LaunchConfiguration('wait_time_green'),
                'max_wait_time': LaunchConfiguration('max_wait_time'),
                'detection_topic': '/detections_1',
                'light_state_topic': '/traffic_light/state_1',
                'light_command_topic': '/traffic_light/command_1',
                'peer_light_topic': '/traffic_light/peer',
                'debug_draw': LaunchConfiguration('debug_draw'),
            }],
            output='screen'
        ),
    ])
    
    # Create launch description
    return LaunchDescription([
        node_0_gstreamer_pipeline_arg,
        node_1_gstreamer_pipeline_arg,
        node_0_calibration_file_arg,
        node_1_calibration_file_arg,
        model_path_arg,
        confidence_threshold_arg,
        wait_time_clear_arg,
        wait_time_green_arg,
        max_wait_time_arg,
        debug_draw_arg,
        traffic_light_0_group,
        traffic_light_1_group,
    ])