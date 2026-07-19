// Decorative UI copy only (headings, hero text, tile blurbs, form labels).
// Ported 1:1 from apps/referral-copilot/app.py's STRINGS / UI_COPY / TILE_COPY.
// Safety-critical, evidence, and trust wording is NEVER hardcoded here — it is
// always fetched from the backend's /api/copy, which is a façade over the
// approved translations in src/localization.py. See src/i18n/governed.ts.

export type LangCode = "en" | "hi" | "mr";

export const LANGUAGE_FALLBACK: Record<string, string> = { en: "English", hi: "हिंदी", mr: "मराठी" };

export const STEP_KEYS = ["intake", "confirm", "results"] as const;

interface StringsShape {
  boundary: string;
  steps: string[];
  eyebrow: string;
}

export const STRINGS: Record<LangCode, StringsShape> = {
  en: {
    boundary:
      "aven helps plan access to care — it does not diagnose, prescribe, promise prices, show live availability, or replace emergency care.",
    steps: ["Tell us", "Confirm", "Your plan"],
    eyebrow: "Care Navigation · Evidence-Backed",
  },
  hi: {
    boundary:
      "aven देखभाल तक पहुंच की योजना बनाने में मदद करता है — यह निदान नहीं करता, दवा नहीं लिखता, कीमतों का वादा नहीं करता, लाइव उपलब्धता नहीं दिखाता, और न ही आपातकालीन देखभाल की जगह लेता है।",
    steps: ["बताएं", "पुष्टि करें", "आपकी योजना"],
    eyebrow: "देखभाल मार्गदर्शन · प्रमाण-आधारित",
  },
  mr: {
    boundary:
      "aven काळजी मिळवण्याचे नियोजन करण्यास मदत करते — हे निदान करत नाही, औषध लिहून देत नाही, किमतींचे आश्वासन देत नाही, थेट उपलब्धता दाखवत नाही किंवा आपत्कालीन काळजीची जागा घेत नाही.",
    steps: ["सांगा", "पुष्टी करा", "तुमची योजना"],
    eyebrow: "काळजी मार्गदर्शन · पुरावा-आधारित",
  },
};

interface UiCopyShape {
  hero_tagline: string;
  hero_sub: string;
  scroll_cue: string;
  nav_cta: string;
  marquee: string[];
  statement_kicker: string;
  statement: string;
  about_eyebrow: string;
  about_title: string;
  about_body: string;
  about_points: [string, string][];
  tiles_eyebrow: string;
  tiles_title: string;
  tiles_hint: string;
  switcher_label: string;
  specifics: string;
  location_label: string;
  location_ph: string;
  refill_rx_label: string;
  refill_rx_help: string;
  lab_order_label: string;
  lab_order_options: { yes: string; unsure: string; no: string };
  extra_label: string;
  extra_ph: string;
  prefs: string;
  prefs_why: string;
  urgency_label: string;
  travel_label: string;
  budget_label: string;
  facility_label: string;
  language_label: string;
  submit: string;
  confirm_title: string;
  confirm_edit: string;
  confirm_go: string;
  confirm_summary: string;
  confirm_see_fields: string;
  confirm_caption: string;
  results_title: string;
  scale: Record<string, string>;
}

