'''Version 0.1'''

import urllib2
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import copy
import nltk.data
from knowledge_base_api import KnowledgeBase
from nltk.tokenize import sent_tokenize
# from nltk import tokenize

kb = KnowledgeBase()

class Recipe:

    def __init__(self, ingredients, steps):
        self.ingredients = ingredients
        self.steps = steps
        self.cooking_methods = []
        self.tools = []
        for step in steps:
            self.tools.append(step.tools)
            if step.action_type == 'cook':
                self.cooking_methods.append(step.action)
            step.print_step()
        self.primary_method = self.cooking_methods[-1]

    def convert_to_output(self):
        output_dict = {}
        output_dict["ingredients"] = [ing.convert_to_output() for ing in self.ingredients]
        output_dict["primary cooking method"] = self.primary_method
        output_dict["cooking methods"] = self.cooking_methods
        output_dict["cooking tools"] = self.tools
        return output_dict


    def proteinTransform(self, transformType):
        if not(transformType == "vegetarian" or transformType == "pescatarian" or
                transformType == "meatify"):
            raise StandardError("Unrecognized transformation.")
        global kb
        newRecipe = Recipe(copy.copy(self.ingredients), copy.copy(self.steps))

        for ingredient in newRecipe.ingredients:
            ingredientInfo = kb.searchIngredientsFor(ingredient.name)
            if ingredientInfo:
                categoryLineage = kb.getIngredientParentLineage(ingredientInfo)
                newIngredients = None
                if "protein" in categoryLineage:
                    while len(categoryLineage) > 0 and not newIngredients:
                        categoryName = categoryLineage[-1]
                        newIngredients = kb.categoryTransform(categoryName, transformType)
                        if newIngredients:
                            ingredient.name = newIngredients[0]
                        categoryLineage = categoryLineage[:-1]
        return newRecipe

    def diyTransformation(self, transformType):
        if not (transformType == "toDIY"):
            raise StandardError("Unrecognized transformation.")

        global kb
        newRecipe = Recipe(copy.copy(self.ingredients), copy.copy(self.steps))


        for ingredient in newRecipe.ingredients:
            ingredientInfo = kb.searchIngredientsFor(ingredient.name)
            if ingredientInfo:
                categoryLineage = kb.categoryLineage(ingredientInfo)

                if ("broth" in categoryLineage) or ("sauce" in categoryLineage):
                    recipeUrl = ingredientInfo["decomposition"]
                    parsedRecipe = parse_url_to_class(recipeUrl)
                    addIng = parsedRecipe.ingredients
                    addSteps = parsedRecipe.steps
                    newRecipe.ingredients+=addIng # assume to ok to list same ingredients twice for now
                    newRecipe.steps = addSteps + newRecipe.steps # new steps are first, so if "add stock" shows up later, it's ok
                      
            #except KeyError:
             #   pass

        return newRecipe

    def healthTransformation(self, transformType):
        if not (transformType in ["to-low-carb", "from-low-carb", "to-low-sodium", "from-low-sodium", "to-low-gi", "from-low-gi"]):
            raise StandardError("Unrecognized transformation.")

        field = ""
        avoid = ""
        if transformType == "to-low-carb":
            field = "carbLevel"
            avoid = "high"
        elif transformType == "from-low-carb":
            field = "carbLevel"
            avoid = "low"
        elif transformType == "to-low-sodium":
            field = "sodiumLevel"
            avoid = "high"
        elif transformType == "from-low-sodium":
            field = "sodiumLevel"
            avoid = "low"
        elif transformType == "to-low-gi":
            field = "glycemicIndex"
            avoid = "high"
        elif transformType == "from-low-gi":
            field = "glycemicIndex"
            avoid = "low"

        global kb
        newRecipe = Recipe(copy.copy(self.ingredients), copy.copy(self.steps))

        for ingredient in newRecipe.ingredients:
            ingredientInfo = kb.searchIngredientsFor(ingredient.name)
            try:
                if ingredientInfo[field] == avoid:
                    lineage = kb.getIngredientParentLineage(ingredientInfo)
                    newIngredient = self._searchForSimilarIngredient(field, avoid, lineage)
                    if newIngredient:
                        ingredient.name = newIngredient
                    else:
                        newRecipe.ingredients.remove(ingredient)
            except KeyError:
                print "Ingredient has no key for " + field

        return newRecipe

    def _searchForSimilarIngredient(self, field, avoid, lineage):
        while len(lineage) > 1:
            parentString = ".".join(lineage)
            ingredientList = kb.getIngredientsWithParent(parentString)
            for ingredient in ingredientList:
                try:
                    if ingredient[field] != avoid:
                        return ingredient["name"]
                except KeyError:
                    print "Ingredient has no key for " + field
            lineage = lineage[:-1]
        return None

        #TODO once we know the API better

        
