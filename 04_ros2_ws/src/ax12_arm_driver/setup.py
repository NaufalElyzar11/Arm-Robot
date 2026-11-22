from setuptools import setup

package_name = 'ax12_arm_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TODO',
    maintainer_email='you@example.com',
    description='ROS 2 driver for the ax12_bridge Arduino firmware',
    license='MIT',
    entry_points={
        'console_scripts': [
            'ax12_driver = ax12_arm_driver.driver_node:main',
            'demo_sequence = ax12_arm_driver.demo_sequence:main',
        ],
    },
)
