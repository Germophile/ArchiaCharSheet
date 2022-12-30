import gspread
import os
from git import Repo
import sys
import re

commit = False
if(len(sys.argv) > 1):
    if(sys.argv[1] == "git"): commit = True

gc = gspread.service_account()

table = gc.open_by_key("1Xx0MkkUTST5Th5Q6aNJObXq9fn5k5P0E8xQcO1HHeVw").sheet1.get_values()

def camelCase(string):
    return string[0].lower()+string[1:].replace(" ","")

class Ability_Type:
    def __init__(self,name,d,f,a,p,m,description):
        self.name = name
        self.sourceDict = []
        if(d == "TRUE"): self.sourceDict.append("d")
        if(f == "TRUE"): self.sourceDict.append("f")
        if(a == "TRUE"): self.sourceDict.append("a")
        if(p == "TRUE"): self.sourceDict.append("p")
        if(m == "TRUE"): self.sourceDict.append("m")
        self.description = description
        self.subtypes = []

    def subtype(self, Subtype):
        self.subtypes.append(Subtype)

    def print(self):
        string = self.name + " ("
        for letter in self.sourceDict: string += letter + ", "
        string = string[:len(string)-2] + ")\n"
        if(len(self.description)>0): string += self.description + "\n"
        for subtype in self.subtypes:
            string += subtype.string()
        print(string)

    def gmbinder(self):
        string = "#### " + self.name + " &nbsp;<span class=\"div-sh4\">"
        for letter in self.sourceDict: string += letter + " "
        string = string[:len(string)-1] + "</span>\n"
        if(len(self.description)>0): string += self.description + "\n"
        string += "___\n"
        for subtype in self.subtypes:
            string += subtype.gmbinder()
        return string


class Subtype:
    def __init__(self,name,costSP,typeSP,costAP,costAPC,description):
        self.name = name
        if(len(costSP)>0): self.costSP = int(costSP)
        else: self.costSP = 0
        self.typeSP = typeSP
        if(len(costAP)>0): self.costAP = int(costAP)
        else: self.costAP = 0
        if(len(costAPC)>0): self.costAPC = int(costAPC)
        else: self.costAPC = 0
        self.description = description
        self.modifiers = []
        self.symbol = {"Permanent":"■","Transient":"□","Either":"◩","AP":"♢"}
    
    def modifier(self,name,costSP,typeSP,repeatable,costAP,costAPC,description):
        self.modifiers.append(Modifier(name,costSP,typeSP,repeatable,costAP,costAPC,description,self.symbol))

    def string(self):
        string = "\t"
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        string += " " + self.name
        for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += " ("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        string += ": " + self.description + "\n"
        for modifier in self.modifiers:
            string += modifier.string()
        return string

    def gmbinder(self):
        string = "- "
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        string += " **" + self.name + " "
        for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += "("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        string += ":** " + self.description.replace("*","\*") + "\n"
        for modifier in self.modifiers:
            string += modifier.gmbinder()
        return string
    
    def roll20(self):
        string = ""
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        string += " " + self.name
        for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += " ("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        return string
        
