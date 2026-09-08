from setuptools import find_packages, setup

package_name = 'resistimap_perception'

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
            'risk_classifier_node = resistimap_perception.risk_classifier_node:main',
            'heatmap_builder_node = resistimap_perception.heatmap_builder_node:main',
        ],
    },
)
