from setuptools import setup, find_packages

setup(
    name="patio_gazebo_tool",
    version="1.0.0",
    description="A drag-and-drop patio/gazebo layout visualization tool built with Tkinter.",
    author="Shreyansh Shethia",
    packages=find_packages(),
    install_requires=[
        "tk"
    ],
    entry_points={
        "console_scripts": [
            "patio-gazebo=patio_gazebo.app:main"
        ]
    },
    include_package_data=True,
)
