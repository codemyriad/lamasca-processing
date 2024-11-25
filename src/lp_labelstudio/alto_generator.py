from typing import List, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom


def create_alto_xml(
    image_width: int,
    image_height: int,
    ocr_results: List[Tuple[List[float], Tuple[str, float]]],
) -> str:
    """
    Create ALTO XML from OCR results

    Args:
        image_width: Width of the original image
        image_height: Height of the original image
        ocr_results: List of (bbox, (text, confidence)) tuples from PaddleOCR
    """
    # Create the root element with namespace
    alto = ET.Element("alto")
    alto.set("xmlns", "http://www.loc.gov/standards/alto/ns-v4#")

    # Create Layout element
    layout = ET.SubElement(alto, "Layout")
    page = ET.SubElement(layout, "Page")
    page.set("ID", "0001")
    page.set("WIDTH", str(float(image_width)))
    page.set("HEIGHT", str(float(image_height)))

    # Create PrintSpace
    printspace = ET.SubElement(page, "PrintSpace")

    # Create TextBlock for each detected text
    for idx, (bbox, (text, confidence)) in enumerate(ocr_results):
        text_block = ET.SubElement(printspace, "TextBlock")
        text_block.set("ID", f"block_{idx}")
        text_block.set("HPOS", str(float(bbox[0])))
        text_block.set("VPOS", str(float(bbox[1])))
        text_block.set("WIDTH", str(float(bbox[2] - bbox[0])))
        text_block.set("HEIGHT", str(float(bbox[3] - bbox[1])))

        # Create TextLine
        text_line = ET.SubElement(text_block, "TextLine")
        text_line.set("HPOS", str(float(bbox[0])))
        text_line.set("VPOS", str(float(bbox[1])))
        text_line.set("WIDTH", str(float(bbox[2] - bbox[0])))
        text_line.set("HEIGHT", str(float(bbox[3] - bbox[1])))

        # Create String
        string = ET.SubElement(text_line, "String")
        string.set("CONTENT", text)
        string.set("HPOS", str(float(bbox[0])))
        string.set("VPOS", str(float(bbox[1])))
        string.set("WIDTH", str(float(bbox[2] - bbox[0])))
        string.set("HEIGHT", str(float(bbox[3] - bbox[1])))
        string.set("WC", str(confidence))  # Word confidence

    # Convert to string with pretty printing
    xmlstr = minidom.parseString(ET.tostring(alto)).toprettyxml(indent="    ")
    return xmlstr
