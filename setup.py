from setuptools import setup, find_packages

setup(
    name='lp-labelstudio',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'Click',
        'layoutparser[ocr]',
        'torch',
        'torchvision',
        'Pillow',
        'detectron2',
        'opencv-python',
        'numpy',
        'paddlepaddle',
        'paddleocr>=2.0.1',
        'jdeskew',
        'PyMuPDF',
        'Flask',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'lp-labelstudio=lp_labelstudio.cli:cli',
        ],
    },
)
