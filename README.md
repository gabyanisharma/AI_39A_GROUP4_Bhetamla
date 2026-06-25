# Bhetamla (भेटौंला) 🤝

**Bhetamla** (Nepali for *"Let's Meet"*) is a modern, feature-rich Meetup Planning, Location Discovery, and Coordination web application designed to help friends plan outings, split fares, and stay safe in the Kathmandu Valley.

---

## 🚀 Key Features

### 📅 Meetup Planner & Scheduler
*   **Coordinate Events:** Create meetups, invite friends, and coordinate dates/times with an interactive calendar sync.
*   **Smart Location Discovery:** Find and save popular restaurants and trending hangout spots in Kathmandu.
*   **Dynamic Preference Matching:** Tailor venue suggestions based on attendees' budget, cuisine, and transport preferences.
*   **Democratic Voting:** Cast votes on proposed meetup locations to reach a group consensus.

### 🚗 Transit & Ride Cost Estimator
*   **Fare Estimation:** Estimate transit fare costs across Kathmandu based on distance and route.
*   **Peak Indicators:** View peak-hour fare surge indicators and normal-hour fare rates.
*   **Waypoint Route Planning:** Map routes with multiple stops using the visual route planner.

### 💬 Social & Group Features
*   **Group Chats:** Chat in real-time with group members directly in the meetup workspace.
*   **Meetup Galleries:** Share and upload photos from your meetups.
*   **Gamified Achievements:** Unlock badges and achievements for planning meetups and exploring new places.

### 🛡️ Safety Hub (SOS)
*   **Emergency Contacts:** Add trusted contacts with defined relationships (friends, family, etc.).
*   **Quick SOS Trigger:** Instantly trigger alert messages and share your location during emergencies.

### 🔔 Smart Notifications
*   **Fare Alerts:** Set up automated alarms to notify you when transit fares drop below a set threshold.
*   **Multi-language Support:** Easily toggle the application interface between English (`en`) and Nepali (`np`).

---

## 🛠️ Technology Stack

*   **Backend:** Python, Flask, Flask-SocketIO
*   **Database:** MySQL / SQLite
*   **Frontend:** Vanilla JS, CSS (Custom Styles & Animations), HTML5
*   **Integrations:** Google Calendar OAuth 2.0, Geolocation & Routing API

---

## ⚙️ Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/gabyanisharma/AI_39A_GROUP4_Bhetamla.git
    cd AI_39A_GROUP4_Bhetamla
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up the Environment:**
    *   Copy `.env.example` to `.env` and fill in the database credentials, secret keys, and API tokens.

5.  **Initialize the Database:**
    ```bash
    python -c "from app.database import initialize_db; initialize_db()"
    ```

6.  **Run the Application:**
    ```bash
    python run.py
    ```
