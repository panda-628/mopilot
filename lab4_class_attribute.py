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



def generate_pre_prompt(name,description):
    prompt_list ={
        'prompt':'',
        'name':'',
        }
    message = []
    prompt1 = PROMPT_MODEL_2_ROUND["prompt1"].format(description)
    prompt2 = PROMPT_MODEL_2_ROUND["prompt2"]
    message = [
        {"role":"user","content":f"{prompt1}"},
        {"role":"user","content":f"{prompt2}"}
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name

    return prompt_list

def run_llm(prompt_list,llm,temperature,max_tokens,top_p,frequency_penalty,presence_penalty):
    log = []
    message = []
    prompt = prompt_list['prompt']

    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    
    openai.api_key=' '

    for i in range(0,len(prompt)):
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
        log.append(f'User:{User_message}\nAI:{AI_answer}')
        message.append({"role":"assistant","content":f'{AI_answer}'})
        log.append(f'\n')
        
    return AI_answer,log




def main(temperature):
    path = file['path']
    os.chdir(path)
    time_now = datetime.datetime.now()
    a1 = tuple(time_now.timetuple()[0:9])
    start_time = time.mktime(a1)
    if running_params['llm'] == 'gpt3.5':
        new_folder = str(start_time)+'-'+running_params['llm']+'-tem'+str(temperature)+'-'+str(running_params['run_llm'])+'round-'+str(running_params['cycle'])+'cycle'
    os.makedirs(new_folder)

    cycle = running_params['cycle']
    model_file = file['model_file']
    oracle_dataset = pd.read_csv(file['model_file'],encoding='latin1')

    name_list = oracle_dataset['Name']
    description_list = oracle_dataset['Description']
    oracle_classes_list = oracle_dataset['Classes']
    oracle_relationships_list = oracle_dataset['Associations']

    all_score_file = f'{path}/{new_folder}/all_score.csv' 
    a = open(all_score_file,"w")
    cycle = running_params['cycle']
    print(f'system,{cycle} times,Ave_Test_Class_precision,\tAve_class_recall,\tAve_class_f1,\tAve_attribute_precision,\tAve_attribute_recall,\tAve_attribute_f1,',file=a)

    prediction_score_file = f'{path}/{new_folder}/test_each_ex_score.csv' 
    ps=open(prediction_score_file,"w")

    print(f'system_name,cycle,Class_precision,class_recall,class_f1,attribute_precision,attribute_recall,attribute_f1,Class match, Class generate, Class oracle,Attribute match,Attribute generate, Attribute oracle',file=ps)


    for name,description,oracle_classes in zip(name_list,description_list,oracle_classes_list):
        output_classes_file = f'{path}/{new_folder}/{name}.csv'
        with open(output_classes_file,"w") as csvfile:
            writer = csv.writer(csvfile)
            log=[]
            
            pre_prompt_list = generate_pre_prompt(name,description)
            sum_test_result = [0,0,0,0,0,0]
            
            ora_cls_parser = FileParser()
            oracle_classes,oracle_relationships = ora_cls_parser.parseLines(oracle_classes)
            cycle =running_params['cycle']
            for c in range(1,cycle+1):
                
                log.append('-'*60)
                log.append('-'*60)
                log.append(f'---------------------{c}/{cycle}------{name}:')

                log.append('-'*60)
                log.append(f'---------------------Prediction AI:')
                Pre_AI_answer,AI_log = run_llm(pre_prompt_list,running_params['llm'],temperature,running_params['max_tokens'],running_params['top_p'],running_params['frequency_penalty'],running_params['presence_penalty'])

                class_info_parse = FileParser()
                generated_classes,relationships = class_info_parse.parseLines(Pre_AI_answer)
                log += AI_log
                log.append('-'*60)
                
                Ma = Matcher()
                matched_name = {}
                matched_class = {}
                unmatched_class = []

                matched_name,matched_class,unmatched_class,log_info = Ma.matchClasses(generated_classes,oracle_classes)
                log += log_info
                
                print(f'-{c}/{cycle}  {name} Prediction have done!')

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
            
            print(f'{name},final_average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=ps)

            
            print(f'{name} ,test average,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=a)

            print(f'-{name}: All round have done!')
            time.sleep(5)


    ps.close()
    a.close()  
    print('Finish!')


if __name__ == '__main__':
    tem_lst = [0.2,0.3,0.4,0.5,0.6,0.7,0.8]
    for tem in tem_lst:
        main(tem)