export const UI_COPY: Record<LangCode, UiCopyShape> = {
  en: {
    hero_tagline: "The right care route — <em>with its receipts.</em>",
    hero_sub: "Describe a care need in plain words. aven plans the next step and shows the evidence behind it.",
    scroll_cue: "Scroll",
    nav_cta: "Explore",
    marquee: [
      "The right route, revealed",
      "Care that comes with its receipts",
      "Honest about the unknowns",
      "Evidence you can see",
    ],
    statement_kicker: "The idea",
    statement:
      'A care need becomes <span class="dim">a clear request, an actionable route,</span> and the proof behind every option.',
    about_eyebrow: "How it works",
    about_title: "Care that comes with its receipts.",
    about_body:
      "Describe a care-access need in plain words. aven turns it into a clear, structured request, then plans an actionable route — showing the evidence behind every option and being honest about what it could not confirm.",
    about_points: [
      ["Say it your way", "Type naturally in English, Hindi, or Marathi. No forms to decode."],
      ["See the proof", "Every option shows what is documented, what conflicts, and what is unknown."],
      ["Plan the next step", "Compare routes by travel and cost, then save a plan to act on."],
    ],
    tiles_eyebrow: "Choose a starting point",
    tiles_title: "What do you need today?",
    tiles_hint: "Each path opens its own form — you can switch between them anytime.",
    switcher_label: "Choose the form for your need",
    specifics: "The specifics",
    location_label: "Where are you starting from?",
    location_ph: "City, district, or pincode",
    refill_rx_label: "I have a current prescription or refill instruction for this medicine",
    refill_rx_help:
      "aven can only plan a refill route when a current prescription is confirmed. We do not change doses or prescribe.",
    lab_order_label: "Has a clinician ordered this test?",
    lab_order_options: { yes: "Yes", unsure: "I am not sure", no: "No" },
    extra_label: "Anything else we should know? (optional)",
    extra_ph: "Example: My doctor said I need a cardiology visit and I cannot travel far.",
    prefs: "Your preferences",
    prefs_why: "Why do we ask this? Travel and budget preferences change route ordering, not care quality.",
    urgency_label: "How soon do you need to act?",
    travel_label: "How far can you travel?",
    budget_label: "How important is minimizing cost?",
    facility_label: "Facility preference",
    language_label: "Preferred language (optional)",
    submit: "Review what aven understood",
    confirm_title: "Please confirm before we plan",
    confirm_edit: "Edit request",
    confirm_go: "Confirm and find routes",
    confirm_summary:
      "You are looking for **{capability}** from **{location}**, **{urgency}**. You prefer **{travel_tolerance} travel burden** and **{facility_preference}** facilities.",
    confirm_see_fields: "See all fields",
    confirm_caption:
      "We use your confirmed request to compare documented facility options. We do not infer price, availability, or eligibility.",
    results_title: "Best next step",
    scale: {},
  },
  hi: {
    hero_tagline: "सही देखभाल मार्ग — <em>प्रमाण के साथ।</em>",
    hero_sub: "अपनी ज़रूरत सरल शब्दों में बताएं। aven अगला कदम तय करता है और उसके पीछे का प्रमाण दिखाता है।",
    scroll_cue: "नीचे देखें",
    nav_cta: "देखें",
    marquee: [
      "सही मार्ग, स्पष्ट रूप से",
      "देखभाल, प्रमाण के साथ",
      "अनिश्चितताओं के बारे में ईमानदार",
      "प्रमाण जो आप देख सकें",
    ],
    statement_kicker: "विचार",
    statement:
      'देखभाल की ज़रूरत बनती है <span class="dim">एक स्पष्ट अनुरोध, एक व्यावहारिक मार्ग,</span> और हर विकल्प के पीछे का प्रमाण।',
    about_eyebrow: "यह कैसे काम करता है",
    about_title: "देखभाल, जो प्रमाण के साथ आती है।",
    about_body:
      "देखभाल तक पहुंच की अपनी ज़रूरत सरल शब्दों में बताएं। aven उसे एक स्पष्ट, संरचित अनुरोध में बदलता है, फिर एक व्यावहारिक मार्ग बनाता है — हर विकल्प के पीछे का प्रमाण दिखाते हुए और जो पुष्टि नहीं हो सकी उसके बारे में ईमानदार रहते हुए।",
    about_points: [
      ["अपने शब्दों में कहें", "अंग्रेज़ी, हिंदी या मराठी में सहज रूप से लिखें। कोई जटिल फ़ॉर्म नहीं।"],
      ["प्रमाण देखें", "हर विकल्प दिखाता है कि क्या प्रलेखित है, क्या विरोधाभासी है, और क्या अज्ञात है।"],
      ["अगला कदम तय करें", "यात्रा और लागत के आधार पर मार्गों की तुलना करें, फिर योजना सहेजें।"],
    ],
    tiles_eyebrow: "शुरुआत चुनें",
    tiles_title: "आज आपको क्या चाहिए?",
    tiles_hint: "हर विकल्प अपना फ़ॉर्म खोलता है — आप कभी भी बदल सकते हैं।",
    switcher_label: "अपनी ज़रूरत के लिए फ़ॉर्म चुनें",
    specifics: "विवरण",
    location_label: "आप कहां से शुरू कर रहे हैं?",
    location_ph: "शहर, ज़िला या पिनकोड",
    refill_rx_label: "मेरे पास इस दवा का मौजूदा पर्चा या दोबारा लेने की सलाह है",
    refill_rx_help:
      "aven दवा दोबारा लेने का मार्ग तभी बना सकता है जब मौजूदा पर्चे की पुष्टि हो। हम खुराक नहीं बदलते और दवा नहीं लिखते।",
    lab_order_label: "क्या किसी चिकित्सक ने यह जांच लिखी है?",
    lab_order_options: { yes: "हां", unsure: "मुझे यकीन नहीं", no: "नहीं" },
    extra_label: "और कुछ जो हमें जानना चाहिए? (वैकल्पिक)",
    extra_ph: "उदाहरण: डॉक्टर ने हृदय रोग विशेषज्ञ से मिलने को कहा है और मैं दूर यात्रा नहीं कर सकता।",
    prefs: "आपकी प्राथमिकताएं",
    prefs_why: "हम यह क्यों पूछते हैं? यात्रा और बजट प्राथमिकताएं मार्गों का क्रम बदलती हैं, देखभाल की गुणवत्ता नहीं।",
    urgency_label: "आपको कितनी जल्दी कार्रवाई करनी है?",
    travel_label: "आप कितनी दूर यात्रा कर सकते हैं?",
    budget_label: "लागत कम करना कितना महत्वपूर्ण है?",
    facility_label: "सुविधा प्राथमिकता",
    language_label: "पसंदीदा भाषा (वैकल्पिक)",
    submit: "देखें aven ने क्या समझा",
    confirm_title: "योजना बनाने से पहले पुष्टि करें",
    confirm_edit: "अनुरोध संपादित करें",
    confirm_go: "पुष्टि करें और मार्ग खोजें",
    confirm_summary:
      "आप खोज रहे हैं **{capability}**, **{location}** से, **{urgency}**। आप **{travel_tolerance} यात्रा भार** और **{facility_preference}** सुविधाएं पसंद करते हैं।",
    confirm_see_fields: "सभी फ़ील्ड देखें",
    confirm_caption:
      "हम आपके पुष्टि किए गए अनुरोध का उपयोग प्रलेखित सुविधा विकल्पों की तुलना करने के लिए करते हैं। हम कीमत, उपलब्धता या पात्रता का अनुमान नहीं लगाते।",
    results_title: "सर्वोत्तम अगला कदम",
    scale: {
      Routine: "सामान्य", Soon: "जल्द", Urgent: "तत्काल",
      Low: "कम", Medium: "मध्यम", High: "अधिक",
      Either: "कोई भी", Public: "सरकारी", Private: "निजी",
    },
  },
  mr: {
    hero_tagline: "योग्य काळजी मार्ग — <em>पुराव्यासह.</em>",
    hero_sub: "तुमची गरज सोप्या शब्दांत सांगा. aven पुढील पाऊल ठरवते आणि त्यामागील पुरावा दाखवते.",
    scroll_cue: "खाली पहा",
    nav_cta: "पहा",
    marquee: [
      "योग्य मार्ग, स्पष्टपणे",
      "काळजी, पुराव्यासह",
      "अनिश्चिततेबद्दल प्रामाणिक",
      "पुरावा जो तुम्ही पाहू शकता",
    ],
    statement_kicker: "कल्पना",
    statement:
      'काळजीची गरज बनते <span class="dim">एक स्पष्ट विनंती, एक कृतीयोग्य मार्ग,</span> आणि प्रत्येक पर्यायामागील पुरावा.',
    about_eyebrow: "हे कसे कार्य करते",
    about_title: "काळजी, जी पुराव्यासह येते.",
    about_body:
      "काळजी मिळवण्याची तुमची गरज सोप्या शब्दांत सांगा. aven ती स्पष्ट, संरचित विनंतीमध्ये बदलते, नंतर कृतीयोग्य मार्ग ठरवते — प्रत्येक पर्यायामागील पुरावा दाखवत आणि ज्याची पुष्टी होऊ शकली नाही त्याबद्दल प्रामाणिक राहत.",
    about_points: [
      ["तुमच्या शब्दांत सांगा", "इंग्रजी, हिंदी किंवा मराठीत सहजपणे लिहा. गुंतागुंतीचे फॉर्म नाहीत."],
      ["पुरावा पहा", "प्रत्येक पर्याय दाखवतो काय नोंदवलेले आहे, काय विसंगत आहे आणि काय अज्ञात आहे."],
      ["पुढील पाऊल ठरवा", "प्रवास आणि खर्चानुसार मार्गांची तुलना करा, नंतर योजना जतन करा."],
    ],
    tiles_eyebrow: "सुरुवात निवडा",
    tiles_title: "आज तुम्हाला काय हवे आहे?",
    tiles_hint: "प्रत्येक पर्याय स्वतःचा फॉर्म उघडतो — तुम्ही कधीही बदलू शकता.",
    switcher_label: "तुमच्या गरजेसाठी फॉर्म निवडा",
    specifics: "तपशील",
    location_label: "तुम्ही कुठून सुरुवात करत आहात?",
    location_ph: "शहर, जिल्हा किंवा पिनकोड",
    refill_rx_label: "माझ्याकडे या औषधाचे सध्याचे प्रिस्क्रिप्शन किंवा पुन्हा घेण्याची सूचना आहे",
    refill_rx_help:
      "सध्याच्या प्रिस्क्रिप्शनची पुष्टी झाल्यावरच aven औषध पुन्हा घेण्याचा मार्ग ठरवू शकते. आम्ही मात्रा बदलत नाही आणि औषध लिहून देत नाही.",
    lab_order_label: "डॉक्टरांनी ही तपासणी सांगितली आहे का?",
    lab_order_options: { yes: "होय", unsure: "मला खात्री नाही", no: "नाही" },
    extra_label: "आणखी काही आम्हाला माहीत असावे? (ऐच्छिक)",
    extra_ph: "उदाहरण: डॉक्टरांनी हृदयरोग तज्ज्ञांकडे जाण्यास सांगितले आहे आणि मी दूर प्रवास करू शकत नाही.",
    prefs: "तुमच्या पसंती",
    prefs_why: "आम्ही हे का विचारतो? प्रवास आणि बजेट पसंती मार्गांचा क्रम बदलतात, काळजीची गुणवत्ता नाही.",
    urgency_label: "तुम्हाला किती लवकर कृती करायची आहे?",
    travel_label: "तुम्ही किती दूर प्रवास करू शकता?",
    budget_label: "खर्च कमी करणे किती महत्त्वाचे आहे?",
    facility_label: "सुविधा पसंती",
    language_label: "पसंतीची भाषा (ऐच्छिक)",
    submit: "aven ने काय समजले ते पहा",
    confirm_title: "नियोजनापूर्वी पुष्टी करा",
    confirm_edit: "विनंती संपादित करा",
    confirm_go: "पुष्टी करा आणि मार्ग शोधा",
    confirm_summary:
      "तुम्ही शोधत आहात **{capability}**, **{location}** येथून, **{urgency}**. तुम्हाला **{travel_tolerance} प्रवास भार** आणि **{facility_preference}** सुविधा हव्या आहेत.",
    confirm_see_fields: "सर्व फील्ड पहा",
    confirm_caption:
      "आम्ही तुमच्या पुष्टी केलेल्या विनंतीचा वापर नोंदणीकृत सुविधा पर्यायांची तुलना करण्यासाठी करतो. आम्ही किंमत, उपलब्धता किंवा पात्रतेचा अंदाज लावत नाही.",
    results_title: "सर्वोत्तम पुढील पाऊल",
    scale: {
      Routine: "नियमित", Soon: "लवकर", Urgent: "तातडीचे",
      Low: "कमी", Medium: "मध्यम", High: "जास्त",
      Either: "कोणतेही", Public: "सरकारी", Private: "खाजगी",
    },
  },
};

