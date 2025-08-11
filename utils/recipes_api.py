import os, requests
SPOON_API='https://api.spoonacular.com/recipes/complexSearch'

def get_api_key():
    return os.environ.get('SPOONACULAR_API_KEY')

def search_recipes(query='',number=10,max_ingredients=None,max_ready_time=None,diet=None,intolerances=None):
    key=get_api_key()
    if not key:
        raise RuntimeError('Missing Spoonacular API key. Set SPOONACULAR_API_KEY in env or Streamlit Secrets.')
    params={'apiKey':key,'query':query or 'dinner','number':number,'addRecipeNutrition':True,'instructionsRequired':True,'sort':'popularity'}
    if max_ingredients: params['maxIngredientCount']=max_ingredients
    if max_ready_time: params['maxReadyTime']=max_ready_time
    if diet: params['diet']=diet
    if intolerances: params['intolerances']=intolerances
    r=requests.get(SPOON_API,params=params,timeout=30); r.raise_for_status(); return r.json().get('results',[])
