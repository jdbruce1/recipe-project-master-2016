from pymongo import MongoClient
import pymongo

# Use this class to communicate with the already created knowledge base
# (pretty bare bones right now, sorry)
class KnowledgeBase:

    def __init__(self):
        self.db = self.connectToKB()
        self.collection = self.db.ingredients

    def connectToKB(self):
        client = MongoClient("mongodb://team2recipes:recipes@ds037415.mlab.com:37415/team2-recipes")
        self.client = client
        return client['team2-recipes']

    def searchIngredientsFor(self, ingredient):
        self.setCurrentCollection("ingredients")
        return self.searchInCollectionFor(ingredient)

    def searchInCollectionFor(self, name):
        result = self.queryOne("name", name)
        return result


    def getIngredientsWithParent(self, parent):
        self.setCurrentCollection("ingredients")
        return self.getWithParent(parent)

    def getWithParent(self, parent):
        return self.queryAllDict({("parent." + parent): {"$exists": True}})

    # the parent property can be stored as {"parent": "biggest.smaller.*.smallest"} and this function
    # will handle making it work
    def getIngredientsByProperties(self, properties):
        self.setCurrentCollection("ingredients")
        return self.getByProperties(properties)

    def getByProperties(self, properties):
        try:
            parent = properties['parent']
            properties['parent.' + parent] = {"$exists": True}
            del properties['parent']
        except KeyError:
            pass
        return self.queryAllDict(properties)



    def setCurrentCollection(self, collectionName):
        self.collection = self.db[collectionName]

    def queryAllValuesOf(self, field):
        return (value[field] for value in self.collection.find().sort([(field, pymongo.ASCENDING)]))


    def queryOne(self, field, value):
        return self.queryOneDict({field:value})


    def queryOneDict(self, query):
        return self.collection.find_one(query)


    def queryAll(self, field, value):
        return self.queryAllDict({field:value})


    def queryAllDict(self, query):
        return self.collection.find(query)

    def upsertNamedRecord(self, data):
        try:
            name = data['name']
        except KeyError:
            raise StandardError("Record to be updated must have name field.")
        del data["name"]
        for key in data.keys():
            if data[key] is None:
                del data[key]
        updateQuery = {"$set": data}
        return self.collection.update_one({"name": name}, updateQuery, upsert=True)

    #Takes in a category of food (subcategory of protein for veg transformation)
    #and a transformation (vegetarian, pescatarian, or meatify) and returns
    #the transformed category.
    def categoryTransform(self, category, transformation):
        if not(transformation == "vegetarian" or transformation == "pescatarian" or
                transformation == "meatify"):
            raise StandardError("Unrecognized transformation.")
        self.setCurrentCollection("transforms")
        response = self.queryOneDict({"transformationType": transformation})
        try:
            value = response["table"][category]
            return value
        except KeyError:
            return None


    def getIngredientParentLineage(self, ingredientResult):
        lineageDict = ingredientResult["parent"]
        lineage = []
        #loop goes until category is no longer a dict
        while True:
            try:
                category = lineageDict.keys()[0]
                lineage.append(category)
                lineageDict = lineageDict[category]
            except AttributeError:
                break
        return lineage

    def insertTransformationMapping(self, transformation, key, value):
        self.setCurrentCollection("transforms")
        self.collection.update_one({"transformationType":transformation},
        {"$set": {"table." + key:value}})




# The following methods are used to make a UI to easily add to the database.

    #db.authenticate('team2recipes', 'recipes')





def collectionUI(db, coll, params):
    print "You selected to work with " + coll + " in the database."
    db.setCurrentCollection(coll)
    run = True
    goback = True
    while run:
        print "What would you like to do?"
        print "\t1: List the names in " + coll + "."
        print "\t2: Investigate a specific member of " + coll + "."
        print "\t3: Add a member to " + coll + "."
        print "\tB: Go back."
        print "\tQ: Quit."

        response = getInput()
        if response == "1":
            elements = db.queryAllValuesOf("name")
            for el in elements:
                print el
        elif response == "2":
            print "Which member would you like to know more about?"
            response = getInput()
            data = db.queryOne("name", response)
            if data is None:
                print "Unable to find a record of that member."
            else:
                printDict(data)
        elif response == "3":
            run = addOneToCollectionUI(db, coll, params)
            goback = run
        elif response == "B" or response == "b" or response == "back":
            run = False
        elif response == "Q" or response == "q" or response == "quit":
            run = False
            goback = False

    return goback

# UI to add a named, parented document to the specified collection
def addOneToCollectionUI(db, coll, parameters):
    print "You selected to add an member to " + coll + "."
    db.setCurrentCollection(coll)
    print "Name of member:"
    name = getInput()
    oldData = db.queryOne("name", name)
    if oldData is not None:
        print "This member of " + coll + " already exists.  Here is the current data on this member."
        printDict(oldData)
        print "If you continue, the data will be overwritten unless you leave the field blank. (B to return.)"
        response = getInput()
        if response == "B" or response == "b" or response == "back":
            return True
        elif response == "Q" or response == "q" or response == "quit":
            return False
    data = {"name":name}
    print "Category lineage: (Format: biggestCategory.smaller.*.smallest)"
    response = getInput()
    if response is not None:
        data['parent.'+response] = True
    else:
        data['parent'] = None
    for key in parameters.keys():
        message = parameters[key]
        value = None
        # input lists of values.. signalled by a list of messages (even if that list has one element)
        if isinstance(message, list):
            index = 0
            if(index < len(message)):
                print message
            currData = getInput()
            dataLst = []
            while currData and not currData.lower() == 'done':
                dataLst.append(currData)
                index += 1
                if(index < len(message)):
                    print message[index]
                currData = getInput()
            if len(dataLst) > 0:
                value = dataLst
        else:
            print parameters[key]
            value = getInput()

        data[key] = value
    print "\nYou are about to create or update a record as follows:"
    printDict(data)
    print "Confirm? (Y to confirm, N to try again, B to go back)"
    response = getInput()
    if response in ['y', 'Y', 'yes']:
        db.upsertNamedRecord(data)
        print "Successfully created/updated member of " + coll + "."
    elif response in ['n', 'N', 'no']:
        return addOneToCollectionUI(db, coll, parameters)
    elif response in ['b', 'B', 'back']:
        return True
    elif response in ['q', 'Q', 'quit']:
        return False
    return True

