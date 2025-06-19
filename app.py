import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import torch
from efficientnet_pytorch import EfficientNet
from PIL import Image
import torchvision.transforms as transforms
import io
import numpy as np

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Chargement du modèle
class_names = [
    'brown_spot',
    'corn_rust',
    'corn_smut',
    'downy_mildew',
    'grey_leaf_spot',
    'healthy',
    'leaf_blight'
]

model = EfficientNet.from_name('efficientnet-b4', num_classes=len(class_names))
model.load_state_dict(torch.load("models/damage_analysis_best_model.pt", map_location="cpu"))
model.eval()

disease_info = {
    "brown_spot": "Taches brunes dues à *Physoderma maydis*.",
    "corn_rust": "Pustules brun-rouille causées par *Puccinia sorghi*.",
    "corn_smut": "Galles noires dues à *Ustilago maydis*.",
    "downy_mildew": "Feuilles blanchâtres causées par des oomycètes.",
    "grey_leaf_spot": "Taches rectangulaires par *Cercospora zeae-maydis*.",
    "healthy": "Feuille saine, pas de signes de maladie.",
    "leaf_blight": "Taches brun-rouge → dessèchement par *Exserohilum turcicum* ou *Colletotrichum graminicola*."
}

# Transformations pour l'image
def get_transform():
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_image(image):
    transform = get_transform()
    image = transform(image).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        probs, classes = torch.topk(probabilities, len(class_names))
    
    return {class_names[i]: probs[0][i].item() for i in range(len(class_names))}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image = Image.open(filepath).convert('RGB')
        predictions = predict_image(image)
        
        top_prediction = max(predictions.items(), key=lambda x: x[1])
        disease_name = top_prediction[0]
        confidence = top_prediction[1]
        
        return jsonify({
            'image_url': f'/static/uploads/{filename}',
            'predictions': predictions,
            'top_prediction': disease_name,
            'confidence': confidence,
            'disease_info': disease_info.get(disease_name, 'Information non disponible')
        })
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

if __name__ == '__main__':
    app.run(debug=True)