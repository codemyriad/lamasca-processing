"""Ground truth data for OCR testing.

Format:
{
    "image_name": {
        "x_y_width_height": {
            "ocr": "text from OCR",
            "ground_truth": "# correct text after manual verification"
        }
    }
}

Uncomment the ground_truth lines as you verify them.
"""

ground_truth_data = {
    # Example structure - will be populated by tests
    # "page1.png": {
    #     "100_200_300_400": {
    #         "ocr": "Detected text",
    #         "ground_truth": "# Correct text"
    #     }
    # }
}
