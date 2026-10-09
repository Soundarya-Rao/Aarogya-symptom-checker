"""
Aarogya — Indian Public Health Symptom Triage
A calm, accessible, native Streamlit triage interface powered by Gemini 3.5 Flash-Lite.
"""

import time
import pandas as pd
import streamlit as st

import db
import emergency_data
from llm_client import assess_symptoms, RateLimitError, LLMError

# Initialize persistence
db.init_db()

LANGUAGES = {
    "English": "English",
    "हिंदी (Hindi)": "Hindi",
    "ಕನ್ನಡ (Kannada)": "Kannada",
    "தமிழ் (Tamil)": "Tamil",
    "తెలుగు (Telugu)": "Telugu",
    "മലയാളം (Malayalam)": "Malayalam",
    "मराठी (Marathi)": "Marathi",
    "বাংলা (Bengali)": "Bengali",
}

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu & Kashmir", "Ladakh", "Puducherry",
    "Chandigarh", "Andaman & Nicobar Islands", "Lakshadweep",
]

# Static translation dictionary for quick-example symptom buttons across all 8 supported languages
EXAMPLE_SCENARIOS = {
    "English": [
        {
            "label": "🚨 Severe chest pain & breathlessness",
            "description": "I have severe chest pain radiating down my left arm and breathlessness for 30 minutes",
            "help": "Example of an emergency scenario (RED)",
        },
        {
            "label": "🤒 High fever & persistent cough for 3 days",
            "description": "I have had a fever of 102F and a persistent cough with yellow mucus for 3 days",
            "help": "Example of a condition requiring a doctor visit (YELLOW)",
        },
        {
            "label": "🤕 Mild headache & tiredness since morning",
            "description": "I have a mild headache and feel a bit tired since this morning",
            "help": "Example of a mild condition manageable at home (GREEN)",
        },
        {
            "label": "🤢 Severe stomach pain & vomiting today",
            "description": "My stomach has been hurting badly and I have vomited twice today",
            "help": "Example of acute discomfort needing evaluation (YELLOW)",
        },
    ],
    "Hindi": [
        {
            "label": "🚨 सीने में तेज दर्द और सांस लेने में तकलीफ",
            "description": "मेरे सीने में तेज दर्द है जो बाएं हाथ में फैल रहा है और 30 मिनट से सांस लेने में तकलीफ हो रही है",
            "help": "आपातकालीन स्थिति का उदाहरण (RED)",
        },
        {
            "label": "🤒 3 दिनों से तेज बुखार और लगातार खांसी",
            "description": "मुझे 3 दिनों से 102°F बुखार है और पीले बलगम के साथ लगातार खांसी आ रही है",
            "help": "डॉक्टर को दिखाने की आवश्यकता वाली स्थिति (YELLOW)",
        },
        {
            "label": "🤕 सुबह से हल्का सिरदर्द और थकान",
            "description": "मुझे आज सुबह से हल्का सिरदर्द है और थोड़ा थका हुआ महसूस कर रहा हूँ",
            "help": "घर पर देखभाल योग्य हल्की स्थिति (GREEN)",
        },
        {
            "label": "🤢 आज पेट में तेज दर्द और उल्टी",
            "description": "मेरे पेट में बहुत तेज दर्द हो रहा है और आज दो बार उल्टी हुई है",
            "help": "डॉक्टरी जांच की आवश्यकता वाला पेट दर्द (YELLOW)",
        },
    ],
    "Kannada": [
        {
            "label": "🚨 ತೀವ್ರ ಎದೆ ನೋವು ಮತ್ತು ಉಸಿರಾಟದ ತೊಂದರೆ",
            "description": "ನನಗೆ ಎಡಗೈಗೆ ಹರಡುವ ತೀವ್ರ ಎದೆ ನೋವಿದೆ ಮತ್ತು 30 ನಿಮಿಷಗಳಿಂದ ಉಸಿರಾಟದ ತೊಂದರೆಯಾಗಿದೆ",
            "help": "ತುರ್ತು ಪರಿಸ್ಥಿತಿಯ ಉದಾಹರಣೆ (RED)",
        },
        {
            "label": "🤒 3 ದಿನಗಳಿಂದ ತೀವ್ರ ಜ್ವರ ಮತ್ತು ನಿರಂತರ ಕೆಮ್ಮು",
            "description": "ನನಗೆ 3 ದಿನಗಳಿಂದ 102°F ಜ್ವರ ಮತ್ತು ಹಳದಿ ಕಫದೊಂದಿಗೆ ನಿರಂತರ ಕೆಮ್ಮು ಇದೆ",
            "help": "ವೈದ್ಯರನ್ನು ಭೇಟಿ ಮಾಡಬೇಕಾದ ಪರಿಸ್ಥಿತಿ (YELLOW)",
        },
        {
            "label": "🤕 ಬೆಳಗಿನಿಂದ ಸೌಮ್ಯ ತಲೆನೋವು ಮತ್ತು ಆಯಾಸ",
            "description": "ನನಗೆ ಇಂದು ಬೆಳಗಿನಿಂದ ಸ್ವಲ್ಪ ತಲೆನೋವು ಮತ್ತು ಆಯಾಸದ ಭಾವನೆ ಇದೆ",
            "help": "ಮನೆಯಲ್ಲೇ ನಿರ್ವಹಿಸಬಹುದಾದ ಸೌಮ್ಯ ಪರಿಸ್ಥಿತಿ (GREEN)",
        },
        {
            "label": "🤢 ಇಂದು ತೀವ್ರ ಹೊಟ್ಟೆ ನೋವು ಮತ್ತು ವಾಂತಿ",
            "description": "ನನ್ನ ಹೊಟ್ಟೆ ತುಂಬಾ ನೋಯುತ್ತಿದೆ ಮತ್ತು ಇಂದು ಎರಡು ಬಾರಿ ವಾಂತಿಯಾಗಿದೆ",
            "help": "ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನದ ಅಗತ್ಯವಿರುವ ಪರಿಸ್ಥಿತಿ (YELLOW)",
        },
    ],
    "Tamil": [
        {
            "label": "🚨 கடுமையான நெஞ்சு வலி & மூச்சுத்திணறல்",
            "description": "எனக்கு இடது கையில் பரவும் கடுமையான நெஞ்சு வலியும் 30 நிமிடங்களாக மூச்சுத்திணறலும் உள்ளது",
            "help": "அவசர சிகிச்சை தேவைப்படும் சூழ்நிலை (RED)",
        },
        {
            "label": "🤒 3 நாட்களாக அதிக காய்ச்சல் & தொடர் இருமல்",
            "description": "எனக்கு 3 நாட்களாக 102°F காய்ச்சலும் மஞ்சள் சளியுடன் தொடர் இருமலும் உள்ளது",
            "help": "மருத்துவரை அணுக வேண்டிய சூழ்நிலை (YELLOW)",
        },
        {
            "label": "🤕 காலையிலிருந்து லேசான தலைவலி & சோர்வு",
            "description": "எனக்கு இன்று காலையிலிருந்து லேசான தலைவலியும் சோர்வாகவும் உள்ளது",
            "help": "வீட்டிலேயே ஓய்வெடுக்கக்கூடிய லேசான நிலை (GREEN)",
        },
        {
            "label": "🤢 இன்று கடுமையான வயிற்று வலி & வாந்தி",
            "description": "எனக்கு வயிறு கடுமையாக வலிக்கிறது, இன்று இரண்டு முறை வாந்தி எடுத்தேன்",
            "help": "மருத்துவ பரிசோதனை தேவைப்படும் வயிற்று வலி (YELLOW)",
        },
    ],
    "Telugu": [
        {
            "label": "🚨 తీవ్రమైన ఛాతీ నొప్పి & శ్వాస తీసుకోవడంలో ఇబ్బంది",
            "description": "నాకు ఎడమ చేతికి వ్యాపించే తీవ్రమైన ఛాతీ నొప్పి మరియు 30 నిమిషాలుగా శ్వాస తీసుకోవడంలో ఇబ్బంది ఉంది",
            "help": "అత్యవసర పరిస్థితికి ఉదాహరణ (RED)",
        },
        {
            "label": "🤒 3 రోజులుగా తీవ్ర జ్వరం & నిరంతర దగ్గు",
            "description": "నాకు 3 రోజులుగా 102°F జ్వరం మరియు పసుపు కఫంతో నిరంతర దగ్గు ఉంది",
            "help": "వైద్యుడిని సంప్రదించాల్సిన పరిస్థితి (YELLOW)",
        },
        {
            "label": "🤕 ఉదయం నుండి స్వల్ప తలనొప్పి & అలసట",
            "description": "నాకు ఈ ఉదయం నుండి స్వల్పంగా తలనొప్పి మరియు అలసటగా ఉంది",
            "help": "ఇంట్లోనే విశ్రాంతితో తగ్గే తేలికపాటి పరిస్థితి (GREEN)",
        },
        {
            "label": "🤢 ఈరోజు తీవ్రమైన కడుపు నొప్పి & వాంతులు",
            "description": "నాకు కడుపు తీవ్రంగా నొప్పిగా ఉంది మరియు ఈరోజు రెండుసార్లు వాంతులు అయ్యాయి",
            "help": "వైద్య పరీక్ష అవసరమయ్యే పరిస్థితి (YELLOW)",
        },
    ],
    "Malayalam": [
        {
            "label": "🚨 കഠിനമായ നെഞ്ചുവേദനയും ശ്വാസതടസ്സവും",
            "description": "എനിക്ക് ഇടതുകൈയിലേക്ക് പടരുന്ന കഠിനമായ നെഞ്ചുവേദനയും 30 മിനിറ്റായി ശ്വാസതടസ്സവുമുണ്ട്",
            "help": "അടിയന്തര സാഹചര്യത്തിൻ്റെ ഉദാഹരണം (RED)",
        },
        {
            "label": "🤒 3 ദിവസമായി കടുത്ത പനിയും വിട്ടുമാറാത്ത ചുമയും",
            "description": "എനിക്ക് 3 ദിവസമായി 102°F പനിയും മഞ്ഞ കഫത്തോടെയുള്ള വിട്ടുമാറാത്ത ചുമയുമുണ്ട്",
            "help": "ഡോക്ടറെ കാണേണ്ട അവസ്ഥ (YELLOW)",
        },
        {
            "label": "🤕 രാവിലെയോടെ ചെറിയ തലവേദനയും ക്ഷീണവും",
            "description": "എനിക്ക് ഇന്ന് രാവിലെ മുതൽ ചെറിയ തലവേദനയും ക്ഷീണവും അനുഭവപ്പെടുന്നു",
            "help": "വീട്ടിലിരുന്ന് നിയന്ത്രിക്കാവുന്ന ചെറിയ അസുഖം (GREEN)",
        },
        {
            "label": "🤢 ഇന്ന് കഠിനമായ വയറുവേദനയും ഛർദ്ദിയും",
            "description": "എനിക്ക് വയറ്റിൽ കഠിനമായ വേദനയുണ്ട്, ഇന്ന് രണ്ടുതവണ ഛർദ്ദിച്ചു",
            "help": "ഡോക്ടറുടെ പരിശോധന ആവശ്യമുള്ള അവസ്ഥ (YELLOW)",
        },
    ],
    "Marathi": [
        {
            "label": "🚨 छातीत तीव्र वेदना आणि श्वास घेण्यास त्रास",
            "description": "माझ्या छातीत डाव्या हाताकडे जाणारी तीव्र वेदना होत असून ३० मिनिटांपासून श्वास घेण्यास त्रास होत आहे",
            "help": "आपत्कालीन परिस्थितीचे उदाहरण (RED)",
        },
        {
            "label": "🤒 ३ दिवसांपासून तीव्र ताप आणि सतत खोकला",
            "description": "मला ३ दिवसांपासून १०२°F ताप असून पिवळ्या कफासह सतत खोकला येत आहे",
            "help": "डॉक्टरांचा सल्ला घेण्याची गरज असलेली स्थिती (YELLOW)",
        },
        {
            "label": "🤕 सकाळपासून हलकी डोकेदुखी आणि थकवा",
            "description": "मला आज सकाळपासून थोडे डोके दुखत असून थकवा जाणवत आहे",
            "help": "घरीच आराम करून बरी होणारी सौम्य स्थिती (GREEN)",
        },
        {
            "label": "🤢 आज पोटात तीव्र दुखणे आणि उलट्या",
            "description": "माझ्या पोटात खूप दुखत असून आज दोनदा उलट्या झाल्या आहेत",
            "help": "वैद्यकीय तपासणीची गरज असलेली स्थिती (YELLOW)",
        },
    ],
    "Bengali": [
        {
            "label": "🚨 বুকে তীব্র ব্যথা এবং শ্বাসকষ্ট",
            "description": "আমার বুকে তীব্র ব্যথা যা বাম হাতে ছড়িয়ে পড়ছে এবং ৩০ মিনিট ধরে শ্বাসকষ্ট হচ্ছে",
            "help": "জরুরি অবস্থার উদাহরণ (RED)",
        },
        {
            "label": "🤒 ৩ দিন ধরে প্রচণ্ড জ্বর এবং ক্রমাগত কাশি",
            "description": "আমার ৩ দিন ধরে ১০২°F জ্বর এবং হলুদ কফসহ ক্রমাগত কাশি হচ্ছে",
            "help": "ডাক্তার দেখানোর প্রয়োজন এমন অবস্থা (YELLOW)",
        },
        {
            "label": "🤕 সকাল থেকে হালকা মাথাব্যথা এবং ক্লান্তি",
            "description": "আমার আজ সকাল থেকে সামান্য মাথাব্যথা এবং কিছুটা ক্লান্তি লাগছে",
            "help": "বাড়িতেই নিরাময়যোগ্য মৃদু সমস্যা (GREEN)",
        },
        {
            "label": "🤢 আজ পেটে তীব্র ব্যথা এবং বমি",
            "description": "আমার পেটে খুব তীব্র ব্যথা করছে এবং আজ দুবার বমি হয়েছে",
            "help": "ডাক্তারি পরীক্ষার প্রয়োজন এমন অবস্থা (YELLOW)",
        },
    ],
}