def getInput():
    try:
        response = raw_input()
    except SyntaxError:
        return None
    return response

def ingredientUI(db):
    print "You selected to work with ingredients in the database."
    db.setCurrentCollection("ingredients")
    run = True
    goback = True
    while run:
        print "What would you like to do?"
        print "\t1: List the names of ingredients."
        print "\t2: Investigate a specific ingredient."
        print "\t3: Add an ingredient."
        print "\tB: Go back."
        print "\tQ: Quit."

        response = getInput()
        if response == "1":
            ings = db.queryAllValuesOf("name")
            for ing in ings:
                print ing
        elif response == "2":
            print "Which ingredient would you like to know more about?"
            response = getInput()
            data = db.queryOne("name", response)
            if data is None:
                print "Unable to find a record of that ingredient."
            else:
                printDict(data)
        elif response == "3":
            run = addOneIngredientUI(db)
            goback = run
        elif response == "B" or response == "b" or response == "back":
            run = False
        elif response == "Q" or response == "q" or response == "quit":
            run = False
            goback = False

    return goback

def addOneIngredientUI(db):
    print "You selected to add an ingredient."
    print "Name of ingredient:"
    name = getInput()
    oldData = db.queryOne("name", name)
    if oldData is not None:
        print "This ingredient already exists.  Here is the current data on this ingredient."
        printDict(oldData)
        print "If you continue, the data will be overwritten unless you leave the field blank. (B to return.)"
        response = getInput()
        if response == "B" or response == "b" or response == "back":
            return True
        elif response == "Q" or response == "q" or response == "quit":
            return False
    data = {"name":name}
    print "Category lineage: (Format: biggestCategory.smaller.*.smallest)"
    response = getInput()
    if response is not None:
        data['parent.'+response + '.' + name] = True
    else:
        data['parent'] = None
    print "Default unit:"
    data['default unit'] = getInput()
    print "1 count of this ingredient is how much default unit? (Quantity -> Volume)"
    data['units per count'] = getInput()
    print "Decomposition information:"
    data['decomposition'] = getInput()
    print "Carb Level? (high, neutral, low):"
    data['carbLevel'] = getInput()
    print "Sodium Level? (high, neutral, low):"
    data['sodiumLevel'] = getInput()
    print "\nYou are about to create or update a record as follows:"
    printDict(data)
    print "Confirm? (Y to confirm, N to try again, B to go back)"
    response = getInput()
    if response in ['y', 'Y', 'yes']:
        db.upsertNamedRecord(data)
        print "Ingredient successfully created/updated."
    elif response in ['n', 'N', 'no']:
        return addOneIngredientUI(db)
    elif response in ['b', 'B', 'back']:
        return True
    elif response in ['q', 'Q', 'quit']:
        return False
    return True

def printDict(data):
    print '{'
    for key in data.keys():
        print str(key) + " : " + str(data[key])
    print '}'


def cookingUI(db):
    return collectionUI(db, "cooking methods",
                        {"heat source": "What is the heat source for this method?",
                         "tools": ["List the tools used for this method. ('Done' to finish)"],
                         "preparations": ["List the possible preparation methods for this cooking method. ('Done' to finish)"]})

def prepUI(db):
    return collectionUI(db, "preparation methods",
                        {"tools": ["List the possible tools used for this method. ('Done' to finish)"]})

def kbmain():
    print "Connecting to recipe knowledge base..."
    try:
        db = KnowledgeBase()
        print "Connected."
    except Exception:
        print "Failed to connect to knowledge base."
        return
    print "Welcome to the recipe knowledge base API."
    run = True
    while run:
        print "What would you like to do?"
        print "\t1: Work with ingredients"
        print "\t2: Work with cooking methods"
        print "\t3: Work with preparation methods"
        print "\tQ: Quit."

        response = getInput()
        if response == "1":
            run = ingredientUI(db)
        elif response == "2":
            run = cookingUI(db)
        elif response == "3":
            run = prepUI(db)
        elif response == "Q" or response == "q" or response == "quit":
            run = False
        else:
            print "Response not recognized. Please try again.\n"


    print "Exiting..."
    db.client.close()


kbmain()
# kb = KnowledgeBase()
# kb.setCurrentCollection("transforms")
# value = [{
#         "transformationType":"meatify",
#         "table": {"vegetarian": ["chicken"], "fish": ["pork"]}
#      },
#     {
#         "transformationType":"vegetarian",
#         "table": {"meat": ["tofu"], "fish": ["tofu"]}
#     },
#     {
#         "transformationType":"pescatarian",
#         "table": {"meat": ["salmon"], "vegetarian":["tuna"]}
#     }]
# kb.collection.insert(value)
