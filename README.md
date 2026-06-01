# 🌾 Farmer Market Price Alert System

## 📌 Overview

The Farmer Market Price Alert System is a Flask-based web application designed to help farmers access market price information and receive timely SMS alerts about commodity prices. The system allows farmers to register their details, view market prices, and receive notifications through Twilio SMS services.

## 🎯 Objectives

* Provide farmers with updated market price information.
* Enable SMS-based price alerts for registered farmers.
* Improve market awareness and decision-making.
* Offer a simple and user-friendly web interface.

## 🚀 Features

* Farmer Registration and Management
* Commodity Price Tracking
* SMS Notifications using Twilio
* Market Information Dashboard
* Scheduled Daily Alerts
* SQLite Database Integration
* Responsive User Interface

## 🛠️ Technologies Used

### Backend

* Python
* Flask

### Database

* SQLite

### Frontend

* HTML
* CSS
* Bootstrap
* JavaScript

### APIs & Services

* Twilio SMS API
* Agmarknet API (Optional)

## 📂 Project Structure

```text
Farmer-Market-Price-System/
│
├── app.py
├── requirements.txt
├── .gitignore
├── .env.example
├── services/
│   ├── sms.py
│   └── market_service.py
│
├── templates/
│   ├── home.html
│   ├── register.html
│   ├── dashboard.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── database.db
```

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/Sateerth/Farmer-Market-Price-System.git
cd Farmer-Market-Price-System
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key

TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

ALERT_HOUR=8
ALERT_MINUTE=0

AGMARKNET_API_KEY=
```

## ▶️ Run the Application

```bash
python app.py
```

The application will start on:

```text
http://127.0.0.1:5000/
```

## 📱 SMS Alert Workflow

1. Farmer registers with a mobile number.
2. Market prices are fetched from the database/API.
3. Scheduled jobs check for updates.
4. Twilio sends SMS alerts to registered farmers.
5. Farmers receive commodity price notifications instantly.

##

## 🔒 Security

* Sensitive credentials are stored in `.env`.
* `.env` is excluded using `.gitignore`.
* Twilio credentials are never committed to GitHub.

## 🌟 Future Enhancements

* Multi-language support.
* AI-based price prediction.
* UPI payment integration.
* Mobile application support.
* Weather forecast integration.
* Voice-based farmer assistance.

## 👨‍💻 Author

**Sateerth Palkar**

GitHub: https://github.com/Sateerth

## 📄 License

This project is developed for educational and learning purposes.
