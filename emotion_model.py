import cv2
import numpy as np
import tensorflow as tf
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Pre-trained Emotion Recognition Model
def load_emotion_model(model_path):
    """
    Loads the pre-trained emotion recognition model from the specified path.
    """
    if not os.path.exists(model_path):
        logging.error(f"Model file not found at: {model_path}")
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    try:
        model = tf.keras.models.load_model(model_path)
        logging.info("Emotion model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Failed to load emotion model: {str(e)}")
        raise Exception(f"Failed to load emotion model: {str(e)}")

# Load Haar Cascade for Face Detection
def load_face_cascade():
    """
    Loads the Haar Cascade classifier for face detection.
    """
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        logging.error(f"Haar Cascade file not found at: {cascade_path}")
        raise FileNotFoundError(f"Haar Cascade file not found at: {cascade_path}")
    return cv2.CascadeClassifier(cascade_path)

# Detect Faces in a Frame
def detect_faces(face_cascade, frame):
    """
    Detects faces in a given frame using the Haar Cascade classifier.
    """
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces, gray_frame

# Preprocess Face for Emotion Analysis
def preprocess_face(face):
    """
    Preprocesses the face image for emotion analysis.
    """
    # Resize to 48x48
    resized_face = cv2.resize(face, (48, 48))
    # Convert to grayscale if not already
    if len(resized_face.shape) == 3:
        resized_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2GRAY)
    # Normalize pixel values to [0, 1]
    normalized_face = resized_face / 255.0
    # Reshape to match model input shape (1, 48, 48, 1)
    reshaped_face = np.reshape(normalized_face, (1, 48, 48, 1))
    return reshaped_face

# Predict Emotion from Preprocessed Face
import numpy as np
import logging

def predict_emotion(emotion_model, face):
    """
    Predicts the emotion from a preprocessed face image.
    """
    emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
    
    predictions = emotion_model.predict(face)[0]  # Get predictions for the first (and only) face
    logging.info(f"Raw predictions: {predictions}")
    
    # Set thresholds
    happy_threshold = 0.5  # Adjust this based on testing
    neutral_threshold = 0.4
    
    # Get the predicted index and confidence
    predicted_index = np.argmax(predictions)
    predicted_emotion = emotion_labels[predicted_index]
    confidence = predictions[predicted_index]
    
    # Apply custom logic for classification
    if predicted_emotion == "Happy" and confidence >= happy_threshold:
        final_emotion = "Happy"
    elif confidence > neutral_threshold:
        final_emotion = "Neutral"
    else:
        final_emotion = "Sad"  # Default fallback for lower confidence levels
    
    logging.info(f"Predicted emotion: {final_emotion} (Confidence: {confidence:.2f})")
    return final_emotion, confidence
