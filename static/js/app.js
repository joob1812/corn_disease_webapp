document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageInput = document.getElementById('imageInput');
    const previewImage = document.getElementById('previewImage');
    const resultContainer = document.getElementById('resultContainer');
    const diseaseName = document.getElementById('diseaseName');
    const confidence = document.getElementById('confidence');
    const diseaseInfo = document.getElementById('diseaseInfo');
    const probabilitiesList = document.getElementById('probabilitiesList');
    const startCameraBtn = document.getElementById('startCamera');
    const liveCamera = document.getElementById('liveCamera');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('captureBtn');

    // Gestion du formulaire d'upload
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (imageInput.files.length === 0) {
            alert('Veuillez sélectionner une image');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', imageInput.files[0]);
        
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            previewImage.src = data.image_url;
            diseaseName.textContent = data.top_prediction;
            confidence.textContent = (data.confidence * 100).toFixed(2) + '%';
            diseaseInfo.innerHTML = data.disease_info;
            
            // Afficher toutes les probabilités
            probabilitiesList.innerHTML = '';
            for (const [disease, prob] of Object.entries(data.predictions)) {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    ${disease}
                    <span class="badge bg-primary rounded-pill">${(prob * 100).toFixed(2)}%</span>
                `;
                probabilitiesList.appendChild(li);
            }
            
            resultContainer.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Une erreur est survenue lors de l\'analyse de l\'image');
        });
    });

    // Gestion de la caméra
    startCameraBtn.addEventListener('click', function() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(stream) {
                    liveCamera.srcObject = stream;
                    liveCamera.style.display = 'block';
                    startCameraBtn.style.display = 'none';
                    
                    // Activer le bouton de capture
                    captureBtn.style.display = 'block';
                    captureBtn.addEventListener('click', function() {
                        canvas.width = liveCamera.videoWidth;
                        canvas.height = liveCamera.videoHeight;
                        canvas.getContext('2d').drawImage(liveCamera, 0, 0);
                        
                        // Convertir en blob et l'envoyer
                        canvas.toBlob(function(blob) {
                            const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
                            const dataTransfer = new DataTransfer();
                            dataTransfer.items.add(file);
                            imageInput.files = dataTransfer.files;
                            
                            // Simuler le submit
                            uploadForm.dispatchEvent(new Event('submit'));
                        }, 'image/jpeg', 0.95);
                    });
                })
                .catch(function(error) {
                    console.error('Erreur caméra:', error);
                    alert('Impossible d\'accéder à la caméra');
                });
        } else {
            alert('Votre navigateur ne supporte pas l\'accès à la caméra');
        }
    });
});