import firebase_admin
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate('central_news\firebase_keys\newsaxis-e5066-firebase-adminsdk-fbsvc-da54ca9646.json')  # path to your Firebase service account credentials file
firebase_admin.initialize_app(cred)
