import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Calculate Stress Level Based on Emotion and Daily Routine
def calculate_stress_level(emotion, daily_routine=None):
    """
    Calculates the stress level based on the detected emotion and optional daily routine.
    """
    # Validate emotion input
    valid_emotions = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
    if emotion not in valid_emotions:
        logging.error(f"Invalid emotion: {emotion}")
        raise ValueError(f"Invalid emotion. Expected one of: {valid_emotions}")

    # Emotion-based stress level
    if emotion in ["Angry", "Fear", "Sad"]:
        stress_level = "HIGH"
    elif emotion in ["Neutral"]:
        stress_level = "MEDIUM"
    else:
        stress_level = "LOW"

    # Adjust stress level based on daily routine (if provided)
    if daily_routine:
        if not isinstance(daily_routine, str):
            logging.error("Daily routine must be a string.")
            raise ValueError("Daily routine must be a string.")

        if "work" in daily_routine.lower() and "exercise" not in daily_routine.lower():
            stress_level = "HIGH"
        elif "exercise" in daily_routine.lower() or "sleep" in daily_routine.lower():
            stress_level = "LOW"

    logging.info(f"Calculated stress level: {stress_level}")
    return stress_level

# Get Recommendation Based on Stress Level
def get_recommendation(stress_level):
    """
    Provides a recommendation based on the calculated stress level.
    """
    if stress_level == "HIGH":
        recommendation = (
            "1. Try deep breathing exercises or take a short walk.\n"
            "2. Practice mindfulness or meditation for 10-15 minutes.\n"
            "3. Take regular breaks during work to relax your mind.\n"
            "4. Consider talking to a friend or counselor about your stress."
        )
    elif stress_level == "MEDIUM":
        recommendation = (
            "1. Listen to calming music or nature sounds.\n"
            "2. Ensure you're getting enough sleep (7-8 hours per night).\n"
            "3. Engage in light physical activity like yoga or stretching.\n"
            "4. Maintain a balanced diet and stay hydrated."
        )
    else:
        recommendation = (
            "1. Keep up the good work! Stay consistent with your exercise and sleep routines.\n"
            "2. Practice gratitude by writing down things you're thankful for.\n"
            "3. Engage in hobbies or activities that bring you joy.\n"
            "4. Help others or volunteer to boost your mood."
        )

    logging.info(f"Recommendation for stress level {stress_level}: {recommendation}")
    return recommendation