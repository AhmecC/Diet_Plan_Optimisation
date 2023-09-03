import pandas as pd
import numpy as np
import sqlite3
from pulp import LpProblem, LpVariable, lpSum, LpMaximize
cnx = sqlite3.connect('nutrition.db')
cursor = cnx.cursor()




### ----- CLEANING DATASET----- ###
df = pd.read_parquet('recipes.parquet', columns=['RecipeId', 'Name', 'RecipeCategory', 'RecipeIngredientParts', 'Calories', 'CarbohydrateContent','ProteinContent','FatContent', 'RecipeServings'])

cat = df.groupby('RecipeCategory')['RecipeId'].count()
df = df[df['RecipeCategory'].isin(cat[cat>500].index)]  # Only include categories > 500 recipes
df = df[df.RecipeCategory != 'Bath/Beauty']

remapping = {
    'Smoothies' : 'Dessert Drink','Shakes' : 'Dessert Drink',
    'Savory Pies' : 'Pie',
    'Ham' : 'Pork',
    'Chicken' : 'Poultry',
    'Apple' : 'Fruit', 'Oranges' : 'Fruit', 'Pineapple' : 'Fruit',
    'Quick Breads' : 'Breads', 'Yeast Breads' : 'Breads',
    'Brown Rice' : 'Rice', 'White Rice' : 'Rice', 'Long Grain Rice' : 'Rice',
    'Pasta Shells' : 'Pasta', 'Penne' : 'Pasta', 'Spaghetti' : 'Pasta',
    'Yam/Sweet Potato' : 'Potato',
    'Drop Cookies' : 'Dessert',
    'Cauliflower' : 'Vegetable', 'Greens' : 'Vegetable', 'Lemon' : 'Vegetable', 'Onions' : 'Vegetable', 'Peppers' : 'Vegetable', 'Salad Dressings' : 'Vegetable', 'Spinach' : 'Vegetable',
    'Veal' : 'Cow', 'Roast Beef' : 'Cow',
    'Stock' : 'Sauce', 'Sauces' : 'Sauce', 'Clear Soup' : 'Sauce',
    'Punch Beverage' : 'Beverages',
    'Black Beans' : 'Beans',
    'Chicken Breast': 'Chicken', 'Chicken Thigh & Leg': 'Chicken', 'Whole Chicken':'Chicken',
    'Frozen Desserts': 'Dessert', 'Bar Cookie': 'Dessert', 'Cheesecake':'Dessert', 'Scones':'Dessert', 'Tarts':'Dessert'}
df['RecipeCategory'].replace(remapping, inplace=True)  # Reduce the number of categories to 59

mean_catg = np.round(df.groupby('RecipeCategory')['RecipeServings'].median())
df['Servings'] = df.apply(lambda row: mean_catg[row['RecipeCategory']] if pd.isna(row['RecipeServings']) else row['RecipeServings'], axis=1)  # Replace NaN servings with median for category
df['CaloriesOne'] = df['Calories'] / df['Servings']  # Adjust calories to reflect only for one serving
df = df.drop(['RecipeServings','Servings','Calories'], axis=1)

df = df[(df.Calories > 20) & (df.Calories < 2000)]  # Only recommend recipes with < 1500 calories 




### ----- CLASSIFYING OFFENSIVE CATEGORIES ----- ###





