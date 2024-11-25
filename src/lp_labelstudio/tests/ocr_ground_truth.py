"""
Ground truth data for OCR testing.

Format:
{
    "image_name": {
        "x_y_width_height": {
            "ocr": "text from OCR",
            "ground_truth": "# correct text after manual verification"
        }
    }
}

Uncomment the ground_truth lines as you verify them.
"""

ground_truth_data = {
    "page_01.jpeg": {
        "1471_933_1724_55": {
            "ocr": "l medico Jgo Sturleseil portabandiera dei pro\nessisti alla Camero",
            "ground_truth": "Il medico Ugo Sturlese il portabandiera dei progressisti alla Camera",
        },
        "1512_1035_1644_288": {
            "ocr": "Unlaico mite contro\ntutti gli integralismi",
            "ground_truth": "Un laico mite contro\ntutti gli integralismi",
        },
        "395_943_831_368": {
            "ocr": "Beppe testone\nbatte una\ngran nasata",
            "ground_truth": "Beppe testone\nbatte una\ngran nasata",
        },
        "340_2110_442_99": {
            "ocr": "saopatodelracdonp\ndelpontesul Gesso",
            "ground_truth": "L'appalto del raddoppio\ndel ponte sul Gesso",
        },
        "389_2244_331_272": {
            "ocr": "Quel\nsindaco\ngnaro",
            "ground_truth": "Quel\nsindaco\nignaro",
        },
        "1183_2279_1290_57": {
            "ocr": "ex deputato Sergio Soavesi arrabbia con ragione",
            "ground_truth": "L'ex deputato Sergio Soavesi arrabbia con ragione",
        },
        "883_2375_1894_96": {
            "ocr": "Testimone.ma in prima pagina",
            "ground_truth": "Testimone, ma in prima pagina",
        },
        "412_2599_310_32": {
            "ocr": "i PaoloTomatis",
            "ground_truth": "di Paolo Tomatis",
        },
        "328_3314_324_295": {
            "ocr": "Ana singolare\nma giustificata\nmonumento\ndi Piazza\nGalimberti",
            "ground_truth": "Una singolare\nma giustificata\nproposta sul\nmonumento\ndi Piazza\nGalimberti",
        },
        "328_3681_323_442": {
            "ocr": "Via que\nsignore\nin\ncappa\ne spada",
            "ground_truth": "Via quel\nsignore\nin\ncappa\ne spada",
        },
        "352_4279_1444_53": {
            "ocr": "*8881888888",
            "ground_truth": "Cicci e Pino fanno proprie le proteste dei signori della tribuna",
        },
        "560_4397_1036_75": {"ocr": "", "ground_truth": "“Fatelo star zitto!”"},
        "2435_1389_315_33": {
            "ocr": "di Franco Bagnis",
            "ground_truth": "di Franco Bagnis",
        },
        "2959_2229_266_78": {"ocr": "", "ground_truth": "È tempo di\nabbonamenti"},
        "1422_3165_304_159": {"ocr": "Pollidi", "ground_truth": "Polli di\nsinistra"},
    },
    "page_02.jpeg": {
        "2697_2084_427_93": {
            "ocr": "Le Poste edil\nmaterale elettorale",
            "ground_truth": "Le Poste ed il\nmateriale elettorale",
        },
        "2769_2230_283_293": {
            "ocr": "Viaggia\na\n70 lire\nil pezzo",
            "ground_truth": "Viaggia\na\n70 lire\nil pezzo",
        },
        "1454_2690_889_81": {
            "ocr": "Quel sindaco ignaro",
            "ground_truth": "Quel sindaco ignaro...",
        },
        "322_2599_630_117": {
            "ocr": "Chi va, chi viene e\nhi si mette insieme",
            "ground_truth": "Chi va, chi viene e\nchi si mette insieme",
        },
        "186_2741_909_32": {
            "ocr": "ATYT",
            "ground_truth": "Notizie dallo Stato Civile di Cuneo",
        },
        "596_2820_71_22": {"ocr": "A", "ground_truth": "Nati"},
        "401_3134_467_20": {"ocr": "", "ground_truth": "Pubblicazioni di matrimonio"},
        "548_3570_174_23": {"ocr": "Vatrinmo", "ground_truth": "Matrimoni"},
        "591_3883_92_23": {"ocr": "Vort", "ground_truth": "Morti"},
        "1213_3880_365_136": {
            "ocr": "Farmacie\ndi turno",
            "ground_truth": "Farmacie\ndi turno",
        },
        "1527_1781_766_51": {
            "ocr": "nvito agli elettori progressist",
            "ground_truth": "Invito agli elettori progressisti",
        },
        "1299_1874_1196_190": {
            "ocr": "Ialtraal portafoglio",
            "ground_truth": "Una mano sul cuore\nl'altra al portafoglio",
        },
        "686_361_397_195": {
            "ocr": "Mite\nlaico e gli\nintegralism",
            "ground_truth": "Mite\nlaico e gli\nintegralismi",
        },
        "175_359_411_129": {
            "ocr": "Beppe e\na gran nasata",
            "ground_truth": "Beppe e\nla gran nasata",
        },
    },
    "page_03.jpeg": {
        "2156_541_914_57": {
            "ocr": "Storia di sangue in Pretura a Cunec",
            "ground_truth": "Storia di sangue in Pretura a Cuneo",
        },
        "2033_638_1159_192": {
            "ocr": "Rubato il congelatore",
            "ground_truth": "Rubato il congelatore\ncon i cadaveri squartati",
        },
        "379_540_1440_55": {
            "ocr": "Continuano le polemiche tra sindaco e comandante dei vigil",
            "ground_truth": "Continuano le polemiche tra sindaco e comandante dei vigili",
        },
        "611_635_979_191": {
            "ocr": "Corpo con due teste\no corpo senza testa?",
            "ground_truth": "Corpo con due teste\no corpo senza testa?",
        },
        "2391_1885_450_45": {
            "ocr": "Richiesta la sospensione",
            "ground_truth": "Richiesta la sospensione",
        },
        "2399_1957_450_117": {
            "ocr": "Non si abbatte\na Bombonina",
            "ground_truth": "Non si abbatte\na Bombonina",
        },
        "385_1825_1434_112": {
            "ocr": "Le norme del tempo che fu sono tuttora in vigore\nael Regolamento di Polizia Municipale.rinnovato nel'92",
            "ground_truth": "Le norme del tempo che fu sono tuttora in vigore\nael Regolamento di Polizia Municipale, rinnovato nel '92",
        },
        "418_1978_1376_180": {
            "ocr": "Cosi deve comportarsi\n'utente degli orinatoi pubblic",
            "ground_truth": "Così deve comportarsi\nl'utente degli orinatoi pubblici",
        },
        "945_3458_821_54": {
            "ocr": "50 alloggi con contributi statal",
            "ground_truth": "150 alloggi con contributi statali",
        },
        "988_3551_729_163": {
            "ocr": "Alloggipopolari\nda200 milioni",
            "ground_truth": "Alloggi popolari\nda 200 milioni",
        },
    },
}