export function tx<K extends keyof UiCopyShape>(lang: LangCode, key: K): UiCopyShape[K] {
  return UI_COPY[lang]?.[key] ?? UI_COPY.en[key];
}

export function scaleLabel(lang: LangCode, value: string): string {
  return UI_COPY[lang]?.scale[value] ?? value;
}

export interface FeatureTile {
  key: string;
  icon: string;
  title: string;
  desc: string;
  detail_label: string;
}

export const FEATURE_TILES_EN: FeatureTile[] = [
  { key: "known_referral", icon: "🩺", title: "Referral or procedure", desc: "Plan a route for a specialty visit or procedure your doctor referred.", detail_label: "What did your doctor refer you for?" },
  { key: "refill", icon: "💊", title: "Medication refill", desc: "Find where to refill a prescription or reach a pharmacy.", detail_label: "What medication do you need refilled?" },
  { key: "lab", icon: "🧪", title: "Lab or blood test", desc: "Locate a facility for a test or blood draw your clinician requested.", detail_label: "What test or blood draw was requested?" },
  { key: "vaccination", icon: "💉", title: "Vaccination", desc: "Find where to get a vaccine or routine immunization.", detail_label: "Which vaccine or immunization are you planning for?" },
  { key: "follow_up", icon: "📅", title: "Follow-up question", desc: "Reconnect with a facility or doctor about an appointment.", detail_label: "Which facility or doctor are you trying to reach?" },
  { key: "symptom_first", icon: "🧭", title: "Not sure what I need", desc: "Talk it through and plan a safe next step. This is not a diagnosis.", detail_label: "What is worrying you today?" },
];

