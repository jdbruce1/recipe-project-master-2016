'''Version 0.1'''

import urllib2
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import copy
import nltk
from knowledge_base_api import KnowledgeBase

kb = KnowledgeBase()

class Recipe:

    def __init__(self, ingredients, steps):
        self.ingredients = ingredients
        self.steps = steps


    def proteinTransform(self, transformType):

        if not(transformType == "vegetarian" or transformType == "pescatarian" or
                transformType == "meatify"):
            raise StandardError("Unrecognized transformation.")
        global kb
        newRecipe = Recipe(copy.copy(self.ingredients), copy.copy(self.steps))

        for ingredient in newRecipe.ingredients:
            ingredientInfo = kb.searchIngredientsFor(ingredient.name)
            if ingredientInfo:
                 try:
                     ingredient["parent"]["protein"]
                     categoryName = "protein." + ingredient["parent"]["protein"].keys()[0]
                     newCategory = kb.categoryTransform(categoryName, transformType)
                     if newCategory != categoryName:
                         newIngredientInfo = kb.getIngredientsWithParent(newCategory)[0]
                         ingredient.name = newIngredientInfo["name"]

                 except KeyError:
                     pass


    def diyTransformation(self, transformType):
        if not (transformType == "toDIY"):
            raise StandardError("Unrecognized transformation.")

        global kb
        newRecipe = Recipe(copy.copy(self.ingredients), copy.copy(self.steps))

        for ingredient in newRecipe.ingredients:
            try:
                if ingredient["parent"]["protein"]["broth"]:
                    recipeUrl = ingredient["parent"]["protein"]["broth"]["url"]
                    parsedRecipe = url_to_strings[recipeUrl] #TODO: url_to_strings to return [ingredients, steps]
                    addIng = parsedRecipe[0] 
                    addSteps = parsedRecipe[1]
                    newRecipe.ingredients+=addIng # assume to ok to list same ingredients twice for now
                    newRecipe.steps = addSteps + newRecipe.steps # new steps are first, so if "add stock" shows up later, it's ok
                    # need to do the same for tools once that's set up
            except KeyError:
                pass

            #NOTE: repeating code for now to avoid dealing with KeyError problems
             try:
                if ingredient["parent"]["sauce"]:
                    recipeUrl = ingredient["parent"]["sauce"]["url"]
                    parsedRecipe = url_to_strings[recipeUrl] #TODO: url_to_strings to return [ingredients, steps]
                    addIng = parsedRecipe[0] 
                    addSteps = parsedRecipe[1]
                    newRecipe.ingredients+=addIng # assume to ok to list same ingredients twice for now
                    newRecipe.steps = addSteps + newRecipe.steps # new steps are first, so if "add sauce" shows up later, it's ok
                    # need to do the same for tools once that's set up
            except KeyError:
                pass

    def healthTransformation(self, transformType):
        if not (transformType=="low-carb" or transformType=="low glycemic index"):
            raise StandardError("Unrecognized transformation.")

        #TODO once we know the API better

        

       

        
        





class Ingredient:
    def __init__(self,input_string):
        global kb
        string_tokens = [w.lower() for w in nltk.wordpunct_tokenize(input_string)]
        self.descriptor = []
        if "(" in string_tokens:
            openIndex = string_tokens.index("(")
            closeIndex = string_tokens.index(")")
            inParens = string_tokens[openIndex+1:closeIndex]
            self.descriptor += " ".join(inParens)
            string_tokens = string_tokens[:openIndex] + string_tokens[closeIndex+1:]

        if "/" in string_tokens:
            tokens_processed = []
            div_index = string_tokens.index("/")
            self.quant = div_strings(string_tokens[div_index-1],string_tokens[div_index+1])
            #print string_tokens
            if div_index > 1:
                self.quant += float(string_tokens[0])
            #string_tokens = string_tokens[:(div_index-1)] + string_tokens[(div_index+2):]
            string_tokens = string_tokens[(div_index+2):]
            #print string_tokens
            #print self.quant
        else:
            try:
                self.quant = float(string_tokens[0])
                string_tokens = string_tokens[1:]
            except ValueError:
                self.quant = None


        unitList = ["tablespoon", "tablespoons", "teaspoons", "teaspoon", "cup", "cups", "pound", "pounds", "ounce", "ounces", "can", "cans","package", "packages", "jar", "jars"]
        #NOTE: the unit list will eventually be stored in the DB, right?
        if string_tokens[0] in unitList:
            self.unit = string_tokens[0]
            string_tokens = string_tokens[1:]
        else:
            if self.quant:
                self.unit = "count"
            else:
                self.unit = None

        self.preparation = []
        if "," in string_tokens:
            commaIndex = string_tokens.index(",")
            self.preparation += " ".join(string_tokens[commaIndex+1:])
            string_tokens = string_tokens[:commaIndex]
            #TODO: need to add when prep method is part of ingredient name (e.g. "sliced mushrooms"); after DB is set up

        wholeName = " ".join(string_tokens)
        if kb.searchIngredientsFor(wholeName):
            self.name = wholeName
        else:
            mainindex = 0
            secondindex = 1
            foundMatch = False
            nameSoFar = ""
            while not foundMatch and mainindex < len(string_tokens):
                while secondindex <= len(string_tokens):

                    tempresult = kb.searchIngredientsFor(
                            " ".join(string_tokens[mainindex:secondindex]))

                    if tempresult:
                        nameSoFar = tempresult["name"]
                        foundMatch = True
                    elif foundMatch:
                        break
                    secondindex += 1

                if foundMatch:
                    break
                mainindex += 1
                secondindex = mainindex + 1

            if nameSoFar == "":
                print "Did not recognize an ingredient in string: " + wholeName
                self.name = wholeName
            else:
                self.name = nameSoFar
            string_tokens = string_tokens[:mainindex] + string_tokens[secondindex-1:]
            self.descriptor += string_tokens



        print str(self.descriptor) + " " + str(self.name)

def div_strings(first, second):
    return float(first)/float(second)

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here
    global kb
    url_to_strings(url)
    # kb = KnowledgeBase()

    results = []

    return results

def url_to_strings(url):
    # response = urllib2.urlopen(url)
    # html = response.read()
    # print html
    r = requests.get(url)
    cont = r.content
    soup = BeautifulSoup(cont, "html.parser")
    raw_ingred = soup.find_all('span', 'recipe-ingred_txt added')
    strs_ingred = [raw.text for raw in raw_ingred]
    raw_steps = soup.find_all('span', 'recipe-directions__list--item')
    strs_steps = [raw.text for raw in raw_steps]
    print strs_steps
    for string_in in strs_ingred:
        Ingredient(string_in)
    return






def main():
    autograder("http://allrecipes.com/recipe/214500/sausage-peppers-onions-and-potato-bake/?internalSource=staff%20pick&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/221314/very-old-meatloaf-recipe/?internalSource=staff%20pick&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/219331/pepperoni-pizza-casserole/?internalSource=rotd&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/40154/shrimp-lemon-pepper-linguini/?internalSource=previously%20viewed&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/72381/orange-roasted-salmon/?internalSource=rotd&referringId=416&referringContentType=recipe%20hub")
main()

