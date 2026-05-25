# app/translations.py

def get_translations(lang="en"):
    translations = {
        "en": {
            "hello": "Hello",
            "login": "Login",
            "register": "Register",
            "dashboard": "Dashboard",
            "logout": "Logout",
            "welcome": "Welcome",
            "meetup": "Meetup",
            "place": "Place",
            "notification": "Notification",
            "plan_meetup": "Plan Meetup",
            "my_groups": "My Groups",
            "saved_places": "Saved Places",
            "safety_hub": "Safety Hub",
            "new_meetup": "New Meetup",
            "settings": "Settings",
            "support": "Support",
            "verified_member": "Verified Member",
            "search": "Search..."
        },
        "np": {
            "hello": "नमस्ते",
            "login": "लगइन",
            "register": "दर्ता",
            "dashboard": "ड्यासबोर्ड",
            "logout": "लगआउट",
            "welcome": "स्वागत छ",
            "meetup": "भेटघाट",
            "place": "स्थान",
            "notification": "सूचना",
            "plan_meetup": "भेटघाट योजना",
            "my_groups": "मेरो समूहहरू",
            "saved_places": "बचत गरिएका स्थानहरू",
            "safety_hub": "सुरक्षा केन्द्र",
            "new_meetup": "नयाँ भेटघाट",
            "settings": "सेटिङहरू",
            "support": "सहयोग",
            "verified_member": "प्रमाणित सदस्य",
            "search": "खोज्नुहोस्..."
        }
    }

    # return dictionary for selected language
    return translations.get(lang, translations["en"])