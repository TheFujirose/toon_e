from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'toon_e'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch files and their parameter files are looked up through
        # get_package_share_directory('toon_e'), so they must be installed.
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        # zed_launch.py passes this path to the ZED SDK as
        # object_detection.custom_onnx_file.
        (os.path.join('share', package_name, 'model'), glob('toon_e/model/*.onnx')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='carson',
    maintainer_email='50027005+TheFujirose@users.noreply.github.com',
    description='Loon-E ASV bringup: ZED X localization, Nav2 and the hardware node.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'toon_e = toon_e.toon_e:main'
        ],
    },
)
