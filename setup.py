from setuptools import setup, find_packages

setup(
    name='lp-labelstudio',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'Click',
        'layoutparser',
        'torch',
        'torchvision',
        'Pillow',
        'detectron2 @ git+https://github.com/facebookresearch/detectron2.git',
        'paddleocr==2.6.0.3',
        'paddlepaddle==2.6.1',
        'opencv-python',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'lp-labelstudio=lp_labelstudio.cli:cli',
        ],
    },
)
