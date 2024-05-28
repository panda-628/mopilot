import json
import os
import time
import re
import pandas as pd
import shutil
import openai
import numpy as np
import datetime
import sys

import pandas as pd
import numpy as np


from collections import Counter
from Levenshtein import distance
from Levenshtein import ratio

from Parser import *
from config import *

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

def generate_relation_prompt(name,classes,description):
    prompt_list ={
        'prompt':'',
        'name':'',
    }
    message = []
    prompt = PROMPT_MODEL_RELATION.format(description,classes)
    message = [
        {"role": "user", "content": f"{prompt}"}    
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name

    return prompt_list

def generate_inherit_relation_prompt(name,classes,description):
    prompt_list ={
        'prompt':'',
        'name':'',
    }
    message = []
    prompt = PROMPT_MODEL_INHERIT_RELATION.format(description,classes)
    message = [
        {"role": "user", "content": f"{prompt}"}    
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name

    return prompt_list

path = file['path']
os.chdir(path)
if running_params['llm'] == 'gpt3.5':
    new_folder = 'tem-' + str(running_params['temperature_inherit_relation']) + 'inheritance' + '-time-' + str(time.time())
os.makedirs(new_folder)

cycle = running_params['cycle']
model_file = file['model_file']
oracle_dataset = pd.read_csv(file['model_file'],encoding='latin1')

name_list = oracle_dataset['Name']
description_list = oracle_dataset['Description']
oracle_classes_list = oracle_dataset['Classes']
oracle_relationships_list = oracle_dataset['Associations']

regex_class_name=pattern = r'([0-9A-Za-z]+(\s*[0-9a-zA-Z]*)*)(\(.*\))'
class_name_list_str_list = []
for classes in oracle_classes_list:
    matched_class_list = re.findall(regex_class_name,classes)
    matched_classes_name_list = []
    matched_class_name_list_str = ""
    for matched_class in matched_class_list:
        if(matched_class[0] == ''):
            matched_classes_name_list.append(matched_class[0] + "()")
            matched_class_name_list_str += matched_class[0]+"()" + '\n'
        else:
            matched_classes_name_list.append(matched_class[0] + "()")
            matched_class_name_list_str += "+" + matched_class[0]+"()" + '\n'
    class_name_list_str_list.append(matched_class_name_list_str)
    print("class_name_list_str_list:",class_name_list_str_list)

map_flag = 0
result_arr = []
for name,description,oracle_classes,oracle_relationships in zip(name_list,description_list,class_name_list_str_list,oracle_relationships_list):
    output_relation_file = f'{path}/{new_folder}/{name}_inheritance_relation.csv'
    f_inheritance_relation = open(output_relation_file,'w')


    oracle_relationships_parser = RelationshipParser()
    oracle_relationships_list = []
    for i in oracle_relationships.split('\n'):
        if i == '':
            continue
        oracle_relationships = oracle_relationships_parser.parse(i)

        if oracle_relationships is None:
            print('i:  ',i)
        oracle_relationships_list.append(oracle_relationships)


    total_presicion = 0
    total_recall = 0
    total_F1 = 0

    for c in range(1,cycle+1):
        inheritance_relation_prompt_list = generate_inherit_relation_prompt(name,oracle_classes,description)
        print("relation_prompt_list:",inheritance_relation_prompt_list)

        print(f'---------------------{c}/{cycle}------{name}:',file=f_inheritance_relation)

        openai.api_key=' '
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = inheritance_relation_prompt_list['prompt'],
            temperature = running_params['temperature_relation'],
            max_tokens = running_params['max_tokens'],
            top_p = running_params['top_p'],
            frequency_penalty = running_params['frequency_penalty'],
            presence_penalty = running_params['presence_penalty'],

            )
        AI_answer = response.choices[0].message.content
        print("AI_answer:",AI_answer)
        generated_inheritance_relationship_parser = RelationshipParser()
        generated_inheritance_relationships_list = []

        AI_answer = AI_answer.partition("Final Inheritance Relationships:")[2]
        print(f'AI_answer_after_cut:{AI_answer}',file = f_inheritance_relation)
        print("AI_answer_after_cut:",AI_answer)

        for i in AI_answer.split('\n'):
            if i == '':
                continue

            generated_inheritance_relationships = generated_inheritance_relationship_parser.parse(i)
            if generated_inheritance_relationships is None:
                print('i = ',i)
                continue

            generated_inheritance_relationships_list.append(generated_inheritance_relationships)
        classMap = {}
        classMap_parser = FileParser()

        classMap_class = classMap_parser.parseLines(oracle_classes_list[map_flag])

        for i in classMap_class:
            for j in i:
                classMap[j.getName()] = j.getName()

        mat = Matcher()
        mat.matchRelationship(generated_inheritance_relationships_list,oracle_relationships_list,classMap)
        if mat.generated_inheritances_count == 0:
            presicion = 0
        else:
            presicion = mat.matched_inheritances_count / mat.generated_inheritances_count
            total_presicion += presicion
        recall = mat.matched_inheritances_count / mat.oracle_inheritances_count
        total_recall += recall
        if presicion + recall == 0:
            F1 = 0
        else:
            F1 = 2*presicion*recall/(presicion + recall)
            total_F1 += F1
        print(f'presicion = {presicion}',file=f_inheritance_relation)
        print(f'recall = {recall}',file=f_inheritance_relation)
        print(f'F1 = {F1}',file=f_inheritance_relation)
    average_presicion = total_presicion / cycle
    average_recall = total_recall / cycle
    average_F1 = total_F1 / cycle
    print(f'average_presicion = {average_presicion}',file=f_inheritance_relation)
    print(f'average_recall = {average_recall}',file=f_inheritance_relation)
    print(f'average_F1 = {average_F1}',file=f_inheritance_relation)

    map_flag += 1

    f_inheritance_relation.close()
    result_arr.append([name,average_presicion,average_recall,average_F1])
output_result_file = f'{path}/{new_folder}/summary_result.csv'
s_result = open(output_result_file,'w')
print('name,presicion,recall,F1',file=s_result)
for n,p,r,f in result_arr:
    print(f'{n},{p},{r},{f}',file=s_result)

s_result.close()