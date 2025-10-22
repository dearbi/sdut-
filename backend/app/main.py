from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import numpy as np
from PIL import Image
from io import BytesIO

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from .db import Base, engine, SessionLocal
from .auth import router as auth_router
from .routers_admin import router as admin_router
from .models import User, Role, UserRole

app = FastAPI(title="肿瘤数智化筛查后端", version="0.1.0")
Base.metadata.create_all(bind=engine)

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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
    top_factors: Dict[str, float]
    recommendations: str


@app.get("/api/v1/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/assess", response_model=AssessResponse)
async def assess(
    payload: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    # 解析JSON载荷
    data: Dict[str, Any] = json.loads(payload)
    # 安全取值与默认
    age = float(data.get("age", 45))
    bmi = float(data.get("bmi", 24))
    smoking = 1.0 if data.get("smoking", False) else 0.0
    alcohol = 1.0 if data.get("alcohol", False) else 0.0
    family_history = 1.0 if data.get("family_history", False) else 0.0
    symptom_score = float(data.get("symptom_score", 3))
    lab_cea = float(data.get("lab_cea", 3))
    lab_ca125 = float(data.get("lab_ca125", 20))

    img_mean = 120.0
    img_std = 30.0
    img_edge = 100.0
    if image is not None:
        file_bytes = await image.read()
        feats = _image_features(file_bytes)
        img_mean, img_std, img_edge = feats["img_mean"], feats["img_std"], feats["img_edge"]

    x = np.array([
        age, bmi, smoking, alcohol, family_history,
        symptom_score, lab_cea, lab_ca125, img_mean, img_std, img_edge
    ], dtype=float)

    # 预测风险
    prob = float(pipe.predict_proba([x])[0][1])
    level = _risk_level(prob)

    # 解释：按贡献度排序，取前5
    contrib_map = _contributions(x)
    top = dict(sorted(contrib_map.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5])

    # 建议（示例规则）
    if level == "高风险":
        rec = "建议尽快进行进一步影像/实验室检查，并咨询专业医生。"
    elif level == "中风险":
        rec = "建议定期复查，优化生活方式，必要时进行专项筛查。"
    else:
        rec = "保持健康生活方式，定期体检与随访。"

    return AssessResponse(
        risk_score=prob,
        risk_level=level,
        top_factors=top,
        recommendations=rec,
    )


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
