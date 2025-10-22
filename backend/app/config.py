"""
配置文件 - 借鉴CTAI项目的专业目录管理策略
"""
import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# 专业医学图像处理目录结构（参考CTAI）
UPLOAD_DIRS = {
    "uploads": DATA_DIR / "uploads",           # 直接上传目录
    "tmp_ct": DATA_DIR / "tmp" / "ct",         # CT文件副本目录
    "tmp_image": DATA_DIR / "tmp" / "image",   # 图像转换目录
    "tmp_mask": DATA_DIR / "tmp" / "mask",     # 分割掩膜目录
    "tmp_draw": DATA_DIR / "tmp" / "draw",     # 处理结果目录
    "reports": DATA_DIR / "reports",           # 报告存储目录
    "models": DATA_DIR / "models",             # AI模型存储目录
}

# 支持的文件格式
SUPPORTED_IMAGE_FORMATS = {
    "common": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
    "medical": [".dcm", ".nii", ".nii.gz"],  # DICOM和NIfTI格式
}

# AI模型配置
MODEL_CONFIG = {
    "segmentation_model": "unet_tumor_segmentation.pth",
    "classification_model": "tumor_classifier.pth",
    "feature_extractor": "medical_feature_extractor.pth",
}

# 图像处理参数
IMAGE_PROCESSING = {
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "target_size": (512, 512),
    "normalization": {
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225]
    }
}

# 风险评估阈值
RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.7,
    "high": 1.0
}

def ensure_directories():
    """确保所有必要的目录存在"""
    for dir_path in UPLOAD_DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)

# 初始化目录
ensure_directories()