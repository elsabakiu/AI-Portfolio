VALID_MATERIALS = [
    "Beton | Mörtel",
    "Beton | Spannbeton",
    "Beton | Stahlbeton",
    "Beton | Schleuderbeton",
    "Mauerwerk | Kalksandstein",
    "Mauerwerk | Betonstein",
    "Mauerwerk | Ziegelstein",
    "Metall | legierten Stahl",
    "Metall | unlegierten Stahl",
    "Steine | Geotextil",
    "Steine | Kies",
]

VALID_DAMAGE_TYPES = [
    "Beton | Feuchte Stelle",
    "Beton | Kantenabbruch",
    "Beton | Rostfahnen",
    "Risse | Gerissen",
    "Risse | Diagonal (nass)",
    "Risse | Längsriss (trocken)",
    "Formänderung | Angrenzend",
    "Formänderung | Abgesackt",
    "Allgemein | Verformt",
    "Allgemein | Abgerissen",
    "Allgemein | Verschlissen/locker",
    "Mauerwerk | Verwitterung",
    "Bewehrung | Lochkorrosion",
    "Maßangabe | Zu groß",
    "Maßangabe | Zu klein",
    "Stahl | Verrostet",
]

VALID_STATUSES = ["Damage", "Suspicion", "Fixed", "Incorrectly detected"]
VALID_QUANTITIES = ["general", "isolated", "one piece"]
VALID_CLASSES = ["1", "2", "3", "4"]
VALID_OPTIONAL_REMARKS = ["Engage external institute", "See last monitoring"]

VALID_MATERIAL_DAMAGE_TYPE_COMBOS = {
    "Beton | Stahlbeton": [
        "Beton | Feuchte Stelle",
        "Beton | Kantenabbruch",
        "Beton | Rostfahnen",
        "Risse | Gerissen",
        "Risse | Diagonal (nass)",
        "Risse | Längsriss (trocken)",
    ],
    "Beton | Mörtel": ["Allgemein | Abgerissen", "Allgemein | Verschlissen/locker"],
    "Beton | Spannbeton": ["Allgemein | Abgerissen"],
    "Beton | Schleuderbeton": ["Beton | Feuchte Stelle"],
    "Mauerwerk | Ziegelstein": ["Mauerwerk | Verwitterung"],
    "Mauerwerk | Kalksandstein": ["Maßangabe | Zu klein"],
    "Mauerwerk | Betonstein": ["Formänderung | Angrenzend"],
    "Metall | legierten Stahl": ["Stahl | Verrostet"],
    "Metall | unlegierten Stahl": ["Stahl | Verrostet", "Allgemein | Verformt"],
    "Steine | Geotextil": ["Formänderung | Abgesackt"],
    "Steine | Kies": ["Maßangabe | Zu groß"],
}
