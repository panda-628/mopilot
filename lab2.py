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

from structure import *
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


def generate_baseline_prompt(name,description):
    prompt_list ={
        'prompt':'',
        'name':'',
        }
    message = []
    # c:running_params["run_llm"]
    prompt = PROMPT_MODEL_1_ROUND.format(description)
    message = [
        {"role": "user", "content": f"{prompt}"}    
    ]
    prompt_list['prompt'] = message
    prompt_list['name'] = name
    
    return prompt_list



def run_llm(prompt_list,llm,temperature,max_tokens,top_p,frequency_penalty,presence_penalty):
    log = []
    message = []
    prompt = prompt_list['prompt']

    os.environ['http_proxy'] = ''#your proxy
    os.environ['https_proxy'] = ''#your proxy
    
    openai.api_key='xx - xxxxxxxxxxxxxxxxxxxxx'


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



class StateMachineCSV:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.pre_result_list =[]
        self.base_result_list =[]
        self.pre_result=[]
        self.base_result=[]
        self.state = -1
        self.AI = 0
        self.cycle =1

    def process_csv(self):
        with open(self.csv_file, newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            for row in csv_reader:
                if row:
                    self._state_transition(','.join(i for i in row))
        return self.pre_result_list,self.base_result_list
    

    def _state_transition(self, row):
        if self.state ==-1:
            if f'---------------------{self.cycle}/30------' in row:
                self.state=0
                print(f'cycle--{self.cycle}')
                self.cycle+=1
                self.pre_result =[]
                self.base_result=[]
        elif self.state == 0:
            if "---------------------Prediction AI:" in row: 
                
                print(f'读取Prediction{row}')
                self.state = 1
            elif "----------------------Baseline AI:" in row:  
                
                print(f'读取Baseline{row}')
                self.state = 4
        elif self.state == 1:
            
            if "AI:" in row:
                
                self.state = 2
        elif self.state ==2:
           
            if "AI:" in row :
                
                row = row.partition("AI:")[2]
                
                self.pre_result.append(row)
                self.state = 3
        elif self.state ==3:
            if "------------------------------------------------------------" in row:
                self.state = 6
            else:
                self.pre_result.append(row)
        elif self.state == 4:
            if "AI:" in row:
                row = row.partition("AI:")[2]
                self.base_result.append(row)
                self.state = 5
        elif self.state == 5:
                
                if "------------------------------------------------------------" in row:
                    self.state = 7
                else:
                    self.base_result.append(row)
        elif self.state ==6:
            self.pre_result_list.append(self.pre_result)
            self.state=0
        elif self.state == 7:
            self.base_result_list.append(self.base_result)
            self.state=-1
        


def calculate(number_class_exact_match,number_class_generated,number_class_solution,number_attribute_exact_match,number_attribute_generated,number_attribute_solution):
    
    if number_class_generated:
      class_precision = number_class_exact_match / number_class_generated
    else:
       class_precision = 0
    if number_class_solution:
      class_recall = number_class_exact_match / number_class_solution
    else:
      class_recall = 0
    if (class_precision + class_recall)==0:
       class_f1 = 0
    else:
      class_f1 = (2 * class_precision * class_recall) / (class_precision + class_recall)
      
    if number_attribute_generated == 0 :
       attribute_precision = 0
    else:
      attribute_precision = number_attribute_exact_match / number_attribute_generated
    if number_attribute_solution:
      attribute_recall = number_attribute_exact_match / number_attribute_solution
    else:
       attribute_recall = 0
    # attribute_f1
    if (attribute_precision + attribute_recall)==0:
       attribute_f1 = 0
    else:
      attribute_f1 = (2 * attribute_precision * attribute_recall) / (attribute_precision + attribute_recall)

    result = [class_precision,class_recall,class_f1,attribute_precision,attribute_recall,attribute_f1,number_class_exact_match,number_class_generated,number_class_solution,number_attribute_exact_match,number_attribute_generated,number_attribute_solution]
    return result



def main():
    temperature = running_params['temperature']
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

    baseline_score_file = f'{path}/{new_folder}/baseline_each_ex_score.csv' 
    bs=open(baseline_score_file,"w")
    print(f'system_name,cycle,Class_precision,class_recall,class_f1,attribute_precision,attribute_recall,attribute_f1,Class match, Class generate, Class oracle,Attribute match,Attribute generate, Attribute oracle',file=bs)


    for name,description,oracle_classes in zip(name_list,description_list,oracle_classes_list):
        output_classes_file = f'{path}/{new_folder}/{name}.csv'
        with open(output_classes_file,"w") as csvfile:
            writer = csv.writer(csvfile)
            log=[]
            input_log_file = f'{path}/{name}.csv'
            
            sum_test_result = [0,0,0,0,0,0]
            sum_baseline_result = [0,0,0,0,0,0]
            
            pre_prompt_list = generate_pre_prompt(name,description)
            
            
            base_prompt_list = generate_baseline_prompt(name,description)

            ora_cls_parser = FileParser()
            oracle_classes,oracle_relationships = ora_cls_parser.parseLines(oracle_classes)
            cycle =running_params['cycle']
            for c in range(1,cycle+1):
                
                log.append('-'*60)
                log.append('-'*60)
                log.append(f'---------------------{c}/{cycle}------{name}:')

                
                log.append('-'*60)
                log.append(f'---------------------Prediction AI:')
                pre_AI_answer,AI_log = run_llm(pre_prompt_list,running_params['llm'],temperature,running_params['max_tokens'],running_params['top_p'],running_params['frequency_penalty'],running_params['presence_penalty'])
                
                
                class_info_parse = FileParser()
                generated_classes,relationships = class_info_parse.parseLines(pre_AI_answer)
                log += AI_log
                log.append('-'*60)

                Pre_Ma = Matcher()
                matched_name = {}
                matched_class = {}
                unmatched_class = []
                
                matched_name,matched_class,unmatched_class,log_info = Pre_Ma.matchClasses(generated_classes,oracle_classes)
                log += log_info
                pre_score = calculate(Pre_Ma.matched_classes_count,Pre_Ma.generated_classes_count,Pre_Ma.oracle_classes_count,Pre_Ma.matched_attributes_count,Pre_Ma.generated_attributes_count,Pre_Ma.oracle_attributes_count)
                print(f'-{c}/{cycle}  {name} Prediction have done!')

                print(f'{name},{cycle},{pre_score[0]:4f},{pre_score[1]:4f},{pre_score[2]:4f},{pre_score[3]:4f},{pre_score[4]:4f},{pre_score[5]:4f},{Pre_Ma.matched_classes_count},{Pre_Ma.generated_classes_count},{Pre_Ma.oracle_classes_count},{Pre_Ma.matched_attributes_count},{Pre_Ma.generated_attributes_count},{Pre_Ma.oracle_attributes_count}',file=ps)

                
                log.append('-'*60)
                log.append(f'---------------------Baseline AI:')
                base_AI_answer,base_AI_log = run_llm(base_prompt_list,running_params['llm'],temperature,running_params['max_tokens'],running_params['top_p'],running_params['frequency_penalty'],running_params['presence_penalty'])
                
                log += base_AI_log
                log.append('-'*60)

                class_info_parse_base = FileParser()
                baseline_classes,relationships = class_info_parse_base.parseLines(base_AI_answer)

                Base_Ma = Matcher()
                matched_name = {}
                matched_class = {}
                unmatched_class = []
                
                matched_name,matched_class,unmatched_class,log_info = Base_Ma.matchClasses(baseline_classes,oracle_classes)
                base_score = calculate(Base_Ma.matched_classes_count,Base_Ma.generated_classes_count,Base_Ma.oracle_classes_count,Base_Ma.matched_attributes_count,Base_Ma.generated_attributes_count,Base_Ma.oracle_attributes_count)
                log += log_info
                print(f'-{c}/{cycle}  {name} Baseline have done!')


                print(f'{name},{cycle},{base_score[0]:4f},{base_score[1]:4f},{base_score[2]:4f},{base_score[3]:4f},{base_score[4]:4f},{base_score[5]:4f},{Base_Ma.matched_classes_count},{Base_Ma.generated_classes_count},{Base_Ma.oracle_classes_count},{Base_Ma.matched_attributes_count},{Base_Ma.generated_attributes_count},{Base_Ma.oracle_attributes_count}',file=bs)

                for j in range(0,6):
                    sum_test_result[j]+=pre_score[j]
                    sum_baseline_result[j]+=base_score[j]
                
                if c % 10 ==0:
                    
                    ave_test_result = [sum_test_result[j] / c for j in range(6)]
                    ave_base_result = [sum_baseline_result[j] / c for j in range(6)]
                    print(f'{name},{c} average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=ps)
                    print(f'{name},{c} average_score,{ave_base_result[0]:4f},{ave_base_result[1]:4f},{ave_base_result[2]:4f},{ave_base_result[3]:4f},{ave_base_result[4]:4f},{ave_base_result[5]:4f}',file=bs)
            for row in log:
                if row:
                    writer.writerow([row])
        
        ave_test_result = [sum_test_result[j] / cycle for j in range(6)]
        ave_base_result = [sum_baseline_result[j] / cycle for j in range(6)]
        print(f'{name} ,test_average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=ps)
        print(f'{name} ,baseline_average_score,{ave_base_result[0]:4f},{ave_base_result[1]:4f},{ave_base_result[2]:4f},{ave_base_result[3]:4f},{ave_base_result[4]:4f},{ave_base_result[5]:4f}',file=bs)
        print(f'{name},test_final_average_score,{ave_test_result[0]:4f},{ave_test_result[1]:4f},{ave_test_result[2]:4f},{ave_test_result[3]:4f},{ave_test_result[4]:4f},{ave_test_result[5]:4f}',file=a)
        print(f'{name},base_final_average_score,{ave_base_result[0]:4f},{ave_base_result[1]:4f},{ave_base_result[2]:4f},{ave_base_result[3]:4f},{ave_base_result[4]:4f},{ave_base_result[5]:4f}',file=a)
    
        
        
        print(f'-{name}: All round have done!')
        time.sleep(5)
       

    bs.close()
    ps.close()
    a.close()
    print('Finish!')


if __name__ == '__main__':
    main()