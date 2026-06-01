from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from services.user_service import UserService

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

def get_user_service():
    from ai.face_recognizer import FaceRecognizer
    from services.user_service import UserService
    return UserService(FaceRecognizer())

# Trusted user functionality removed as per requirements
