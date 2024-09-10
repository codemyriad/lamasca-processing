import importlib.util
import sys

def find_paddleocr_path():
    try:
        spec = importlib.util.find_spec("paddleocr")
        if spec is not None:
            return spec.origin
    except ImportError as e:
        # If ImportError occurs, try to extract the path from the error message
        error_msg = str(e)
        if "paddleocr" in error_msg and "No module named" in error_msg:
            # The path might be in the error message
            parts = error_msg.split("'")
            if len(parts) >= 2:
                return parts[1]
    
    return None

def main():
    paddleocr_path = find_paddleocr_path()
    if paddleocr_path:
        print(f"PaddleOCR path: {paddleocr_path}")
    else:
        print("Unable to find PaddleOCR path.")

if __name__ == "__main__":
    main()
