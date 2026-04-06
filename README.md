# ♻ Smart Waste Management System

A web-based application that helps users identify waste materials using **Deep Learning** and locate nearby **recycling centres** for proper disposal.

## 📌 Project Overview

The **Smart Waste Management System** is designed to promote proper waste segregation and sustainable recycling practices.  
Users can upload an image of waste, and the system classifies it into the appropriate category using a trained **MobileNet deep learning model**.

After identifying the waste type, the system helps users find nearby **recycling centres** using location-based services.

---

## 🚀 Features

- 👤 User Registration and Login
- 🖼 Upload waste images for classification
- 🤖 AI-based waste identification using **MobileNet**
- 📍 Locate nearby recycling centres
- 🗺 Google Maps integration for navigation
- 🗄 Store user and recycling centre details in database
- 🛠 Admin module to manage recycling centre data

---

## 🧠 Technologies Used

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Flask (Python)

### Database
- SQLite

### Machine Learning / AI
- TensorFlow
- MobileNet (CNN Model)

### APIs / Tools
- Google Maps API
- VS Code
- Jupyter Notebook

---

## 📂 Project Modules

### 1. User Module
- Register and login
- Upload waste image
- View predicted waste category
- Search nearby recycling centres

### 2. Admin Module
- Add recycling centres
- Update recycling centres
- Delete recycling centres
- Monitor system usage

### 3. Map & Location Module
- Show nearby recycling centres
- Detect user location
- Provide directions using Google Maps

---

## 🛠 How It Works

1. User registers and logs into the system  
2. User uploads an image of waste material  
3. Flask backend receives the image  
4. The trained **MobileNet model** processes the image  
5. The system predicts the waste category  
6. Nearby recycling centres are retrieved from the database  
7. The results are displayed along with map navigation  

---

## 🧾 Waste Categories

The model is trained to classify waste into categories such as:

- Plastic
- Paper
- Metal
- Glass
- Biological
- Battery
- Trash
- Cardboard
- Shoes
- Clothes

---

## 📊 Dataset Information

- **Dataset Source:** Kaggle Garbage Dataset
- **Number of Classes:** 10
- **Total Images:** 13,348

---

## ⚙ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Abhinaya-Bolishetti/Smart_Waste_Management_System.git
````

### 2. Navigate to the project folder

```bash
cd Smart_Waste_Management_System
```

### 3. Create virtual environment (optional but recommended)

```bash
python -m venv venv
```

### 4. Activate virtual environment

#### On Windows

```bash
venv\Scripts\activate
```

#### On Mac/Linux

```bash
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Flask application

```bash
python app.py
```

### 7. Open in browser

```bash
http://127.0.0.1:5000/
```

---

## 📁 Project Structure

```bash
Smart_Waste_Management_System/
│── static/
│   ├── css/
│   ├── js/
│   └── images/
│
│── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── result.html
│
│── model/
│   └── mobilenet_model.h5
│
│── uploads/
│
│── app.py
│── database.db
│── requirements.txt
│── README.md
```

---

## 🧪 Algorithms Used

* Image Classification Algorithm (**CNN / MobileNet**)
* Waste Centre Filtering Algorithm
* Distance Calculation Algorithm
* Admin CRUD Operations

---

## 📌 Non-Functional Requirements

* **Performance:** Fast waste image classification and quick response
* **Scalability:** Supports future growth in users and data
* **Availability:** Accessible whenever users need it
* **Compatibility:** Works on modern browsers and devices
* **Usability:** Simple and user-friendly interface

---

## 🎯 Advantages

* Helps users identify waste correctly
* Promotes proper waste disposal
* Encourages recycling habits
* Reduces manual effort in finding recycling centres
* Supports environmental sustainability

---

## 📸 Expected Output

* User uploads waste image
* System predicts waste type
* Nearby recycling centres are displayed
* Navigation support is provided through maps

---

## 🔮 Future Enhancements

* Real-time recycling centre updates
* Reward points for eco-friendly disposal
* More accurate waste classification model
* Multi-language support
* Mobile app version

---


## 🌱 Conclusion

The **Smart Waste Management System** provides an intelligent and user-friendly solution for waste identification and disposal guidance.
By combining **Deep Learning**, **Flask**, and **location-based services**, the system helps users classify waste and find nearby recycling centres efficiently.

This project promotes proper waste segregation, supports recycling practices, and contributes to **environmental sustainability**.

---

## ⭐ If you like this project

Give it a **star** on GitHub ⭐
