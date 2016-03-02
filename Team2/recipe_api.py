'''Version 0.1'''

import urllib2

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here

    parse(url)

    return results

def parse(url):
	response = urllib2.urlopen(url)
	html = response.read()
	print html

def main():
	autograder('http://allrecipes.com/recipe/44868/spicy-garlic-lime-chicken/?internalSource=popular&referringContentType=home%20page')

main()

