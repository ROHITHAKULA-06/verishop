"""L2 Input Processor tests."""
from app.layers.l2_input_processor.text_processor import TextProcessor
from app.layers.l2_input_processor.image_processor import ImageProcessor
from PIL import Image
import io, base64

def test_text_processor():
    tp = TextProcessor()
    result = tp.process("  <b>Wireless</b>  headphones   for  gaming  ")
    assert result["cleaned_text"].strip()
    assert result["word_count"] > 0
    assert result["language"] == "en"

def test_text_processor_empty():
    tp = TextProcessor()
    result = tp.process("")
    assert result["word_count"] == 0

def test_image_processor_base64():
    ip = ImageProcessor()
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    result = ip.process(b64)
    assert result["image"] is not None
    assert result["metadata"]["width"] <= 512