# Localized input placeholders across all 8 supported languages
INPUT_PLACEHOLDERS = {
    "English": "Describe how you feel in simple words (e.g. where it hurts, how long you have felt this way, and any other symptoms)...",
    "Hindi": "सरल शब्दों में बताएं कि आप कैसा महसूस कर रहे हैं (उदा. दर्द कहाँ है, कितने समय से है, और अन्य लक्षण)...",
    "Kannada": "ನಿಮಗೆ ಹೇಗನಿಸುತ್ತದೆ ಎಂದು ಸರಳ ಪದಗಳಲ್ಲಿ ವಿವರಿಸಿ (ಉದಾ. ಎಲ್ಲಿ ನೋವುಂಟುಮಾಡುತ್ತದೆ, ಎಷ್ಟು ಸಮಯದಿಂದ ಹೀಗಿದೆ)...",
    "Tamil": "உங்கள் அறிகுறிகளை எளிய சொற்களில் விவரிக்கவும் (எ.கா. எங்கு வலிக்கிறது, எவ்வளவு காலமாக உள்ளது)...",
    "Telugu": "మీరు ఎలా భావిస్తున్నారో సాధారణ పదాలలో వివరించండి (ఉదా. ఎక్కడ నొప్పిగా ఉంది, ఎంతకాలంగా ఉంది)...",
    "Malayalam": "നിങ്ങൾക്ക് എന്തു തോന്നുന്നുവെന്ന് ലളിതമായ വാക്കുകളിൽ വിവരിക്കുക (ഉദാ. എവിടെ വേദനിക്കുന്നു, എത്ര നാളായി)...",
    "Marathi": "तुम्हाला कसे वाटते ते सोप्या शब्दांत सांगा (उदा. कुठे दुखत आहे, किती वेळापासून, इतर लक्षणे)...",
    "Bengali": "সহজ কথায় বর্ণনা করুন আপনি কেমন অনুভব করছেন (যেমন কোথায় ব্যথা করছে, কতদিন ধরে এমন হচ্ছে)...",
}

