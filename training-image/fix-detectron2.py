import importlib.util
import sys
import os
import re


def find_detectron2_path():
    spec = importlib.util.find_spec("detectron2")
    if spec is not None:
        return os.path.dirname(spec.origin)
    return None


def fix_detectron2_imports(detectron2_dir):
    detectron2_file = os.path.join(detectron2_dir, "data/transforms/transform.py")
    if not os.path.exists(detectron2_file):
        print(f"Error: {detectron2_file} not found.")
        return

    with open(detectron2_file, "r") as file:
        content = file.read()

    # Replace the import statements
    modified_content = re.sub(r"Image.LINEAR", "Image.BILINEAR", content)

    if modified_content != content:
        with open(detectron2_file, "w") as file:
            file.write(modified_content)
        print(f"Successfully updated {detectron2_file}")
    else:
        print(f"No changes were necessary in {detectron2_file}")


def main():
    detectron2_path = find_detectron2_path()
    if detectron2_path:
        print(f"detectron2 path: {detectron2_path}")
        fix_detectron2_imports(detectron2_path)
    else:
        print("Unable to find detectron2 path.")


if __name__ == "__main__":
    main()
