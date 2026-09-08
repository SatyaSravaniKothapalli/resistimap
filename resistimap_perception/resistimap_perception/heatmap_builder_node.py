#!/usr/bin/env python3
"""
heatmap_builder_node
----------------------
Subscribes to RiskClassification messages and maintains a live grid of
results, printing an updated text heatmap to the terminal after each cell.

Uses simple color-coded terminal output (ANSI codes) so risk levels are
visually distinct without needing a GUI library -- reliable for a live
demo on any machine/terminal.
"""

import rclpy
from rclpy.node import Node

from resistimap_msgs.msg import RiskClassification

# ANSI color codes per risk label
COLORS = {
    "very_high": "\033[41m",   # red background
    "high": "\033[43m",        # yellow background
    "low_moderate": "\033[46m",  # cyan background
    "low": "\033[42m",         # green background
}
RESET = "\033[0m"

SHORT = {
    "very_high": "VH",
    "high": "HI",
    "low_moderate": "LM",
    "low": "LO",
}


class HeatmapBuilderNode(Node):
    def __init__(self):
        super().__init__('heatmap_builder_node')
        self.grid = {}  # (x, y) -> label
        self.max_x = 0
        self.max_y = 0

        self.subscription = self.create_subscription(
            RiskClassification, 'risk_classification', self.on_classification, 10
        )
        self.get_logger().info('heatmap_builder_node started, waiting for classifications...')

    def on_classification(self, msg):
        self.grid[(msg.grid_x, msg.grid_y)] = msg.label
        self.max_x = max(self.max_x, msg.grid_x)
        self.max_y = max(self.max_y, msg.grid_y)
        self.print_heatmap()

    def print_heatmap(self):
        print("\n--- ResistiMap Live Heatmap ---")
        for x in range(self.max_x + 1):
            row = ""
            for y in range(self.max_y + 1):
                label = self.grid.get((x, y))
                if label is None:
                    row += " .. "
                else:
                    color = COLORS.get(label, "")
                    row += f" {color}{SHORT.get(label, '??')}{RESET} "
            print(row)
        print("-------------------------------\n")


def main(args=None):
    rclpy.init(args=args)
    node = HeatmapBuilderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
