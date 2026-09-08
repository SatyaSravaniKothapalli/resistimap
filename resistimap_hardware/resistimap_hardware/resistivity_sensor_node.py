#!/usr/bin/env python3
import math
import random

import rclpy
from rclpy.node import Node

from resistimap_msgs.msg import Resistivity

SIMULATE = True
PROBE_SPACING_A = 0.05
KNOWN_CURRENT_I = 0.001
PUBLISH_HZ = 1.0


class ResistivitySensorNode(Node):
    def __init__(self):
        super().__init__('resistivity_sensor_node')
        self.publisher_ = self.create_publisher(Resistivity, 'resistivity', 10)
        self.timer = self.create_timer(1.0 / PUBLISH_HZ, self.publish_reading)
        self.grid_x = 0
        self.grid_y = 0
        self.get_logger().info('resistivity_sensor_node started in SIMULATE mode (no real hardware read).')

    def read_voltage(self):
        return random.uniform(0.05, 0.9)

    def compute_resistivity(self, voltage):
        resistance = voltage / KNOWN_CURRENT_I
        rho = 2 * math.pi * PROBE_SPACING_A * resistance
        return rho

    def publish_reading(self):
        voltage = self.read_voltage()
        rho = self.compute_resistivity(voltage)
        msg = Resistivity()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'probe_array'
        msg.rho = rho
        msg.grid_x = self.grid_x
        msg.grid_y = self.grid_y
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published rho={rho:.2f} ohm-m at cell ({self.grid_x}, {self.grid_y})')


def main(args=None):
    rclpy.init(args=args)
    node = ResistivitySensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()