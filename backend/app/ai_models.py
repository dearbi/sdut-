"""
AI模型管理器 - 借鉴CTAI项目的模型管理和预测流程
"""
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path
import json

from .config import MODEL_CONFIG, RISK_THRESHOLDS, UPLOAD_DIRS

logger = logging.getLogger(__name__)

class EnhancedAIModelManager:
    """增强的AI模型管理器"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_metrics = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化多个AI模型"""
        # 主要风险评估模型
        self.models['risk_assessment'] = LogisticRegression(
            random_state=42, 
            max_iter=1000,
            class_weight='balanced'
        )
        
        # 随机森林模型（用于特征重要性分析）
        self.models['feature_analysis'] = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            class_weight='balanced'
        )
        
        # 梯度提升模型（用于高精度预测）
        self.models['advanced_prediction'] = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        # 对应的标准化器
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
    
    def train_enhanced_models(self, features: np.ndarray, labels: np.ndarray):
        """训练增强的AI模型"""
        logger.info("开始训练增强AI模型...")
        
        for model_name, model in self.models.items():
            try:
                # 标准化特征
                scaler = self.scalers[model_name]
                features_scaled = scaler.fit_transform(features)
                
                # 训练模型
                model.fit(features_scaled, labels)
                
                # 交叉验证评估
                cv_scores = cross_val_score(model, features_scaled, labels, cv=5)
                self.model_metrics[model_name] = {
                    'cv_mean': float(np.mean(cv_scores)),
                    'cv_std': float(np.std(cv_scores)),
                    'cv_scores': cv_scores.tolist()
                }
                
                # 特征重要性（如果模型支持）
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = model.feature_importances_.tolist()
                elif hasattr(model, 'coef_'):
                    self.feature_importance[model_name] = np.abs(model.coef_[0]).tolist()
                
                logger.info(f"模型 {model_name} 训练完成，CV得分: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
            except Exception as e:
                logger.error(f"训练模型 {model_name} 时出错: {e}")
    
    def predict_risk_comprehensive(self, features: Dict[str, float], 
                                 image_features: Optional[Dict[str, float]] = None,
                                 segmentation_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """综合风险预测 - 整合多种特征和模型"""
        
        # 准备特征向量
        feature_vector = self._prepare_feature_vector(features, image_features, segmentation_results)
        
        # 多模型预测
        predictions = {}
        probabilities = {}
        
        for model_name, model in self.models.items():
            try:
                scaler = self.scalers[model_name]
                features_scaled = scaler.transform([feature_vector])
                
                # 预测概率
                if hasattr(model, 'predict_proba'):
                    prob = model.predict_proba(features_scaled)[0]
                    probabilities[model_name] = {
                        'low_risk': float(prob[0]) if len(prob) > 1 else 1.0 - float(prob[0]),
                        'high_risk': float(prob[1]) if len(prob) > 1 else float(prob[0])
                    }
                
                # 预测类别
                prediction = model.predict(features_scaled)[0]
                predictions[model_name] = int(prediction)
                
            except Exception as e:
                logger.error(f"模型 {model_name} 预测时出错: {e}")
                predictions[model_name] = 0
                probabilities[model_name] = {'low_risk': 0.5, 'high_risk': 0.5}
        
        # 集成预测结果
        ensemble_result = self._ensemble_predictions(predictions, probabilities)
        
        # 生成详细分析
        detailed_analysis = self._generate_detailed_analysis(
            feature_vector, features, image_features, segmentation_results, ensemble_result
        )
        
        return {
            'risk_probability': ensemble_result['probability'],
            'risk_level': ensemble_result['level'],
            'confidence': ensemble_result['confidence'],
            'individual_predictions': predictions,
            'individual_probabilities': probabilities,
            'detailed_analysis': detailed_analysis,
            'recommendations': self._generate_recommendations(ensemble_result, detailed_analysis)
        }
    
    def _prepare_feature_vector(self, features: Dict[str, float], 
                              image_features: Optional[Dict[str, float]] = None,
                              segmentation_results: Optional[Dict[str, Any]] = None) -> List[float]:
        """准备特征向量"""
        feature_vector = []
        
        # 基础临床特征
        clinical_features = [
            features.get('age', 0) / 100.0,  # 归一化年龄
            features.get('bmi', 25) / 50.0,  # 归一化BMI
            features.get('smoking', 0),
            features.get('alcohol', 0),
            features.get('family_history', 0),
            features.get('symptom_score', 0) / 10.0,  # 归一化症状评分
            features.get('cea_level', 0) / 100.0,  # 归一化CEA
            features.get('ca125_level', 0) / 1000.0,  # 归一化CA-125
        ]
        feature_vector.extend(clinical_features)
        
        # 图像特征
        if image_features:
            img_features = [
                image_features.get('mean_intensity', 0) / 255.0,
                image_features.get('std_intensity', 0) / 255.0,
                image_features.get('entropy', 0) / 10.0,
                image_features.get('contrast', 0) / 255.0,
                image_features.get('edge_density', 0),
                image_features.get('contour_area', 0) / 100000.0,
                image_features.get('fft_mean', 0) / 10000.0,
                image_features.get('fft_std', 0) / 10000.0,
            ]
            feature_vector.extend(img_features)
        else:
            feature_vector.extend([0.0] * 8)  # 填充零值
        
        # 分割结果特征
        if segmentation_results:
            seg_features = [
                segmentation_results.get('num_regions', 0) / 10.0,
                segmentation_results.get('total_area', 0) / 100000.0,
                segmentation_results.get('largest_region_area', 0) / 50000.0,
            ]
            feature_vector.extend(seg_features)
        else:
            feature_vector.extend([0.0] * 3)  # 填充零值
        
        return feature_vector
    
    def _ensemble_predictions(self, predictions: Dict[str, int], 
                            probabilities: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """集成多个模型的预测结果"""
        # 加权平均概率
        weights = {
            'risk_assessment': 0.4,
            'feature_analysis': 0.3,
            'advanced_prediction': 0.3
        }
        
        weighted_prob = 0.0
        total_weight = 0.0
        
        for model_name, prob_dict in probabilities.items():
            weight = weights.get(model_name, 0.2)
            weighted_prob += prob_dict['high_risk'] * weight
            total_weight += weight
        
        if total_weight > 0:
            final_probability = weighted_prob / total_weight
        else:
            final_probability = 0.5
        
        # 确定风险等级
        if final_probability < RISK_THRESHOLDS['low']:
            risk_level = 'low'
        elif final_probability < RISK_THRESHOLDS['medium']:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # 计算置信度
        pred_values = list(predictions.values())
        confidence = 1.0 - (np.std(pred_values) if len(pred_values) > 1 else 0.0)
        
        return {
            'probability': float(final_probability),
            'level': risk_level,
            'confidence': float(confidence)
        }
    
    def _generate_detailed_analysis(self, feature_vector: List[float], 
                                  features: Dict[str, float],
                                  image_features: Optional[Dict[str, float]],
                                  segmentation_results: Optional[Dict[str, Any]],
                                  ensemble_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细分析报告"""
        analysis = {
            'clinical_factors': {},
            'image_factors': {},
            'segmentation_factors': {},
            'risk_factors': []
        }
        
        # 临床因素分析
        age = features.get('age', 0)
        bmi = features.get('bmi', 25)
        cea = features.get('cea_level', 0)
        ca125 = features.get('ca125_level', 0)
        
        analysis['clinical_factors'] = {
            'age_risk': 'high' if age > 60 else 'medium' if age > 45 else 'low',
            'bmi_risk': 'high' if bmi > 30 or bmi < 18.5 else 'low',
            'cea_risk': 'high' if cea > 5.0 else 'medium' if cea > 3.0 else 'low',
            'ca125_risk': 'high' if ca125 > 35.0 else 'medium' if ca125 > 20.0 else 'low'
        }
        
        # 图像因素分析
        if image_features:
            analysis['image_factors'] = {
                'texture_complexity': 'high' if image_features.get('entropy', 0) > 7 else 'medium' if image_features.get('entropy', 0) > 5 else 'low',
                'edge_prominence': 'high' if image_features.get('edge_density', 0) > 0.1 else 'low',
                'intensity_variation': 'high' if image_features.get('std_intensity', 0) > 50 else 'low'
            }
        
        # 分割因素分析
        if segmentation_results:
            analysis['segmentation_factors'] = {
                'region_count': segmentation_results.get('num_regions', 0),
                'suspicious_areas': 'detected' if segmentation_results.get('largest_region_area', 0) > 1000 else 'none'
            }
        
        # 风险因素汇总
        risk_factors = []
        if features.get('smoking', 0):
            risk_factors.append('吸烟史')
        if features.get('family_history', 0):
            risk_factors.append('家族史')
        if age > 60:
            risk_factors.append('高龄')
        if cea > 5.0:
            risk_factors.append('CEA升高')
        if ca125 > 35.0:
            risk_factors.append('CA-125升高')
        
        analysis['risk_factors'] = risk_factors
        
        return analysis
    
    def _generate_recommendations(self, ensemble_result: Dict[str, Any], 
                                detailed_analysis: Dict[str, Any]) -> List[str]:
        """生成个性化建议"""
        recommendations = []
        risk_level = ensemble_result['level']
        
        if risk_level == 'high':
            recommendations.extend([
                '建议立即就医进行进一步检查',
                '考虑进行CT或MRI影像学检查',
                '建议咨询肿瘤专科医生',
                '定期监测肿瘤标志物水平'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                '建议3-6个月内复查',
                '保持健康的生活方式',
                '定期体检，关注相关指标',
                '如有症状加重，及时就医'
            ])
        else:
            recommendations.extend([
                '继续保持健康的生活方式',
                '建议年度常规体检',
                '注意饮食均衡和适量运动',
                '避免已知的危险因素'
            ])
        
        # 基于具体风险因素的建议
        risk_factors = detailed_analysis.get('risk_factors', [])
        if '吸烟史' in risk_factors:
            recommendations.append('强烈建议戒烟')
        if 'CEA升高' in risk_factors or 'CA-125升高' in risk_factors:
            recommendations.append('建议进一步检查肿瘤标志物的变化趋势')
        
        return recommendations
    
    def get_model_performance(self) -> Dict[str, Any]:
        """获取模型性能指标"""
        return {
            'metrics': self.model_metrics,
            'feature_importance': self.feature_importance,
            'model_info': {name: str(type(model).__name__) for name, model in self.models.items()}
        }
    
    def save_models(self, directory: str = "models"):
        """保存训练好的模型"""
        save_dir = UPLOAD_DIRS[directory]
        
        for model_name, model in self.models.items():
            model_path = save_dir / f"{model_name}_model.joblib"
            scaler_path = save_dir / f"{model_name}_scaler.joblib"
            
            joblib.dump(model, model_path)
            joblib.dump(self.scalers[model_name], scaler_path)
        
        # 保存元数据
        metadata = {
            'model_metrics': self.model_metrics,
            'feature_importance': self.feature_importance
        }
        metadata_path = save_dir / "model_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模型已保存到 {save_dir}")
    
    def load_models(self, directory: str = "models"):
        """加载预训练的模型"""
        load_dir = UPLOAD_DIRS[directory]
        
        for model_name in self.models.keys():
            model_path = load_dir / f"{model_name}_model.joblib"
            scaler_path = load_dir / f"{model_name}_scaler.joblib"
            
            if model_path.exists() and scaler_path.exists():
                self.models[model_name] = joblib.load(model_path)
                self.scalers[model_name] = joblib.load(scaler_path)
        
        # 加载元数据
        metadata_path = load_dir / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.model_metrics = metadata.get('model_metrics', {})
                self.feature_importance = metadata.get('feature_importance', {})
        
        logger.info(f"模型已从 {load_dir} 加载")

# 全局模型管理器实例
ai_model_manager = EnhancedAIModelManager()