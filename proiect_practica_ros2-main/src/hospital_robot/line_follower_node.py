#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist

LINE_DETECTED = True
LINEAR_SPEED = 0.15       # m/s
SENSOR_TIMEOUT_SEC = 0.5


class LineFollower(Node):
    def __init__(self):
        super().__init__('line_follower')

        self.front_left = False
        self.front_center = False
        self.front_right = False
        self.motion_enabled = True  # pornit implicit; poti opri robotul oricand publicand False pe /motion/enable

        self.front_left_last_msg_time = None
        self.front_center_last_msg_time = None
        self.front_right_last_msg_time = None

        self.create_subscription(Bool, 'line_sensor/front_left', self._on_front_left, 10)
        self.create_subscription(Bool, 'line_sensor/front_center', self._on_front_center, 10)
        self.create_subscription(Bool, 'line_sensor/front_right', self._on_front_right, 10)
        self.create_subscription(Bool, '/motion/enable', self._on_motion_enable, 10)

        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.line_detected_pub = self.create_publisher(Bool, '/line_follower/line_detected', 10)

        self.timer = self.create_timer(0.05, self._control_loop)
        self.get_logger().info('Line Follower Node pornit cu logica inversata ceruta!')

    def _on_front_left(self, msg: Bool):
        self.front_left = msg.data
        self.front_left_last_msg_time = self.get_clock().now()

    def _on_front_center(self, msg: Bool):
        self.front_center = msg.data
        self.front_center_last_msg_time = self.get_clock().now()

    def _on_front_right(self, msg: Bool):
        self.front_right = msg.data
        self.front_right_last_msg_time = self.get_clock().now()

    def _on_motion_enable(self, msg: Bool):
        self.motion_enabled = msg.data

    def _is_stale(self, last_msg_time) -> bool:
        if last_msg_time is None:
            return True
        elapsed_sec = (self.get_clock().now() - last_msg_time).nanoseconds / 1e9
        return elapsed_sec > SENSOR_TIMEOUT_SEC

    def _control_loop(self):
        fl_on = (not self._is_stale(self.front_left_last_msg_time)) and (self.front_left == LINE_DETECTED)
        fc_on = (not self._is_stale(self.front_center_last_msg_time)) and (self.front_center == LINE_DETECTED)
        fr_on = (not self._is_stale(self.front_right_last_msg_time)) and (self.front_right == LINE_DETECTED)

        front_visible = fl_on or fc_on or fr_on
        line_visible = front_visible

        line_msg = Bool()
        line_msg.data = line_visible
        self.line_detected_pub.publish(line_msg)

        if not self.motion_enabled:
            self.cmd_pub.publish(Twist())
            return

        cmd = Twist()

        if fc_on and fl_on and fr_on:
            # Toti trei senzorii vad linia (linie lata / intersectie) -> inainte (logica inversata)
            cmd.linear.x = 0.0
            cmd.angular.z = -LINEAR_SPEED

        elif fl_on and fr_on and not fc_on:
            # Stanga + dreapta, fara centru -> tratam ca aliniat, inainte (logica inversata)
            cmd.linear.x = 0.0
            cmd.angular.z = -LINEAR_SPEED

        elif fc_on and not fl_on and not fr_on:
            # Doar centrul vede linia -> mers înainte cu logica inversată cerută
            cmd.linear.x = 0.0
            cmd.angular.z = -LINEAR_SPEED

        elif fc_on and fl_on and not fr_on:
            # Centru + stanga
            cmd.linear.x = LINEAR_SPEED * 0.5
            cmd.angular.z = -LINEAR_SPEED * 0.8

        elif fc_on and fr_on and not fl_on:
            # Centru + dreapta
            cmd.linear.x = LINEAR_SPEED * 0.5
            cmd.angular.z = -LINEAR_SPEED * 0.8

        elif fl_on and not fc_on and not fr_on:
            # Doar stanga
            cmd.linear.x = -LINEAR_SPEED * 0.2
            cmd.angular.z = -LINEAR_SPEED * 1.2

        elif fr_on and not fc_on and not fl_on:
            # Doar dreapta
            cmd.linear.x = LINEAR_SPEED * 0.2
            cmd.angular.z = -LINEAR_SPEED * 1.2

        else:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.get_logger().warn('Linie pierduta complet!')

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = LineFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()