import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'hospital_robot'
    pkg_share = get_package_share_directory(pkg_name)

    # Calea către fișierul URDF
    urdf_path = os.path.join(pkg_share, 'urdf', 'ansamblu_final.urdf')

    # 1. Setăm calea pentru ca Gazebo să găsească mesh-urile (stl)
    install_dir = os.path.join(pkg_share, '..')
    set_gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=install_dir
    )

    # 2. Citim conținutul URDF în memorie
    with open(urdf_path, 'r') as infp:
        robot_description_content = infp.read()

    # 3. Pornește Gazebo încărcând harta primită de la echipă
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    world_path = os.path.join(pkg_share, 'worlds', 'l_open_track_world2.sdf')

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'{world_path} -r --render-engine ogre'}.items(),
    )

    # 4. Publică starea robotului
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content, 'use_sim_time': True}]
    )

    # 5. Spawnează robotul în Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', urdf_path,
            '-name', 'hospital_robot',
            '-allow_renaming', 'true',
            '-z', '0.02',
            '-R', '0.0',
            '-P', '0.0',
            '-Y', '0.0'
        ],
        output='screen'
    )

    # 6. Bridge ROS2 <-> Gazebo (fara Image, nu mai avem nevoie de camere)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/ray_sensors@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
        ],
        output='screen'
    )

    # 7. Senzor de linie "ground truth" - calculeaza matematic daca robotul
    #    e pe linie, pe baza de /odom + geometria liniei din world file.
    #    Inlocuieste complet abordarea cu camere (randarea nu functiona
    #    pe aceasta masina - randare software fara accelerare GPU).
    line_sensor_ground_truth_node = Node(
        package='hospital_robot',
        executable='line_sensor_ground_truth.py',
        output='screen'
    )

    # 8. Nodul de Urmărire a Liniei (neschimbat)
    line_follower_node = Node(
        package='hospital_robot',
        executable='line_follower_node.py',
        output='screen'
    )

    return LaunchDescription([
        set_gazebo_resource_path,
        gazebo_launch,
        robot_state_publisher_node,
        spawn_entity,
        bridge,
        line_sensor_ground_truth_node,
        line_follower_node
    ])