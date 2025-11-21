import numpy as np
from app.image_processor import medical_processor

def test_abcde_structure():
    img = np.random.rand(512, 512, 3).astype('float32')
    ab = medical_processor.calculate_ABCDE(img)
    assert set(ab.keys()) == {"A","B","C","D","E"}
    assert "asymmetry" in ab["A"]
    assert "border" in ab["B"]
    assert "color_variation" in ab["C"]
    assert "diameter_px" in ab["D"]