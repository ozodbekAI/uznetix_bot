"""Text utilities for multilingual support"""


def detect_script(text: str) -> str:
    """
    Detect if text is in latin or cyrillic script
    Returns: 'latin' or 'cyrillic'
    """
    if not text:
        return "latin"
    
    cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    latin_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
    
    return "cyrillic" if cyrillic_chars > latin_chars else "latin"


def convert_to_uzbek_script(text: str, target_script: str) -> str:
    """
    Convert Uzbek text between Latin and Cyrillic scripts.
    
    Args:
        text: Input text
        target_script: 'latin' or 'cyrillic'
    
    Returns:
        Converted text
    """
    if not text:
        return text
    
    # Mapping Latin to Cyrillic
    latin_to_cyr = {
        # Uppercase singles
        'A': 'А', 'B': 'Б', 'D': 'Д', 'E': 'Е', 'F': 'Ф', 'G': 'Г', 'H': 'Ҳ',
        'I': 'И', 'J': 'Ж', 'K': 'К', 'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О',
        'P': 'П', 'Q': 'Қ', 'R': 'Р', 'S': 'С', 'T': 'Т', 'U': 'У', 'V': 'В',
        'X': 'Х', 'Y': 'Й', 'Z': 'З',
        # Uppercase specials (len=2)
        "O'": 'Ў', "G'": 'Ғ', 'Sh': 'Ш', 'Ch': 'Ч', 'Ng': 'Нг',
        # Lowercase singles
        'a': 'а', 'b': 'б', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г', 'h': 'ҳ',
        'i': 'и', 'j': 'ж', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'q': 'қ', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'v': 'в',
        'x': 'х', 'y': 'й', 'z': 'з',
        # Lowercase specials (len=2)
        "o'": 'ў', "g'": 'ғ', 'sh': 'ш', 'ch': 'ч', 'ng': 'нг',
        # Apostrophe
        "ʼ": 'ъ', "'": 'ъ'
    }
    
    # Mapping Cyrillic to Latin
    cyr_to_latin = {v: k for k, v in latin_to_cyr.items()}
    
    current_script = detect_script(text)
    if current_script == target_script:
        return text
    
    # Convert
    if target_script == "cyrillic":
        mapping = latin_to_cyr
        for lat, cyr_char in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(lat, cyr_char)
    else:  # latin
        mapping = cyr_to_latin
        for cyr_char, lat in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(cyr_char, lat)
    
    return text


