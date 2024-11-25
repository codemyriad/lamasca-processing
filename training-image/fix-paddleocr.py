import importlib.util
import sys
import os
import re


def find_paddleocr_path():
    try:
        spec = importlib.util.find_spec("paddleocr")
        if spec is not None:
            return os.path.dirname(spec.origin)
    except ImportError as e:
        # If ImportError occurs, try to extract the path from the error message
        error_msg = str(e)
        if "paddleocr" in error_msg and "No module named" in error_msg:
            # The path might be in the error message
            parts = error_msg.split("'")
            if len(parts) >= 2:
                return os.path.dirname(parts[1])

    return None


def fix_paddleocr_imports(paddleocr_dir):
    paddleocr_file = os.path.join(paddleocr_dir, "paddleocr.py")
    if not os.path.exists(paddleocr_file):
        print(f"Error: {paddleocr_file} not found.")
        return

    with open(paddleocr_file, "r") as file:
        content = file.read()

    # Replace the import statements
    modified_content = re.sub(
        r"from tools\.infer import", "from paddleocr.tools.infer import", content
    )

    if modified_content != content:
        with open(paddleocr_file, "w") as file:
            file.write(modified_content)
        print(f"Successfully updated {paddleocr_file}")
    else:
        print(f"No changes were necessary in {paddleocr_file}")


def main():
    paddleocr_path = find_paddleocr_path()
    if paddleocr_path:
        print(f"PaddleOCR path: {paddleocr_path}")
        fix_paddleocr_imports(paddleocr_path)
    else:
        print("Unable to find PaddleOCR path.")


if __name__ == "__main__":
    main()
