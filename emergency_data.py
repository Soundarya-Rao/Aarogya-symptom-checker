"""
Verified emergency helpline numbers for India.

Design decision: these are NOT fetched from an LLM. Phone numbers are exactly
the kind of fact a language model can confidently hallucinate, and getting one
wrong here has real safety consequences. National numbers are constant across
all states; only a small set of state-specific helplines vary, and those are
listed explicitly below so they can be verified/updated by a human, not guessed
by a model at request time.

Sources to verify/update against periodically:
- https://www.india.gov.in (National Emergency helplines)
- Respective state government health department pages
"""

NATIONAL_NUMBERS = {
    "All-in-one Emergency": "112",
    "Ambulance": "108",
    "Police": "100",
    "Fire": "101",
    "Women Helpline": "1091",
    "Child Helpline": "1098",
    "Mental Health / Suicide Prevention (KIRAN)": "1800-599-0019",
    "COVID-19 Helpline": "1075",
}

# Only populate this with state-specific numbers you have personally verified.
# Leave a state out entirely if you don't have a confirmed number for it --
# the national numbers above always apply as a fallback, and the UI should
# never silently show an unverified number.
STATE_SPECIFIC_NUMBERS = {
    "Karnataka": {
        "Karnataka State Ambulance (Arogya Kavacha)": "108",
    },
    "Delhi": {
        "Delhi Police Women Helpline": "181",
    },
    # Add more states here only after verifying the number from an official source.
}