const TILE_COPY: Record<Exclude<LangCode, "en">, Record<string, [string, string, string]>> = {
  hi: {
    known_referral: ["रेफरल या प्रक्रिया", "डॉक्टर द्वारा बताई गई विशेषज्ञ जांच या प्रक्रिया के लिए मार्ग बनाएं।", "आपके डॉक्टर ने किसके लिए रेफर किया?"],
    refill: ["दवा दोबारा लेना", "पर्चा दोबारा भरवाने या दवा की दुकान तक पहुंचने की जगह खोजें।", "आपको कौन सी दवा दोबारा चाहिए?"],
    lab: ["लैब या रक्त जांच", "चिकित्सक द्वारा बताई गई जांच या रक्त नमूने के लिए सुविधा खोजें।", "कौन सी जांच या रक्त नमूना बताया गया?"],
    vaccination: ["टीकाकरण", "टीका या नियमित प्रतिरक्षण कहां मिलेगा, यह खोजें।", "आप किस टीके या प्रतिरक्षण की योजना बना रहे हैं?"],
    follow_up: ["अनुवर्ती प्रश्न", "अपॉइंटमेंट के बारे में सुविधा या डॉक्टर से दोबारा संपर्क करें।", "आप किस सुविधा या डॉक्टर तक पहुंचना चाहते हैं?"],
    symptom_first: ["मुझे नहीं पता क्या चाहिए", "बात करें और सुरक्षित अगला कदम तय करें। यह निदान नहीं है।", "आज आपको क्या चिंता है?"],
  },
  mr: {
    known_referral: ["संदर्भ किंवा प्रक्रिया", "डॉक्टरांनी सुचवलेल्या तज्ज्ञ भेटीसाठी किंवा प्रक्रियेसाठी मार्ग ठरवा.", "तुमच्या डॉक्टरांनी कशासाठी संदर्भ दिला?"],
    refill: ["औषध पुन्हा घेणे", "प्रिस्क्रिप्शन पुन्हा भरण्यासाठी किंवा औषधालयापर्यंत पोहोचण्यासाठी जागा शोधा.", "तुम्हाला कोणते औषध पुन्हा हवे आहे?"],
    lab: ["प्रयोगशाळा किंवा रक्त तपासणी", "डॉक्टरांनी सांगितलेल्या तपासणीसाठी किंवा रक्त नमुन्यासाठी सुविधा शोधा.", "कोणती तपासणी किंवा रक्त नमुना सांगितला होता?"],
    vaccination: ["लसीकरण", "लस किंवा नियमित लसीकरण कुठे मिळेल ते शोधा.", "तुम्ही कोणत्या लसीचे नियोजन करत आहात?"],
    follow_up: ["पाठपुरावा प्रश्न", "अपॉइंटमेंटबद्दल सुविधा किंवा डॉक्टरांशी पुन्हा संपर्क साधा.", "तुम्ही कोणत्या सुविधेशी किंवा डॉक्टरांशी संपर्क साधू इच्छिता?"],
    symptom_first: ["मला काय हवे ते माहीत नाही", "चर्चा करा आणि सुरक्षित पुढील पाऊल ठरवा. हे निदान नाही.", "आज तुम्हाला कशाची चिंता आहे?"],
  },
};