TEXTS = {
    "welcome": {
        "latin": """Assalomu alaykum{user_name}!

🤖 Men Uznetix Advisor botiman. Sizga O'zbekistonda investitsiya qilishda yordam beraman.

Men sizga:
✅ Maqsadlaringizga mos investitsiya g'oyalarini topaman
✅ Aksiyalar, ETF va boshqa vositalarni tavsiya qilaman  
✅ Oddiy va tushunarli tilda tushuntiraman
✅ Risklar haqida ogohlantiraman""",
        "cyrillic": """Ассалому алайкум{user_name}!

🤖 Мен Uznetix Advisor ботиман. Сизга Ўзбекистонда инвестиция қилишда ёрдам бераман.

Мен сизга:
✅ Мақсадларингизга мос инвестиция ғояларини топаман
✅ Акциялар, ETF ва бошқа воситаларни тавсия қиламан  
✅ Оддий ва тушунарли тилда тушунтираман
✅ Рисклар ҳақида огоҳлантираман"""
    },
    "welcome_uznetix": {
        "latin": """Assalomu alaykum{user_name}!

🤖 Uznetix Advisor botiga xush kelibsiz! Men sizga O'zbekiston bozoridagi eng yaxshi investitsiya imkoniyatlarini topishda yordam beraman.
""",
        "cyrillic": """Ассалому алайкум{user_name}!

🤖 Uznetix Advisor ботга хуш келибсиз! Мен сизга Ўзбекистон бозоридаги энг яхши инвестиция имкониятларини топишда ёрдам бераман.
"""
    },
    "welcome_back_uznetix": {
        "latin": """Xush kelibsiz, {user_name}!

Uznetix Advisor sizni eslayapti. Yangi investitsiya tahlili olishni xohlaysizmi?""",
        "cyrillic": """Хуш келибсиз, {user_name}!

Uznetix Advisor сизни эслаяпти. Янги инвестиция таҳлили олишни хоҳлайсизми?"""
    },
    "verification_success_uznetix": {
        "latin": """✅ Uznetix mijozingiz tasdiqlandi!

Endi to'liq funksiyalardan foydalanishingiz mumkin. Keling, shaxsiy investitsiya profilingizni yaratamiz!""",
        "cyrillic": """✅ Uznetix мижозингиз тасдиқланди!

Энди тўлиқ функциялардан фойдаланишингиз мумкин. Келинг, шахсий инвестиция профилингизни яратамиз!"""
    },
    "interview_start_uznetix": {
        "latin": """🎯 Uznetix Advisor suhbati boshlandi!

Sizning maqsadlaringiz, byudjetingiz va risk darajangizni aniqlash uchun bir nechta savol beraman. Javoblaringiz asosida eng mos aksiya va ETF tavsiyalarini beraman.""",
        "cyrillic": """🎯 Uznetix Advisor суҳбати бошланди!

Сизнинг мақсадларингиз, бюджетингиз ва риск даражангизни аниқлаш учун бир нечта савол бераман. Жавобларингиз асосида энг мос акция ва ETF тавсияларини бераман."""
    },
    "interview_response_prefix": {
        "latin": "Tushundim! Keyingi savol:",
        "cyrillic": "Тушундим! Кейинги савол:"
    },
    "interview_complete_uznetix": {
        "latin": """✅ Suhbat yakunlandi! Rahmat ishtirokingiz uchun.

Endi sizning profilingizga mos Uznetix bo'yicha eng yaxshi investitsiya g'oyalarini tayyorlayapman...""",
        "cyrillic": """✅ Суҳбат яқунланди! Раҳмат иштирокингиз учун.

Энди сизнинг профилингизга мос Uznetix бўйича энг яхши инвестиция ғояларини тайёрлаяпман..."""
    },
    "interview_cancelled_uznetix": {
        "latin": """❌ Suhbat bekor qilindi.

Uznetix Advisor asosiy menyusiga qaytdingiz. Har qanday vaqtda yangi suhbat boshlashingiz mumkin!""",
        "cyrillic": """❌ Суҳбат бекор қилинди.

Uznetix Advisor асосий менюсига қайтдингиз. Ҳар қандай вақтда янги суҳбат бошлашингиз мумкин!"""
    },
    "clarification_start": {
        "latin": "Iltimos, 'boshladik' yoki 'boshlash' deb yozing.",
        "cyrillic": "Илтимос, 'бошладик' ёки 'бошлаш' деб ёзинг."
    },
    
    "welcome_back": {
        "latin": """Xush kelibsiz{user_name}! 

Men sizni eslayapman. Yangi investitsiya tavsiyasi olmoqchimisiz?""",
        "cyrillic": """Хуш келибсиз{user_name}!

Мен сизни эслаяпман. Янги инвестиция тавсияси олмоқчимисиз?"""
    },
    
    "disclaimer": {
        "latin": """⚠️ MUHIM:
Bu tavsiyalar faqat ma'lumot uchun. Men moliyaviy maslahatchi emasman. Har qanday investitsiya o'zingiz mas'uliyatida!""",
        "cyrillic": """⚠️ МУҲИМ:
Бу тавсиялар фақат маълумот учун. Мен молиявий маслаҳатчи эмасман. Ҳар қандай инвестиция ўзингиз масъулиятида!"""
    },
    
    "verification_prompt": {
        "latin": """✉️ Uznetix mijozi ekanligingizni tasdiqlash uchun GetCourse'dagi emailingizni yuboring.

Masalan: example@gmail.com""",
        "cyrillic": """✉️ Uznetix мижози эканлигингизни тасдиқлаш учун GetCourse'даги emailингизни юборинг.

Масалан: example@gmail.com"""
    },
    
    "checking_access": {
        "latin": "⏳ Tekshiryapman...",
        "cyrillic": "⏳ Текшираяпман..."
    },
    
    "verification_success": {
        "latin": """✅ Tasdiqlandi!

Endi siz botdan foydalanishingiz mumkin. Keling, investitsiya rejangizni tuzamiz!""",
        "cyrillic": """✅ Тасдиқланди!

Энди сиз ботдан фойдаланишингиз мумкин. Келинг, инвестиция режангизни тузамиз!"""
    },
    
    "verification_failed": {
        "latin": """❌ Kechirasiz, sizni Uznetix mijozi sifatida topa olmadim.

Iltimos, to'g'ri emailni kiriting yoki Uznetix.com saytidan kursga yoziling.""",
        "cyrillic": """❌ Кечирасиз, сизни Uznetix мижози сифатида топа олмадим.

Илтимос, тўғри emailни киритинг ёки Uznetix.com сайтидан курсга ёзилинг."""
    },
    
    "verification_required": {
        "latin": "Botdan foydalanish uchun tasdiqlash majburiy!",
        "cyrillic": "Ботдан фойдаланиш учун тасдиқлаш мажбурий!"
    },
    
    "invalid_email": {
        "latin": "❌ Email noto'g'ri ko'rinadi. Qaytadan kiriting.",
        "cyrillic": "❌ Email нотўғри кўринади. Қайтадан киритинг."
    },
    
    "interview_start": {
        "latin": """🎯 Ajoyib! Men sizga eng mos investitsiya g'oyalarini topish uchun bir nechta savol beraman.

Savollarga oddiy, o'z so'zlaringiz bilan javob bering. Bu 2-3 daqiqa oladi.

Birinchi savol:""",
        "cyrillic": """🎯 Ажойиб! Мен сизга энг мос инвестиция ғояларини топиш учун бир нечта савол бераман.

Саволларга оддий, ўз сўзларингиз билан жавоб беринг. Бу 2-3 дақиқа олади.

Биринчи савол:"""
    },
    
    "interview_complete": {
        "latin": "✅ Rahmat! Endi sizga tavsiya tayyorlayapman...",
        "cyrillic": "✅ Раҳмат! Энди сизга тавсия тайёрлаяпман..."
    },
    
    "generating_recommendation": {
        "latin": "🤔 Sizning profilingizga mos tavsiyalar qidiryapman...",
        "cyrillic": "🤔 Сизнинг профилингизга мос тавсиялар қидираяпман..."
    },
    
    "recommendation_reminder": {
        "latin": """💡 Eslatma:
• Bu shaxsiy tavsiya emas, umumiy yo'nalish
• Har qanday investitsiya xavfli
• Moliyaviy maslahatchi bilan maslahatlashing
• Maqsadlaringiz o'zgarganda qaytib keling""",
        "cyrillic": """💡 Эслатма:
• Бу шахсий тавсия эмас, умумий йўналиш
• Ҳар қандай инвестиция хавфли
• Молиявий маслаҳатчи билан маслаҳатлашинг
• Мақсадларингиз ўзгарганда қайтиб келинг"""
    },
    
    "interview_cancelled": {
        "latin": "❌ So'rovnoma bekor qilindi. Asosiy menyuga qaytdingiz.",
        "cyrillic": "❌ Сўровнома бекор қилинди. Асосий менюга қайтдингиз."
    },
    
    "error_general": {
        "latin": "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "cyrillic": "❌ Хатолик юз берди. Илтимос, қайтадан уриниб кўринг."
    },
    
    "error_session_expired": {
        "latin": "❌ Sessiya tugadi. Iltimos, qaytadan boshlang.",
        "cyrillic": "❌ Сессия тугади. Илтимос, қайтадан бошланг."
    },
    
    "error_recommendation": {
        "latin": "❌ Tavsiya tayyorlashda xatolik. Iltimos, qaytadan urinib ko'ring.",
        "cyrillic": "❌ Тавсия тайёрлашда хатолик. Илтимос, қайтадан уриниб кўринг."
    },
    
    "button_start": {
        "latin": "🚀 Boshlash",
        "cyrillic": "🚀 Бошлаш"
    },
    
    "button_new_interview": {
        "latin": "📝 Yangi tavsiya",
        "cyrillic": "📝 Янги тавсия"
    },
    
    "button_new_interview_uznetix": {
        "latin": "📊 Uznetix tahlili olish",
        "cyrillic": "📊 Uznetix таҳлили олиш"
    },
    
    "button_cancel": {
        "latin": "❌ Bekor qilish",
        "cyrillic": "❌ Бекор қилиш"
    },
    
    "button_skip": {
        "latin": "⏭ O'tkazib yuborish",
        "cyrillic": "⏭ Ўтказиб юбориш"
    },
    "interview_start": {
        "latin": "🎯 Investitsiya intervyusi boshlanmoqda...\n\nMen sizga eng mos investitsiya variantlarini topishda yordam beraman. Bir necha savol beraman.",
        "cyrillic": "🎯 Инвестиция интервюси бошланмоқда...\n\nМен сизга энг мос инвестиция вариантларини топишда ёрдам бераман. Бир неча савол бераман."
    },
    
    "generating_recommendation": {
        "latin": "⏳ Tavsiya tayyorlanmoqda...\n\nBir oz kuting, sizning ma'lumotlaringiz asosida eng yaxshi variantlarni tanlayman.",
        "cyrillic": "⏳ Тавсия тайёрланмоқда...\n\nБир оз кутинг, сизнинг маълумотларингиз асосида энг яхши вариантларни танлайман."
    },
    
    "interview_complete": {
        "latin": "✅ Intervyu tugadi!\n\nYana yangi tavsiya olmoqchi bo'lsangiz, quyidagi tugmani bosing.",
        "cyrillic": "✅ Интервью тугади!\n\nЯна янги тавсия олмоқчи бўлсангиз, қуйидаги тугмани босинг."
    },
    
    "error_generating_recommendation": {
        "latin": "❌ Tavsiya yaratishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "cyrillic": "❌ Тавсия яратишда хатолик юз берди. Илтимос, қайтадан уриниб кўринг."
    },
    
    "verification_required": {
        "latin": "⛔️ Ushbu funksiyadan foydalanish uchun avval ro'yxatdan o'tishingiz kerak.",
        "cyrillic": "⛔️ Ушбу функциядан фойдаланиш учун аввал рўйхатдан ўтишингиз керак."
    },
    "continue_chat_offer": {
        "latin": "💬 Aksiyalar va investitsiyalar bo'yicha savollaringiz bormi?\n\nMen Uznetix Advisor sifatida sizga yordam berishga tayyorman!",
        "cyrillic": "💬 Акциялар ва инвестициялар бўйича саволларингиз борми?\n\nМен Uznetix Advisor сифатида сизга ёрдам беришга тайёрман!"
    },
    
    "chat_ready": {
        "latin": "✅ Tayyor! Aksiyalar, portfel, yoki investitsiyalar haqida savol bering.\n\nMasalan: \"Tesla aksiyasi haqida nima deyish mumkin?\" yoki \"Qaysi aksiya yaxshiroq?\"",
        "cyrillic": "✅ Тайёр! Акциялар, портфель, ёки инвестициялар ҳақида савол беринг.\n\nМасалан: \"Tesla акцияси ҳақида нима дейиш мумкин?\" ёки \"Қайси акция яхшироқ?\""
    },
    
    "back_to_menu_text": {
        "latin": "🏠 Asosiy menyuga qaytdingiz.",
        "cyrillic": "🏠 Асосий менюга қайтдингиз."
    },
    
    "main_menu_text": {
        "latin": "🏠 Asosiy menyu",
        "cyrillic": "🏠 Асосий меню"
    },
    
    "button_continue_chat": {
        "latin": "💬 Davom etish (savol berish)",
        "cyrillic": "💬 Давом этиш (савол бериш)"
    },
    
    "button_back_to_menu": {
        "latin": "🏠 Asosiy menyuga qaytish",
        "cyrillic": "🏠 Асосий менюга қайтиш"
    },
    
    "button_new_interview_uznetix": {
        "latin": "🎯 Yangi investitsiya tavsiyasi olish",
        "cyrillic": "🎯 Янги инвестиция тавсияси олиш"
    },
    
    "error_generating_recommendation": {
        "latin": "❌ Tavsiya yaratishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "cyrillic": "❌ Тавсия яратишда хатолик юз берди. Илтимос, қайтадан уриниб кўринг."
    },
    
    "verification_required": {
        "latin": "⛔️ Ushbu funksiyadan foydalanish uchun avval ro'yxatdan o'tishingiz kerak.",
        "cyrillic": "⛔️ Ушбу функциядан фойдаланиш учун аввал рўйхатдан ўтишингиз керак."
    },
    
    "error_general": {
        "latin": "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki /start buyrug'ini yuboring.",
        "cyrillic": "❌ Хатолик юз берди. Илтимос, қайтадан уриниб кўринг ёки /start буйруғини юборинг."
    }

}


def get_text(key: str, script: str = "latin", **kwargs) -> str:
    """
    Get text in specified script with optional formatting
    
    Args:
        key: Text key
        script: 'latin' or 'cyrillic'
        **kwargs: Format arguments
    
    Returns:
        Formatted text string
    """
    if key not in TEXTS:
        return f"Text not found: {key}"
    
    text = TEXTS[key].get(script, TEXTS[key].get("latin", ""))
    
    # Format user_name specially
    if "user_name" in kwargs:
        user_name = kwargs["user_name"]
        if user_name:
            kwargs["user_name"] = f" {user_name}"
        else:
            kwargs["user_name"] = ""
    
    try:
        return text.format(**kwargs)
    except KeyError:
        return text