# Static translations for emergency service labels across all 8 supported languages
SERVICE_TRANSLATIONS = {
    "All-in-one Emergency": {
        "Hindi": "सभी आपातकाल",
        "Kannada": "ಎಲ್ಲಾ ತುರ್ತು ಸೇವೆಗಳು",
        "Tamil": "அனைத்து அவசர சேவைகள்",
        "Telugu": "అన్ని అత్యవసర సేవలు",
        "Malayalam": "എല്ലാ അടിയന്തര സേവനങ്ങളും",
        "Marathi": "सर्व आपत्कालीन सेवा",
        "Bengali": "সমস্ত জরুরি পরিষেবা",
    },
    "Ambulance": {
        "Hindi": "एम्बुलेंस",
        "Kannada": "ಆಂಬ್ಯುಲೆನ್ಸ್",
        "Tamil": "ஆம்புலன்ஸ்",
        "Telugu": "అంబులెన్స్",
        "Malayalam": "ആംബുലൻസ്",
        "Marathi": "रुग्णवाहिका",
        "Bengali": "অ্যাম্বুলেন্স",
    },
    "Police": {
        "Hindi": "पुलिस",
        "Kannada": "ಪೊಲೀಸ್",
        "Tamil": "காவல்துறை",
        "Telugu": "పోలీస్",
        "Malayalam": "പോലീസ്",
        "Marathi": "पोलीस",
        "Bengali": "পুলিশ",
    },
    "Fire": {
        "Hindi": "दमकल",
        "Kannada": "ಅಗ್ನಿಶಾಮಕ",
        "Tamil": "தீயணைப்பு",
        "Telugu": "అగ్నిమాపక దళం",
        "Malayalam": "ഫയർ ഫോഴ്സ്",
        "Marathi": "अग्निशामक दल",
        "Bengali": "দমকল",
    },
    "Women Helpline": {
        "Hindi": "महिला हेल्पलाइन",
        "Kannada": "ಮಹಿಳಾ ಸಹಾಯವಾಣಿ",
        "Tamil": "பெண்கள் உதவி எண்",
        "Telugu": "మహిళా హెల్ప్‌లైన్",
        "Malayalam": "വനിതാ ഹെൽപ്പ് ലൈൻ",
        "Marathi": "महिला हेल्पलाइन",
        "Bengali": "মহিলা হেল্পলাইন",
    },
    "Child Helpline": {
        "Hindi": "चाइल्ड हेल्पलाइन",
        "Kannada": "ಮಕ್ಕಳ ಸಹಾಯವಾಣಿ",
        "Tamil": "குழந்தைகள் உதவி எண்",
        "Telugu": "చిల్డ్రన్ హెల్ప్‌లైన్",
        "Malayalam": "കുട്ടികളുടെ ഹെൽപ്പ് ലൈൻ",
        "Marathi": "बाल हेल्पलाइन",
        "Bengali": "শিশু হেল্পলাইন",
    },
    "Mental Health / Suicide Prevention (KIRAN)": {
        "Hindi": "मानसिक स्वास्थ्य हेल्पलाइन (किरण)",
        "Kannada": "ಮಾನಸಿಕ ಆರೋಗ್ಯ ಸಹಾಯವಾಣಿ (ಕಿರಣ್)",
        "Tamil": "மனநல உதவி எண் (கிரண்)",
        "Telugu": "మానసిక ఆరోగ్య హెల్ప్‌లైన్ (కిరణ్)",
        "Malayalam": "മാനസികാരോഗ്യ ഹെൽപ്പ് ലൈൻ (കിരൺ)",
        "Marathi": "मानसिक आरोग्य हेल्पलाइन (किरण)",
        "Bengali": "মানসিক স্বাস্থ্য হেল্পলাইন (কিরণ)",
    },
    "COVID-19 Helpline": {
        "Hindi": "कोविड-19 हेल्पलाइन",
        "Kannada": "ಕೋವಿಡ್-19 ಸಹಾಯವಾಣಿ",
        "Tamil": "கோவிட்-19 உதவி எண்",
        "Telugu": "కోవిడ్-19 హెల్ప్‌లైన్",
        "Malayalam": "കോവിഡ്-19 ഹെൽപ്പ് ലൈൻ",
        "Marathi": "कोव्हिड-१९ हेल्पलाइन",
        "Bengali": "কোভিড-১৯ হেল্পলাইন",
    },
    "Karnataka State Ambulance (Arogya Kavacha)": {
        "Hindi": "कर्नाटक राज्य एम्बुलेंस (आरोग्य कवच)",
        "Kannada": "ಕರ್ನಾಟಕ ರಾಜ್ಯ ಆಂಬ್ಯುಲೆನ್ಸ್ (ಆರೋಗ್ಯ ಕವಚ)",
        "Tamil": "கர்நாடக மாநில ஆம்புலன்ஸ் (ஆரோக்ய கவசா)",
        "Telugu": "కర్ణాటక రాష్ట్ర అంబులెన్స్ (ఆరోగ్య కవచ)",
        "Malayalam": "കർണാടക സംസ്ഥാന ആംബുലൻസ് (ആരോഗ്യ കവച)",
        "Marathi": "कर्नाटक राज्य रुग्णवाहिका (आरोग्य कवच)",
        "Bengali": "কর্ণাটক রাজ্য অ্যাম্বুলেন্স (আরোগ্য কবচ)",
    },
    "Delhi Police Women Helpline": {
        "Hindi": "दिल्ली पुलिस महिला हेल्पलाइन",
        "Kannada": "ದೆಹಲಿ ಪೊಲೀಸ್ ಮಹಿಳಾ ಸಹಾಯವಾಣಿ",
        "Tamil": "டெல்லி காவல்துறை பெண்கள் உதவி எண்",
        "Telugu": "ఢిల్లీ పోలీస్ మహిళా హెల్ప్‌లైన్",
        "Malayalam": "ഡൽഹി പോലീസ് വനിതാ ഹെൽപ്പ് ലൈൻ",
        "Marathi": "दिल्ली पोलीस महिला हेल्पलाइन",
        "Bengali": "দিল্লি পুলিশ মহিলা হেল্পলাইন",
    },
}