export function tileCopy(lang: LangCode, careTask: string): FeatureTile {
  const base = FEATURE_TILES_EN.find((t) => t.key === careTask)!;
  if (lang === "en") return base;
  const translated = TILE_COPY[lang]?.[careTask];
  if (!translated) return base;
  const [title, desc, detail_label] = translated;
  return { ...base, title, desc, detail_label };
}

export const TASK_QUESTIONS: Record<string, string> = {
  known_referral: "What specialty, procedure, or care need did your doctor write down?",
  refill: "What medicine and formulation do you need refilled?",
  lab: "What test or blood draw did your clinician request?",
  vaccination: "Which vaccine or immunization are you planning for?",
  symptom_first: "What is worrying you today? We can help plan a possible next care step, not diagnose it.",
  follow_up: "Which facility or doctor are you trying to reach?",
};

export const CARE_TASKS_EN: Record<string, string> = {
  known_referral: "Referral, specialty, or procedure",
  refill: "Medication refill or pharmacy",
  lab: "Lab test or blood draw",
  vaccination: "Vaccination or immunization",
  symptom_first: "I am not sure what care I need",
  follow_up: "Follow-up or appointment question",
};

export const OPTION_ICONS: Record<string, string> = {
  "Best documented fit": "🥇",
  "Lower-burden route": "🧭",
  "Alternative to verify": "🔍",
};

export const FEEDBACK_OPTIONS: Record<string, string> = {
  "It was helpful": "helpful",
  "Something needs correction": "needs_correction",
  "I am not sure yet": "not_sure",
  "The service was not available": "service_unavailable",
  "The price was different": "price_differed",
  "I went to this facility": "accepted",
  "I did not go": "not_visited",
};
