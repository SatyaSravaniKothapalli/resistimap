#!/usr/bin/env python3
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_msgs.msg import String, Bool
from resistimap_msgs.msg import Resistivity
from resistimap_msgs.action import ScanGrid


class GridCoverageActionServer(Node):
    def __init__(self):
        super().__init__('grid_coverage_action_server')
        self.cb_group = ReentrantCallbackGroup()

        self._action_server = ActionServer(
            self,
            ScanGrid,
            'scan_grid',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.cb_group,
        )

        self.goto_pub = self.create_publisher(String, 'motor/goto_cell', 10, callback_group=self.cb_group)
        self._arrived_event = threading.Event()
        self.create_subscription(String, 'motor/arrived', self._on_arrived, 10, callback_group=self.cb_group)

        self.probe_cmd_pub = self.create_publisher(String, 'probe/command', 10, callback_group=self.cb_group)
        self._probe_event = threading.Event()
        self.create_subscription(Bool, 'probe/lowered', self._on_probe_status, 10, callback_group=self.cb_group)

        self._latest_rho = None
        self._rho_event = threading.Event()
        self.create_subscription(Resistivity, 'resistivity', self._on_resistivity, 10, callback_group=self.cb_group)

        self.get_logger().info('grid_coverage_action_server ready.')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'Received scan goal: {goal_request.grid_rows}x{goal_request.grid_cols}')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel request received.')
        return CancelResponse.ACCEPT

    def _on_arrived(self, msg):
        self._arrived_event.set()

    def _on_probe_status(self, msg):
        self._probe_event.set()

    def _on_resistivity(self, msg):
        self._latest_rho = msg
        self._rho_event.set()

    def drive_to_cell(self, x, y):
        self._arrived_event.clear()
        self.goto_pub.publish(String(data=f'{x},{y}'))
        self._arrived_event.wait(timeout=5.0)

    def set_probes(self, command):
        self._probe_event.clear()
        self.probe_cmd_pub.publish(String(data=command))
        self._probe_event.wait(timeout=5.0)

    def read_resistivity(self):
        self._latest_rho = None
        self._rho_event.clear()
        self._rho_event.wait(timeout=5.0)
        return self._latest_rho

    def execute_callback(self, goal_handle):
        rows = goal_handle.request.grid_rows
        cols = goal_handle.request.grid_cols
        total_cells = rows * cols
        completed = 0
        feedback_msg = ScanGrid.Feedback()
        for row in range(rows):
            col_range = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
            for col in col_range:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result = ScanGrid.Result()
                    result.success = False
                    result.message = f'Scan canceled after {completed}/{total_cells} cells.'
                    return result
                self.drive_to_cell(row, col)
                self.set_probes('lower')
                rho_msg = self.read_resistivity()
                self.set_probes('raise')
                completed += 1
                feedback_msg.cells_completed = completed
                feedback_msg.cells_total = total_cells
                feedback_msg.current_x = row
                feedback_msg.current_y = col
                feedback_msg.last_rho = rho_msg.rho if rho_msg else 0.0
                feedback_msg.last_label = ''
                goal_handle.publish_feedback(feedback_msg)
                self.get_logger().info(f'Cell ({row},{col}) done: rho={feedback_msg.last_rho:.2f} [{completed}/{total_cells}]')
        goal_handle.succeed()
        result = ScanGrid.Result()
        result.success = True
        result.message = f'Scan complete: {completed}/{total_cells} cells measured.'
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GridCoverageActionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