# Static translations for critical emergency section headers across all 8 supported languages
SECTION_HEADER_TRANSLATIONS = {
    "emergency_numbers": {
        "English": "Verified Emergency Numbers for {state}",
        "Hindi": "{state} के लिए सत्यापित आपातकालीन नंबर",
        "Kannada": "{state} ಗಾಗಿ ಪರಿಶೀಲಿಸಲಾದ ತುರ್ತು ಸಂಖ್ಯೆಗಳು",
        "Tamil": "{state}-க்கான சரிபார்க்கப்பட்ட அவசர உதவி எண்கள்",
        "Telugu": "{state} కోసం ధృవీకరించబడిన అత్యవసర నంబర్లు",
        "Malayalam": "{state}-ലെ സ്ഥിരീകരിച്ച അടിയന്തര നമ്പറുകൾ",
        "Marathi": "{state} साठी पडताळलेले आपत्कालीन क्रमांक",
        "Bengali": "{state}-এর জন্য যাচাইকৃত জরুরি নম্বর",
    },
    "first_aid": {
        "English": "What to do right now while waiting for the ambulance",
        "Hindi": "एम्बुलेंस की प्रतीक्षा करते समय अभी क्या करें",
        "Kannada": "ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗಾಗಿ ಕಾಯುತ್ತಿರುವಾಗ ಈಗ ಏನು ಮಾಡಬೇಕು",
        "Tamil": "ஆம்புலன்ஸிற்காக காத்திருக்கும் போது இப்போது என்ன செய்ய வேண்டும்",
        "Telugu": "అంబులెన్స్ కోసం వేచి ఉన్నప్పుడు ఇప్పుడు ఏమి చేయాలి",
        "Malayalam": "ആംബുലൻസിനായി കാത്തിരിക്കുമ്പോൾ ഇപ്പോൾ എന്തുചെയ്യണം",
        "Marathi": "रुग्णवाहिकेची वाट पाहत असताना आता काय करावे",
        "Bengali": "অ্যাম্বুলেন্সের জন্য অপেক্ষা করার সময় এখন কী করবেন",
    },
    "advice": {
        "English": "Advice for you",
        "Hindi": "आपके लिए सलाह",
        "Kannada": "ನಿಮಗಾಗಿ ಸಲಹೆ",
        "Tamil": "உங்களுக்கான ஆலோசனை",
        "Telugu": "మీ కోసం సలహా",
        "Malayalam": "നിങ്ങൾക്കുള്ള നിർദ്ദേശം",
        "Marathi": "तुमच्यासाठी सल्ला",
        "Bengali": "আপনার জন্য পরামর্শ",
    },
    "possible_conditions": {
        "English": "Possible conditions to discuss with a doctor",
        "Hindi": "डॉक्टर से चर्चा के लिए संभावित स्थितियां",
        "Kannada": "ವೈದ್ಯರೊಂದಿಗೆ ಚರ್ಚಿಸಬಹುದಾದ ಸಂಭಾವ್ಯ ಪರಿಸ್ಥಿತಿಗಳು",
        "Tamil": "மருத்துவரிடம் விவாதிக்க வேண்டிய சாத்தியமான நிலைமைகள்",
        "Telugu": "వైద్యునితో చర్చించాల్సిన సంభావ్య పరిస్థితులు",
        "Malayalam": "ഡോക്ടറുമായി ചർച്ച ചെയ്യേണ്ട സാധ്യമായ അവസ്ഥകൾ",
        "Marathi": "डॉक्टरांशी चर्चा करण्यासाठी संभाव्य परिस्थिती",
        "Bengali": "ডাক্তারের সাথে আলোচনা করার মতো সম্ভাব্য সমস্যা",
    },
    "emergency_just_in_case": {
        "English": "Emergency numbers, just in case",
        "Hindi": "आपातकालीन नंबर, केवल सावधानी के लिए",
        "Kannada": "ತುರ್ತು ಸಂಖ್ಯೆಗಳು, ಮುನ್ನೆಚ್ಚರಿಕೆಯಾಗಿ",
        "Tamil": "அவசர உதவி எண்கள், முன்னெச்சரிக்கையாக",
        "Telugu": "అత్యవసర నంబర్లు, కేవలం ముందుజాగ్రత్తగా",
        "Malayalam": "അടിയന്തര നമ്പറുകൾ, ഒരു മുൻകരുതലിനായി",
        "Marathi": "आपत्कालीन क्रमांक, खबरदारी म्हणून",
        "Bengali": "জরুরি নম্বর, শুধুমাত্র সতর্কতার জন্য",
    },
}

