import torch
from torchvision import models, transforms
from PIL import Image
import json

# CLIP
from transformers import CLIPProcessor, CLIPModel
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# CLIP labels
labels = [
    "healthy green plant",
    "plant with yellow leaves",
    "plant with brown spots",
    "dry plant with curled leaves",
    "overwatered plant with soft leaves",
    "plant with fungus",
    "indoor plant near window",
    "plant in pot soil wet",
]

plant_labels = [
    "hoya plant",
    "monstera plant",
    "ficus plant",
    "succulent",
    "cactus",
    "orchid",
    "snake plant",
]


CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry___Powdery_mildew",
    "Cherry___healthy",
    "Corn___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn___Northern_Leaf_Blight",
    "Corn___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy"
]


def clean_label(label):
    return label.replace("___", " ").replace("_", " ").lower()


def analyze_image_clip(image_path: str):
    image = Image.open(image_path)

    inputs = clip_processor(
        text=labels,
        images=image,
        return_tensors="pt",
        padding=True
    )
    outputs = clip_model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)

    topk = probs[0].topk(3)
    results = [labels[i] for i in topk.indices]
    return results

def detect_plant_type(image_path: str):
    image = Image.open(image_path)

    inputs = clip_processor(
        text=plant_labels,
        images=image,
        return_tensors="pt",
        padding=True
    )
    outputs = clip_model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    best_idx = probs.argmax().item()
    return plant_labels[best_idx]


# === Plant disease MobileNetV2 ===
disease_model_path = "app/ai/models/mobilenetv2_plant.pth"



# === СОЗДАЁМ МОДЕЛЬ ===
model_mobilenet = models.mobilenet_v2(
    pretrained=False,
    num_classes=len(CLASS_NAMES)
)

# === ЗАГРУЖАЕМ ВЕСА ===
disease_model_path = "app/ai/models/mobilenetv2_plant.pth"

model_mobilenet.load_state_dict(
    torch.load(disease_model_path, map_location="cpu"),
    strict=False
)

model_mobilenet.eval()

# === PREPROCESS ===
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])



# Предобработка
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])


def analyze_plant_disease_torch(image_path: str, top_k: int = 3):
    img = Image.open(image_path).convert("RGB")
    input_tensor = preprocess(img).unsqueeze(0)

    with torch.no_grad():
        output = model_mobilenet(input_tensor)
        probs = torch.nn.functional.softmax(output, dim=1)
        topk_res = torch.topk(probs, top_k)

    results = []
    for idx, score in zip(topk_res.indices[0], topk_res.values[0]):
        results.append({"label": CLASS_NAMES[idx], "score": float(score)})

    return results