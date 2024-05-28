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

os.environ['http_proxy'] = ''#your proxy
os.environ['https_proxy'] = ''#your proxy

def generate_relation_prompt(name,classes,description):
    prompt_list ={
        'prompt':'',
        'name':'',
    }
    message = []
    prompt = PROMPT_MODEL_RELATION['prompt2'].format(description,classes)
    prompt1 = PROMPT_MODEL_RELATION['prompt1']
    answer1 = PROMPT_MODEL_RELATION['answer1']
    message = [
        {"role":"user","content":f'{prompt1}'},
        {"role":"assistant","content":f'{answer1}'},
        {"role": "user", "content": f'{prompt}'}    
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
    new_folder = 'all-relationships' + 'tem-' + str(running_params['temperature_relation']) + 'time-' + str(time.time())
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
for name,description,oracle_classes,oracle_relationship in zip(name_list,description_list,class_name_list_str_list,oracle_relationships_list):
    output_relation_file = f'{path}/{new_folder}/{name}_decompose_relation.csv'
    f_decompose_relation = open(output_relation_file,'w',encoding='UTF-8')

    oracle_relationships_parser = RelationshipParser()
    oracle_relationships_list = []
    for i in oracle_relationship.split('\n'):
        if i == '':
            continue
        print("按换行符读取的每一行i = ",i)
        oracle_relationship = oracle_relationships_parser.parse(i)

        if oracle_relationship is None:
            print('未解析成功的oracle_i:  ',i)
        elif oracle_relationship.getSource().__contains__(" ") or oracle_relationship.getTarget().__contains__(" "):
            print('未解析成功的oracle_i:  ',i)
            oracle_relationship = oracle_relationships_parser.parse(i)
            

        oracle_relationships_list.append(oracle_relationship)

    total_result_presicion = 0
    total_result_recall = 0
    total_result_F1 = 0

    for c in range(1,cycle+1):
        relation_prompt_list = generate_relation_prompt(name,oracle_classes,description)
        print("relation_prompt_list:",relation_prompt_list)

        inherit_relation_prompt_list = generate_inherit_relation_prompt(name,oracle_classes,description)
        print("inherit_relation_prompt_list:",inherit_relation_prompt_list)

        print(f'---------------------{c}/{cycle}------{name}:',file=f_decompose_relation)

        openai.api_key=' '
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = relation_prompt_list['prompt'],
            temperature = running_params['temperature_relation'],
            max_tokens = running_params['max_tokens'],
            top_p = running_params['top_p'],
            frequency_penalty = running_params['frequency_penalty'],
            presence_penalty = running_params['presence_penalty'],

            )
        AI_answer_association = response.choices[0].message.content
        print("AI_answer:",AI_answer_association)
        generated_relationship_parser = RelationshipParser()
        generated_relationships_list = []

        AI_answer_association = AI_answer_association.partition("Final Association Relationships:")[2].partition("# Final Composition Relationships:")[0] + AI_answer_association.partition("Final Composition Relationships:")[2].partition("# Final Inheritance Relationships:")[0] + AI_answer_association.partition("Final Inheritance Relationships:")[2]
        print(f'AI_answer_after_cut:{AI_answer_association}',file = f_decompose_relation)
        print("AI_answer_after_cut:",AI_answer_association)

        classMap = {}
        classMap_parser = FileParser()

        classMap_class = classMap_parser.parseLines(oracle_classes_list[map_flag])

        for i in classMap_class:
            for j in i:
                classMap[j.getName()] = j.getName()


        for i in AI_answer_association.split('\n'):
            if i == '':
                continue
            print("generated i = ",i)
            generated_relationships = generated_relationship_parser.parse(i)
            if generated_relationships is None:
                print('generated_i = ',i)
                continue

            generated_relationships_list.append(generated_relationships)

        mat1 = Matcher()
        mat1.matchRelationship(generated_relationships_list,oracle_relationships_list,classMap)


        response2 = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = inherit_relation_prompt_list['prompt'],
            temperature = running_params['temperature_relation'],
            max_tokens = running_params['max_tokens'],
            top_p = running_params['top_p'],
            frequency_penalty = running_params['frequency_penalty'],
            presence_penalty = running_params['presence_penalty'],

            )
        AI_answer_inheritance = response2.choices[0].message.content
        print("AI_answer:",AI_answer_inheritance)
        generated_inheritance_relationship_parser = RelationshipParser()
        generated_inheritance_relationships_list = []

        AI_answer_inheritance = AI_answer_inheritance.partition("# Final Inheritance Relationships:")[2]
        print(f'AI_answer_after_cut:{AI_answer_inheritance}',file = f_decompose_relation)
        print("AI_answer_after_cut:",AI_answer_inheritance)

        for i in AI_answer_inheritance.split('\n'):
            if i == '':
                continue
            print("generated i = ",i)
            generated_inheritance_relationships = generated_inheritance_relationship_parser.parse(i)
            if generated_inheritance_relationships is None:
                print('generated_i = ',i)
                continue
            generated_inheritance_relationships_list.append(generated_relationships)

        mat2 = Matcher()
        mat2.matchRelationship(generated_inheritance_relationships_list,oracle_relationships_list,classMap)


        if mat1.generated_associations_count + mat2.generated_inheritances_count == 0:
            result_presicion = 0
        else:
            result_presicion = (mat1.matched_associations_count + mat2.matched_inheritances_count) / (mat1.generated_associations_count + mat2.generated_inheritances_count)
            total_result_presicion += result_presicion
        result_recall = (mat1.matched_associations_count + mat2.matched_inheritances_count) / (mat1.oracle_associations_count + mat2.oracle_inheritances_count)
        total_result_recall += result_recall
        if result_presicion + result_recall == 0:
            result_F1 = 0
        else:
            result_F1 = 2*result_presicion*result_recall/(result_presicion + result_recall)
            total_result_F1 += result_F1

        print(f'result_presicion = {result_presicion}',file=f_decompose_relation)
        print(f'result_recall = {result_recall}',file=f_decompose_relation)
        print(f'result_F1 = {result_F1}',file=f_decompose_relation)

    average_result_presicion = total_result_presicion / cycle
    average_result_recall = total_result_recall / cycle
    average_result_F1 = total_result_F1 / cycle
    print(f'average_result_presicion = {average_result_presicion}',file=f_decompose_relation)
    print(f'average_result_recall = {average_result_recall}',file=f_decompose_relation)
    print(f'average_result_F1 = {average_result_F1}',file=f_decompose_relation)

    map_flag += 1

    f_decompose_relation.close()
    result_arr.append([name,average_result_presicion,average_result_recall,average_result_F1])
output_result_file = f'{path}/{new_folder}/summary_result.csv'
s_result = open(output_result_file,'w')
print('name,presicion,recall,F1',file=s_result)
for n,p,r,f in result_arr:
    print(f'{n},{p},{r},{f}',file=s_result)

s_result.close()