prep_actions = ['whisk','drizzle','preheat','transfer','place','pour','stir','add','mix','boil','cover','sprinkle']
cook_actions = ['heat','cook','bake','simmer','fry','roast']
post_actions = ['remove','garnish','season','serve']
all_actions = prep_actions+cook_actions+post_actions

cooking_tools = ['oven','skillet']
prep_tools = ['knife','cup','bowl','dish']
all_tools = cooking_tools+prep_tools

class Step:
    def __init__(self,input_string,ingredient_list):
        global kb
        self.text = input_string
        string_tokens = [w.lower() for w in nltk.wordpunct_tokenize(input_string)]
        
        self.action = None
        index = 0
        while not self.action and index < len(string_tokens):
            if string_tokens[index] in prep_actions:
                self.action = string_tokens[index]
                self.action_type = 'prep'
            elif string_tokens[index] in cook_actions:
                self.action = string_tokens[index]
                self.action_type = 'cook'
            elif string_tokens[index] in post_actions:
                self.action = string_tokens[index]
                self.action_type = 'post'
            index += 1
        if not self.action:
            self.action_type = None
            print "Action unidentified in " + self.text
            self.action = 'unknown'

        string_tokens = string_tokens[index:]

        self.ingredients = []
        for ingredient in ingredient_list:
            if set(string_tokens) & set(nltk.wordpunct_tokenize(ingredient.name)):
                self.ingredients.append(ingredient)

        self.tools = []
        for tool in all_tools:
            if tool in self.text:
                self.tools.append(tool)

    def split_up(self):
        text_index = 0
        string_tokens = [w.lower() for w in nltk.wordpunct_tokenize(self.text)]
        while text_index < len(string_tokens):
            word = string_tokens[text_index]
            if word in all_actions and word != self.action:
                newBeforeStep = Step(trim_and_join(string_tokens[:text_index]), self.ingredients)
                newAfterStep = Step(trim_and_join(string_tokens[text_index:]), self.ingredients)
                return [newBeforeStep, newAfterStep]
            text_index += 1
        return [self]


    def print_step(self):
        print "\nText: "+self.text
        print "Action: "+self.action
        print "Ingredients: "+", ".join([i.name for i in self.ingredients])
        print "Tools: "+ str(self.tools)

def trim_and_join(str_tokens):
    while str_tokens[-1] == 'and' or str_tokens[-1] == ',':
        str_tokens = str_tokens[:-1]
    return ' '.join(str_tokens)


class Ingredient:
    def __init__(self,input_string):
        global kb

        #tokenize 
        string_tokens = [w.lower() for w in nltk.wordpunct_tokenize(input_string)]
        self.descriptor = []
        #make parenthesized things descriptors
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

        self.preparation = [""]
        if "," in string_tokens:
            commaIndex = string_tokens.index(",")
            self.preparation = ' '.join(string_tokens[commaIndex+1:])
            string_tokens = string_tokens[:commaIndex]
        #     prepIndex = 0
        #     for word in string_tokens[commaIndex+1:]:
        #         if word == "and":
        #             self.preparation[prepIndex] = self.preparation[prepIndex][:-1]
        #             self.preparation.append("")
        #             prepIndex += 1
        #             continue
        #         else:
        #             self.preparation[prepIndex] += word+" "
        #     self.preparation[prepIndex] = self.preparation[prepIndex][:-1]
        # else:
        #     self.preparation = None

        self.prep_desc = None
                # self.preparation += word + " "
            # if len(string_tokens[commaIndex+1:]) > 1:
            #     self.preparation += " ".join(string_tokens[commaIndex+1:])
            #     print "Prep looks like: "+str(self.preparation)
            #     string_tokens = string_tokens[:commaIndex]
            # else:
            #     self.preparation = string_tokens[commaIndex+1:]
            #     string_tokens = string_tokens[:commaIndex]
            #     print "Prep looks like: "+str(self.preparation)
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

        # print str(self.descriptor) + " " + str(self.name)

    def convert_to_output(self):
        # print "Processing " + self.name
        output_dict = {}
        output_dict["name"] = self.name
        output_dict["quantity"] = str(self.quant)
        output_dict["measurement"] = str(self.unit)
        output_dict["descriptor"] = str(self.descriptor)
        output_dict["preparation"] = str(self.preparation)
        output_dict["prep-description"] = str(self.prep_desc)
        return output_dict

    def print_ingredient(self):
        ing_dict = self.convert_to_output()
        ing_amount = ing_dict["quantity"] + " " + ing_dict["measurement"]
        ing_descript = " " + ing_dict["descriptor"]
        ing_name = " " + ing_dict["name"]
        ing_prep = ", " + ing_dict["preparation"]

        if ing_descript == []:
            ing_string = ing_amount + ing_name
        else:
            ing_string = ing_amount + ing_descript + ing_name
        if ing_prep != [""]:
            ing_string += ing_prep

        print ing_string
        return

def div_strings(first, second):
    return float(first)/float(second)

