#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist


INPUT_CMD_VEL_TOPIC = 'cmd_vel'                                     
MOTION_ENABLE_TOPIC = '/motion/enable'                              
OUTPUT_CMD_VEL_TOPIC = '/diff_drive_controller/cmd_vel'   

CMD_VEL_TIMEOUT_SEC = 0.5
MOTION_ENABLE_TIMEOUT_SEC = 1.0  


LOOP_RATE_HZ = 20.0


class MotorSafetyWatchdog(Node):

    def __init__(self):
        super().__init__('motor_safety_watchdog')

        self.last_cmd_vel = Twist()
        self.last_cmd_vel_time = None

        self.motion_enabled = False
        self.last_motion_enable_time = None

        self.create_subscription(Twist, INPUT_CMD_VEL_TOPIC, self._on_cmd_vel, 10)
        self.create_subscription(Bool, MOTION_ENABLE_TOPIC, self._on_motion_enable, 10)

        self.cmd_vel_pub = self.create_publisher(Twist, OUTPUT_CMD_VEL_TOPIC, 10)

        self.timer = self.create_timer(1.0 / LOOP_RATE_HZ, self._control_loop)

        self.get_logger().info(
            f'Motor Safety Watchdog pornit. '
            f'{INPUT_CMD_VEL_TOPIC} -> {OUTPUT_CMD_VEL_TOPIC} (gated de {MOTION_ENABLE_TOPIC})'
        )



    def _on_cmd_vel(self, msg: Twist):
        self.last_cmd_vel = msg
        self.last_cmd_vel_time = self.get_clock().now()

    def _on_motion_enable(self, msg: Bool):
        self.motion_enabled = msg.data
        self.last_motion_enable_time = self.get_clock().now()



    def _is_stale(self, last_time, timeout_sec: float) -> bool:
        if last_time is None:
            return True
        elapsed_sec = (self.get_clock().now() - last_time).nanoseconds / 1e9
        return elapsed_sec > timeout_sec

    def _control_loop(self):
        motion_enable_stale = self._is_stale(self.last_motion_enable_time, MOTION_ENABLE_TIMEOUT_SEC)
        cmd_vel_stale = self._is_stale(self.last_cmd_vel_time, CMD_VEL_TIMEOUT_SEC)


        should_stop = motion_enable_stale or (not self.motion_enabled) or cmd_vel_stale

        if should_stop:
            self.cmd_vel_pub.publish(Twist())  
            return

        self.cmd_vel_pub.publish(self.last_cmd_vel)


def main(args=None):
    rclpy.init(args=args)
    node = MotorSafetyWatchdog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_vel_pub.publish(Twist())  
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
