"""Seed data: ~100 Kathmandu Valley restaurants & cafes.

Each tuple matches the column order used by the restaurants seed in
``app.database._seed_kathmandu_restaurants``:

    (name, address, latitude, longitude, category, cuisine, price_range,
     rating, review_count, ambience, opening_time, closing_time,
     description, avg_cost_per_person)

Coordinates are approximate, grouped by real neighbourhoods across the
valley (Thamel, Durbar Marg, Lazimpat, Jhamsikhel, Patan, Boudha, etc.)
so the midpoint / nearby-venue features have realistic density to work
with. ``price_range`` is one of 'budget' | 'mid' | 'expensive'.
"""

KATHMANDU_RESTAURANTS = [
    # ── Thamel ───────────────────────────────────────────────────────
    ("Fire and Ice Pizzeria", "Tridevi Marg, Thamel", 27.7148, 85.3128, "Restaurant", "Italian", "mid", 4.5, 412, "lively", "11:00:00", "22:00:00", "Wood-fired pizzas and a buzzing crowd in central Thamel.", 950),
    ("Third Eye Restaurant", "Chaksibari Marg, Thamel", 27.7141, 85.3110, "Restaurant", "Indian", "mid", 4.3, 198, "casual", "11:00:00", "22:30:00", "Long-running Indian and Nepali kitchen popular with travellers.", 850),
    ("Yangling Tibetan Restaurant", "Mandala Street, Thamel", 27.7156, 85.3116, "Restaurant", "Tibetan", "budget", 4.4, 263, "casual", "08:00:00", "21:30:00", "Famous for hearty momos and thukpa at honest prices.", 500),
    ("La Dolce Vita", "Thamel Marg, Thamel", 27.7159, 85.3122, "Restaurant", "Italian", "mid", 4.4, 176, "romantic", "12:00:00", "22:00:00", "Cosy Italian trattoria with house-made pasta.", 1100),
    ("Pumpernickel Bakery", "Chaksibari Marg, Thamel", 27.7138, 85.3113, "Cafe", "Bakery", "budget", 4.2, 154, "garden", "07:00:00", "20:00:00", "Garden bakery cafe great for breakfast meetups.", 450),
    ("Or2K Cushion Lounge", "Mandala Street, Thamel", 27.7152, 85.3120, "Restaurant", "Mediterranean", "mid", 4.3, 221, "cozy", "09:00:00", "22:00:00", "Vegetarian mezze on floor cushions, relaxed vibe.", 900),
    ("Decode Yoga & Cafe", "Saat Ghumti, Thamel", 27.7162, 85.3105, "Cafe", "Cafe", "mid", 4.5, 97, "quiet", "07:30:00", "20:30:00", "Calm wellness cafe with healthy bowls and coffee.", 600),
    ("New Orleans Cafe", "Jyatha, Thamel", 27.7128, 85.3134, "Restaurant", "Continental", "mid", 4.3, 188, "lively", "10:00:00", "23:00:00", "Courtyard restaurant with live music nights.", 1000),
    ("Roadhouse Cafe Thamel", "Jyatha, Thamel", 27.7126, 85.3137, "Restaurant", "Italian", "mid", 4.4, 209, "casual", "10:00:00", "22:30:00", "Wood-fired pizza branch tucked off the main strip.", 1100),
    ("Cafe Mitra", "Chaksibari Marg, Thamel", 27.7144, 85.3108, "Restaurant", "Continental", "expensive", 4.6, 132, "romantic", "12:00:00", "22:00:00", "Intimate fine-dining spot with curated wine list.", 1900),

    # ── Durbar Marg / Kamaladi ───────────────────────────────────────
    ("Hankook Sarang", "Durbar Marg, Kathmandu", 27.7115, 85.3175, "Restaurant", "Korean", "mid", 4.4, 168, "casual", "11:00:00", "22:00:00", "Authentic Korean BBQ in the heart of the city.", 1300),
    ("Chez Caroline", "Babar Mahal Revisited", 27.6985, 85.3265, "Restaurant", "French", "expensive", 4.6, 211, "garden", "09:00:00", "22:00:00", "European bistro in a heritage courtyard.", 1800),
    ("K-Too Beer & Steakhouse", "Durbar Marg, Kathmandu", 27.7108, 85.3178, "Restaurant", "Steakhouse", "expensive", 4.5, 240, "lively", "11:00:00", "23:00:00", "Steaks, burgers and cold beer near the palace.", 1700),
    ("The Ship Restaurant", "Kamaladi, Kathmandu", 27.7060, 85.3220, "Restaurant", "Continental", "mid", 4.2, 143, "lively", "11:00:00", "22:30:00", "Nautical-themed bar and grill for big groups.", 1100),
    ("Bota Momo Durbar Marg", "Durbar Marg, Kathmandu", 27.7120, 85.3182, "Restaurant", "Nepali", "budget", 4.3, 320, "casual", "10:00:00", "21:00:00", "Steamed and jhol momos, always a queue.", 400),
    ("Java House Durbar Marg", "Durbar Marg, Kathmandu", 27.7112, 85.3179, "Cafe", "Coffee", "mid", 4.4, 287, "lively", "07:00:00", "21:00:00", "Flagship coffee house, a classic meeting point.", 650),
    ("Wunjala Moskva", "Naxal, Kathmandu", 27.7170, 85.3275, "Restaurant", "Nepali", "expensive", 4.5, 121, "garden", "12:00:00", "22:00:00", "Newari and Russian fusion in a leafy garden.", 1600),

    # ── Lazimpat / Lainchaur ─────────────────────────────────────────
    ("1905 Suites & Restaurant", "Kantipath, Lazimpat", 27.7185, 85.3185, "Restaurant", "Continental", "mid", 4.4, 176, "garden", "08:00:00", "22:00:00", "Heritage lawn cafe hosting weekend markets.", 1200),
    ("Tamarind Restaurant", "Lazimpat, Kathmandu", 27.7225, 85.3205, "Restaurant", "Continental", "mid", 4.3, 154, "garden", "08:00:00", "22:00:00", "Garden dining with a broad continental menu.", 1100),
    ("Or-Tho Restaurant", "Lazimpat, Kathmandu", 27.7231, 85.3212, "Restaurant", "Korean", "mid", 4.2, 98, "casual", "11:00:00", "21:30:00", "Homestyle Korean meals near the embassies.", 1000),
    ("Cafe Cheeno", "Lazimpat, Kathmandu", 27.7218, 85.3208, "Cafe", "Cafe", "mid", 4.5, 142, "cozy", "07:30:00", "21:00:00", "Brunch-friendly cafe with strong espresso.", 700),
    ("Hyatt Rox Restaurant", "Boudha Road, Kathmandu", 27.7222, 85.3618, "Restaurant", "Continental", "expensive", 4.6, 188, "fine_dining", "06:30:00", "23:00:00", "Hotel fine dining with poolside terrace.", 2500),

    # ── Naxal / Bhatbhateni / Baluwatar ──────────────────────────────
    ("Roadhouse Cafe Bhatbhateni", "Bhatbhateni, Kathmandu", 27.7221, 85.3305, "Restaurant", "Italian", "mid", 4.4, 233, "casual", "10:00:00", "22:30:00", "Reliable pizza and pasta beside the supermarket.", 1100),
    ("Bawarchi Restaurant", "Naxal, Kathmandu", 27.7158, 85.3282, "Restaurant", "Indian", "mid", 4.3, 167, "family_friendly", "11:00:00", "22:00:00", "North Indian curries and biryani for groups.", 900),
    ("Cafe Swotha", "Naxal, Kathmandu", 27.7162, 85.3278, "Cafe", "Cafe", "mid", 4.4, 112, "quiet", "08:00:00", "20:30:00", "Quiet courtyard cafe for catch-ups.", 650),
    ("Sajha Chiya Ghar", "Baluwatar, Kathmandu", 27.7282, 85.3288, "Cafe", "Cafe", "budget", 4.2, 89, "casual", "07:00:00", "20:00:00", "Local tea house with snacks and milk tea.", 300),
    ("The Burger House & Crunchy Fried Chicken", "Baluwatar, Kathmandu", 27.7275, 85.3295, "Restaurant", "Fast Food", "budget", 4.1, 204, "casual", "10:00:00", "22:00:00", "Crowd-pleasing burgers and fried chicken.", 550),
    ("Imago Dei Cafe", "Naxal, Kathmandu", 27.7150, 85.3290, "Cafe", "Cafe", "mid", 4.5, 76, "quiet", "08:00:00", "20:00:00", "Art-gallery cafe, calm and creative.", 700),

    # ── Maharajgunj / Chabahil ───────────────────────────────────────
    ("Le Trio Restaurant", "Maharajgunj, Kathmandu", 27.7382, 85.3292, "Restaurant", "Continental", "expensive", 4.5, 143, "fine_dining", "11:00:00", "22:30:00", "Upscale continental kitchen near the hospital.", 1900),
    ("Or2K Maharajgunj", "Maharajgunj, Kathmandu", 27.7375, 85.3285, "Restaurant", "Mediterranean", "mid", 4.3, 121, "cozy", "09:00:00", "22:00:00", "Second Or2K outpost with the same mezze menu.", 900),
    ("Chabahil Sekuwa Corner", "Chabahil, Kathmandu", 27.7178, 85.3470, "Restaurant", "Nepali", "budget", 4.2, 256, "lively", "16:00:00", "23:00:00", "Smoky grilled sekuwa and chilled drinks.", 600),
    ("Roadhouse Cafe Chabahil", "Chabahil, Kathmandu", 27.7185, 85.3462, "Restaurant", "Italian", "mid", 4.3, 138, "casual", "10:00:00", "22:30:00", "North-city branch for pizza nights.", 1100),

    # ── Boudha ───────────────────────────────────────────────────────
    ("Garden Kitchen Boudha", "Boudha, Kathmandu", 27.7215, 85.3622, "Restaurant", "Continental", "mid", 4.4, 167, "garden", "08:00:00", "22:00:00", "Stupa-view garden restaurant, relaxed afternoons.", 1000),
    ("Flavors Cafe Boudha", "Boudha, Kathmandu", 27.7208, 85.3615, "Cafe", "Cafe", "mid", 4.5, 142, "rooftop", "07:00:00", "21:00:00", "Rooftop cafe overlooking the great stupa.", 650),
    ("Utse Tibetan Restaurant", "Boudha, Kathmandu", 27.7220, 85.3608, "Restaurant", "Tibetan", "budget", 4.3, 188, "casual", "08:00:00", "21:30:00", "Classic Tibetan dishes near the kora.", 550),
    ("Double Dorje Cafe", "Boudha, Kathmandu", 27.7212, 85.3628, "Cafe", "Cafe", "mid", 4.4, 96, "quiet", "07:30:00", "20:00:00", "Quiet meditative cafe with good filter coffee.", 600),
    ("Stupa View Restaurant", "Boudha, Kathmandu", 27.7218, 85.3612, "Restaurant", "Vegetarian", "mid", 4.5, 173, "rooftop", "09:00:00", "21:30:00", "Vegetarian terrace dining facing the stupa.", 1100),

    # ── Jhamsikhel / Sanepa (Lalitpur) ───────────────────────────────
    ("The Yellow House", "Sanepa, Lalitpur", 27.6812, 85.3078, "Cafe", "Cafe", "mid", 4.6, 211, "garden", "07:30:00", "21:00:00", "Bright garden cafe loved for brunch.", 800),
    ("Cafe Soma Jhamel", "Jhamsikhel, Lalitpur", 27.6759, 85.3145, "Cafe", "Cafe", "mid", 4.5, 198, "cozy", "07:30:00", "21:30:00", "Leafy courtyard for long catch-ups.", 700),
    ("Heritage Kitchen & Bar", "Jhamsikhel, Lalitpur", 27.6762, 85.3150, "Restaurant", "Continental", "mid", 4.4, 165, "lively", "11:00:00", "23:00:00", "Bar and grill at the heart of Jhamel.", 1200),
    ("Bajeko Sekuwa Jhamsikhel", "Jhamsikhel, Lalitpur", 27.6755, 85.3138, "Restaurant", "Nepali", "mid", 4.3, 287, "family_friendly", "11:00:00", "22:00:00", "Famous Nepali grill chain, generous portions.", 850),
    ("Sing Ma Food Court", "Jhamsikhel, Lalitpur", 27.6766, 85.3148, "Restaurant", "Chinese", "budget", 4.2, 176, "casual", "11:00:00", "21:30:00", "Hand-pulled noodles and dumplings.", 600),
    ("The Tap House", "Jhamsikhel, Lalitpur", 27.6758, 85.3152, "Restaurant", "Continental", "mid", 4.4, 221, "lively", "12:00:00", "23:00:00", "Craft beer bar with pub food and big screens.", 1100),
    ("Cafe Du Temple Patan", "Pulchowk, Lalitpur", 27.6792, 85.3168, "Restaurant", "Continental", "mid", 4.3, 134, "garden", "08:00:00", "22:00:00", "Garden dining a short walk from Patan square.", 1000),
    ("Karma Coffee Roasters", "Jhamsikhel, Lalitpur", 27.6760, 85.3140, "Cafe", "Coffee", "budget", 4.5, 152, "quiet", "07:30:00", "20:00:00", "Specialty roaster, laptop-friendly mornings.", 500),
    ("Coffee Pasal Jhamel", "Jhamsikhel, Lalitpur", 27.6764, 85.3155, "Cafe", "Coffee", "budget", 4.4, 118, "cozy", "07:00:00", "20:30:00", "No-frills neighbourhood coffee bar.", 350),
    ("Le Sherpa Restaurant", "Lazimpat, Kathmandu", 27.7340, 85.3275, "Restaurant", "Continental", "expensive", 4.6, 244, "garden", "08:00:00", "22:00:00", "Farm-to-table garden venue and weekend market.", 2000),

    # ── Pulchowk / Kupondole / Jawalakhel ────────────────────────────
    ("The Village Cafe", "Pulchowk, Lalitpur", 27.6795, 85.3172, "Restaurant", "Nepali", "mid", 4.4, 167, "family_friendly", "11:00:00", "21:30:00", "Community cafe serving authentic Newari thali.", 800),
    ("Dhokaima Cafe", "Patan Dhoka, Lalitpur", 27.6748, 85.3215, "Restaurant", "Continental", "mid", 4.5, 198, "garden", "08:00:00", "22:00:00", "Garden restaurant in a restored Newari home.", 1100),
    ("Si Taleju Restaurant", "Kupondole, Lalitpur", 27.6845, 85.3162, "Restaurant", "Newari", "mid", 4.3, 121, "cozy", "11:00:00", "21:30:00", "Traditional Newari plates and local liquor.", 750),
    ("The Old House Riverside", "Jhamsikhel, Lalitpur", 27.6746, 85.3122, "Restaurant", "Continental", "expensive", 4.6, 256, "lively", "12:00:00", "23:00:00", "Riverside lounge with live music nights.", 1800),
    ("Jawalakhel Bara House", "Jawalakhel, Lalitpur", 27.6722, 85.3112, "Restaurant", "Newari", "budget", 4.3, 213, "casual", "08:00:00", "20:00:00", "Crispy wo (bara) and chatamari done right.", 400),
    ("Cafe 32", "Kupondole, Lalitpur", 27.6852, 85.3168, "Cafe", "Cafe", "mid", 4.2, 88, "quiet", "08:00:00", "20:30:00", "Quiet upstairs cafe for reading and work.", 600),
    ("Sasa Mama Pulchowk", "Pulchowk, Lalitpur", 27.6788, 85.3175, "Restaurant", "Tibetan", "budget", 4.4, 264, "casual", "10:00:00", "21:00:00", "Beloved local momo and noodle spot.", 450),

    # ── Patan Durbar Square area ─────────────────────────────────────
    ("Cafe de Patan", "Mangal Bazar, Patan", 27.6735, 85.3248, "Cafe", "Cafe", "mid", 4.5, 187, "cozy", "08:00:00", "21:00:00", "Heritage cafe steps from Patan Durbar Square.", 700),
    ("Museum Cafe Patan", "Patan Museum, Patan", 27.6740, 85.3258, "Cafe", "Continental", "mid", 4.6, 165, "garden", "09:00:00", "18:00:00", "Tranquil garden cafe inside the museum grounds.", 900),
    ("The Inn Patan", "Mangal Bazar, Patan", 27.6731, 85.3252, "Restaurant", "Continental", "mid", 4.3, 121, "rooftop", "09:00:00", "21:30:00", "Rooftop dining over the temple square.", 1000),
    ("Honacha Newari Restaurant", "Patan Durbar Square", 27.6728, 85.3245, "Restaurant", "Newari", "budget", 4.4, 298, "casual", "10:00:00", "20:00:00", "Iconic smoky Newari eatery off the square.", 350),
    ("Taleju Restaurant & Bar", "Patan Dhoka, Lalitpur", 27.6745, 85.3238, "Restaurant", "Continental", "mid", 4.2, 96, "lively", "11:00:00", "22:30:00", "Rooftop bar with valley views.", 1000),

    # ── New Road / Basantapur / Ason / Indrachowk ────────────────────
    ("Or2K New Road", "New Road, Kathmandu", 27.7032, 85.3115, "Restaurant", "Mediterranean", "mid", 4.2, 132, "casual", "09:00:00", "21:30:00", "Vegetarian mezze in the busy bazaar.", 850),
    ("Snowman Cafe", "Freak Street, Basantapur", 27.7022, 85.3078, "Cafe", "Bakery", "budget", 4.3, 176, "cozy", "08:00:00", "20:00:00", "Old-school cafe famous for chocolate cake.", 400),
    ("Cafe de Cathmandu", "Basantapur, Kathmandu", 27.7045, 85.3072, "Cafe", "Cafe", "budget", 4.1, 98, "casual", "08:00:00", "20:30:00", "Square-view cafe for people watching.", 450),
    ("Newari Khaja Ghar Ason", "Ason, Kathmandu", 27.7068, 85.3102, "Restaurant", "Newari", "budget", 4.4, 234, "casual", "09:00:00", "20:00:00", "Bustling traditional snack house in old town.", 350),
    ("Diyalo Restaurant", "Sundhara, Kathmandu", 27.7000, 85.3142, "Restaurant", "Nepali", "budget", 4.2, 145, "family_friendly", "08:00:00", "21:00:00", "Daal-bhaat and Nepali set meals downtown.", 450),

    # ── Putalisadak / Dillibazar / Anamnagar ─────────────────────────
    ("Roadhouse Cafe Dillibazar", "Dillibazar, Kathmandu", 27.7072, 85.3286, "Restaurant", "Italian", "mid", 4.3, 154, "casual", "10:00:00", "22:30:00", "Familiar pizza menu on the east side.", 1100),
    ("Black Olives Cafe", "Putalisadak, Kathmandu", 27.7038, 85.3225, "Restaurant", "Continental", "mid", 4.3, 132, "cozy", "10:00:00", "22:00:00", "Casual continental and Indian sharing plates.", 900),
    ("Western Tandoori Restaurant", "Putalisadak, Kathmandu", 27.7042, 85.3232, "Restaurant", "Indian", "mid", 4.2, 121, "family_friendly", "11:00:00", "22:00:00", "Tandoor grills and rich curries.", 850),
    ("Cafe Soma Baber Mahal", "Anamnagar, Kathmandu", 27.6998, 85.3258, "Cafe", "Cafe", "mid", 4.4, 109, "garden", "07:30:00", "21:00:00", "Garden coffee spot near Babar Mahal.", 700),
    ("Momo Hut Anamnagar", "Anamnagar, Kathmandu", 27.7005, 85.3252, "Restaurant", "Nepali", "budget", 4.3, 287, "casual", "10:00:00", "21:00:00", "Buff and veg momos, quick and cheap.", 350),

    # ── Battisputali / Gaushala / Sinamangal ─────────────────────────
    ("Bhojan Griha Heritage", "Dillibazar, Kathmandu", 27.7072, 85.3280, "Restaurant", "Nepali", "expensive", 4.5, 211, "fine_dining", "11:00:00", "22:00:00", "Cultural dining in a restored Rana mansion.", 1800),
    ("Krishnarpan Fine Dining", "Battisputali, Kathmandu", 27.7048, 85.3492, "Restaurant", "Nepali", "expensive", 4.7, 121, "fine_dining", "18:00:00", "22:00:00", "Multi-course Nepali tasting menu.", 3500),
    ("Sinamangal Sekuwa Ghar", "Sinamangal, Kathmandu", 27.6968, 85.3548, "Restaurant", "Nepali", "budget", 4.2, 198, "lively", "16:00:00", "23:00:00", "Grilled sekuwa near the airport.", 550),
    ("Gaushala Thakali Kitchen", "Gaushala, Kathmandu", 27.7095, 85.3445, "Restaurant", "Thakali", "mid", 4.4, 176, "family_friendly", "10:00:00", "21:30:00", "Authentic Thakali set with refills.", 650),

    # ── Sanepa / Kupondole more ──────────────────────────────────────
    ("Roadhouse Cafe Sanepa", "Sanepa, Lalitpur", 27.6818, 85.3082, "Restaurant", "Italian", "mid", 4.4, 187, "casual", "10:00:00", "22:30:00", "Sanepa branch with garden seating.", 1100),
    ("Local Project Cafe", "Sanepa, Lalitpur", 27.6822, 85.3088, "Cafe", "Cafe", "mid", 4.5, 143, "cozy", "08:00:00", "21:00:00", "Trendy cafe with brunch and specialty coffee.", 750),
    ("The Workshop Eatery", "Kupondole, Lalitpur", 27.6848, 85.3158, "Restaurant", "Continental", "mid", 4.5, 165, "lively", "11:00:00", "23:00:00", "Industrial-chic eatery with craft cocktails.", 1300),
    ("Newa Lahana", "Kirtipur, Kathmandu", 27.6790, 85.2780, "Restaurant", "Newari", "mid", 4.5, 232, "family_friendly", "11:00:00", "21:00:00", "Authentic Newari feast with cultural views.", 800),

    # ── Kalanki / Kalimati / Balkhu (west) ───────────────────────────
    ("Kalimati Thakali Bhanchha", "Kalimati, Kathmandu", 27.6968, 85.2972, "Restaurant", "Thakali", "budget", 4.3, 198, "family_friendly", "09:00:00", "21:00:00", "Hearty Thakali khana set in the west.", 500),
    ("Hotel Himalaya Coffee Shop", "Kupondole Heights, Lalitpur", 27.6838, 85.3175, "Cafe", "Continental", "expensive", 4.4, 121, "garden", "07:00:00", "22:00:00", "Poolside hotel coffee shop and bakery.", 1500),
    ("Trisara Garden Lazimpat", "Lazimpat, Kathmandu", 27.7228, 85.3215, "Restaurant", "Nepali", "mid", 4.5, 188, "garden", "12:00:00", "22:00:00", "Open courtyard Newari restaurant.", 1300),
    ("Places Rooftop Thamel", "Thamel, Kathmandu", 27.7160, 85.3112, "Restaurant", "Continental", "mid", 4.4, 142, "rooftop", "11:00:00", "23:00:00", "Skyline rooftop popular for group hangouts.", 1100),

    # ── Sundhara / Tripureshwar / Teku ───────────────────────────────
    ("Civil Mall Food Court", "Sundhara, Kathmandu", 27.7008, 85.3138, "Restaurant", "Fast Food", "budget", 4.0, 256, "casual", "10:00:00", "21:00:00", "Mall food court with many quick options.", 500),
    ("Cafe Tripureshwar", "Tripureshwar, Kathmandu", 27.6952, 85.3162, "Cafe", "Cafe", "budget", 4.1, 87, "casual", "08:00:00", "20:00:00", "Riverside-road cafe for quick coffee.", 400),
    ("Teku Sekuwa Station", "Teku, Kathmandu", 27.6938, 85.3098, "Restaurant", "Nepali", "budget", 4.2, 167, "lively", "16:00:00", "23:00:00", "Evening sekuwa and chiura spot.", 500),

    # ── Bouddha extended / Tinchuli / Mitrapark ──────────────────────
    ("Tinchuli Coffee Corner", "Tinchuli, Kathmandu", 27.7242, 85.3585, "Cafe", "Coffee", "budget", 4.3, 94, "cozy", "07:00:00", "20:30:00", "Neighbourhood espresso bar near Boudha.", 350),
    ("Mitrapark Newari Bhoj", "Mitrapark, Kathmandu", 27.7158, 85.3492, "Restaurant", "Newari", "budget", 4.2, 132, "casual", "10:00:00", "21:00:00", "Local Newari samay baji platters.", 400),
    ("Saturday Cafe Boudha", "Boudha, Kathmandu", 27.7205, 85.3632, "Cafe", "Cafe", "mid", 4.5, 121, "rooftop", "07:30:00", "20:00:00", "Sunny rooftop brunch near the monasteries.", 650),

    # ── Kuleshwar / Ekantakuna / Satdobato (south) ───────────────────
    ("Ekantakuna Thali House", "Ekantakuna, Lalitpur", 27.6648, 85.3122, "Restaurant", "Nepali", "budget", 4.2, 154, "family_friendly", "09:00:00", "21:00:00", "Unlimited daal-bhaat for hungry groups.", 450),
    ("Satdobato Momo Center", "Satdobato, Lalitpur", 27.6582, 85.3242, "Restaurant", "Nepali", "budget", 4.3, 221, "casual", "10:00:00", "21:00:00", "Popular momo joint on the ring road.", 350),
    ("Cafe Hessed", "Lagankhel, Lalitpur", 27.6668, 85.3232, "Cafe", "Cafe", "mid", 4.4, 132, "quiet", "08:00:00", "21:00:00", "Calm study cafe with good pastries.", 600),
    ("Roadhouse Cafe Lagankhel", "Lagankhel, Lalitpur", 27.6672, 85.3228, "Restaurant", "Italian", "mid", 4.3, 143, "casual", "10:00:00", "22:30:00", "South-Patan branch for pizza fans.", 1100),

    # ── Maitighar / Thapathali / Babarmahal ──────────────────────────
    ("Baber Mahal Cafe", "Babar Mahal, Kathmandu", 27.6982, 85.3268, "Cafe", "Cafe", "mid", 4.4, 121, "garden", "08:00:00", "21:00:00", "Courtyard cafe among boutique shops.", 700),
    ("Thapathali Dhau & Sweets", "Thapathali, Kathmandu", 27.6925, 85.3215, "Cafe", "Sweets", "budget", 4.2, 98, "casual", "08:00:00", "20:00:00", "Juju dhau and Newari sweets.", 300),
    ("Maitighar Multi Cuisine", "Maitighar, Kathmandu", 27.6938, 85.3192, "Restaurant", "Continental", "mid", 4.1, 87, "casual", "10:00:00", "22:00:00", "All-day multi-cuisine near the mandala.", 850),

    # ── Chhetrapati / Sorhakhutte / Paknajol ─────────────────────────
    ("Chhetrapati Thakali", "Chhetrapati, Kathmandu", 27.7112, 85.3068, "Restaurant", "Thakali", "budget", 4.3, 176, "family_friendly", "09:00:00", "21:00:00", "Classic Thakali set near Thamel's edge.", 500),
    ("Paknajol Rooftop Cafe", "Paknajol, Thamel", 27.7178, 85.3098, "Cafe", "Cafe", "mid", 4.3, 109, "rooftop", "07:30:00", "21:00:00", "Quiet rooftop on the north end of Thamel.", 600),
    ("Sorhakhutte Sekuwa", "Sorhakhutte, Kathmandu", 27.7195, 85.3082, "Restaurant", "Nepali", "budget", 4.2, 143, "lively", "16:00:00", "23:00:00", "Evening grills and cold drinks.", 500),

    # ── Misc valley favourites ───────────────────────────────────────
    ("Embassy Restaurant", "Lainchaur, Kathmandu", 27.7195, 85.3168, "Restaurant", "Continental", "mid", 4.3, 132, "casual", "11:00:00", "22:00:00", "Long-standing diner near the embassies.", 900),
    ("The Factory Cafe", "Pulchowk, Lalitpur", 27.6802, 85.3162, "Cafe", "Cafe", "mid", 4.5, 167, "lively", "08:00:00", "22:00:00", "Spacious industrial cafe and co-work spot.", 750),
    ("Roadhouse Cafe Pulchowk", "Pulchowk, Lalitpur", 27.6798, 85.3178, "Restaurant", "Italian", "mid", 4.4, 198, "casual", "10:00:00", "22:30:00", "Patan's busiest pizza branch.", 1100),
    ("Bota Bhatti Jhamel", "Jhamsikhel, Lalitpur", 27.6752, 85.3146, "Restaurant", "Nepali", "mid", 4.3, 221, "lively", "12:00:00", "22:30:00", "Boozy Newari bhatti with grilled snacks.", 700),
    ("Cafe Kalo Pothi", "Thamel, Kathmandu", 27.7146, 85.3124, "Restaurant", "Continental", "mid", 4.3, 154, "cozy", "08:00:00", "22:00:00", "Brunch and burgers in central Thamel.", 950),
    ("Northfield Cafe", "Thamel, Kathmandu", 27.7152, 85.3128, "Restaurant", "Mexican", "mid", 4.4, 176, "garden", "07:00:00", "22:00:00", "Garden cafe known for breakfast and burritos.", 1000),
    ("Places of Asia", "Jhamsikhel, Lalitpur", 27.6761, 85.3149, "Restaurant", "Asian", "mid", 4.3, 132, "lively", "11:00:00", "23:00:00", "Pan-Asian sharing plates and cocktails.", 1200),
    ("Roadhouse Cafe Jhamel", "Jhamsikhel, Lalitpur", 27.6757, 85.3143, "Restaurant", "Italian", "mid", 4.5, 254, "casual", "10:00:00", "22:30:00", "Flagship Jhamel pizza and pasta house.", 1100),
    ("Cafe Nepal Lazimpat", "Lazimpat, Kathmandu", 27.7212, 85.3202, "Cafe", "Cafe", "budget", 4.2, 98, "casual", "07:30:00", "20:30:00", "Simple neighbourhood coffee and tea.", 400),
    ("The Bakery Cafe Teku", "Teku, Kathmandu", 27.6945, 85.3105, "Cafe", "Bakery", "budget", 4.1, 187, "family_friendly", "08:00:00", "21:00:00", "Family bakery chain with quick bites.", 450),
    ("Tibet Kitchen Thamel", "Thamel, Kathmandu", 27.7155, 85.3114, "Restaurant", "Tibetan", "mid", 4.5, 176, "cozy", "11:00:00", "22:00:00", "Refined Tibetan cuisine and butter tea.", 900),
    ("Chopstix Thamel", "Thamel, Kathmandu", 27.7143, 85.3118, "Restaurant", "Chinese", "mid", 4.3, 143, "casual", "11:00:00", "22:00:00", "Indian-Chinese favourites for groups.", 800),
    ("Or-Khid Thai Kitchen", "Lazimpat, Kathmandu", 27.7222, 85.3198, "Restaurant", "Thai", "mid", 4.4, 121, "cozy", "11:30:00", "22:00:00", "Aromatic Thai curries and stir-fries.", 1100),
    ("Sushi Ko", "Durbar Marg, Kathmandu", 27.7118, 85.3172, "Restaurant", "Japanese", "expensive", 4.5, 132, "fine_dining", "12:00:00", "22:00:00", "Fresh sushi and sashimi platters.", 1900),
    ("Falcha Newa Kitchen", "Patan Dhoka, Lalitpur", 27.6744, 85.3232, "Restaurant", "Newari", "mid", 4.4, 154, "family_friendly", "11:00:00", "21:30:00", "Modern take on Newari classics.", 750),
    ("Cafe Encounter Boudha", "Boudha, Kathmandu", 27.7210, 85.3625, "Cafe", "Cafe", "mid", 4.3, 96, "rooftop", "07:30:00", "20:30:00", "Mellow rooftop with stupa views.", 600),
    ("The Coffee Shop Kupondole", "Kupondole, Lalitpur", 27.6850, 85.3164, "Cafe", "Coffee", "budget", 4.2, 87, "quiet", "07:30:00", "20:00:00", "Tiny specialty coffee corner.", 400),
    ("Roadhouse Cafe Maharajgunj", "Maharajgunj, Kathmandu", 27.7378, 85.3288, "Restaurant", "Italian", "mid", 4.3, 132, "casual", "10:00:00", "22:30:00", "North-city pizza branch near the hospital.", 1100),
    ("Newa Chhen Restaurant", "Patan, Lalitpur", 27.6738, 85.3242, "Restaurant", "Newari", "mid", 4.5, 198, "cozy", "11:00:00", "21:30:00", "Heritage-home Newari dining in Patan.", 800),
    ("Or2K Pulchowk", "Pulchowk, Lalitpur", 27.6796, 85.3166, "Restaurant", "Mediterranean", "mid", 4.3, 121, "casual", "09:00:00", "22:00:00", "Patan branch of the vegetarian favourite.", 900),
    ("Gokarna Forest Cafe", "Gokarna, Kathmandu", 27.7468, 85.3855, "Cafe", "Continental", "expensive", 4.6, 121, "garden", "08:00:00", "21:00:00", "Forest-resort cafe for a quiet escape.", 1600),
]


