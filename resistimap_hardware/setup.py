from setuptools import find_packages, setup

package_name = 'resistimap_hardware'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='satya-sravani',
    maintainer_email='satyasravanikothapalli@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'resistivity_sensor_node = resistimap_hardware.resistivity_sensor_node:main',
            'motor_driver_node = resistimap_hardware.motor_driver_node:main',
            'probe_actuator_node = resistimap_hardware.probe_actuator_node:main',
            'grid_coverage_action_server = resistimap_hardware.grid_coverage_action_server:main',
        ],
    },
)
