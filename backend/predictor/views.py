import joblib
import pandas as pd

from pathlib import Path
from django.conf import settings
from django.shortcuts import render

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from .models import Prediction

from django.utils import timezone


MODEL_PATH = (
    Path(settings.BASE_DIR)
    / "predictor"
    / "ml_models"
    / "medical_no_show_model.pkl"
)

model = joblib.load(MODEL_PATH)

def signup(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            return render(
                request,
                "predictor/signup.html",
                {"error": "Passwords do not match."}
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "predictor/signup.html",
                {"error": "Username already exists."}
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("dashboard")

    return render(request, "predictor/signup.html")

def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        return render(
            request,
            "predictor/login.html",
            {"error": "Invalid username or password."}
        )

    return render(request, "predictor/login.html")

def logout_view(request):

    logout(request)

    return redirect("login")


@login_required
def home(request):

    if request.method == "POST":

        # Patient information
        name = request.POST["name"]
        contact = request.POST["contact"]
        gender = request.POST["gender"]
        age = int(request.POST["age"])
        neighbourhood = request.POST["neighbourhood"]

        # Medical information
        scholarship = int(request.POST["scholarship"])
        hypertension = int(request.POST["hypertension"])
        diabetes = int(request.POST["diabetes"])
        alcoholism = int(request.POST["alcoholism"])
        handicap = int(request.POST["handicap"])
        sms_received = int(request.POST["sms_received"])

        # Appointment information
        scheduled_day = request.POST["scheduled_day"]
        appointment_day = request.POST["appointment_day"]

       
        # feature engineering
     

        scheduled = pd.to_datetime(scheduled_day)
        appointment = pd.to_datetime(appointment_day)

        waiting_days = (appointment - scheduled.normalize()).days

        scheduled_hour = scheduled.hour
        scheduled_day_of_week = scheduled.dayofweek
        appointment_day_of_week = appointment.dayofweek
        appointment_month = appointment.month
        appointment_day_number = appointment.day

        appointment_weekend = int(appointment.dayofweek >= 5)

        same_day_booking = int(waiting_days == 0)

        long_wait = int(waiting_days > 30)

        # V1 history features
        previous_appointments = 0
        previous_no_shows = 0
        previous_attendance = 0
        previous_attendance_rate = 0
        previous_no_show_rate = 0
        days_since_previous_appointment = -1


        # Model input

        input_data = pd.DataFrame([{
            "gender": gender,
            "age": age,
            "neighbourhood": neighbourhood,
            "scholarship": scholarship,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "alcoholism": alcoholism,
            "handicap": handicap,
            "sms_received": sms_received,
            "waiting_days": waiting_days,
            "scheduled_hour": scheduled_hour,
            "scheduled_day_of_week": scheduled_day_of_week,
            "appointment_day_of_week": appointment_day_of_week,
            "appointment_month": appointment_month,
            "appointment_day_number": appointment_day_number,
            "appointment_weekend": appointment_weekend,
            "same_day_booking": same_day_booking,
            "long_wait": long_wait,
            "previous_appointments": previous_appointments,
            "previous_no_shows": previous_no_shows,
            "previous_attendance": previous_attendance,
            "previous_attendance_rate": previous_attendance_rate,
            "previous_no_show_rate": previous_no_show_rate,
            "days_since_previous_appointment": days_since_previous_appointment,
        }])

        # Prediction

        probability = model.predict_proba(input_data)[0][1]

        prediction = int(probability >= 0.5)

        probability_percent = round(probability * 100, 2)

        if probability_percent >= 70:

            risk_level = "High"

            recommendation = (
                "Consider sending an appointment reminder "
                "or confirming the appointment with the patient."
            )

        elif probability_percent >= 40:

            risk_level = "Moderate"

            recommendation = (
                "Consider sending a reminder to the patient "
                "before the appointment."
            )

        else:

            risk_level = "Low"

            recommendation = (
                "The appointment has a relatively low "
                "predicted no-show risk."
            )

        # SAVE PREDICTION

        Prediction.objects.create(
            user=request.user,

            name=name,
            contact=contact,

            age=age,
            gender=gender,
            neighbourhood=neighbourhood,

            scholarship=scholarship,
            hypertension=hypertension,
            diabetes=diabetes,
            alcoholism=alcoholism,
            handicap=handicap,
            sms_received=sms_received,

            scheduled_day=scheduled_day,
            appointment_day=appointment_day,

            probability=probability_percent,
            risk_level=risk_level,
            recommendation=recommendation,
        )

        return render(
            request,
            "predictor/result.html",
            {
                "probability": probability_percent,
                "risk_level": risk_level,
                "recommendation": recommendation,
            }
        )

    return render(request, "predictor/home.html")

@login_required
def dashboard(request):

    predictions = Prediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    today = timezone.localdate()

    todays_appointments = predictions.filter(
        appointment_day=today
    ).order_by("scheduled_day")

    total_predictions = predictions.count()

    high_risk = predictions.filter(
        risk_level="High"
    ).count()

    moderate_risk = predictions.filter(
        risk_level="Moderate"
    ).count()

    low_risk = predictions.filter(
        risk_level="Low"
    ).count()

    if total_predictions > 0:

        average_probability = round(
            sum(p.probability for p in predictions)
            / total_predictions,
            2
        )

    else:

        average_probability = 0

    context = {
        "predictions": predictions[:10],
        "todays_appointments": todays_appointments,

        "total_predictions": total_predictions,

        "high_risk": high_risk,
        "moderate_risk": moderate_risk,
        "low_risk": low_risk,

        "average_probability": average_probability,
    }

    return render(
        request,
        "predictor/dashboard.html",
        context
    )