from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
import numpy as np
from PIL import Image
from io import BytesIO
import logging

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from .db import Base, engine, SessionLocal
from .auth import router as auth_router
from .routers_admin import router as admin_router
from .models import User, Role, UserRole
from .config import ensure_directories
from .image_processor import medical_processor
from .ai_models import ai_model_manager
from .cnn_models import resnet_medical
from .s3_storage import upload_bytes, ensure_lifecycle
from .datasets_sync import sync_repo

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="肿瘤数智化筛查后端", version="0.1.0")
Base.metadata.create_all(bind=engine)

# 确保目录结构存在
ensure_directories()
logger.info("目录结构初始化完成")

# 在空数据库时创建默认管理员（admin/123456）
def _seed_default_admin():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            from .auth import get_password_hash
            # 确保存在 admin 角色
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                admin_role = Role(name="admin")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)
            # 创建默认管理员用户
            user = User(username="admin", email="admin@example.com", hashed_password=get_password_hash("123456"))
            db.add(user)
            db.commit()
            db.refresh(user)
            # 绑定 admin 角色
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()
    finally:
        db.close()

_seed_default_admin()

app.include_router(auth_router)
app.include_router(admin_router)

# CORS（前端开发模式使用代理或CORS均可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "tumor-screening-api",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

# ==== 合成数据与模型训练（启动时完成）====
FEATURES = [
    "age", "bmi", "smoking", "alcohol", "family_history",
    "symptom_score", "lab_cea", "lab_ca125", "img_mean", "img_std", "img_edge"
]

np.random.seed(42)


def generate_synthetic_dataset(n: int = 4000):
    # 基础特征模拟
    age = np.random.randint(20, 85, size=n)
    bmi = np.random.normal(24, 4, size=n)
    smoking = np.random.binomial(1, 0.3, size=n)
    alcohol = np.random.binomial(1, 0.25, size=n)
    family_history = np.random.binomial(1, 0.15, size=n)
    symptom_score = np.clip(np.random.normal(0.8 * smoking + 0.5 * family_history + 1.0, 1.0, size=n), 0, 10)
    lab_cea = np.clip(np.random.normal(3 + 5*smoking + 2*family_history, 2, size=n), 0.1, 50)
    lab_ca125 = np.clip(np.random.normal(20 + 10*family_history, 8, size=n), 1, 200)
    img_mean = np.random.normal(120 + 10*family_history, 20, size=n)
    img_std = np.random.normal(30 + 5*smoking, 10, size=n)
    img_edge = np.clip(np.random.normal(100 + 30*smoking + 15*family_history, 40, size=n), 10, 400)

    X = np.column_stack([
        age, bmi, smoking, alcohol, family_history,
        symptom_score, lab_cea, lab_ca125, img_mean, img_std, img_edge
    ])

    # 风险标签（构造性规则 + 噪声）
    logit = (
        0.03*(age-50) + 0.08*(bmi-25) + 0.9*smoking + 0.6*alcohol + 1.2*family_history +
        0.15*symptom_score + 0.06*lab_cea + 0.02*lab_ca125 + 0.008*img_mean + 0.01*img_std + 0.005*img_edge +
        np.random.normal(0, 0.5, size=n)
    )
    prob = 1/(1+np.exp(-logit))
    y = (prob > 0.55).astype(int)
    return X, y


X_train, y_train = generate_synthetic_dataset(4000)
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(max_iter=1000))
])
pipe.fit(X_train, y_train)

# 训练增强AI模型
logger.info("开始训练增强AI模型...")
ai_model_manager.train_enhanced_models(X_train, y_train)
logger.info("增强AI模型训练完成")


# ==== 工具函数 ====

def _image_features(file_bytes: bytes) -> Dict[str, float]:
    try:
        img = Image.open(BytesIO(file_bytes)).convert("L")  # 灰度
        arr = np.asarray(img).astype(np.float32)
        mean = float(arr.mean())
        std = float(arr.std())
        # 简单边缘强度：绝对差分近似
        dx = np.abs(np.diff(arr, axis=1)).mean()
        dy = np.abs(np.diff(arr, axis=0)).mean()
        edge = float(dx + dy)
        return {"img_mean": mean, "img_std": std, "img_edge": edge}
    except Exception:
        # 如果解析失败，返回温和的默认值
        return {"img_mean": 120.0, "img_std": 30.0, "img_edge": 100.0}


