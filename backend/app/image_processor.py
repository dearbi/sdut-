"""
医学图像处理模块 - 借鉴CTAI项目的专业图像处理流程
"""
import numpy as np
import cv2
from PIL import Image, ImageEnhance
from typing import Dict, Tuple, Optional, Any
import io
import logging
from pathlib import Path

from .config import IMAGE_PROCESSING, UPLOAD_DIRS

logger = logging.getLogger(__name__)

class MedicalImageProcessor:
    """专业医学图像处理器"""
    
    def __init__(self):
        self.target_size = IMAGE_PROCESSING["target_size"]
        self.max_file_size = IMAGE_PROCESSING["max_file_size"]
    
    def validate_image(self, file_bytes: bytes) -> bool:
        """验证图像文件"""
        if len(file_bytes) > self.max_file_size:
            raise ValueError(f"文件大小超过限制: {len(file_bytes)} > {self.max_file_size}")
        
        try:
            Image.open(io.BytesIO(file_bytes))
            return True
        except Exception as e:
            logger.error(f"图像验证失败: {e}")
            return False
    
    def preprocess_image(self, file_bytes: bytes) -> np.ndarray:
        """图像预处理 - 参考CTAI的预处理流程"""
        # 加载图像
        image = Image.open(io.BytesIO(file_bytes))
        
        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整大小
        image = image.resize(self.target_size, Image.Resampling.LANCZOS)
        
        # 转换为numpy数组
        img_array = np.array(image, dtype=np.float32)
        
        # 归一化到[0,1]
        img_array = img_array / 255.0
        
        return img_array
    
    def enhance_medical_image(self, img_array: np.ndarray) -> np.ndarray:
        """医学图像增强"""
        # 转换回PIL进行增强
        img_pil = Image.fromarray((img_array * 255).astype(np.uint8))
        
        # 对比度增强
        enhancer = ImageEnhance.Contrast(img_pil)
        img_pil = enhancer.enhance(1.2)
        
        # 锐度增强
        enhancer = ImageEnhance.Sharpness(img_pil)
        img_pil = enhancer.enhance(1.1)
        
        return np.array(img_pil, dtype=np.float32) / 255.0
    
    def extract_advanced_features(self, img_array: np.ndarray) -> Dict[str, float]:
        """提取高级图像特征 - 借鉴CTAI的特征提取方法"""
        # 转换为灰度图像进行特征提取
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor((img_array * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        else:
            gray = (img_array * 255).astype(np.uint8)
        
        features = {}
        
        # 基础统计特征
        features['mean_intensity'] = float(np.mean(gray))
        features['std_intensity'] = float(np.std(gray))
        features['min_intensity'] = float(np.min(gray))
        features['max_intensity'] = float(np.max(gray))
        
        # 纹理特征
        features['entropy'] = self._calculate_entropy(gray)
        features['contrast'] = self._calculate_contrast(gray)
        
        # 边缘特征
        edges = cv2.Canny(gray, 50, 150)
        features['edge_density'] = float(np.sum(edges > 0) / edges.size)
        features['edge_mean'] = float(np.mean(edges))
        
        # 形状特征
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            features['contour_area'] = float(cv2.contourArea(largest_contour))
            features['contour_perimeter'] = float(cv2.arcLength(largest_contour, True))
        else:
            features['contour_area'] = 0.0
            features['contour_perimeter'] = 0.0
        
        # 频域特征
        fft = np.fft.fft2(gray)
        fft_magnitude = np.abs(fft)
        features['fft_mean'] = float(np.mean(fft_magnitude))
        features['fft_std'] = float(np.std(fft_magnitude))
        
        return features

    def calculate_ABCDE(self, img_array: np.ndarray) -> Dict[str, Any]:
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor((img_array * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        else:
            gray = (img_array * 255).astype(np.uint8)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        asymmetry = 0.0
        border_irregularity = 0.0
        color_var = float(np.std(gray))
        diameter_px = 0.0
        evolving = 'unknown'
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(cnt)
            peri = cv2.arcLength(cnt, True)
            border_irregularity = float(4 * np.pi * area / (peri ** 2)) if peri > 0 else 0.0
            x, y, w, h = cv2.boundingRect(cnt)
            diameter_px = float(max(w, h))
            M = cv2.moments(cnt)
            if M['m00'] != 0:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                left = gray[:, :cx]
                right = np.fliplr(gray[:, cx:])
                minw = min(left.shape[1], right.shape[1])
                asymmetry = float(np.mean(np.abs(left[:, :minw] - right[:, :minw]))) / 255.0
        return {
            "A": {"asymmetry": asymmetry, "desc": "越大越不对称"},
            "B": {"border": border_irregularity, "desc": "接近1更规则"},
            "C": {"color_variation": color_var, "desc": "颜色差异越大风险越高"},
            "D": {"diameter_px": diameter_px, "desc": "像素直径估计"},
            "E": {"evolving": evolving, "desc": "需时间序列支持"}
        }
    
    def _calculate_entropy(self, image: np.ndarray) -> float:
        """计算图像熵"""
        hist, _ = np.histogram(image, bins=256, range=(0, 256))
        hist = hist / hist.sum()
        hist = hist[hist > 0]  # 移除零值
        entropy = -np.sum(hist * np.log2(hist))
        return float(entropy)
    
    def _calculate_contrast(self, image: np.ndarray) -> float:
        """计算图像对比度"""
        return float(np.std(image))
    
    def simulate_segmentation(self, img_array: np.ndarray) -> Dict[str, Any]:
        """模拟肿瘤分割 - 简化版本，实际应使用深度学习模型"""
        gray = cv2.cvtColor((img_array * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        
        # 使用阈值分割模拟肿瘤区域检测
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找连通区域
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        segmentation_results = {
            'num_regions': len(contours),
            'total_area': float(np.sum(binary > 0)),
            'largest_region_area': 0.0,
            'regions_info': []
        }
        
        if contours:
            # 分析每个区域
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                if area > segmentation_results['largest_region_area']:
                    segmentation_results['largest_region_area'] = float(area)
                
                segmentation_results['regions_info'].append({
                    'region_id': i,
                    'area': float(area),
                    'perimeter': float(perimeter),
                    'circularity': float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0
                })
        
        return segmentation_results
    
    def save_processed_image(self, img_array: np.ndarray, filename: str, 
                           directory: str = "tmp_image") -> Path:
        """保存处理后的图像"""
        save_dir = UPLOAD_DIRS[directory]
        save_path = save_dir / filename
        
        # 转换为PIL图像并保存
        img_pil = Image.fromarray((img_array * 255).astype(np.uint8))
        img_pil.save(save_path)
        
        return save_path

# 全局处理器实例
medical_processor = MedicalImageProcessor()