class Modifier:
    def __init__(self,name,costSP,typeSP,repeatable,costAP,costAPC,description,symbol):
        self.name = name
        if(len(costSP)>0): self.costSP = int(costSP)
        else: self.costSP = 0
        self.typeSP = typeSP
        self.repeatableAP = False
        if(len(costAP)>0): 
            if("*" in costAP):
                self.repeatableAP = True
                self.costAP = int(costAP[costAP.index("*")+1:])
            else: self.costAP = int(costAP)
        else: self.costAP = 0
        if(len(costAPC)>0): self.costAPC = int(costAPC)
        else: self.costAPC = 0
        if(len(repeatable)>0): self.repeatable = repeatable
        else: self.repeatable = "none"
        self.description = description
        self.symbol = symbol
    
    def string(self):
        string = "\t\t"
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        string += " " + self.name
        for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += " ("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        string += ": " + self.description + "\n"
        return string

    def gmbinder(self):
        string = "- &nbsp;&nbsp;"
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        if(self.repeatable): string += "\*"
        string += " " + self.name
        if(self.repeatableAP): string += "\*"
        if(self.costAP > 0): string += " "
        for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += " ("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        string += ": " + self.description.replace("*","\*") + "\n"
        return string
    
    def roll20(self):
        string = ""
        if(self.repeatable == "none"):
            string = f'<br>{self.cost()}<input type="checkbox" name="{camelCase(self.name)}"> {self.name}{self.apCost()}: {self.description}</input>\n'
        elif(self.repeatable == "multiplier"):
            string = f'<br>{self.cost()}<input type="number" name="{camelCase(self.name)}"  step="1" value="0" min="0" max="10"> {self.name}{self.apCost()}: {self.description}</input>\n'
        elif(self.repeatable == "list"):
            string = f'<br>{self.cost()} {self.name}{self.apCost()}: '
            intermediate = self.description
            count = intermediate.count('*')
            for _ in range(count):
                string +=  intermediate[:intermediate.index("*")]
                intermediate = intermediate[intermediate.index("*")+1:]
                if(intermediate[0] == "("):
                    intermediate = intermediate[1:]
                    substring = intermediate[:intermediate.index(")")]
                    intermediate = intermediate[intermediate.index(")")+1:]
                else:
                    substring = re.split("\W+",intermediate)[0]
                    intermediate = intermediate[len(substring):]
                string += f'<input type="checkbox" name ="{camelCase(self.name+substring)}">{substring}</input>'     
            string += intermediate
        return string

    def cost(self):
        string = ""
        for _ in range(self.costSP): string += self.symbol[self.typeSP]
        return string

    def apCost(self):
        string = ""
        if(self.costAP > 0):
            string = " "
            for _ in range(self.costAP): string += self.symbol["AP"]
        if(self.costAPC > 0): 
            string += " ("
            for _ in range(self.costAPC): string += self.symbol["AP"]
            string += ")"
        return string

table.pop(0)
abilities = []
while(len(table)>0):
    if(len(table[0][0]) > 1):
        abilities.append(Ability_Type(table[0][0],table[0][1],table[0][2],table[0][3],table[0][4],table[0][5],table[0][13]))
        table.pop(0)
        while(len(table[0][6]) > 0):
            subtype = Subtype(table[0][6],table[0][8],table[0][9],table[0][11],table[0][12],table[0][13])
            table.pop(0)
            while(len(table[0][7]) > 0):
                subtype.modifier(table[0][7],table[0][8],table[0][9],table[0][10],table[0][11],table[0][12],table[0][13])
                table.pop(0)
            abilities[len(abilities)-1].subtype(subtype)
    else: table.pop(0)

for ability in abilities:
    print(ability.gmbinder())

class Source:
    def __init__(self, name, letter,abilities):
        self.name = name
        self.abilityTypes = []
        for ability in abilities:
            if letter in ability.sourceDict:
                self.abilityTypes.append(ability)

sourceDict = {
    "Divine":Source("Divine","d",abilities),
    "Profane":Source("Profane","f",abilities),
    "Arcane":Source("Arcane","a",abilities),
    "Primeval":Source("Primeval","p",abilities),
    "Mundane":Source("Mundane","m",abilities)
}
""" 
sourceDict["d"] = sourceDict["Divine"]
sourceDict["f"] = sourceDict["Profane"]
sourceDict["a"] = sourceDict["Arcane"]
sourceDict["p"] = sourceDict["Primeval"]
sourceDict["m"] = sourceDict["Mundane"] """

f = open("archia-charsheet.html")
html = f.read()
f.close()
f = open("archia-charsheet.css")
css = f.read()
f.close()

html = html.split("\n")
css = css.split("\n")

#write repeating_abilities html
repeating_abilities_index = html.index("    <!--repeating_abilities code below this will be modified by script-->")
del html[repeating_abilities_index+1:html.index("    <!--repeating_abilities code above this will be modified by script-->")]
repeating_abilities = "  <br>Source: <select name=\"attr_abilitySource\">\n    <option value=\"None\" selected=\"selected\"></option>\n"
for key in sourceDict:
    repeating_abilities += "    <option value=\"" + key + "\">" + key + "</option>\n"
repeating_abilities += "  </select>\n  <br>Ability Type: \n"
for key in sourceDict:
    repeating_abilities += "    <span class=\"" + key + "\">\n        <select name=\"attr_abilityType" + key + "\" class=\"abilityType " + key + "\">\n            <option value=\"None\" selected=\"selected\"></option>\n"
    for ability in sourceDict[key].abilityTypes:
        repeating_abilities += "            <option value=\"" + ability.name + "\">" + ability.name + "</option>\n"
    repeating_abilities += "        </select>\n    </span>\n"