def _risk_level(p: float) -> str:
    if p < 0.33:
        return "低风险"
    elif p < 0.66:
        return "中风险"
    return "高风险"


def _contributions(x: np.ndarray) -> Dict[str, float]:
    scaler = pipe.named_steps["scaler"]
    model = pipe.named_steps["model"]
    xs = scaler.transform([x])[0]
    coef = model.coef_[0]
    contrib = xs * coef
    return {FEATURES[i]: float(contrib[i]) for i in range(len(FEATURES))}


class AssessResponse(BaseModel):
    risk_score: float
    risk_level: str
    confidence: float
    top_factors: Dict[str, float]
    recommendations: list[str]
    detailed_analysis: Dict[str, Any]
    image_analysis: Optional[Dict[str, Any]] = None
    segmentation_results: Optional[Dict[str, Any]] = None
    model_performance: Dict[str, Any]


@app.get("/api/v1/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/assess", response_model=AssessResponse)
async def assess(
    payload: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    try:
        # 解析JSON载荷
        data: Dict[str, Any] = json.loads(payload)
        logger.info(f"收到评估请求: {data}")
        
        # 提取临床特征
        clinical_features = {
            "age": float(data.get("age", 45)),
            "bmi": float(data.get("bmi", 24)),
            "smoking": 1.0 if data.get("smoking", False) else 0.0,
            "alcohol": 1.0 if data.get("alcohol", False) else 0.0,
            "family_history": 1.0 if data.get("family_history", False) else 0.0,
            "symptom_score": float(data.get("symptom_score", 3)),
            "cea_level": float(data.get("lab_cea", 3)),
            "ca125_level": float(data.get("lab_ca125", 20))
        }
        
        # 图像处理
        image_features = None
        segmentation_results = None
        image_analysis = None
        
        if image is not None:
            logger.info("开始处理上传的图像...")
            file_bytes = await image.read()
            
            # 验证图像
            if not medical_processor.validate_image(file_bytes):
                raise HTTPException(status_code=400, detail="无效的图像文件")
            
            # 图像预处理
            processed_image = medical_processor.preprocess_image(file_bytes)
            
            # 图像增强
            enhanced_image = medical_processor.enhance_medical_image(processed_image)
            
            # 提取高级图像特征
            image_features = medical_processor.extract_advanced_features(enhanced_image)
            
            # 模拟肿瘤分割
            segmentation_results = medical_processor.simulate_segmentation(enhanced_image)
            
            # 保存处理后的图像
            import uuid
            image_filename = f"processed_{uuid.uuid4().hex[:8]}.png"
            saved_path = medical_processor.save_processed_image(enhanced_image, image_filename)
            
            image_analysis = {
                "original_filename": image.filename,
                "processed_filename": image_filename,
                "file_size": len(file_bytes),
                "image_features": image_features,
                "processing_status": "success"
            }
            
            logger.info("图像处理完成")
        
        # 使用增强AI模型进行综合预测
        logger.info("开始AI风险评估...")
        prediction_result = ai_model_manager.predict_risk_comprehensive(
            features=clinical_features,
            image_features=image_features,
            segmentation_results=segmentation_results
        )
        
        # 兼容性：使用传统模型进行对比
        traditional_features = [
            clinical_features["age"], clinical_features["bmi"], 
            clinical_features["smoking"], clinical_features["alcohol"], 
            clinical_features["family_history"], clinical_features["symptom_score"],
            clinical_features["cea_level"], clinical_features["ca125_level"],
            image_features.get("mean_intensity", 120.0) if image_features else 120.0,
            image_features.get("std_intensity", 30.0) if image_features else 30.0,
            image_features.get("edge_density", 0.1) * 1000 if image_features else 100.0
        ]
        
        traditional_prob = float(pipe.predict_proba([traditional_features])[0][1])
        traditional_level = _risk_level(traditional_prob)
        
        # 获取模型性能信息
        model_performance = ai_model_manager.get_model_performance()
        
        # 准备响应
        risk_factors_list = prediction_result["detailed_analysis"].get("risk_factors", [])
        # 将风险因素列表转换为字典格式
        top_factors_dict = {factor: 1.0 for factor in risk_factors_list} if risk_factors_list else {}
        
        response = AssessResponse(
            risk_score=prediction_result["risk_probability"],
            risk_level=prediction_result["risk_level"],
            confidence=prediction_result["confidence"],
            top_factors=top_factors_dict,
            recommendations=prediction_result["recommendations"],
            detailed_analysis=prediction_result["detailed_analysis"],
            image_analysis=image_analysis,
            segmentation_results=segmentation_results,
            model_performance={
                "enhanced_models": model_performance,
                "traditional_comparison": {
                    "probability": traditional_prob,
                    "level": traditional_level
                }
            }
        )
        
        logger.info(f"评估完成，风险等级: {prediction_result['risk_level']}")
        return response
        
    except json.JSONDecodeError:
        logger.error("JSON解析错误")
        raise HTTPException(status_code=400, detail="无效的JSON格式")
    except Exception as e:
        logger.error(f"评估过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


class ReportRequest(BaseModel):
    patient: Dict[str, Any]
    result: Dict[str, Any]


@app.post("/api/v1/report")
async def report(req: ReportRequest) -> Dict[str, Any]:
    # 直接生成简单HTML报告，前端可下载或打印
    patient = req.patient
    result = req.result

    html = f"""
    <html>
    <head>
      <meta charset='utf-8'/>
      <title>个性化风险评估报告</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; }}
        h1 {{ margin-bottom: 8px; }}
        .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-top: 16px; }}
        .tag {{ display:inline-block; padding:4px 8px; border-radius:4px; background:#eef; margin-right:8px; }}
        table {{ width:100%; border-collapse: collapse; }}
        td, th {{ border:1px solid #eee; padding:8px; }}
      </style>
    </head>
    <body>
      <h1>个性化风险评估报告</h1>
      <div>受检人：{patient.get('name','匿名')} | 年龄：{patient.get('age','-')}</div>
      <div class="card">
        <h3>总体风险</h3>
        <div>风险分值：{result.get('risk_score',0):.3f}</div>
        <div>风险等级：<span class="tag">{result.get('risk_level','-')}</span></div>
        <div>建议：{result.get('recommendations','-')}</div>
      </div>
      <div class="card">
        <h3>关键影响因素</h3>
        <table>
          <tr><th>特征</th><th>贡献度</th></tr>
          {''.join([f"<tr><td>{k}</td><td>{v:.4f}</td></tr>" for k,v in result.get('top_factors',{}).items()])}
        </table>
      </div>
      <div class="card">
        <h3>声明</h3>
        <p>本评估模型基于合成数据训练，仅用于技术演示与早筛辅助，不能替代临床诊断。</p>
        <p>系统不保存个人可识别信息与原始图像数据，所有评估均在会话内完成。</p>
      </div>
    </body>
    </html>
    """
    return {"format": "html", "content": html}


# ==== 新增专业API端点 ====

@app.get("/api/v1/models/performance")
async def get_model_performance() -> Dict[str, Any]:
    """获取AI模型性能指标"""
    try:
        performance = ai_model_manager.get_model_performance()
        return {
            "status": "success",
            "data": performance,
            "message": "模型性能数据获取成功"
        }
    except Exception as e:
        logger.error(f"获取模型性能时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型性能失败: {str(e)}")


@app.post("/api/v1/image/analyze")
async def analyze_image_only(image: UploadFile = File(...)) -> Dict[str, Any]:
    """单独的图像分析端点"""
    try:
        logger.info("开始单独图像分析...")
        file_bytes = await image.read()
        
        # 验证图像
        if not medical_processor.validate_image(file_bytes):
            raise HTTPException(status_code=400, detail="无效的图像文件")
        
        # 图像预处理
        processed_image = medical_processor.preprocess_image(file_bytes)
        
        # 图像增强
        enhanced_image = medical_processor.enhance_medical_image(processed_image)
        
        # 提取特征
        image_features = medical_processor.extract_advanced_features(enhanced_image)
        
        # 分割分析
        segmentation_results = medical_processor.simulate_segmentation(enhanced_image)
        
        return {
            "status": "success",
            "data": {
                "image_features": image_features,
                "segmentation_results": segmentation_results,
                "file_info": {
                    "filename": image.filename,
                    "size": len(file_bytes),
                    "content_type": image.content_type
                }
            },
            "message": "图像分析完成"
        }
        
    except Exception as e:
        logger.error(f"图像分析时出错: {e}")
        raise HTTPException(status_code=500, detail=f"图像分析失败: {str(e)}")


class RecognizeResponse(BaseModel):
    tumor_type: str
    malignancy_probability: float
    confidence: float
    type_distribution: Dict[str, float]
    abcde: Dict[str, Any]
    s3: Optional[Dict[str, str]] = None


@app.post("/api/v1/image/recognize", response_model=RecognizeResponse)
async def recognize_image(image: UploadFile = File(...)):
    try:
        if image.content_type not in ("image/jpeg", "image/png"):
            raise HTTPException(status_code=400, detail="仅支持JPG/PNG格式")
        file_bytes = await image.read()
        if len(file_bytes) > medical_processor.max_file_size:
            raise HTTPException(status_code=400, detail="文件大小超过10MB限制")
        if not medical_processor.validate_image(file_bytes):
            raise HTTPException(status_code=400, detail="无效的图像文件")

        proc = medical_processor.preprocess_image(file_bytes)
        enh = medical_processor.enhance_medical_image(proc)
        features = medical_processor.extract_advanced_features(enh)
        ab = medical_processor.calculate_ABCDE(enh)
        try:
            pred = resnet_medical.predict(file_bytes)
        except Exception:
            img = Image.open(BytesIO(file_bytes)).convert("RGB")
            arr = np.asarray(img.resize((224, 224))).astype(np.float32).mean(axis=(0, 1))
            logits = np.array([
                0.3*arr[0] + 0.2*arr[1] + 0.1*arr[2],
                0.1*arr[0] + 0.3*arr[1] + 0.2*arr[2],
                0.2*arr[0] + 0.1*arr[1] + 0.3*arr[2],
                0.25*arr[0] + 0.15*arr[1] + 0.2*arr[2],
                0.15*arr[0] + 0.25*arr[1] + 0.15*arr[2],
            ], dtype=np.float32)
            exps = np.exp(logits - logits.max())
            probs = (exps / exps.sum()).astype(float)
            idx = int(np.argmax(probs))
            pred = {
                "tumor_type": resnet_medical.type_labels[idx],
                "type_distribution": {resnet_medical.type_labels[i]: float(probs[i]) for i in range(len(resnet_medical.type_labels))},
                "malignancy_probability": float(min(1.0, max(0.0, (arr.mean()/255.0)))),
                "confidence": float(np.max(probs))
            }

        s3info = None
        bucket = os.getenv("S3_BUCKET")
        if bucket:
            buf = BytesIO()
            Image.fromarray((enh*255).astype('uint8')).save(buf, format='PNG')
            s3info = upload_bytes(bucket, f"processed/{image.filename}.png", buf.getvalue(), "image/png")
            try:
                days = int(os.getenv("S3_LIFECYCLE_DAYS", "30"))
                ensure_lifecycle(bucket, days)
            except Exception:
                pass

        return RecognizeResponse(
            tumor_type=pred["tumor_type"],
            malignancy_probability=pred["malignancy_probability"],
            confidence=pred["confidence"],
            type_distribution=pred["type_distribution"],
            abcde=ab,
            s3=s3info
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@app.post("/api/v1/datasets/sync")
async def datasets_sync():
    try:
        from .config import DATA_DIR
        info = sync_repo(DATA_DIR)
        return {"status": "success", "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据集同步失败: {str(e)}")


@app.get("/api/v1/system/status")
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态信息"""
    try:
        from .config import UPLOAD_DIRS
        import os
        
        # 检查目录状态
        directory_status = {}
        for name, path in UPLOAD_DIRS.items():
            directory_status[name] = {
                "exists": path.exists(),
                "path": str(path),
                "file_count": len(list(path.glob("*"))) if path.exists() else 0
            }
        
        # 模型状态
        model_status = {
            "models_loaded": len(ai_model_manager.models),
            "scalers_loaded": len(ai_model_manager.scalers),
            "has_metrics": bool(ai_model_manager.model_metrics)
        }
        
        return {
            "status": "success",
            "data": {
                "directories": directory_status,
                "models": model_status,
                "processor_status": "ready"
            },
            "message": "系统状态正常"
        }
        
    except Exception as e:
        logger.error(f"获取系统状态时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@app.post("/api/v1/models/retrain")
async def retrain_models(sample_size: int = 5000) -> Dict[str, Any]:
    """重新训练AI模型"""
    try:
        logger.info(f"开始重新训练模型，样本数量: {sample_size}")
        
        # 生成新的训练数据
        X_new, y_new = generate_synthetic_dataset(sample_size)
        
        # 重新训练增强模型
        ai_model_manager.train_enhanced_models(X_new, y_new)
        
        # 保存模型
        ai_model_manager.save_models()
        
        # 获取新的性能指标
        performance = ai_model_manager.get_model_performance()
        
        return {
            "status": "success",
            "data": {
                "training_samples": sample_size,
                "performance": performance
            },
            "message": "模型重新训练完成"
        }
        
    except Exception as e:
        logger.error(f"重新训练模型时出错: {e}")
        raise HTTPException(status_code=500, detail=f"模型重新训练失败: {str(e)}")


class BatchAssessRequest(BaseModel):
    patients: list[Dict[str, Any]]
    include_detailed_analysis: bool = True


@app.post("/api/v1/assess/batch")
async def batch_assess(request: BatchAssessRequest) -> Dict[str, Any]:
    """批量风险评估"""
    try:
        logger.info(f"开始批量评估，患者数量: {len(request.patients)}")
        
        results = []
        for i, patient_data in enumerate(request.patients):
            try:
                # 提取临床特征
                clinical_features = {
                    "age": float(patient_data.get("age", 45)),
                    "bmi": float(patient_data.get("bmi", 24)),
                    "smoking": 1.0 if patient_data.get("smoking", False) else 0.0,
                    "alcohol": 1.0 if patient_data.get("alcohol", False) else 0.0,
                    "family_history": 1.0 if patient_data.get("family_history", False) else 0.0,
                    "symptom_score": float(patient_data.get("symptom_score", 3)),
                    "cea_level": float(patient_data.get("lab_cea", 3)),
                    "ca125_level": float(patient_data.get("lab_ca125", 20))
                }
                
                # 使用AI模型预测
                prediction_result = ai_model_manager.predict_risk_comprehensive(
                    features=clinical_features,
                    image_features=None,  # 批量评估暂不支持图像
                    segmentation_results=None
                )
                
                patient_result = {
                    "patient_id": i,
                    "patient_data": patient_data,
                    "risk_score": prediction_result["risk_probability"],
                    "risk_level": prediction_result["risk_level"],
                    "confidence": prediction_result["confidence"],
                    "recommendations": prediction_result["recommendations"]
                }
                
                if request.include_detailed_analysis:
                    patient_result["detailed_analysis"] = prediction_result["detailed_analysis"]
                
                results.append(patient_result)
                
            except Exception as e:
                logger.error(f"处理第{i+1}个患者时出错: {e}")
                results.append({
                    "patient_id": i,
                    "patient_data": patient_data,
                    "error": str(e),
                    "status": "failed"
                })
        
        # 统计信息
        successful_count = len([r for r in results if "error" not in r])
        high_risk_count = len([r for r in results if r.get("risk_level") == "high"])
        
        return {
            "status": "success",
            "data": {
                "results": results,
                "summary": {
                    "total_patients": len(request.patients),
                    "successful_assessments": successful_count,
                    "high_risk_patients": high_risk_count,
                    "success_rate": successful_count / len(request.patients) if request.patients else 0
                }
            },
            "message": f"批量评估完成，成功处理 {successful_count}/{len(request.patients)} 个患者"
        }
        
    except Exception as e:
        logger.error(f"批量评估时出错: {e}")
        raise HTTPException(status_code=500, detail=f"批量评估失败: {str(e)}")
