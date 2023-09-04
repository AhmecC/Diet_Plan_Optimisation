## Diet Plan Optimisation
This is the back-end to an application that will return a list of recipes that maximises a specified calorie goal and macros (Protein, Carbs and Fat). You can specify your calorie goal and filter out recipes that include offensive ingredients (Dairy/Gluten etc...)
> Recipe data isn't perfectly categoried, so offending ingredients may still be included

## Skills Used:
In this project, I show proficiency  in **pandas** by effectively cleaning and manipulating the dataset to maximise the value gained. I leveraged **SQL** with sqlite3 to create a fast database to empower an efficient application. I showed my approach to an unfamiliar package **pulp**, showing how skillfully identified its capabilities to achieve my goal of optimisation.

## Extra Information:
- Dataset is from [Kaggle](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews)
- To reduce clutter ```list_of_lists.txt``` includes all long lists of words
- recipes without servings are median of category they're in
- kcal and macros are adjusted to reflect 1 serving
- ChatGPT lists of common dietary restrictions used to pinpoint offending ingredients
- Optimisation constrained by certain categories (e.g. Only one drink allowed)

