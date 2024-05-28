import json
import os
import csv
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

def generate_pre_prompt(name,description):
    prompt_list ={
        'prompt':'',
        'name':'',
        }
    message = []
    prompt1 = PROMPT_MODEL_2_ROUND["prompt1"].format(description)
    prompt2 = PROMPT_MODEL_2_ROUND["prompt2"]
    message = [
        {"role": "system", "content":"As a professional software architect, you are creating a class model."},
        {"role":"user","content":f"{prompt1}"},
        {"role":"user","content":f"{prompt2}"}
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name

    return prompt_list

def generate_baseline_prompt(name,description):
    prompt_list ={
        'prompt':'',
        'name':'',
        }
    message = []
    prompt1 = PROMPT_MODEL_1_ROUND.format(description)
    message = [
        {"role": "system", "content":"Generate the lists of model classes and associations from a given description. There are only 3 types of associations: associate, inherit, contain. Do not use other name for associations."},
        {"role":"user","content":f"{prompt1}"},
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name

    return prompt_list



def run_llm(prompt_list,llm,temperature,max_tokens,top_p,frequency_penalty,presence_penalty):
    log = []
    message = []
    prompt = prompt_list['prompt']

    os.environ['http_proxy'] = 'http://127.0.0.1:10809'
    os.environ['https_proxy'] = 'http://127.0.0.1:10809'
    
    openai.api_key=''
    # client = OpenAI(
        # base_url="https://api.gptsapi.net/v1",
        # api_key="sk-25Xdd89e6e1e84e7ea52378d7b82362253a53995eb52vUzn"
        # )
    message.append(prompt[0])
    for i in range(1,len(prompt)):
        message.append(prompt[i])
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = message,
            temperature = temperature,
            max_tokens = max_tokens,
            top_p = top_p,
            frequency_penalty = frequency_penalty,
            presence_penalty = presence_penalty,

            )
        User_message = prompt[i]['content']
        AI_answer = response.choices[0].message.content
        print("LLM_AI_answer:",AI_answer)
        log.append(f'User:{User_message}\nAI:{AI_answer}')
        message.append({"role":"assistant","content":f'{AI_answer}'})
        log.append(f'\n')
        
    return AI_answer,log


def main_association_relationship(f_relation_file,f_inherit_file,AI_answer,generated_classes,matched_name,name,description,oracle_relationships_list):

    prompt_classes = []
    for i in generated_classes:
        cls_name = i.getName()
        name = f'+ {cls_name}()\n'
        prompt_classes.append(name)
    
    print("AI_answer:",AI_answer)
    print(f'AI_answer:{AI_answer}',file = f_relation_file)
    generated_relationship_parser = RelationshipParser()
    generated_relationships_list = []

    print(f'AI_answer_after_cut:{AI_answer}',file = f_relation_file)
    print("AI_answer_after_cut:",AI_answer)
    for i in AI_answer.split('\n'):
        if i == '':
            continue
        generated_relationships = generated_relationship_parser.parse(i)
        if generated_relationships is None:
                print('i = ',i)
                continue
        generated_relationships_list.append(generated_relationships)

    
    mat = Matcher()
    mat.matchRelationship(generated_relationships_list,oracle_relationships_list,matched_name)
    print(f'generated_associations_count,{ mat.generated_associations_count}',file=f_relation_file)
    print(f'matched_associations_count,{ mat.matched_associations_count}',file=f_relation_file)
    print(f'oracle_associations_count,{ mat.oracle_associations_count}',file=f_relation_file)
    return mat.generated_associations_count,mat.matched_associations_count,mat.oracle_associations_count




def main_inherit_relationship(f_relation_file,f_inherit_file,AI_answer,generated_classes,matched_name,name,description,oracle_relationships_list):

    prompt_classes = []
    for i in generated_classes:
        cls_name = i.getName()
        name = f'+ {cls_name}()\n'
        prompt_classes.append(name)
    
    print("AI_answer:",AI_answer)
    print(f'AI_answer:{AI_answer}',file = f_inherit_file)
    generated_relationship_parser = RelationshipParser()
    generated_relationships_list = []

    print(f'AI_answer_after_cut:{AI_answer}',file = f_inherit_file)
    print("AI_answer_after_cut:",AI_answer)
    for i in AI_answer.split('\n'):
        if i == '':
            continue
        generated_relationships = generated_relationship_parser.parse(i)
        if generated_relationships is None:
                print('i = ',i)
                continue
        generated_relationships_list.append(generated_relationships)

    
    mat = Matcher()
    mat.matchRelationship(generated_relationships_list,oracle_relationships_list,matched_name)
    
    print(f'generated_inheritances_count,{ mat.generated_inheritances_count}',file=f_inherit_file)
    print(f'matched_inheritances_count,{ mat.matched_inheritances_count}',file=f_inherit_file)
    print(f'oracle_inheritances_count,{ mat.oracle_inheritances_count}',file=f_inherit_file)
    return mat.generated_inheritances_count,mat.matched_inheritances_count,mat.oracle_inheritances_count




def main(temperature):
    path = file['baseline_path']
    os.chdir(path)
    time_now = datetime.datetime.now()
    a1 = tuple(time_now.timetuple()[0:9])
    start_time = time.mktime(a1)
    if running_params['llm'] == 'gpt3.5':
        new_folder_cls = str(start_time)+'-'+running_params['llm']+'-tem'+str(temperature)+'-'+str(running_params['run_llm'])+'round-'+str(running_params['cycle'])+'cycle'
    os.makedirs(new_folder_cls)


    os.chdir(path)
    if running_params['llm'] == 'gpt3.5':
        new_folder = 'relaitonship-tem-' + str(running_params['temperature_relation']) + 'time-' + str(time.time())
    os.makedirs(new_folder)

    cycle = running_params['cycle']
    model_file = file['model_file']
    oracle_dataset = pd.read_csv(file['model_file'],encoding='UTF-8')

    name_list = oracle_dataset['Name']
    description_list = oracle_dataset['Description']
    oracle_classes_list = oracle_dataset['Classes']
    oracle_relationships_list = oracle_dataset['Associations']

    all_score_file = f'{path}/{new_folder_cls}/all_score.csv' 
    a = open(all_score_file,"w",encoding='UTF-8')
    cycle = running_params['cycle']
    print(f'system,{cycle} times,Ave_Test_Class_precision,\tAve_class_recall,\tAve_class_f1,\tAve_attribute_precision,\tAve_attribute_recall,\tAve_attribute_f1,',file=a)

    prediction_score_file = f'{path}/{new_folder_cls}/base_each_ex_score.csv' 
    ps=open(prediction_score_file,"w",encoding='UTF-8')

    print(f'system_name,cycle,Class_precision,class_recall,class_f1,attribute_precision,attribute_recall,attribute_f1,Class match, Class generate, Class oracle,Attribute match,Attribute generate, Attribute oracle',file=ps)
    
    output_result_file = f'{path}/{new_folder}/summary_result.csv'
    s_result = open(output_result_file,'w',encoding='UTF-8')
    print('name,cycle,asso_presicion,asso_recall,asso_F1,inhe_precision,inhe_recall,inhe_F1',file=s_result)
    
    for name,description,oracle_classes,oracle_relationships in zip(name_list,description_list,oracle_classes_list,oracle_relationships_list):
        output_classes_file = f'{path}/{new_folder_cls}/{name}.csv'
        output_relation_file = f'{path}/{new_folder}/{name}_relation.csv'
        output_inherit_file = f'{path}/{new_folder}/{name}_inherit.csv'
        f_relation_file = open(output_relation_file,'w',encoding='UTF-8')
        f_inherit_file = open(output_inherit_file,'w',encoding='UTF-8')
        
        oracle_relationships_parser = RelationshipParser()
        after_parse_oracle_relationships_list = []
        for i in oracle_relationships.split('\n'):
            if i == '':
                continue
            i = i.strip()
            oracle_relationship = oracle_relationships_parser.parse(i)

            if oracle_relationship is None:
                print(i)
            after_parse_oracle_relationships_list.append(oracle_relationship)
        with open(output_classes_file,"w",encoding='UTF-8') as csvfile:
            writer = csv.writer(csvfile)
            log=[]
            
            base_prompt_list = generate_baseline_prompt(name,description)
            sum_test_result = [0,0,0,0,0,0]
            
            ora_cls_parser = FileParser()
            oracle_classes,oracle_relationships = ora_cls_parser.parseLines(oracle_classes)
            cycle =running_params['cycle']

            relationship_total_presicion = 0
            relationship_total_recall = 0
            relationship_total_F1 = 0

            average_rela_presicion = 0
            average_rela_recall = 0
            average_rela_F1 = 0

            for c in range(1,cycle+1):
                
                log.append('-'*60)
                log.append('-'*60)
                log.append(f'---------------------{c}/{cycle}------{name}:')

                log.append('-'*60)
                log.append(f'---------------------Baseline AI:')
                Base_AI_answer,AI_log = run_llm(base_prompt_list,running_params['llm'],temperature,running_params['max_tokens'],running_params['top_p'],running_params['frequency_penalty'],running_params['presence_penalty'])
                print(f'Base_AI_answer:{Base_AI_answer}',file=f_relation_file)
                print("Base_AI_answer:",Base_AI_answer)
                class_info_parse = FileParser()
                generated_classes,relationships = class_info_parse.parseLines(Base_AI_answer)
                log += AI_log
                log.append('-'*60)
                
                Ma = Matcher()
                matched_name = {}
                matched_class = {}
                unmatched_class = []
                matched_name,matched_class,unmatched_class,log_info = Ma.matchClasses(generated_classes,oracle_classes)
                print("matched_name :",matched_name)
                
                Base_Re_AI_answer = Base_AI_answer.partition("Relationships")[2]
                print(f'---------------------{c}/{cycle}------{name}:',file=f_relation_file)
                generated_associations_count,matched_associations_count,oracle_associations_count =main_association_relationship(f_relation_file,f_inherit_file,Base_Re_AI_answer,generated_classes,matched_name,name,description,after_parse_oracle_relationships_list)
                
                generated_inheritances_count,matched_inheritances_count,oracle_inheritances_count = main_inherit_relationship(f_relation_file,f_inherit_file,Base_Re_AI_answer,generated_classes,matched_name,name,description,after_parse_oracle_relationships_list)
                

                log += log_info
                
                print(f'-{c}/{cycle}  {name} Baseline have done!')
            
                generated_relationship_count = generated_associations_count+generated_inheritances_count
                matched_relationship_count = matched_associations_count+matched_inheritances_count
                oracle_relationship_count = oracle_associations_count+oracle_inheritances_count
                
                if generated_relationship_count:
                    relationship_presicion = matched_relationship_count / generated_relationship_count
                else:
                    relationship_presicion = 0
                if oracle_associations_count:
                    relationship_recall = matched_relationship_count / oracle_relationship_count
                else:
                    relationship_recall = 0
                if (relationship_presicion + relationship_recall):
                    relationship_f1 = 2*relationship_presicion*relationship_recall/(relationship_presicion+relationship_recall)
                else:
                    relationship_f1 = 0
                
                relationship_total_presicion += relationship_recall
                relationship_total_recall += relationship_recall
                relationship_total_F1 += relationship_f1

                print(f'presicion = {relationship_presicion}',file=f_relation_file)
                print(f'recall = {relationship_recall}',file=f_relation_file)
                print(f'F1 = {relationship_f1}',file=f_relation_file)

                pre_score = [0,0,0,0,0,0]
                classes_presicion = Ma.matched_classes_count / Ma.generated_classes_count
                classes_recall = Ma.matched_classes_count / Ma.oracle_classes_count
                if classes_presicion+classes_recall == 0:
                    classes_F1 = 0
                else:
                    classes_F1 = 2*classes_presicion*classes_recall/(classes_presicion + classes_recall)

                atr_presicion = Ma.matched_attributes_count / Ma.generated_attributes_count
                atr_recall = Ma.matched_attributes_count / Ma.oracle_attributes_count
                if atr_presicion+atr_recall == 0:
                    atr_F1 = 0
                else:
                    atr_F1 = 2*atr_presicion*atr_recall/(atr_presicion + atr_recall)
                
                print(f'{name},{cycle},{classes_presicion:4f},{classes_recall:4f},{classes_F1:4f},{atr_presicion:4f},{atr_recall:4f},{atr_F1:4f},{Ma.matched_classes_count},{Ma.generated_classes_count}, {Ma.oracle_classes_count},{Ma.matched_attributes_count},{Ma.generated_attributes_count}, {Ma.oracle_attributes_count}',file=ps)
                
                pre_score = [classes_presicion,classes_recall,classes_F1,atr_presicion,atr_recall,atr_F1]
                for j in range(0,6):
                    sum_test_result[j]+=pre_score[j]

                if c % 5 ==0:
                    ave_test_result = [sum_test_result[j] / c for j in range(6)]
                    print(f'{name},{c} average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=ps)
            
            for row in log:
                if row:
                    writer.writerow([row])
            ave_test_result = [sum_test_result[j] / cycle for j in range(6)]

            average_rela_presicion = relationship_presicion /cycle
            average_rela_recall = relationship_total_recall /cycle
            average_rela_F1 = relationship_total_F1 /cycle


            print(f'average_rela_presicion = {average_rela_presicion}',file=f_relation_file)
            print(f'average_rela_recall = {average_rela_recall}',file=f_relation_file)
            print(f'average_rela_F1 = {average_rela_F1}',file=f_relation_file)
            
            print(f'{name},summary_result,{average_rela_presicion:4f},{average_rela_recall:4f},{average_rela_F1:4f}',file=s_result)

            print(f'{name},final_average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=ps)  
            print(f'{name} ,base average,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=a)
            
            print(f'-{name}: All round have done!')
            f_relation_file.close()
            time.sleep(5)


    ps.close()
    a.close()  
    print('Baseline Finish!')


if __name__ == '__main__':
    main(0.7)