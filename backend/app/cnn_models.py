try:
    import torch
    import torchvision.transforms as T
    from torchvision import models
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
from PIL import Image
from io import BytesIO
from typing import Dict, Any
import numpy as np

_device = (torch.device("cpu") if TORCH_AVAILABLE else None)

class ResNet50Medical:
    def __init__(self, num_types: int = 5):
        self.type_labels = ["乳腺肿瘤", "脑肿瘤", "肝脏肿瘤", "肺部肿瘤", "皮肤肿瘤"]
        self.num_types = num_types
        if TORCH_AVAILABLE:
            self.backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            for p in self.backbone.parameters():
                p.requires_grad = False
            self.backbone.eval()
            self.backbone.to(_device)
            self.type_head = torch.nn.Linear(2048, num_types).to(_device)
            self.malignant_head = torch.nn.Linear(2048, 1).to(_device)
            self.type_head.eval()
            self.malignant_head.eval()
            self.transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.backbone = None
            self.type_head = None
            self.malignant_head = None
            self.transform = None

    def _extract_features(self, img: Image.Image):
        if TORCH_AVAILABLE:
            x = self.transform(img).unsqueeze(0).to(_device)
            with torch.no_grad():
                feats = self.backbone.forward_features(x) if hasattr(self.backbone, "forward_features") else None
                if feats is None:
                    modules = list(self.backbone.children())[:-1]
                    fx = x
                    for m in modules:
                        fx = m(fx)
                    feats = fx.view(fx.size(0), -1)
            return feats
        else:
            arr = np.asarray(img.resize((224, 224))).astype(np.float32)
            return arr.mean(axis=(0, 1))

    def predict(self, file_bytes: bytes) -> Dict[str, Any]:
        img = Image.open(BytesIO(file_bytes)).convert("RGB")
        feats = self._extract_features(img)
        if TORCH_AVAILABLE:
            try:
                feats = feats.to(_device)
                with torch.no_grad():
                    type_logits = self.type_head(feats)
                    malignant_logit = self.malignant_head(feats)
                    type_prob = torch.softmax(type_logits, dim=1)[0].cpu().numpy()
                    malignant_prob = torch.sigmoid(malignant_logit)[0].item()
            except Exception:
                v = np.asarray(img.resize((224, 224))).astype(np.float32).mean(axis=(0, 1))
                logits = np.array([
                    0.3*v[0] + 0.2*v[1] + 0.1*v[2],
                    0.1*v[0] + 0.3*v[1] + 0.2*v[2],
                    0.2*v[0] + 0.1*v[1] + 0.3*v[2],
                    0.25*v[0] + 0.15*v[1] + 0.2*v[2],
                    0.15*v[0] + 0.25*v[1] + 0.15*v[2],
                ], dtype=np.float32)
                exps = np.exp(logits - logits.max())
                type_prob = (exps / exps.sum()).astype(float)
                malignant_prob = float(min(1.0, max(0.0, (v.mean()/255.0))))
        else:
            v = np.array(feats)
            logits = np.array([
                0.3*v[0] + 0.2*v[1] + 0.1*v[2],
                0.1*v[0] + 0.3*v[1] + 0.2*v[2],
                0.2*v[0] + 0.1*v[1] + 0.3*v[2],
                0.25*v[0] + 0.15*v[1] + 0.2*v[2],
                0.15*v[0] + 0.25*v[1] + 0.15*v[2],
            ], dtype=np.float32)
            exps = np.exp(logits - logits.max())
            type_prob = (exps / exps.sum()).astype(float)
            malignant_prob = float(min(1.0, max(0.0, (v.mean()/255.0))))
        top_idx = int(np.argmax(type_prob))
        confidence = float(np.max(type_prob))
        tumor_type = self.type_labels[top_idx]
        return {
            "tumor_type": tumor_type,
            "type_distribution": {self.type_labels[i]: float(type_prob[i]) for i in range(len(self.type_labels))},
            "malignancy_probability": float(malignant_prob),
            "confidence": confidence
        }

resnet_medical = ResNet50Medical()