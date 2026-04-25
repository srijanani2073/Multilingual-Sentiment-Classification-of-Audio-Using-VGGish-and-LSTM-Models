# Multilingual Audio Sentiment Classification using VGGish and LSTM

## Overview
This project implements a multilingual speech emotion recognition (SER) system that classifies emotions from audio signals using a hybrid deep learning architecture. The model combines convolutional neural networks (CNN) with VGGish embeddings, long short-term memory (LSTM) networks for temporal modeling, and a logistic regression meta-classifier in a stacked ensemble framework.

The system is designed to work across multiple languages and achieves high accuracy in emotion classification tasks.

## Key Features
- Multilingual emotion recognition across diverse datasets
- Hybrid architecture combining CNN, LSTM, and ensemble learning
- Advanced audio preprocessing techniques
- Robust feature extraction using MFCC, ZCR, RMSE, and VGGish embeddings
- High classification accuracy (~93.5%)

## Model Architecture
Audio Input  
→ Preprocessing (Noise, Stretch, Shift, Pitch)  
→ Feature Extraction  
   → LSTM (ZCR, RMSE, MFCC)  
   → CNN (VGGish Features)  
→ Stacked Ensemble (Logistic Regression)  
→ Emotion Classification  

## Dataset
The model is trained on multiple benchmark datasets:

- RAVDESS (English): Emotional speech and song dataset  
- EMO-DB (German): Actor-based emotional speech dataset  
- TESS (English): High-quality emotional speech dataset  
- Kannada Dataset (Kannada): Regional emotional dataset  
- BanglaSER (Bengali): Speech emotion dataset  

Emotions classified:
- Anger
- Disgust
- Fear
- Happiness
- Neutral
- Sadness
- Surprise

## Preprocessing Pipeline
- Noise injection for robustness
- Time stretching to preserve temporal information
- Random shifting
- Pitch transformation
- Silence trimming for CNN input

## Feature Extraction

For LSTM:
- Zero Crossing Rate (ZCR)
- Root Mean Square Energy (RMSE)
- Mel Frequency Cepstral Coefficients (MFCC)

For CNN:
- Pretrained VGGish embeddings

## Model Details

LSTM Model:
- Two LSTM layers with 64 units each
- Captures temporal dependencies in audio
- Accuracy: ~83.47%

CNN Model:
- Five convolutional blocks
- Batch normalization and dropout applied
- Accuracy: ~93.33%

Ensemble Model:
- Combines outputs from CNN and LSTM
- Logistic regression as meta-classifier
- Final accuracy: ~93.57%

## Results

- Accuracy: 93%
- Precision: 0.94
- Recall: 0.93
- F1 Score: 0.94
- ROC-AUC: 0.99

The model demonstrates strong performance across all emotion classes and reduces misclassification between similar emotions.


## How to Run

1. Clone the repository

git clone https://github.com/your-username/audio-sentiment-analysis.git

cd audio-sentiment-analysis


2. Install dependencies

pip install -r requirements.txt


3. Run the notebook

jupyter notebook notebooks/final-model.ipynb


## Applications
- Virtual assistants
- Mental health monitoring
- Customer service analytics
- Emotion-aware communication systems

## Limitations
- Sensitive to real-world noise conditions
- Limited to audio modality (no multimodal inputs)
- Performance may vary across accents and cultures

## Future Work
- Integration with transformer-based models
- Multimodal learning (audio + text + visual)
- Real-time deployment optimization
- Expansion to low-resource languages

## Publication
This project is published as a research paper:
"Multilingual Sentiment Classification of Audio Using VGGish and LSTM Models"
DOI: 10.1177/18758967251345859

[Paper](https://doi.org/10.1177/18758967251345859)

## Authors
- Sivapra Baskar Sri Janani    
- Venkatasubramanian Sruthi
- Jeyagopi Sanjana  
- Pandurangan Janarthanan 
