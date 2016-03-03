from pymongo import MongoClient
import pymongo

# Use this class to communicate with the already created knowledge base
# (pretty bare bones right now, sorry)
class KnowledgeBase:

    def __init__(self):
        self.db = connectToKB()
        self.collection = self.db.ingredients


    def searchIngredientsFor(self, ingredient):
        self.setCurrentCollection("ingredients")
        result = self.queryOne("name", ingredient)
        return result

    def getIngredientsWithParent(self, parent):
        self.setCurrentCollection("ingredients")
        return self.queryAllDict({("parent." + parent): {"$exists": True}})

    # the parent property can be stored as {"parent": "biggest.smaller.*.smallest"} and this function
    # will handle making it work
    def getIngredientsByProperties(self, properties):
        try:
            parent = properties['parent']
            properties['parent.' + parent] = {"$exists": True}
            del properties['parent']
        except KeyError:
            pass
        self.setCurrentCollection("ingredients")
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




# The following methods are used to make a UI to easily add to the database.
def connectToKB():
    client = MongoClient("mongodb://team2recipes:recipes@ds037415.mlab.com:37415/team2-recipes")
    #client = MongoClient("ds037415.mlab.com", 37415)
    return client['team2-recipes']
    #db.authenticate('team2recipes', 'recipes')


def queryAllValuesOf(coll, field):
    return (value[field] for value in coll.find().sort([(field, pymongo.ASCENDING)]))


def queryOne(coll, field, value):
    return queryOneDict(coll, {field:value})


def queryOneDict(coll, query):
    return coll.find_one(query)


def queryAll(coll, field, value):
    return queryAllDict(coll, {field:value})


def queryAllDict(coll, query):
    return coll.find(query)


def upsertNamedRecord(coll, data):
    try:
        name = data['name']
    except KeyError:
        raise StandardError("Record to be updated must have name field.")
    del data["name"]
    for key in data.keys():
        if data[key] is None:
            del data[key]
    updateQuery = {"$set": data}
    return coll.update_one({"name": name}, updateQuery, upsert=True)


def collectionUI(coll):
    pass

def getInput():
    try:
        response = raw_input()
    except SyntaxError:
        return None
    return response

def ingredientUI(db):
    print "You selected to work with ingredients in the database."
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
            ings = queryAllValuesOf(db.ingredients, "name")
            for ing in ings:
                print ing
        elif response == "2":
            print "Which ingredient would you like to know more about?"
            response = getInput()
            data = queryOne(db.ingredients, "name", response)
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
    oldData = queryOne(db.ingredients, "name", name)
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
        data['parent.'+response] = True
    else:
        data['parent'] = None
    print "Default unit:"
    data['default unit'] = getInput()
    print "1 count of this ingredient is how much default unit? (Quantity -> Volume)"
    data['units per count'] = getInput()
    print "Decomposition information:"
    data['decomposition'] = getInput()
    print "\nYou are about to create or update a record as follows:"
    printDict(data)
    print "Confirm? (Y to confirm, N to try again, B to go back)"
    response = getInput()
    if response in ['y', 'Y', 'yes']:
        upsertNamedRecord(db.ingredients, data)
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


def addCookingUI(db):
    pass

def addPrepUI(db):
    pass

def main():
    print "Connecting to recipe knowledge base..."
    try:
        db = connectToKB()
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
            run = addCookingUI(db)
        elif response == "3":
            run = addPrepUI(db)
        elif response == "Q" or response == "q" or response == "quit":
            run = False
        else:
            print "Response not recognized. Please try again.\n"


    print "Exiting..."
    db.client.close()

main()