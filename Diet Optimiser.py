import pandas as pd
import numpy as np
import sqlite3
import re
from pulp import LpProblem, LpVariable, lpSum, LpMaximize
cnx = sqlite3.connect('nutrition.db')
cursor = cnx.cursor()





### ----- CLEANING DATASET----- ###
df = pd.read_parquet('recipes.parquet', columns=['RecipeId', 'Name', 'RecipeCategory', 'RecipeIngredientParts', 'Calories', 'CarbohydrateContent','ProteinContent','FatContent', 'RecipeServings'])

cat = df.groupby('RecipeCategory')['RecipeId'].count()
df = df[df['RecipeCategory'].isin(cat[cat>500].index)]  # Only include categories > 500 recipes
df = df[df.RecipeCategory != 'Bath/Beauty']

remapping = {}
df['RecipeCategory'].replace(remapping, inplace=True)  # Reduce the number of categories to 59

mean_catg = np.round(df.groupby('RecipeCategory')['RecipeServings'].median())  # Fill missing serving values with median of its category
df['RecipeServings'] = df.apply(lambda row: mean_catg[row['RecipeCategory']] if pd.isna(row['RecipeServings']) else row['RecipeServings'], axis=1) 

df['Calories'] = df['Calories'] / df['RecipeServings']  # Adjust Kcal and Macros by servings 
df['CarbohydrateContent'] = df['CarbohydrateContent'] / df['RecipeServings']
df['ProteinContent'] = df['ProteinContent'] / df['RecipeServings']
df['FatContent'] = df['FatContent'] / df['RecipeServings']

df = df.drop(['RecipeServings'], axis=1)
df = df[(df.Calories > 20) & (df.Calories < 1500)]





### ----- CLASSIFYING OFFENSIVE CATEGORIES ----- ###
s = df.apply(lambda x: pd.Series(x['RecipeIngredientParts']),axis=1).stack().reset_index(level=1, drop=True) 
s = s[s.value_counts() > 1]  # Gets all ingredients out :)

def offensive_ingredients(offend, s_):
    offensive = []
    for x in offend:
        pattern = re.compile(r'\b{}(\S*-\S*)?\b'.format(re.escape(x)), flags=re.IGNORECASE)
        for i in s_.index:
            if pattern.search(i) and 'free' not in i.lower():  # Assume if 'free' is there then it doesn't have e.g. Dairy/Gluten
                offensive.append(i)
    return offensive

gluten_ingredients = []
gluten = offensive_ingredients(gluten_included, s)  # This returns all gluten ingredients (to best of its ability)

dairy_ingredients = []
dairy = offensive_ingredients(dairy_ingredients, s)

meat_ingredients = []
meat = offensive_ingredients(meat_ingredients, s)

seafood_ingredients = []
seafood = offensive_ingredients(seafood_ingredients, s)

egg_ingredients = []
egg = offensive_ingredients(egg_ingredients, s)

haram_ingredients = []
haram = offensive_ingredients(haram_ingredients, s)

df['Haram'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in haram for i in x) else 0)  # Create binary columns for if recipe contains offending ingredient
df['Egg'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in egg for i in x) else 0)
df['Seafood'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in seafood for i in x) else 0)
df['Meat'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in meat for i in x) else 0)
df['Dairy'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in dairy for i in x) else 0)
df['Gluten'] = df['RecipeIngredientParts'].apply(lambda x: 1 if any(i in gluten for i in x) else 0)





### ----- CREATE SQL TABLE ----- ###
cursor.execute("""CREATE TABLE recipe_info 
             (RecipeId INTEGER PRIMARY KEY,
              Name TEXT,
              RecipeCategory TEXT,
              RecipeIngredientParts TEXT,
              Calories REAL,
              CarbohydrateContent REAL,
              ProteinContent REAL,
              FatContent REAL,
              Haram BOOLEAN,
              Egg BOOLEAN,
              Seafood BOOLEAN,
              Meat BOOLEAN,
              Dairy BOOLEAN,
              Gluten BOOLEAN)""")

df.to_sql('recipe_info', cnx, if_exists='append', index=False)





### ----- SORTING BY PREFERENCES ----- ###
unwanted = ['Seafood', 'Meat']
WHERE = ' AND'.join(f' NOT {x}' for x in unwanted)
cursor.execute(f"""SELECT RecipeId, Name, RecipeCategory, Calories,CarbohydrateContent,ProteinContent,FatContent FROM recipe_info
                WHERE {WHERE}""")

valid_recipes = cursor.fetchall()
valid_recipes = pd.DataFrame(valid_recipes, columns = ['RecipeId','name', 'category', 'calories', 'carbs', 'protein', 'fat'])
valid = valid_recipes.sample(2000).reset_index(drop=True)  # Sample down so that prob.solve() can work :(





### ----- OPTIMISATION WITH PULP ----- ###
prob = LpProblem('max_recipes', LpMaximize)
variables = LpVariable.dicts('name', valid['RecipeId'], 0, 1, cat='Binary')

prob += lpSum([valid['calories'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]), "TotalCalories"  # Objective : Maximise Calories

kcal = 2000
carbs, protein, fat = (kcal * 0.4)/4 , (kcal * 0.3)/4,  (kcal * 0.3)/9  
prob += lpSum([valid['calories'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) <= kcal  # Constraints : kcal & Macros
prob += lpSum([valid['protein'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) >= protein * 0.75
prob += lpSum([valid['protein'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) <= protein
prob += lpSum([valid['carbs'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) >= carbs * 0.75
prob += lpSum([valid['carbs'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) <= carbs
prob += lpSum([valid['fat'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) >= fat * 0.75
prob += lpSum([valid['fat'][i] * variables[recipe] for i, recipe in enumerate(valid['RecipeId'])]) <= fat

cats = {}
for i, recipe in enumerate(valid['RecipeId']):  # Gets all RecipeId's per Category
    category = valid['category'].iloc[i]
    if category not in cats:
        cats[category] = []
    cats[category].append(variables[recipe])

max_recipes = 10
prob += lpSum(variables) <= max_recipes

prob += lpSum(cats['Dessert']) == 1  # Forces 1 Dessert
prob += lpSum(cats['Beverages']) + lpSum(cats['Dessert Drink']) == 1  # Forces 1 Drink

prob.solve()

optimised = [int(v.name[5:]) for v in prob.variables() if v.varValue > 0]
total = valid[valid.RecipeId.isin(optimised)]





### ----- OPTIMISED OUTPUT ----- ###
total[['name','calories','carbs','protein','fat']]
total.sum()[['calories','protein','carbs','fat']]























