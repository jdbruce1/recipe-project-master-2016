'''Version 0.1'''

import urllib2
import requests
from bs4 import BeautifulSoup
import nltk

class Ingredient:
	def __init__(self,input_string):
		string_tokens = nltk.wordpunct_tokenize(input_string)
		if "/" in string_tokens:
			tokens_processed = []
			div_index = string_tokens.index("/")
			self.quant = div_strings(string_tokens[div_index-1],string_tokens[div_index+1])
			string_tokens = string_tokens[:(div_index-1)] + string_tokens[(div_index+2):]
		else:
			try:
				self.quant = float(string_tokens[0])
				string_tokens = string_tokens[1:]
			except ValueError:
				self.quant = None
		print str(self.quant) + str(string_tokens)

def div_strings(first, second):
	return float(first)/float(second)

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here

    url_to_strings(url)

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
	for string_in in strs_ingred:
		Ingredient(string_in)
	return 

def main():
	autograder("http://allrecipes.com/recipe/40154/shrimp-lemon-pepper-linguini/?internalSource=previously%20viewed&referringContentType=home%20page")

main()

