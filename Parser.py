import re

from structure import *

class ResultParser:
    def __init__(self):
        self.pattensAndHandlers = [] 

    def add(self,patten,handler):
        regex = re.compile(patten)
        self.pattensAndHandlers.append((regex,handler))
    
    def parse(self,input):
        input = input.strip()
        for regex,handler in self.pattensAndHandlers:
            match = regex.match(input)
            if match is not None:
                return handler(match)
        return None

class AttributeParser(ResultParser):
    regex = r'(.+)\s*:\s*(.+)'
    regex2 = r'(.+)'
    regex_oracle = r'(\S+)\s+(\S+)'
    def handler(self,match):
        name = match.group(1)
        type = match.group(2)
        return AttributeDef(name,type)
    def handler2(self,match):
        name = match.group(1)
        return AttributeDef(name,'')
    def handler_oracle(self,match):
        type = match.group(1)
        name = match.group(2)
        return AttributeDef(name,type)
    
    def __init__(self):
        super().__init__()
        self.add(self.regex,lambda match:self.handler(match))
        self.add(self.regex_oracle,lambda match:self.handler_oracle(match))
        self.add(self.regex2,lambda match:self.handler2(match))

class ClassParser(ResultParser):
    regex = r'\d+\.\s*[*]*\s*([^*(]+)\s*[*]*\s*[\(\{]([^()]*)[\)\}](\s*:.*)?'
    regex1 = r'[*]*\s*([a-zA-Z][^*(]*)\s*[*]*\s*\((.*)\)(\s*:.*)?'
    regex2 = r'\d+\.\s*[*]*\s*([^*(:]+)()(\s*:.*)?'
    def handler(self,match,kind):
        name = match.group(1)
        attribute_string = match.group(2)
        cls = ClassDef(name,kind)
        parser = AttributeParser()
        for attribute in attribute_string.split(','):
            attr = parser.parse(attribute)
            if attr is not None:
                cls.getAttributes().append(attr)
        return cls
    def __init__(self,kind):
        super().__init__()
        self.add(self.regex,lambda match:self.handler(match,kind))
        self.add(self.regex1,lambda match:self.handler(match,kind))
        self.add(self.regex2,lambda match:self.handler(match,kind))



class RelationshipParser(ResultParser): 

    def checkMultiplicity(self,mul):
        if mul is None:
            return False
        if mul.__contains__('..'):
            mul = mul.split('..')[1]
        if mul == '1':
            return False
        else:
            return True
    
    regex_association = r'[+\-]?\s*(\d+|[*]|\d+\.\.[0-9*]+)*\s*([A-Z].*)\s+associate\s+(\d+|[*]|\d+\.\.[0-9*]+)\s*([A-Z].*)'
    regex_aggregation = r'[+\-]?\s*(\d+|[*]|\d+\.\.[0-9*]+)*\s*([A-Z].*)\s+contain\s+(\d+|[*]|\d+\.\.[0-9*]+)\s*([A-Z].*)'

    def handler1(self,match,kind):
        mulSrc = self.checkMultiplicity(match.group(1))
        src = match.group(2)
        src = src.partition('(')[0]
        mulTrg = self.checkMultiplicity(match.group(3))
        trg = match.group(4)
        trg = trg.partition('(')[0]
        return RelationshipDef(src,trg,kind,mulSrc,mulTrg)
    
    regex_inheritance = r'[+\-]?\s*([A-Z].*)\s+extends\s+([A-Z].*)'
    regex_inheritance_baseline = r'[+\-]?\s*\d*\s*([A-Z].*)\s+inherit\s+([A-Z].*)'


    def handler2(self,match):
        src = match.group(1)
        src = src.partition('(')[0]
        trg = match.group(2)
        trg = trg.partition('(')[0]
        return RelationshipDef(src,trg,KIND_INHERITANCE,False,False)
    
    def __init__(self):
        super().__init__()
        self.add(self.regex_association,lambda match:self.handler1(match,KIND_ASSOCIATION))
        self.add(self.regex_aggregation,lambda match:self.handler1(match,KIND_AGGREGATION))
        self.add(self.regex_inheritance,lambda match:self.handler2(match))
        self.add(self.regex_inheritance_baseline,lambda match:self.handler2(match))

class FileParser:
    def parseLines(self,lines):
        list_classes = []
        list_relationships = []
        line_list = lines.split('\n')
        class_parser = ClassParser(KIND_CLASS)
        relation_parser = RelationshipParser()
        for line in line_list:
            line = line.strip()
            if line == '':
                continue
            if line.startswith('Enumeration:') or line.startswith('Enumerations:'):
                class_parser = ClassParser(KIND_ENUM)
            elif line.startswith('Classes:') or line.startswith('Class:'):
                class_parser = ClassParser(KIND_CLASS)
            else:
                class_result = class_parser.parse(line)
                if class_result is not None:
                    list_classes.append(class_result)
                else:
                    relation_result = relation_parser.parse(line)
                    if relation_result is not None:
                        list_relationships.append(relation_result)
                
        return list_classes,list_relationships
    