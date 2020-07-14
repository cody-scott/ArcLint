import json
import re
import datetime
import os

import arcpy

regex_flag_dict = {
    # 'ASCII' re.A, # this is py3 only so wont work in arcgis desktop
    'IGNORECASE': re.I,
    'LOCALE': re.L,
    "MULTILINE": re.M,
    "DOTMATCH": re.S,
    "UNICODE": re.U,
    "VERBOSE": re.X,
}

def main(json_path, feature, output_location=None, output_file_name=None):
    output_file = format_output_file(output_location, output_file_name)


    start_time = datetime.datetime.now()
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    json_obj = read_json(json_path)
    rule_data = compile_rules(json_obj)

    results = _arc_process(rule_data, feature)

    save_json(format_results(results, start_str), output_file)


def format_output_file(output_location, output_file_name):
    if output_location is None:
        output_location = ""
    if output_file_name is None:
        output_file_name = "results.json"

    if not output_file_name.endswith(".json"):
        output_file_name += ".json"

    return os.path.join(output_location, output_file_name)


def read_json(_json_path):
    js = None
    with open(_json_path, 'r') as fl:
        js = json.loads(fl.read())
    return js


def save_json(_json_data, output_file):
    with open(output_file, 'w') as fl:
        fl.write(json.dumps(_json_data))


def format_results(rule_data, _datetime_str): 
    # format fields
    # format groups
    out_fields = {}
    out_groups = {}

    for field in rule_data['Fields']:
        field_result = []
        for rule in rule_data['Fields'][field]:
            if not rule['output']:
                continue

            field_result.append({
                "ruleName": rule['ruleName'],
                "errorIDs": rule['result']
            })

        if len(field_result) == 0:
            continue

        out_fields[field] = field_result
    
    for group in rule_data['Groups']:
        out_groups[group] = {
            "errorIDs": rule_data['Groups'][group]['result'],
            'description': rule_data['Groups'][group]['description']
        }

    result = {
        "run_datetime": _datetime_str,
        "fields": out_fields,
        "groups": out_groups,
    }
    return result


def _arc_process(rule_data, feature):
    """
    impure function as i am modifying the rule_data

    input = {
        "Rules": rule_dict,
        "Fields": field_dict,
        "Groups": group_dict
    }
    returns dictionary of the rules"""
    fields = [field for field in rule_data['Fields']]
    
    with arcpy.da.SearchCursor(feature, ["OID@"] + fields) as sc:
        for row in sc:
            _id = row[0]

            for ix, value in enumerate(row[1:]):
                field_rules = rule_data['Fields'][fields[ix]]
                # append ID to each rule if they test = False
                [rule['result'].append(_id) for rule in field_rules if rule['rule'](value)]

            for group_name in rule_data['Groups']:
                group = rule_data['Groups'][group_name]
                group_func = any if group.get('match') == 'any' else all
                group_result = group_func([True if _id in r['result'] else False for r in group['rules']])
                if group_result == True:
                    group['result'].append(_id) 


    return rule_data


# region Linters
def regex_lint(value, _regex):
    # if regex is good, return true, else return false
    if len(_regex.findall(str(value))) > 0:
        return True
    else:
        return False


def range_lint(value, firstValue, secondValue, outside):
    lv = min(firstValue, secondValue)
    mx = max(firstValue, secondValue)

    result = True if value >= lv and value <= mx else False
    result = not result if outside else result 
    
    return result


# region builders
def compile_rules(json_obj):
    rule_dict = _compile_global_rules(json_obj)
    field_dict = _compile_field_rules(json_obj, rule_dict)
    group_dict = _compile_group_rules(json_obj, field_dict)
    return {
        "Rules": rule_dict,
        "Fields": field_dict,
        "Groups": group_dict
    }


def _compile_global_rules(json_obj):
    """
    returns 
    rule name is either global_RULENAME for global or fieldname_RULENAME for field specific ones
    {
        rule_name: rule_function > str: function
    }
    """
    rule_dict = {}
    for rule in json_obj.get('globalRules', []):
        rule_name = rule.get('ruleName', '').upper()
        nm = 'global_{}'.format(rule_name)
        f = _parse_rule(rule)
        rule_dict[nm] = f
    return rule_dict


def _compile_field_rules(json_obj, rule_dict):
    """
    returns:
    {
        FieldName > str: {
            'result': [] > str: list,
            'ruleName': ruleName > str: str,
            'rule': rule_dict[fieldname_rule_name] > str: function, 
        }
    }
    """
    field_dict = {}
    for field in json_obj.get('fields', []):
        field_rules = []

        field_name = field.get('fieldName')
        for rule in field.get('rules', []):
            rule_name = rule.get('ruleName', '').upper()
            rule_type = rule.get('type')
            output_rule = rule.get('output', True)
            nm = None
            if rule_type is None and 'global_{}'.format(rule_name) in rule_dict:
                nm = 'global_{}'.format(rule_name)                
            else:
                nm = '{}_{}'.format(field_name, rule_name)
                rule_dict[nm] = _parse_rule(rule)

            field_rules.append({
                'result': [],
                'ruleName': rule_name,
                'rule': rule_dict[nm],
                'output': output_rule
            })
        field_dict[field_name] = field_rules
    return field_dict


def _compile_group_rules(json_obj, field_dict):
    """
    rules are the address to the rule from the field dictionary. when updating the result in the field results, should be available here
    returns
    {
        group_name: {
            "result": [], # array of ids with errors,
            "match": "all" or "any", # type of match to test for
            "rules": [group_rules], # array of the rules for this group
        }
    }
    """
    group_dict = {}
    for group in json_obj.get("ruleGroups", []):
        group_name = group.get("groupName", "")
        match_type = group.get("match", "")
        group_rules = []
        for rule in group.get("rules", []):
            f = rule.get("fieldName")
            rn = rule.get("ruleName","").upper()
            group_rules += [r for r in field_dict[f] if r['ruleName']==rn]
        group_dict[group_name] = {
            "result": [],
            "match": match_type,
            "rules": group_rules,
            "description": group.get('description', '')
        }
    return group_dict


def _parse_rule(rule):
    func_dct = {
        'regex': _parse_regex,
        'range': _parse_range
    }

    return func_dct[rule.get('type')](rule)


# region parse rules
def _parse_regex(rule):
    _pattern = rule.get('pattern')
    flags = rule.get('flags', [])

    pat_flags = 0
    for f in flags:
        if f is None:
            continue
        pat_flags |= regex_flag_dict.get(f.upper(), 0)

    _regex = re.compile(_pattern, pat_flags)
    def f(x): return regex_lint(x, _regex)
    return f


def _parse_range(rule):
    f_value = rule.get('fromValue')
    s_value = rule.get('toValue')
    outside = rule.get('outside', False)
    def f(x): return range_lint(x, f_value, s_value, outside)
    return f


if __name__ == "__main__":
    feat = r"C:\Users\scody\Desktop\ArcPro Model\AllPipes2020\Data\ModelNetwork.gdb\facility_junction"

    main('facil_jct.json', feat)