# Static translations for main triage result banners across all 8 supported languages
SEVERITY_BANNERS = {
    "RED": {
        "title": {
            "English": "EMERGENCY: Go to a hospital immediately",
            "Hindi": "आपातकाल: तुरंत अस्पताल जाएं",
            "Kannada": "ತುರ್ತು ಪರಿಸ್ಥಿತಿ: ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ತೆರಳಿ",
            "Tamil": "அவசரநிலை: உடனடியாக மருத்துவமனைக்குச் செல்லவும்",
            "Telugu": "అత్యవసర పరిస్థితి: వెంటనే ఆసుపత్రికి వెళ్లండి",
            "Malayalam": "അടിയന്തരാവസ്ഥ: ഉടൻ ആശുപത്രിയിൽ പോകുക",
            "Marathi": "तातडीची परिस्थिती: लगेच रुग्णालयात जा",
            "Bengali": "জরুরি অবস্থা: অবিলম্বে হাসপাতালে যান",
        },
        "body": {
            "English": "These symptoms indicate a potentially life-threatening situation. **Do not wait.** Please call an ambulance or head to the nearest emergency department right now.",
            "Hindi": "ये लक्षण जीवन के लिए गंभीर खतरा हो सकते हैं। **बिल्कुल प्रतीक्षा न करें।** तुरंत एम्बुलेंस बुलाएं या नजदीकी आपातकालीन विभाग में जाएं।",
            "Kannada": "ಈ ಲಕ್ಷಣಗಳು ಜೀವಕ್ಕೆ ಅಪಾಯಕಾರಿಯಾದ ಪರಿಸ್ಥಿತಿಯನ್ನು ಸೂಚಿಸುತ್ತವೆ. **ತಡಮಾಡಬೇಡಿ.** ತಕ್ಷಣವೇ ಆಂಬ್ಯುಲೆನ್ಸ್ ಕರೆ ಮಾಡಿ ಅಥವಾ ಹತ್ತಿರದ ತುರ್ತು ಚಿಕಿತ್ಸಾ ವಿಭಾಗಕ್ಕೆ ತೆರಳಿ.",
            "Tamil": "இந்த அறிகுறிகள் உயிருக்கு ஆபத்தான நிலையைக் குறிக்கின்றன. **தாமதிக்க வேண்டாம்.** உடனே ஆம்புலன்ஸை அழைக்கவும் அல்லது அவசர சிகிச்சை பிரிவுக்குச் செல்லவும்.",
            "Telugu": "ఈ లక్షణాలు ప్రాణాంతక పరిస్థితిని సూచిస్తున్నాయి. **వేచి ఉండకండి.** వెంటనే అంబులెన్స్‌ను పిలవండి లేదా అత్యవసర విభాగానికి వెళ్లండి.",
            "Malayalam": "ഈ ലക്ഷണങ്ങൾ ജീവന് തന്നെ അപകടകരമായേക്കാവുന്ന അവസ്ഥയെ സൂചിപ്പിക്കുന്നു. **ഒട്ടും വൈകരുത്.** ഉടൻ ആംബുലൻസ് വിളിക്കുകയോ അത്യാഹിത വിഭാഗത്തിൽ എത്തുകയോ ചെയ്യുക.",
            "Marathi": "ही लक्षणे संभाव्य जीवघेणी परिस्थिती दर्शवतात. **वाट पाहू नका.** त्वरित रुग्णवाहिका बोलवा किंवा जवळच्या आपत्कालीन विभागात जा.",
            "Bengali": "এই লক্ষণগুলি প্রাণঘাতী পরিস্থিতি নির্দেশ করে। **অপেক্ষা করবেন না।** অবিলম্বে একটি অ্যাম্বুলেন্স ডাকুন বা নিকটস্থ জরুরি বিভাগে যান।",
        },
    },
    "YELLOW": {
        "title": {
            "English": "Doctor consultation advised today",
            "Hindi": "आज ही डॉक्टर से परामर्श लें",
            "Kannada": "ಇಂದೇ ವೈದ್ಯರ ಸಲಹೆ ಪಡೆಯಿರಿ",
            "Tamil": "இன்றே மருத்துவரை அணுகவும்",
            "Telugu": "ఈరోజే వైద్యుడిని సంప్రదించండి",
            "Malayalam": "ഇന്നുതന്നെ ഡോക്ടറുടെ ഉപദേശം തേടുക",
            "Marathi": "आजच डॉक्टरांचा सल्ला घ्या",
            "Bengali": "আজই ডাক্তারের পরামর্শ নিন",
        },
        "body": {
            "English": "Your symptoms do not look like an immediate life threat, but they need an in-person medical evaluation by a doctor or clinic within 24 hours.",
            "Hindi": "आपके लक्षण तत्काल जानलेवा नहीं लगते, लेकिन 24 घंटे के भीतर डॉक्टर या क्लिनिक में चिकित्सकीय जांच आवश्यक है।",
            "Kannada": "ನಿಮ್ಮ ಲಕ್ಷಣಗಳು ತಕ್ಷಣದ ಪ್ರಾಣಾಪಾಯವಲ್ಲದಿದ್ದರೂ, 24 ಗಂಟೆಗಳ ಒಳಗೆ ವೈದ್ಯರು ಅಥವಾ ಕ್ಲಿನಿಕ್‌ನಲ್ಲಿ ತಪಾಸಣೆ ಮಾಡಿಸಿಕೊಳ್ಳುವುದು ಅಗತ್ಯವಾಗಿದೆ.",
            "Tamil": "உங்கள் அறிகுறிகள் உடனடி உயிருக்கு ஆபத்தானதாகத் தெரியவில்லை, ஆனால் 24 மணி நேரத்திற்குள் மருத்துவர் அல்லது கிளினிக்கில் பரிசோதனை தேவைப்படுகிறது.",
            "Telugu": "మీ లక్షణాలు తక్షణ ప్రాణాంతకం కాకపోవచ్చు, కానీ 24 గంటల్లోపు వైద్యుడి ద్వారా క్లినికల్ పరీక్ష చేయించుకోవడం అవసరం.",
            "Malayalam": "ലക്ഷണങ്ങൾ ഉടനടി ജീവന് ഭീഷണിയല്ലെങ്കിലും 24 മണിക്കൂറിനുള്ളിൽ ഒരു ഡോക്ടറുടെയോ ക്ലിനിക്കിന്റെയോ നേരിട്ടുള്ള പരിശോധന ആവശ്യമാണ്.",
            "Marathi": "तुमची लक्षणे तात्काळ जीवघेणी नसली तरी २४ तासांच्या आत डॉक्टरांकडून किंवा क्लिनिकमध्ये तपासणी करून घेणे आवश्यक आहे.",
            "Bengali": "আপনার লক্ষণগুলি তাৎক্ষণিকভাবে প্রাণঘাতী মনে না হলেও ২৪ ঘণ্টার মধ্যে ডাক্তারের কাছে বা ক্লিনিকে গিয়ে পরীক্ষা করানো প্রয়োজন।",
        },
    },
    "GREEN": {
        "title": {
            "English": "Safe to rest at home",
            "Hindi": "घर पर आराम करना सुरक्षित है",
            "Kannada": "ಮನೆಯಲ್ಲಿ ವಿಶ್ರಾಂತಿ ಪಡೆಯುವುದು ಸುರಕ್ಷಿತ",
            "Tamil": "வீட்டில் ஓய்வெடுப்பது பாதுகாப்பானது",
            "Telugu": "ఇంట్లోనే విశ్రాంతి తీసుకోవడం సురక్షితం",
            "Malayalam": "വീട്ടിൽ വിശ്രമിക്കുന്നത് സുരക്ഷിതമാണ്",
            "Marathi": "घरी आराम करणे सुरक्षित आहे",
            "Bengali": "বাড়িতে বিশ্রাম নেওয়া নিরাপদ",
        },
        "body": {
            "English": "Your symptoms appear mild and manageable at home with rest, hydration, and monitoring. If your condition worsens or new symptoms appear, consult a healthcare provider.",
            "Hindi": "आपके लक्षण हल्के प्रतीत होते हैं और घर पर आराम, पर्याप्त पानी और निगरानी से ठीक हो सकते हैं। यदि स्थिति बिगड़े या नए लक्षण दिखें, तो डॉक्टर से संपर्क करें।",
            "Kannada": "ನಿಮ್ಮ ಲಕ್ಷಣಗಳು ಸೌಮ್ಯವಾಗಿದ್ದು ವಿಶ್ರಾಂತಿ, ನೀರು ಸೇವನೆ ಮತ್ತು ನಿಗಾ ಇಡುವುದರೊಂದಿಗೆ ಮನೆಯಲ್ಲೇ ನಿರ್ವಹಿಸಬಹುದು. ಪರಿಸ್ಥಿತಿ ಬಿಗಡಾಯಿಸಿದರೆ ಅಥವಾ ಹೊಸ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
            "Tamil": "உங்கள் அறிகுறிகள் லேசானவை, ஓய்வு, போதுமான தண்ணீர் குடித்தல் மற்றும் கவனிப்புடன் வீட்டிலேயே குணமடையக்கூடியவை. நிலைமை மோசமடைந்தால் மருத்துவரை அணுகவும்.",
            "Telugu": "మీ లక్షణాలు తేలికపాటివి మరియు విశ్రాంతి, ద్రవ పదార్థాలు తీసుకోవడం మరియు పర్యవేక్షణతో ఇంట్లోనే ఉపశమనం పొందవచ్చు. పరిస్థితి విషమిస్తే వైద్యుడిని సంప్రదించండి.",
            "Malayalam": "ലക്ഷണങ്ങൾ ലഘുവായതാണ്, വിശ്രമം, ധാരാളം വെള്ളം കുടിക്കൽ, നിരീക്ഷണം എന്നിവയിലൂടെ വീട്ടിൽ തന്നെ നിയന്ത്രിക്കാം. അവസ്ഥ വഷളായാൽ ഡോക്ടറെ കാണുക.",
            "Marathi": "तुमची लक्षणे सौम्य असून विश्रांती, पाणी पिणे आणि लक्ष ठेवल्यास घरी बरी होऊ शकतात. त्रास वाढल्यास किंवा नवीन लक्षणे आढळल्यास डॉक्टरांशी संपर्क साधा.",
            "Bengali": "আপনার লক্ষণগুলি মৃদু এবং বাড়িতে বিশ্রাম, প্রচুর জল খাওয়া ও পর্যবেক্ষণের মাধ্যমে যত্ন নেওয়া সম্ভব। অবস্থা আরও খারাপ হলে ডাক্তারের পরামর্শ নিন।",
        },
    },
}


