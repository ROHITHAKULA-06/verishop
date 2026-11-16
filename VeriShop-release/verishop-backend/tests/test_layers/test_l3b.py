"""L3b Vision Pipeline tests."""
from PIL import Image
from app.layers.l3b_vision_pipeline.structural_analyzer import StructuralAnalyzer
from app.layers.l3b_vision_pipeline.manipulation_detector import ManipulationDetector
from app.layers.l3b_vision_pipeline.clip_image import CLIPImageEncoder

def test_structural_analyzer():
    sa = StructuralAnalyzer()
    img = Image.new("RGB", (200, 100), color="blue")
    result = sa.analyze(img)
    assert result["width"] == 200
    assert result["height"] == 100
    assert result["aspect_ratio"] == 2.0

def test_manipulation_detector():
    md = ManipulationDetector()
    img = Image.new("RGB", (100, 100), color="white")
    result = md.detect(img)
    assert "is_manipulated" in result
    assert "ela_score" in result

def test_clip_image_mock():
    enc = CLIPImageEncoder()
    img = Image.new("RGB", (64, 64), color="green")
    emb = enc.encode(img)
    assert len(emb) == 512
