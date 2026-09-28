#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

class LineSensorCameraBridge(Node):
    def __init__(self):
        super().__init__('line_sensor_camera_bridge')
        names = ['front_left', 'front_center', 'front_right']
        self.pubs = {}
        for n in names:
            # Publică în continuare Bool către sistemul tău de mașină de stări
            self.pubs[n] = self.create_publisher(Bool, f'line_sensor/{n}', 10)
            # Ascultă distanțele laser în loc de imagini
            self.create_subscription(
                LaserScan, f'line_sensor/{n}/scan',
                lambda msg, n=n: self._on_scan(msg, n), 10)
        
        self.get_logger().info('Line Sensor (Ray Mode) pornit și ascultă distanțele spre podea.')

    def _on_scan(self, msg: LaserScan, name: str):
        # Preluăm singurul punct măsurat
        dist = msg.ranges[0] if msg.ranges else 999.0
        
        # Logăm distanța pentru calibrare. 
        # Când e pe podea va fi o valoare (ex: 0.070), când e pe linie va fi mai mică (ex: 0.065)
        self.get_logger().info(f'Senzor {name} - Distanta: {dist:.4f} m')
        
        out = Bool()
        # SETEAZĂ AICI PRAGUL DUPĂ CE VEZI VALORILE ÎN TERMINAL!
        # Dacă podeaua e la 0.07m și linia e la 0.06m, un prag de 0.065 e perfect.
        out.data = dist < 0.065 
        
        self.pubs[name].publish(out)

def main(args=None):
    rclpy.init(args=args)
    node = LineSensorCameraBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()