def get_severity_banner(severity: str, language: str = "English") -> dict:
    """
    Returns localized primary title & body, along with English reference title & body.
    """
    sev = (severity or "GREEN").upper().strip()
    sev_data = SEVERITY_BANNERS.get(sev, SEVERITY_BANNERS["GREEN"])
    title_dict = sev_data.get("title", {})
    body_dict = sev_data.get("body", {})

    en_title = title_dict.get("English", "")
    en_body = body_dict.get("English", "")

    loc_title = title_dict.get(language, en_title)
    loc_body = body_dict.get(language, en_body)

    return {
        "title": loc_title,
        "body": loc_body,
        "en_title": en_title,
        "en_body": en_body,
    }



def get_bilingual_header(header_key: str, language: str = "English", **kwargs) -> str:
    """
    Returns a bilingual section header: English alongside the selected language.
    If English is selected, returns only the English header.
    Example for Hindi:
      'What to do right now while waiting for the ambulance / एम्बुलेंस की प्रतीक्षा करते समय अभी क्या करें'
    """
    header_dict = SECTION_HEADER_TRANSLATIONS.get(header_key, {})
    eng_template = header_dict.get("English", "")
    eng_text = eng_template.format(**kwargs) if kwargs else eng_template

    if not language or language == "English":
        return eng_text

    loc_template = header_dict.get(language, "")
    if not loc_template:
        return eng_text

    loc_text = loc_template.format(**kwargs) if kwargs else loc_template
    return f"{eng_text} / {loc_text}"