repeating_abilities += "\n  <br>Ability Subtype: \n"
repeating_subtypes = ""
for ability in abilities:
    repeating_abilities += "    <span class=\"" + ability.name + "\">\n        <select name=\"attr_abilitySubtype" + ability.name + "\" class =\"abilitySubType " + ability.name + "\">\n            <option value=\"None\" selected=\"selected\"></option>\n"
    for subtype in ability.subtypes:
        repeating_abilities += "            <option value=\"" + subtype.name + "\">" + subtype.roll20() + "</option>\n"
        repeating_subtypes += "    <span class=\""+subtype.name.replace(" ","-")+"\">\n"
        for modifier in subtype.modifiers:
            repeating_subtypes += "        " + modifier.roll20()
        repeating_subtypes += "    </span>\n"
    repeating_abilities += "        </select>\n    </span>\n"
html.insert(repeating_abilities_index+1,repeating_abilities)
html.insert(repeating_abilities_index+2,repeating_subtypes)

#write repeating_abilities javascript
repeating_abilities_index = html.index("  <!--Repeating_abilities script:-->")
del html[repeating_abilities_index+1:html.index("  <!--/Repeating_abilities script-->")]
getAttrs = "\"repeating_abilities_abilitySource\",\"repeating_abilities_abilityType\",\"repeating_abilities_abilitySubtype\""
for source in sourceDict:
    getAttrs += ",\"repeating_abilities_abilityType" + source + "\""
repeating_abilities = f'''\n  on("change:repeating_abilities:abilitySource", function() {{
    getAttrs([{getAttrs}], function(values) {{
        var source = values.repeating_abilities_abilitySource;
        var type = values["repeating_abilities_abilityType"+source];
        setAttrs({{"repeating_abilities_abilityType":type}});
    }});
  }});'''
html.insert(repeating_abilities_index+1,repeating_abilities)

getAttrs = "\"repeating_abilities_abilityType\""
for ability in abilities:
    getAttrs += ",\"repeating_abilities_abilitySubtype" + ability.name + "\""
repeating_abilities = f'''\n  on("change:repeating_abilities:abilityType", function() {{
    getAttrs([{getAttrs}], function(values) {{
        var type = values.repeating_abilities_abilityType;
        var subtype = values["repeating_abilities_abilitySubtype"+type];
        setAttrs({{"repeating_abilities_abilitySubtype":subtype}});
    }});
  }});'''
html.insert(repeating_abilities_index+2,repeating_abilities)

repeating_abilities = ""
for source in sourceDict:
    repeating_abilities += f'''  on("change:repeating_abilities:abilityType{source}", function() {{
    getAttrs(["repeating_abilities_abilityType{source}"], function(values) {{
      setAttrs({{"repeating_abilities_abilityType":values.repeating_abilities_abilityType{source}}});
    }});
  }});
'''
for ability in abilities:
    repeating_abilities += f'''  on("change:repeating_abilities:abilitySubtype{ability.name}", function() {{
    getAttrs(["repeating_abilities_abilitySubtype{ability.name}"], function(values) {{
      setAttrs({{"repeating_abilities_abilitySubtype":values.repeating_abilities_abilitySubtype{ability.name}}});
    }});
  }});
'''
html.insert(repeating_abilities_index+3,repeating_abilities)

css = css[:css.index("/*Code below this point will be written by system-write*/")+1]

repeating_abilities = ""
for source in sourceDict:
    repeating_abilities += (f'''.charsheet  input.abilitySource:not([value="{source}"]) ~ div.editor > span.{source} {{
    display: none
}}\n''')
for ability in abilities:
    repeating_abilities += f'''.charsheet  input.abilityType:not([value="{ability.name}"]) ~ div.editor > span.{ability.name} {{
    display: none
}}\n'''
    for subtype in ability.subtypes:
        repeating_abilities += f'''.charsheet  input.abilitySubtype:not([value="{subtype.name}"]) ~ div.editor > span.{subtype.name.replace(" ","-")} {{
    display: none
}}\n'''

css.append(repeating_abilities)

#making the filetext and writing it to a file
def write(filetype, contents):
    filetext = ""
    for line in contents:
        filetext += line + "\n"
    f = open("archia-charsheet." + filetype, "w")
    f.write(filetext)
    f.close()
    
write("html", html)
write("css",css)

path_to_git = r"../.git"
commit_message = "commit from python script"

def git_push():
    try:
        repo = Repo(path_to_git)
        repo.git.add(update=True)
        repo.index.commit(commit_message)
        origin = repo.remote(name='origin')
        origin.push()
    except:
        print('Some error occured while pushing the code')    

if(commit): git_push()
