import os
import pandas as pd

# dir of current file
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, 'entities.pkl'), 'rb') as f:
    entities = pd.read_pickle(f)
    
    
# data frame is a fact, and one entity that is within that fact
# transform into a fact with a list of unqiue entity labels for that fact
facts_df = pd.DataFrame(columns=['fact', 'entity_names'])
facts_df['fact'] = entities['fact'].drop_duplicates().reset_index(drop=True)
facts_df['entity_names'] = entities['fact'].apply(lambda x: set([ent.name for ent in x.ents]))


# get unique list of facts
facts_series = entities['fact'].drop_duplicates().reset_index(drop=True)
entities_series = entities.groupby('fact')['name'].unique()

# get facts to the unique entities
facts_df = pd.concat(facts_series, entities_series, axis=1)



# function to get all ent names for a fact
def get_entity_names(series: pd.Series):
    # get all rows with fact == input fact
    return entities[entities['fact'] == series['fact']]['name']

# get set of entity labels for each fact. using the 
# facts_df['entity_names'] = entities['fact'].apply(lambda x: set([ent.name for ent in x.ents]))

facts_df['entity_names'] = entities.apply(get_entity_names, axis=1)


# pretty print df
print(facts_df)
# get first row
print(facts_df.iloc[0])
print('foo')