def get_emergency_numbers(state: str, language: str = "English") -> dict:
    """
    Returns a dict of {service_name: number} for the given state and language.
    Always includes national numbers. Adds state-specific numbers only if
    they have been manually verified and added to STATE_SPECIFIC_NUMBERS.

    When language is not English, service names are displayed bilingually:
    e.g. 'All-in-one Emergency / सभी आपातकाल: 112' so English never disappears.
    """
    base_numbers = dict(NATIONAL_NUMBERS)
    base_numbers.update(STATE_SPECIFIC_NUMBERS.get(state, {}))

    if not language or language == "English":
        return base_numbers

    bilingual_numbers = {}
    for service, number in base_numbers.items():
        translation = SERVICE_TRANSLATIONS.get(service, {}).get(language)
        if translation:
            label = f"{service} / {translation}"
        else:
            label = service
        bilingual_numbers[label] = number
    return bilingual_numbers


def has_state_specific_numbers(state: str) -> bool:
    """
    Returns True if official state-specific helpline numbers have been verified
    and populated in STATE_SPECIFIC_NUMBERS for the given state.
    """
    return bool(STATE_SPECIFIC_NUMBERS.get(state))


STATE_FALLBACK_NOTE_TRANSLATIONS = {
    "English": "State-specific helplines aren't verified for {state} yet — the national numbers above work everywhere in India.",
    "Hindi": "{state} के लिए राज्य-स्तरीय हेल्पलाइन अभी सत्यापित नहीं हैं — ऊपर दिए गए राष्ट्रीय नंबर पूरे भारत में काम करते हैं।",
    "Kannada": "{state} ಗೆ ರಾಜ್ಯ-ನಿರ್ದಿಷ್ಟ ಸಹಾಯವಾಣಿಗಳು ಇನ್ನೂ ಪರಿಶೀಲಿಸಲ್ಪಟ್ಟಿಲ್ಲ — ಮೇಲಿನ ರಾಷ್ಟ್ರೀಯ ಸಂಖ್ಯೆಗಳು ಭಾರತದಾದ್ಯಂತ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ.",
    "Tamil": "{state}-க்கான மாநில அளவிலான உதவி எண்கள் இன்னும் சரிபார்க்கப்படவில்லை — மேலே உள்ள தேசிய எண்கள் இந்தியா முழுவதும் செயல்படுகின்றன.",
    "Telugu": "{state} కోసం రాష్ట్ర-నిర్దిష్ట హెల్ప్‌లైన్‌లు ఇంకా ధృవీకరించబడలేదు — పైన పేర్కొన్న జాతీయ నంబర్లు భారతదేశవ్యాప్తంగా పనిచేస్తాయి.",
    "Malayalam": "{state}-ലെ സംസ്ഥാനതല ഹെൽപ്പ് ലൈനുകൾ ഇതുവരെ സ്ഥിരീകരിച്ചിട്ടില്ല — മുകളിൽ നൽകിയിരിക്കുന്ന ദേശീയ നമ്പറുകൾ ഇന്ത്യയിലുടനീളം ലഭ്യമാണ്.",
    "Marathi": "{state} साठी राज्य-विशिष्ट हेल्पलाइन अद्याप पडताळलेल्या नाहीत — वरील राष्ट्रीय क्रमांक संपूर्ण भारतात कार्य करतात.",
    "Bengali": "{state}-এর জন্য রাজ্য-ভিত্তিক হেল্পলাইন এখনও যাচাই করা হয়নি — উপরের জাতীয় নম্বরগুলি সমগ্র ভারতে কার্যকর।",
}


def get_state_fallback_note(state: str, language: str = "English") -> str:
    """
    Returns a calm, honest, non-alarming bilingual note when a state has
    only national numbers verified.
    If English is selected, returns the English note.
    If another supported language is selected, returns 'English note / Local note'.
    """
    en_text = STATE_FALLBACK_NOTE_TRANSLATIONS["English"].format(state=state)
    if not language or language == "English":
        return en_text

    loc_template = STATE_FALLBACK_NOTE_TRANSLATIONS.get(language)
    if not loc_template:
        return en_text

    loc_text = loc_template.format(state=state)
    return f"{en_text} / {loc_text}"


def format_emergency_numbers(state: str, language: str = "English") -> str:
    """Markdown-formatted string for display in Streamlit."""
    numbers = get_emergency_numbers(state, language=language)
    lines = [f"**{service}:** {number}" for service, number in numbers.items()]
    return "\n\n".join(lines)

