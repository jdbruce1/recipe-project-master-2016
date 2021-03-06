# unit insertions

kb = KnowledgeBase()
kb.setCurrentCollection("units")
value = [{
        "name": "tablespoons",
        "alt_names": ["tablespoon","T","Tbs.","Tbs","Tbsp","Tbsp.","tbs.","tbs","tbsp","tbsp."],
        "type": "volume",
        "#default": .0625
     },
     {
        "name": "cups",
        "alt_names": ["cup","Cup","Cups"],
        "type": "volume",
        "#default": 1
     },
     {
        "name": "teaspoons",
        "alt_names": ["teaspoon","t","tsp.","tsp"],
        "type": "volume",
        "#default": .020833
     },
     {
        "name": "pints",
        "alt_names": ["pint","pt.","Pint","Pt.","Pints"],
        "type": "volume",
        "#default": 2
     },
     {
        "name": "quarts",
        "alt_names": ["quart","qt.","Quart","Qt.","Quarts"],
        "type": "volume",
        "#default": 4
     },
     {
        "name": "gallons",
        "alt_names": ["gallon","gal.","Gallon","Gallons","Gal."],
        "type": "volume",
        "#default": 16
     },
     {
        "name": "mililiters",
        "alt_names": ["mililiter","mililitres","mililitre","mL","mL.","ml","ml.","Mililiter","Mililiters","Mililitres","Mililitre"],
        "type": "volume",
        "#default": .0042267
     },
     {
        "name": "litres",
        "alt_names": ["liter","L","Litres","Litres"],
        "type": "volume",
        "#default": 4.2267
     },
     {
        "name": "pinch",
        "alt_names": ["pinches","Pinch","Pinches"],
        "type": "volume",
        "#default": .001302
     },
     {
        "name": "grams",
        "alt_names": ["gram","g","g.","Grams","Gram","G"],
        "type": "mass",
        "#default": .035
     },
     {
        "name": "kilograms",
        "alt_names": ["kilogram","kg","kg.","Kilograms","Kilogram","Kg","Kg."],
        "type": "mass",
        "#default": 35.3
     },
     {
        "name": "ounces",
        "alt_names": ["ounce","oz","oz.","Oz","Oz.","Ounces","Ounce"],
        "type": "mass",
        "#default": 1
     },
     {
        "name": "pounds",
        "alt_names": ["pound", "lb","lb.","lbs","lbs."],
        "type": "mass",
        "#default": 16
     },
     {
        "name": "fluid ounces",
        "alt_names": ["fluid ounce","fl. oz.","fl. ounces","fl. ounce","fl. oz","fl oz.","fl oz"],
        "type": "volume",
        "#default": .125
     }]
kb.collection.insert(value)

# transform insertions

kb = KnowledgeBase()
kb.setCurrentCollection("transforms")
value = [{
        "transformationType":"meatify",
        "table": 
        {"vegetarian": ["chicken"], 
        "fish": ["pork"],
        "beans": ["ground beef"],
        "portobello": ["beef"],
        "tofu": ["chicken"],
        "vegetable stock": ["chicken stock"]
        }
     },
    {
        "transformationType":"vegetarian",
        "table": 
        {"meat": ["tofu"], 
        "fish": ["tofu"],
        "beef": ["portobello mushrooms"],
        "bacon": ["bread crumbs"],
        "prosciutto": ["bread crumbs"],
        "meat stock": ["vegetable stock"]
        }
    },
    {
        "transformationType":"pescatarian",
        "table": 
        {"meat": ["salmon"], 
        "vegetarian":["tuna"],
        "beef": ["portobello mushrooms"],
        "steak": ["tuna steak"],
        "pork": ["tilapia"],
        "poultry": ["tilapia"],
        "bacon": ["bread crumbs"],
        "prosciutto": ["bread crumbs"],
        "meat stock": ["vegetable stock"]
        }
    }]
kb.collection.insert(value)