# Static translations for "Check another symptom" button across all 8 supported languages
RESET_BUTTON_LABELS = {
    "English": "🔄 Check another symptom",
    "Hindi": "🔄 Check another symptom / अन्य लक्षण जांचें",
    "Kannada": "🔄 Check another symptom / ಮತ್ತೊಂದು ಲಕ್ಷಣವನ್ನು ಪರಿಶೀಲಿಸಿ",
    "Tamil": "🔄 Check another symptom / மற்றொரு அறிகுறியை சரிபார்க்கவும்",
    "Telugu": "🔄 Check another symptom / మరొక లక్షణాన్ని తనిఖీ చేయండి",
    "Malayalam": "🔄 Check another symptom / മറ്റൊരു രോഗലക്ഷണം പരിശോധിക്കുക",
    "Marathi": "🔄 Check another symptom / दुसरे लक्षण तपासा",
    "Bengali": "🔄 Check another symptom / অন্য উপসর্গ পরীক্ষা করুন",
}

# Page configuration
st.set_page_config(
    page_title="Aarogya — Health Symptom Checker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Visual Polish: Deep Trust Teal (#0C4A60) Design System & Responsive CSS
st.markdown("""
<style>
/* Page Title Typography: bolder & prominent */
h1, [data-testid="stHeading"] h1 {
    color: #0C4A60 !important;
    font-size: 2.35rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 0.2rem !important;
}

/* Institutional top header accent */
header[data-testid="stHeader"] {
    border-bottom: 1px solid #CBD5E1 !important;
    background-color: rgba(240, 244, 246, 0.95) !important;
    backdrop-filter: blur(8px) !important;
}

/* Section Subheaders: Teal Vertical Accent Bar */
h3, [data-testid="stHeading"] h3 {
    color: #0C4A60 !important;
    font-weight: 700 !important;
    font-size: 1.15rem !important;
    border-left: 3.5px solid #0C4A60 !important;
    padding-left: 10px !important;
    margin-top: 0.2rem !important;
    margin-bottom: 0.6rem !important;
    line-height: 1.3 !important;
}

/* Primary "Check My Symptoms" Button */
button[kind="primary"], [data-testid="stBaseButton-primary"] {
    background-color: #0C4A60 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.65rem 1.25rem !important;
    border-radius: 8px !important;
    border: 1px solid #083344 !important;
    box-shadow: 0 2px 6px rgba(12, 74, 96, 0.28) !important;
    letter-spacing: 0.01em !important;
    transition: all 0.18s ease-in-out !important;
}

button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
    background-color: #083344 !important;
    border-color: #041E28 !important;
    box-shadow: 0 4px 14px rgba(12, 74, 96, 0.38) !important;
    transform: translateY(-1px) !important;
}

button[kind="primary"]:active, [data-testid="stBaseButton-primary"]:active {
    transform: translateY(0px) !important;
    box-shadow: 0 1px 3px rgba(12, 74, 96, 0.25) !important;
}

/* Secondary Example & Utility Buttons */
button[kind="secondary"], [data-testid="stBaseButton-secondary"] {
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border-radius: 8px !important;
    font-size: 0.92rem !important;
    transition: all 0.15s ease-in-out !important;
}

button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover {
    border-color: #0C4A60 !important;
    background-color: #F0F9FF !important;
    color: #0C4A60 !important;
    box-shadow: 0 2px 6px rgba(12, 74, 96, 0.12) !important;
}

/* =========================================================================
   CARD CONTAINERS: Crisp pure-white cards on soft teal-tinted background (#F0F4F6)
   ========================================================================= */

/* Common Card Base: Single clean border, rounded corners, subtle elevation */
div.st-key-intake_card,
div[class*="st-key-intake_card"],
div.st-key-examples_card,
div[class*="st-key-examples_card"],
div.st-key-input_card,
div[class*="st-key-input_card"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(12, 74, 96, 0.05) !important;
}

/* Sidebar Card 3: About this service
   Clean left accent bar via inset box-shadow. The outer border remains a uniform
   1px solid #CBD5E1 with border-radius: 10px all around, while the 4px inset shadow
   follows the inner curve seamlessly with ZERO corner collision or seam. */
div.st-key-about_card,
div[class*="st-key-about_card"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    box-shadow: inset 4px 0 0 0 #0C4A60, 0 1px 4px rgba(12, 74, 96, 0.05) !important;
}

/* The About Card itself has the left accent bar, so remove the redundant bar
   from its internal subheader so it reads cleanly as plain title text */
div[class*="st-key-about_card"] h3,
div[class*="st-key-about_card"] [data-testid="stHeading"] h3 {
    border-left: none !important;
    padding-left: 0 !important;
}

/* Subtle separator between bullet list and disclaimer in About Card */
div[class*="st-key-about_card"] [data-testid="stCaptionContainer"] {
    border-top: 1px solid #E2E8F0 !important;
    padding-top: 0.6rem !important;
    margin-top: 0.35rem !important;
    color: #64748B !important;
    line-height: 1.45 !important;
}

/* FLATTEN NESTED BOX CLUTTER:
   Strictly prevent any child element containers from receiving borders, backgrounds,
   or box-shadows. Every card is ONE flat card with plain content inside. */
div[class*="st-key-intake_card"] > div,
div[class*="st-key-examples_card"] > div,
div[class*="st-key-about_card"] > div,
div[class*="st-key-input_card"] > div {
    border: none !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

/* Subtle horizontal divider styling */
hr, [data-testid="stDivider"] {
    border-color: #E2E8F0 !important;
    margin-top: 0.75rem !important;
    margin-bottom: 0.75rem !important;
}

/* Responsive Narrow Screen Reflow */
@media (max-width: 768px) {
    /* Clean vertical stacking on mobile widths */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
        margin-bottom: 0.75rem !important;
    }

    /* Edge margins for mobile devices */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1.25rem !important;
        padding-bottom: 2rem !important;
    }

    /* Responsive headline size */
    h1, [data-testid="stHeading"] h1 {
        font-size: 1.85rem !important;
    }

    /* Emergency buttons full width on small screens */
    [data-testid="stLinkButton"] {
        width: 100% !important;
        margin-bottom: 0.5rem !important;
    }
}
</style>
""", unsafe_allow_html=True)


# Session state initialization for pre-filled example symptoms & scroll
if "symptoms_input" not in st.session_state:
    st.session_state["symptoms_input"] = ""
if "scroll_to_top" not in st.session_state:
    st.session_state["scroll_to_top"] = False

def set_example_symptom(text: str):
    """Callback to pre-fill symptoms input area."""
    st.session_state["symptoms_input"] = text

def reset_assessment():
    """Callback to clear symptom input and trigger scroll back to top on next render."""
    st.session_state["symptoms_input"] = ""
    st.session_state["scroll_to_top"] = True

def format_severity_badge(severity: str) -> str:
    """Formats severity value using Streamlit colored markdown."""
    sev = (severity or "").strip().upper()
    if sev == "RED":
        return ":red[**RED**]"
    elif sev == "YELLOW":
        return ":orange[**YELLOW**]"
    elif sev == "GREEN":
        return ":green[**GREEN**]"
    return f"**{severity}**"


# Institutional Header
st.title("🏥 Aarogya Health Triage")
st.caption(
    "A calm, accessible public-health triage assistant for India · Supports 8 languages · Verified official helplines"
)
st.divider()

# Navigation Tabs
tab_checker, tab_analytics = st.tabs(["Check Symptoms", "Analytics & Insights"])

# ==========================================
# TAB 1: CHECK SYMPTOMS
# ==========================================
with tab_checker:
    # Smoothly scroll back to input on the render immediately following "Check another symptom"
    if st.session_state.get("scroll_to_top"):
        st.session_state["scroll_to_top"] = False
        st.components.v1.html(
            """
            <script>
            (function() {
                function doScroll() {
                    try {
                        const doc = window.parent.document;
                        const main = doc.querySelector('section.stMain, [data-testid="stMain"], .main');
                        if (main) {
                            main.scrollTo({ top: 0, behavior: 'smooth' });
                        }
                        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                    } catch (e) {
                        console.error("Scroll error:", e);
                    }
                }
                doScroll();
                setTimeout(doScroll, 50);
                setTimeout(doScroll, 150);
                setTimeout(doScroll, 300);
            })();
            </script>
            """,
            height=0,
        )

    col_left, col_right = st.columns([1, 1.35], gap="large")

    # ----------------------------------------------------
    # LEFT PANEL: Intake Settings, Scenarios & Trust
    # ----------------------------------------------------
    with col_left:
        with st.container(key="intake_card", border=True):
            st.subheader("Your details")
            
            selected_lang_label = st.selectbox(
                "Choose language / भाषा चुनें",
                options=list(LANGUAGES.keys()),
                index=0,
                help="Select the language you want to read and describe your symptoms in.",
            )
            language_name = LANGUAGES[selected_lang_label]

            selected_state = st.selectbox(
                "Select your state / राज्य चुनें",
                options=INDIAN_STATES,
                index=INDIAN_STATES.index("Karnataka") if "Karnataka" in INDIAN_STATES else 0,
                help="Helpline numbers will be tailored to your state.",
            )

        with st.container(key="examples_card", border=True):
            st.subheader("Example situations")
            st.caption("Tap any situation below to test the triage logic:")

            examples = EXAMPLE_SCENARIOS.get(language_name, EXAMPLE_SCENARIOS["English"])
            for ex in examples:
                st.button(
                    ex["label"],
                    on_click=set_example_symptom,
                    args=(ex["description"],),
                    use_container_width=True,
                    help=ex.get("help", ""),
                )

        with st.container(key="about_card", border=True):
            st.subheader("About this service")
            st.markdown("""
            - **Human-verified helplines:** National numbers (112, 108) and state directories are verified from official sources, never invented by AI.
            - **8 Indian languages:** English, Hindi, Kannada, Tamil, Telugu, Malayalam, Marathi, and Bengali.
            - **Completely private:** We never ask for your name, phone number, or personal identity.
            """)
            st.caption(
                "⚕️ This service provides informational guidance on how quickly to seek medical care. "
                "It does not replace an in-person doctor's examination."
            )

    # ----------------------------------------------------
    # RIGHT PANEL: Symptom Description & Triage Verdict
    # ----------------------------------------------------
    with col_right:
        with st.container(key="input_card", border=True):
            st.subheader("Describe what you are experiencing")
            
            placeholder_text = INPUT_PLACEHOLDERS.get(language_name, INPUT_PLACEHOLDERS["English"])

            symptoms_input = st.text_area(
                "Describe symptoms:",
                key="symptoms_input",
                height=150,
                placeholder=placeholder_text,
                help="Type naturally in your selected language.",
                label_visibility="collapsed",
            )

            evaluate_clicked = st.button(
                "Check My Symptoms",
                use_container_width=True,
                type="primary",
            )

        # ----------------------------------------------------
        # RESULTS SECTION
        # ----------------------------------------------------
        if evaluate_clicked:
            clean_input = symptoms_input.strip()
            if not clean_input:
                st.warning("Please type your symptoms or tap one of the examples on the left first.")
            else:
                try:
                    # Clean native progress indicator
                    with st.status("Evaluating symptoms...", expanded=True) as status_box:
                        st.write(f"Analyzing symptoms in **{language_name}**...")
                        t0 = time.time()
                        
                        assessment = assess_symptoms(clean_input, selected_state, language_name)
                        call_duration = time.time() - t0
                        
                        st.write(f"Clinical analysis completed in **{call_duration:.2f} seconds**.")
                        st.write("Verifying safety checks and clinical guidelines...")
                        st.write(f"Locating official emergency directory for **{selected_state}**...")
                        
                        # Save anonymized record
                        db.log_consultation(
                            state=selected_state,
                            language=language_name,
                            symptom_text_english=assessment.symptoms_in_english or clean_input,
                            severity=assessment.severity,
                            emergency=assessment.emergency,
                        )
                        st.write("Consultation recorded anonymously.")
                        
                        status_box.update(
                            label=f"Triage complete ({call_duration:.2f}s)",
                            state="complete",
                            expanded=False,
                        )

                    # ------------------------------------------------
                    # THE DISTINCTIVE MEMORABLE ELEMENT: Triage Verdict Banner
                    # ------------------------------------------------
                    if assessment.severity == "RED":
                        banner = emergency_data.get_severity_banner("RED", language=language_name)
                        if language_name == "English":
                            banner_text = f"## 🚨 {banner['title']}\n\n{banner['body']}"
                        else:
                            banner_text = f"## 🚨 {banner['title']}\n\n{banner['body']}\n\n---\n**English:** **{banner['en_title']}** — {banner['en_body']}"
                        st.error(banner_text)

                        call_col1, call_col2 = st.columns(2)
                        with call_col1:
                            st.link_button(
                                "Call 112 (Universal Emergency)",
                                "tel:112",
                                use_container_width=True,
                                type="primary",
                            )
                        with call_col2:
                            st.link_button(
                                "Call 108 (Ambulance Service)",
                                "tel:108",
                                use_container_width=True,
                            )

                        # First Aid Steps (Bilingual header)
                        if assessment.first_aid_steps:
                            with st.container(border=True):
                                first_aid_header = emergency_data.get_bilingual_header("first_aid", language_name)
                                st.subheader(f"🩹 {first_aid_header}")
                                for i, step in enumerate(assessment.first_aid_steps, 1):
                                    st.markdown(f"**{i}.** {step}")

                        # Verified State Emergency Directory (Bilingual header & bilingual numbers)
                        with st.container(border=True):
                            em_header = emergency_data.get_bilingual_header("emergency_numbers", language_name, state=selected_state)
                            st.subheader(f"🚑 {em_header}")
                            st.caption("Human-verified official contact numbers:")
                            emergency_dict = emergency_data.get_emergency_numbers(selected_state, language=language_name)
                            
                            ecols = st.columns(2)
                            for idx, (service, num) in enumerate(emergency_dict.items()):
                                with ecols[idx % 2]:
                                    st.markdown(f"• **{service}:** [{num}](tel:{num}) 📞")

                            if not emergency_data.has_state_specific_numbers(selected_state):
                                st.caption(f"ℹ️ {emergency_data.get_state_fallback_note(selected_state, language_name)}")

                    elif assessment.severity == "YELLOW":
                        banner = emergency_data.get_severity_banner("YELLOW", language=language_name)
                        if language_name == "English":
                            banner_text = f"## ⚠️ {banner['title']}\n\n{banner['body']}"
                        else:
                            banner_text = f"## ⚠️ {banner['title']}\n\n{banner['body']}\n\n---\n**English:** **{banner['en_title']}** — {banner['en_body']}"
                        st.warning(banner_text)

                    else:
                        banner = emergency_data.get_severity_banner("GREEN", language=language_name)
                        if language_name == "English":
                            banner_text = f"## ✅ {banner['title']}\n\n{banner['body']}"
                        else:
                            banner_text = f"## ✅ {banner['title']}\n\n{banner['body']}\n\n---\n**English:** **{banner['en_title']}** — {banner['en_body']}"
                        st.success(banner_text)

                    # What you should do advice (Bilingual header)
                    with st.container(border=True):
                        advice_header = emergency_data.get_bilingual_header("advice", language_name)
                        st.subheader(f"💡 {advice_header}")
                        st.write(assessment.what_to_do)

                    # Possible Conditions (Bilingual header)
                    with st.container(border=True):
                        cond_header = emergency_data.get_bilingual_header("possible_conditions", language_name)
                        st.subheader(f"🩺 {cond_header}")
                        st.caption("These are plausible possibilities based on the symptoms described, not a confirmed medical diagnosis:")
                        for cond in assessment.possible_conditions:
                            st.markdown(f"• **{cond}**")

                    # Calm, quiet emergency numbers for YELLOW and GREEN (collapsed by default)
                    if assessment.severity in ("YELLOW", "GREEN"):
                        quiet_em_header = emergency_data.get_bilingual_header("emergency_just_in_case", language_name)
                        with st.expander(f"📞 {quiet_em_header}", expanded=False):
                            st.caption("Human-verified official contact numbers for your state:")
                            emergency_dict = emergency_data.get_emergency_numbers(selected_state, language=language_name)
                            ecols = st.columns(2)
                            for idx, (service, num) in enumerate(emergency_dict.items()):
                                with ecols[idx % 2]:
                                    st.markdown(f"• **{service}:** [{num}](tel:{num})")

                            if not emergency_data.has_state_specific_numbers(selected_state):
                                st.caption(f"ℹ️ {emergency_data.get_state_fallback_note(selected_state, language_name)}")

                    # Collapsible English translation preview for non-English checks
                    if language_name != "English":
                        with st.expander("View English translation of this assessment"):
                            st.markdown(f"**Translated symptoms:** {assessment.symptoms_in_english}")
                            st.markdown(f"**Severity classification:** {format_severity_badge(assessment.severity)} | **Emergency trigger:** **{assessment.emergency}**")

                    # ----------------------------------------------------
                    # Action: Check another symptom (clears input & resets view)
                    # ----------------------------------------------------
                    st.write("")
                    reset_label = RESET_BUTTON_LABELS.get(language_name, RESET_BUTTON_LABELS["English"])
                    st.button(
                        reset_label,
                        key="btn_check_another",
                        use_container_width=True,
                        type="secondary",
                        on_click=reset_assessment,
                        help="Clear current results and start a new symptom check",
                    )


                except RateLimitError as e:
                    wait_time = int(e.retry_delay) if e.retry_delay else 30
                    st.error(f"""
                    ### System is busy right now
                    The service is experiencing high traffic. Please wait approximately **{wait_time} seconds** before submitting again.
                    
                    🚨 **If this is an emergency:** If you have severe chest pain, difficulty breathing, slurred speech, or heavy bleeding, **do not wait** — call **112** or **108** immediately!
                    """)
                except LLMError as e:
                    st.error(f"""
                    ### Connection error
                    Could not reach the server right now. Please check your internet connection and try again shortly.
                    
                    🚨 **If this is an emergency**, please call **112** or **108** directly.
                    """)
                except Exception as e:
                    st.error(f"Something unexpected occurred: {e}. In case of emergency, call 112 immediately.")

    st.divider()
    st.caption(
        "⚕️ **Medical Disclaimer:** Aarogya provides guidance to help you understand urgency and find emergency resources. "
        "It is not a substitute for clinical diagnosis or treatment by a licensed physician. If you are ever uncertain about your condition, seek immediate professional medical attention."
    )


# ==========================================
# TAB 2: ANALYTICS & INSIGHTS (CLEAN NATIVE STREAMLIT)
# ==========================================
with tab_analytics:
    st.subheader("Consultation Trends & Usage")
    st.caption("Real-time consultation metrics, severity distribution, and language usage across India.")

    records = db.fetch_all_consultations()
    if not records:
        st.info("No consultations logged yet. Run a check in the 'Check Symptoms' tab to see analytics.")
    else:
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        total_count = len(df)
        red_count = len(df[df["severity"] == "RED"])
        red_pct = (red_count / total_count * 100) if total_count else 0
        top_lang = df["language"].mode()[0] if not df.empty else "N/A"
        top_state = df["state"].mode()[0] if not df.empty else "N/A"

        # KPI Metrics Row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Consultations", total_count)
        mcol2.metric("Emergency Rate", f"{red_pct:.1f}%", help="Percentage of cases classified as RED")
        mcol3.metric("Top Language", top_lang)
        mcol4.metric("Top State", top_state)

        st.divider()

        # Visualizations Row
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            st.markdown("**Severity Distribution**")
            sev_counts = df["severity"].value_counts().reindex(["GREEN", "YELLOW", "RED"]).fillna(0)
            st.bar_chart(sev_counts)

        with vcol2:
            st.markdown("**Consultations by Language**")
            lang_counts = df["language"].value_counts()
            st.bar_chart(lang_counts)

        st.divider()
        st.markdown("**Recent Consultations (Anonymized)**")

        display_df = df[["timestamp", "state", "language", "severity", "emergency", "symptom_text_english"]].copy()
        display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        display_df.rename(columns={
            "timestamp": "Time (UTC)",
            "state": "State",
            "language": "Language",
            "severity": "Severity",
            "emergency": "Emergency",
            "symptom_text_english": "Symptoms (English Translation)",
        }, inplace=True)

        st.dataframe(display_df, use_container_width=True, hide_index=True)