# ── Fake restaurant offers (demo data) ───────────────────────────────
# Each tuple is (restaurant_name, title, description, discount_percent).
# ``restaurant_name`` must match a name above (or an existing demo row) so
# the seed can link the offer to a real restaurant via foreign key. These
# are deliberately fictional deals for the project demo. discount_percent
# of 0 means it's a combo/freebie deal rather than a straight % discount.
KATHMANDU_OFFERS = [
    # Patan Durbar Square cluster
    ("Cafe de Patan", "Group brunch discount", "20% off on groups of 3+ · Valid today", 20),
    ("Museum Cafe Patan", "Free dessert deal", "Free dessert with any set meal", 0),
    ("Honacha Newari Restaurant", "Newari samay baji combo", "Samay baji platter + local drink at a flat rate", 0),
    ("The Inn Patan", "Rooftop happy hour", "15% off rooftop platters before 6 PM", 15),
    ("Newa Chhen Restaurant", "Heritage thali offer", "10% off the Newari heritage thali", 10),
    # Thamel cluster
    ("Fire and Ice Pizzeria", "Pizza for groups", "Buy 2 large pizzas, get 1 garlic bread free", 0),
    ("Yangling Tibetan Restaurant", "Momo combo", "Momo + thukpa combo at NPR 499", 0),
    ("Or2K Cushion Lounge", "Veggie mezze deal", "15% off the sharing mezze platter", 15),
    ("Tibet Kitchen Thamel", "Butter tea on us", "Free butter tea with any main course", 0),
    ("Northfield Cafe", "Breakfast special", "20% off breakfast sets before 11 AM", 20),
    # Durbar Marg cluster
    ("K-Too Beer & Steakhouse", "Steak night", "20% off steaks every weekday evening", 20),
    ("Java House Durbar Marg", "Coffee combo", "Buy 2 coffees, get 1 pastry free", 0),
    ("Bota Momo Durbar Marg", "Jhol momo deal", "Free jhol momo plate on orders above NPR 1,000", 0),
    ("Sushi Ko", "Sushi platter offer", "15% off the signature sushi platter", 15),
    # Jhamsikhel / Sanepa / Pulchowk cluster
    ("The Tap House", "Pub grub deal", "Free fries bucket with any 2 pints", 0),
    ("Bajeko Sekuwa Jhamsikhel", "Sekuwa group set", "10% off sekuwa sets for groups of 4+", 10),
    ("Roadhouse Cafe Jhamel", "Pizza Tuesday", "25% off all pizzas on Tuesdays", 25),
    ("Karma Coffee Roasters", "Refill hour", "Free filter coffee refill before noon", 0),
    ("The Yellow House", "Brunch combo", "15% off weekend brunch platters", 15),
    ("Dhokaima Cafe", "Garden lunch deal", "Free dessert with any garden lunch set", 0),
    ("The Factory Cafe", "Co-work coffee", "Buy 1 coffee, get 1 half price all day", 0),
    # Lazimpat / Maharajgunj cluster
    ("Le Sherpa Restaurant", "Farm-to-table offer", "10% off the farm-to-table tasting plate", 10),
    ("Cafe Cheeno", "Brunch special", "Free pastry with any breakfast set", 0),
    ("Trisara Garden Lazimpat", "Newari evening", "15% off Newari platters after 6 PM", 15),
    # Boudha cluster
    ("Stupa View Restaurant", "Rooftop veg deal", "20% off vegetarian set meals", 20),
    ("Flavors Cafe Boudha", "Stupa-view coffee", "Buy 2 coffees, get 1 cheesecake free", 0),
    ("Utse Tibetan Restaurant", "Thenthuk combo", "Thenthuk + momo combo at NPR 450", 0),
    # Existing demo restaurants
    ("Himalayan Java Coffee", "Study session combo", "Buy 2 coffees, get 1 pastry free before 5 PM", 0),
    ("Bhojan Griha", "Cultural dinner offer", "10% off the cultural dinner set for groups", 10),
    ("Roadhouse Cafe", "Group pizza deal", "20% off on orders above NPR 2,500", 20),
]
