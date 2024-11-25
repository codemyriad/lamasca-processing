from setuptools import setup, find_packages

setup(
    name="lp-labelstudio",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "Click",
        "layoutparser[ocr]",
        "torch",
        "torchvision",
        "pillow~=10.3",
        "detectron2",
        "opencv-python",
        "numpy",
        "paddlepaddle",
        "paddleocr>=2.0.1",
        "jdeskew",
        "PyMuPDF",
        "Flask",
        "requests",
        "requests-file",
        "gunicorn==22.0.0",
        "label-studio-ml @ git+https://github.com/HumanSignal/label-studio-ml-backend.git",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "lp-labelstudio=lp_labelstudio.cli:cli",
        ],
    },
)
