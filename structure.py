from config import *

from Levenshtein import ratio

KIND_CLASS = "class"
KIND_INHERITANCE = "inheritance"
KIND_ASSOCIATION = "association"
KIND_AGGREGATION = "aggregation"
KIND_ENUM = "enum"
class ClassDef:
    name = ""
    kind = ""
    attributes = []
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind
        self.attributes = []
    def getName(self):
        return self.name
    def getKind(self):
        return self.kind
    def getAttributes(self):
        return self.attributes
    def isMatched(self,oracle):
        if ratio(self.name.lower(),oracle.name.lower()) >= running_params['ratio']:
            return True
        else:
            cand=list(oracle.attributes)
            matched = 0
            for attr in self.attributes:
                for i in range(len(cand)):
                    if attr.isMatched(cand[i]):
                        matched += 1
                        cand.pop(i)
                        break
            union = len(self.attributes) + len(oracle.attributes) - matched
            if union:
                jacc = matched / (len(self.attributes) + len(oracle.attributes) - matched)
            else:
                jacc = 0
            return jacc >= running_params['jaccard']
    def isNameMatched(self,oracle):
        return ratio(self.name.strip().lower(),oracle.name.strip().lower()) >= running_params['ratio']
    
class Matcher:
    matched_classes_count = 0
    matched_attributes_count = 0
    matched_associations_count = 0
    matched_inheritances_count = 0

    generated_classes_count = 0
    generated_attributes_count = 0
    generated_associations_count = 0
    generated_inheritances_count = 0

    oracle_classes_count = 0
    oracle_attributes_count = 0
    oracle_associations_count = 0
    oracle_inheritances_count = 0

    def matchClasses(self,generated_classes,oracle_classes):
        log_info = []
        classes = generated_classes.copy()
        oracle = oracle_classes.copy()

        generated_counts = len(classes)
        oracle_counts = len(oracle)
        correct_counts = 0


        matched_name = {}
        matched_class = {}
        unmatched = []
        final_unmatched = []

        for cls in oracle:
            for str in cls.getAttributes():
                self.oracle_attributes_count +=1
        
        for cls in classes:
            for str in cls.getAttributes():
                self.generated_attributes_count +=1
            
        for cls in classes:
            flag = False
            for i in range(len(oracle)):
                if cls.isNameMatched(oracle[i]):
                    flag = True
                    matched_name[cls.getName().strip()] = oracle[i].getName().strip()
                    matched_class[cls] = oracle[i]
                    str = f' O  Class:{cls.getName()}  Oracle:{oracle[i].getName()}'
                    log_info.append(str)
                    matched_attr,log_atr = self.matchAttributes(cls.getAttributes(),oracle[i].getAttributes())
                    log_info+=(log_atr)
                    correct_counts += 1
                    oracle.pop(i)
                    break
            if not flag:
                unmatched.append(cls)
        for cls in unmatched:
            flag = False
            for i in range(len(oracle)):
                if cls.isMatched(oracle[i]):
                    flag = True
                    matched_name[cls.getName().strip()] = oracle[i].getName().strip()
                    matched_class[cls] = oracle[i]
                    str = f' O  Class:{cls.getName()}  Oracle:{oracle[i].getName()} '
                    log_info.append(str)
                    matched_attr,log_atr = self.matchAttributes(cls.getAttributes(),oracle[i].getAttributes())
                    log_info+=(log_atr)
                    correct_counts += 1
                    oracle.pop(i)
                    break
            if not flag:
                final_unmatched.append(cls)
                matched_name[cls.getName().strip()] = cls.getName().strip()
                str = f' X  Class:{cls.getName()}'
                log_info.append(str)
                for str in cls.getAttributes():
                    log_info.append(f'   X  Attribute:{str.getName()} ')
        
        
        self.matched_classes_count = correct_counts
        self.generated_classes_count = generated_counts 
        self.oracle_classes_count = oracle_counts
   
        return matched_name,matched_class,final_unmatched,log_info
    
    def matchAttributes(self,generated_attributes,oracle_attributes):
        log_info =[]
        matched_attr = {}
        attribute = generated_attributes.copy()
        oracle = oracle_attributes.copy()

        generated_counts = len(attribute)
        oracle_counts = len(oracle)
        correct_counts = 0
        log = []

        for attr in generated_attributes:
            flag = False
            if 'etc' in attr.getName() or '...' in attr.getName():
                continue
            for i in range(len(oracle)):
                if attr.isNameMatched(oracle[i]):
                    matched_attr[attr.getName()] = oracle[i].getName()
                    log_info.append(f'   O  Attribute:{attr.getName()}  Oracle:{oracle[i].getName()} ')
                    correct_counts += 1
                    flag = True
                    oracle.pop(i)
                    break
            if not flag:
                log_info.append( f'   X  Attribute:{attr.getName()} ')

        self.matched_attributes_count += correct_counts

        return matched_attr,log_info

    
    def matchRelationship(self,generated_relationships,oracle_relationships,classMap):

        matched_rel = {}
        relationship = generated_relationships.copy()
        oracle = oracle_relationships.copy()

        self.oracle_associations_count = sum(map(lambda x: 1 if x and x.getKind() != KIND_INHERITANCE else 0,oracle_relationships))
        self.oracle_inheritances_count = sum(map(lambda x: 1 if x and x.getKind() == KIND_INHERITANCE else 0,oracle_relationships))

        self.generated_associations_count = sum(map(lambda x: 1 if x.getKind() != KIND_INHERITANCE else 0,generated_relationships))
        self.generated_inheritances_count = sum(map(lambda x: 1 if x.getKind() == KIND_INHERITANCE else 0,generated_relationships))

        self.matched_associations_count = 0
        self.matched_inheritances_count = 0

        for rel in relationship:

            if rel.getSource() not in list(classMap.keys()) or rel.getTarget() not in list(classMap.keys()):
                if rel.getKind() == KIND_INHERITANCE:
                    self.generated_inheritances_count -= 1
                else:
                    self.generated_associations_count -= 1
                print("关系中的类并不是oracle中的")
                continue
            for i in range(len(oracle)):

                if rel.isMatched(oracle[i],classMap):
                    if rel.getKind() == KIND_INHERITANCE:
                        self.matched_inheritances_count += 1
                    else:
                        self.matched_associations_count += 1
                    matched_rel[rel] = oracle[i]
                    oracle.pop(i)
                    break

        return matched_rel
    
    def matchModel(self,generated_model,oracle_model):
        generated_classes,generated_relationships = generated_model
        oracle_classes,oracle_relationships = oracle_model
        matched_name, matched_class = self.matchClassesAndAttributes(generated_classes, oracle_classes)
        matched_rel = self.matchRelationship(generated_relationships,oracle_relationships,matched_name)
        return matched_class,matched_rel

    def matchClassesAndAttributes(self, generated_classes, oracle_classes):
        matched_name,matched_class = self.matchClasses(generated_classes,oracle_classes)
        for g_cls,o_cls in matched_class.items():
            self.matchAttributes(g_cls.getAttributes(),o_cls.getAttributes())
        return matched_name,matched_class
            
    
