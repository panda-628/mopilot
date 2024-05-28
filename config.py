running_params = {
    'llm':'gpt3.5',
    'run_llm':2, 
    'cycle':10,
    'temperature': 0.7,
    'temperature_relation' : 0.3,
    'base-temperature': 0.7, 
    'temperature_inherit_relation':0.1,
    'max_tokens': 3000,
    'top_p': 1,
    'frequency_penalty': 0,
    'presence_penalty': 0,
    'ratio':0.9,
    'jaccard':0.6,
    'jaccard_ratio':0.9
}

file ={
    'path': ' ',#our approach output path
    'baseline_path': ' ',#baseline output path
    'our_path': ' ',#out approach output path
    'initial_file':' ',#system description
    'model_file':' ',#oracle
    'model_file_lab1':' '#oracle
}


PROMPT_MODEL_2_ROUND= {
'prompt1': """Generate the lists of enumerations, classes and attributes from a given <Description>.
#Description 
{}
""",
'prompt2': """List all the classes and enumerations using format:
Enumerations:
1.enumeration(literals):[one-sentence rationale]
2.enumeration(literals):[one-sentence rationale]
...
Classes:
1.classname(attributeName1: attributeType1, attributeName2: attributeType2 ):[one-sentence rationale]
2.classname(attributeName1: attributeType1, attributeName2: attributeType2 ):[one-sentence rationale]
...
""" 
}

PROMPT_MODEL_1_ROUND= """Generate the lists of enumerations, classes and attributes from a given <Description>.
List all the classes and enumerations using format:
Enumerations:
1.enumeration(literals):[one-sentence rationale]
2.enumeration(literals):[one-sentence rationale]
...
Classes:
1.classname(attributeName1: attributeType1, attributeName2: attributeType2 ):[one-sentence rationale]
2.classname(attributeName1: attributeType1, attributeName2: attributeType2 ):[one-sentence rationale]
...

#Description 
{}

"""

PROMPT_MODEL_BASE="""
Create a class diagram for the following description by giving the enumerations, classes, and relationships using format:
Enumerations:
1.enumerationName(literals)
2.enumerationName(literals)
(there might be no or multiple enumerations)

Class:
1.className(attributeName1 : attributeType1,attributeName2 : attributeType2 (there might be multiple attributes))
2.className(attributeName1 : attributeType1,attributeName2 : attributeType2 (there might be multiple attributes))
(there might be multiple classes)

Relationships:
mul1 class1 associate mul2 class2 (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*]).
(there might be multiple associations)

class1 inherit class2 (class1 and class2 are classes above)
(there might be multiple inheritance)

mul1 class1 contain mul2 class2 (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])
(there might be multiple composition)

#Description 
{}
"""

PROMPT_MODEL_RELATION="""
You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2023-04
Current date: [current date]

#TASK

Step1. To create a class model based on the <description> and the given <classes>, list all the Association relationships using the following format.

+ [mul1] [class1] associate [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*]). 

Step2. To create a class model based on the <description> and the given <classes>, list all the Composition relationships using the following format.

+ [mul1] [class1] contain [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])

Step3. Semantically check and remove the associations relationships generated above to ensure there are no redundant bidirectional associations. There is no need to display the results of this step

Step4. Semantically identify possible derived relations among the Association generated above. There is no need to display the results of this step.

Step5. Delete the derived relationships.There is no need to display the results of this step.

Step6. You need only to list the remaining associations relationships. Using the following format:
# Final Association Relationships:
+ [mul1] [class1] associate [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])
# Final Composition Relationships:
+ [mul1] [class1] contain [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])

#Description
{}

#Classes
{}
"""

PROMPT_MODEL_INHERIT_RELATION="""
You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2023-04
Current date: [current date]

#TASK
Step1. Clarify the difference between inheritance relationships and association relationships:
An Association declares that there can be links between objects of the associated classes. It is a "has-a" relationship.
Inheritance refers to the process of copying attributes and methods from the parent class to the subclass. It is an "is-a" relationship.
Step2. To create a class model based on the <description> and the given <classes>, only list all the inheritance(is-a) relationships using the following format strictly:
# Final Inheritance Relationships:
+ [class1] extends [class2] (class1 and class2 are classes above)
#Description
{}

#Classes
{}
"""

PROMPT_MODEL_ALL_RELATION="""
You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2023-04
Current date: [current date]

#TASK

Step1. To create a class model based on the <description> and the given <classes>, list all the Association relationships using the following format.

+ [mul1] [class1] associate [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options [0..*, 1, 0..1, 1..*]). 

Step2. To create a class model based on the <description> and the given <classes>, list all the Composition relationships using the following format.

+ [mul1] [class1] contain [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options [0..*, 1, 0..1, 1..*])

Step3. Semantically check and remove the associations relationships generated above to ensure there are no redundant bidirectional associations. There is no need to display the results of this step

Step4. Semantically identify possible derived relations among the Association generated above. There is no need to display the results of this step.

Step5. Delete the derived relationships.There is no need to display the results of this step.

Step6. Clarify the difference between inheritance relationships and association relationships:
An Association declares that there can be links between objects of the associated classes. It is a "has-a" relationship.
Inheritance refers to the process of copying attributes and methods from the parent class to the subclass. It is an "is-a" relationship.

Step7. To create a class model based on the <description> and the given <classes>, only list all the inheritance (is-a) relationships using the following format:
+ [class1] extends [class2] (class1 and class2 are classes above)

Step8. There is no need to display the results of the previous steps. If one of the generated relationships is empty, there is no need to print anything. You need to list the generated relationships strictly in the following format: 
# Final Association Relationships:
+ [mul1] [class1] associate [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])
# Final Composition Relationships:
+ [mul1] [class1] contain [mul2] [class2] (class1 and2 are classes above. mul1 and mul2 are one of the following options[0..*, 1, 0..1, 1..*])
# Final Inheritance Relationships:
+ [class1] extends [class2] (class1 and class2 are classes above)

#Description
{}

#Classes
{}
"""
if __name__ == "__main__":
    pass