def print_out(obj,indent):
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                print_out(v,indent+"    ")
            elif k == "name":
                print '%s : %s' % (k, v)
            else:
                print indent + '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                print_out(v,indent+"    ")
            else:
                print indent + v
    else:
        print obj

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here
    global kb
    r = parse_url_to_class(url)
    #r_trans = r.healthTransformation("to-low-sodium")
    r_out = r.convert_to_output()
    print_out(r_out,"")

    results = []

    return results

def parse_steps(step_strings,ingredient_list):
    # tokenizer = nltk.data.load('tokenizers/punkt/english/pickle')
    # print step_strings
    parsed_steps = []
    for og_step in step_strings:
        if len(og_step) == 0:
            continue
        sentences = sent_tokenize(og_step)#tokenizer.tokenize(og_step)
        for sentence in sentences:
            parsed_steps.append(Step(sentence,ingredient_list))
    split_steps = []
    for step in parsed_steps:
        split_steps += step.split_up()
    print split_steps

    return split_steps


def parse_url_to_class(url):
    # response = urllib2.urlopen(url)
    # html = response.read()
    # print html
    try:
        r = requests.get(url)
        cont = r.content
        soup = BeautifulSoup(cont, "html.parser")
        raw_ingred = soup.find_all('span', 'recipe-ingred_txt added')
        strs_ingred = [raw.text for raw in raw_ingred]
        parsed_ingred = [Ingredient(string_in) for string_in in strs_ingred]
        raw_steps = soup.find_all('span', 'recipe-directions__list--item')
        strs_steps = [raw.text for raw in raw_steps]
        parsed_steps = parse_steps(strs_steps,parsed_ingred)
        parsed_recipe = Recipe(parsed_ingred,parsed_steps)
    except Exception:
        parsed_recipe = False
    return parsed_recipe

def interface():
    print "Welcome to the Recipe API"

    recipe = False
    while True:

        while not recipe:
            url = raw_input("Please enter a recipe url from AllRecipes.com: ")
            recipe = parse_url_to_class(url)

        print "Got it. What would you like to do?\n"
        print "1: View recipe"
        print "2: View ingredients"
        print "3: View steps"
        print "4: Transform recipe"
        print "5: Choose a different recipe"
        print "6: Quit"

        choices = ["1","2","3","4","5","6"]

        func = raw_input("\n")
        while func not in choices:
            func = raw_input("Please enter a number 1-6: ")

        if func == "1":
            print "\nPrinting your recipe:"
            print_out(recipe, " ")
        elif func == "2":
            print "\nGetting ingredient list:"
            recipe.printIngredients() #TODO: printIngredients in Recipe
        elif func == "3":
            print "\nGetting recipe steps:"
            recipe.printSteps() #TODO: printSteps in Recipe
        elif func == "4":
            while True:
                print "\nWhich transformation would you like to do?"
                print "1: Transform to vegetarian"
                print "2: Transform from vegetarian"
                print "3: Transform to pescatarian"
                print "4: Transform from pescatarian"
                print "5: Transform to DIY"
                print "6: Transform to low carb"
                print "7: Transform from low carb"
                print "8: Transform to low sodium"
                print "9: Transform from low sodium"
                print "10: Transform to low glycemic index"
                print "11: Transform from low glycemic index"
                print "12: Go back"

                transformType = raw_input("\n")

                tchoices = ["1","2","3","4","5","6","7","8","9","10","11","12"]
                while transformType not in tchoices:
                    transformType = raw_input("Please enter a number 1-12: ")


    

        result = 0
        if func == "1":
            print "\nGetting award names"
            result = get_awards(year)
        elif func == "2":
            print "\nGetting nominees"
            result = get_nominees(year)
        elif func == "3":
            print "\nGetting winners"
            print_winners(get_winner(year))
        elif func == "4":
            print "\nGetting hosts"
            result = get_hosts(year)
        elif func == "5":
            print "\nGetting presenters"
            result = get_presenters(year)
        elif func == "6":
            print "\nGetting red carpet results"
            best, worst, discuss = best_dressed(year)
            print "Best dressed: " + best
            print "Worst dressed: " + worst
            print "Most discussed: " + discuss
        elif func == "7":
            year = get_year()
        elif func == "8":
            break


        if result != 0:
            if isinstance(result, dict):
                print_dict(result)
            elif isinstance(result, list):
                print_list(result)

        print "\n"

    return


def main():
    #autograder("http://allrecipes.com/recipe/214500/sausage-peppers-onions-and-potato-bake/?internalSource=staff%20pick&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/221314/very-old-meatloaf-recipe/?internalSource=staff%20pick&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/219331/pepperoni-pizza-casserole/?internalSource=rotd&referringContentType=home%20page")
    #autograder("http://allrecipes.com/recipe/40154/shrimp-lemon-pepper-linguini/?internalSource=previously%20viewed&referringContentType=home%20page")
    autograder("http://allrecipes.com/recipe/72381/orange-roasted-salmon/?internalSource=rotd&referringId=416&referringContentType=recipe%20hub")
    interface()


if __name__ == '__main__':
    main()