class AttributeDef:
    name = ""
    type = ""
    def __init__(self,name,type):
        self.name = name
        self.type = type
    def getName(self):
        return self.name
    def getType(self):
        return self.type
    def isMatched(self,oracle):
        if ratio(self.name.lower(),oracle.name.lower()) >= running_params['ratio'] and self.type == oracle.getType():
            return True
        return False
    def isNameMatched(self,oracle):
        if ratio(self.name.lower(),oracle.name.lower()) >= running_params['ratio']:
            return True
        return False

class RelationshipDef:
    source = ""
    target = ""
    kind = ""
    srcMulti=False
    trgMulti=False
    def __init__(self,source,target,kind,srcMulti,trgMulti):
        self.source = source
        self.target = target
        self.kind = kind
        self.srcMulti = srcMulti
        self.trgMulti = trgMulti
    def getSource(self):
        return self.source
    def getTarget(self):
        return self.target
    def getKind(self):
        return self.kind
    def getSrcMulti(self):
        return self.srcMulti
    def getTrgMulti(self):
        return self.trgMulti
    
    def isMatched(self,oracle,classMap):
        if self.getSource() not in list(classMap.keys()) or self.getTarget() not in list(classMap.keys()):
            return False
        if self.kind == KIND_INHERITANCE or self.kind == KIND_AGGREGATION:
            if self.getKind() != oracle.getKind():
                return False
            if  classMap[self.getSource()] == oracle.getSource() and classMap[self.getTarget()] == oracle.getTarget():
                return True
            return False
        if self.kind == KIND_ASSOCIATION :
            if oracle.getKind() == KIND_INHERITANCE:
                return False
            if classMap[self.getSource()] == oracle.getSource() or classMap[self.getTarget()] == oracle.getTarget():
                return True
            if classMap[self.getSource()] == oracle.getTarget() or classMap[self.getTarget()] == oracle.getSource():
                return True

        return False
    
    
