import json
import re

regex_flag_dict = {
    # 'ASCII' re.A, # this is py3 only so wont work in arcgis desktop
    'IGNORECASE': re.I,
    'LOCALE': re.L,
    "MULTILINE": re.M,
    "DOTMATCH": re.S,
    "UNICODE": re.U,
    "VERBOSE": re.X,
}

# region Linters
def regex_lint(value, _regex):
    # if regex is good, return true, else return false
    if len(_regex.findall(str(value))) > 0:
        return False
    else:
        return True


def range_lint(value, firstValue, secondValue):
    lv = min(firstValue, secondValue)
    mx = max(firstValue, secondValue)

    if value >= lv and value <= mx:
        return True
    else:
        return False


# region builders
def compile_rules(json_obj):
    rule_dict = compile_global_rules(json_obj)
    field_dict = compile_field_rules(json_obj, rule_dict)
    group_dict = compile_group_rules(json_obj, field_dict)
    return {
        "Rules": rule_dict,
        "Fields": field_dict,
        "Groups": group_dict
    }


def compile_global_rules(json_obj):
    rule_dict = {}
    for rule in json_obj.get('globalRules'):
        rule_name = rule.get('ruleName', '').upper()
        nm = 'global_{}'.format(rule_name)
        f = _parse_rule(rule)
        rule_dict[nm] = f
    return rule_dict


def compile_field_rules(json_obj, rule_dict):
    field_dict = {}
    for field in json_obj.get('fields', {}):
        field_rules = []

        field_name = field.get('fieldName')
        for rule in field.get('rules', []):
            rule_name = rule.get('ruleName', '').upper()
            
            nm = None
            f = None

            if 'global_{}'.format(rule_name) in rule_dict:
                nm = 'global_{}'.format(rule_name)                
            else:
                nm = '{}_{}'.format(field_name, rule_name)
                rule_dict[nm] = _parse_rule(rule)

            field_rules.append({
                'result': [],
                'ruleName': rule_name,
                'rule': rule_dict[nm]
            })
        
        field_dict[field_name] = field_rules
    return field_dict


def compile_group_rules(json_obj, field_dict):
    group_dict = {}
    for group in json_obj.get("ruleGroups", []):
        group_name = group.get("groupName", "")
        match_type = group.get("match", "")
        group_rules = []
        for rule in group.get("rules", []):
            f = rule.get("fieldName")
            rn = rule.get("ruleName","").upper()
            group_rules += [r for r in field_dict[f] if r['ruleName']==rn]
        group_dict[group_name] = group_rules
    return group_dict


def _parse_rule(rule):
    func_dct = {
        'regex': _parse_regex,
        'range': _parse_range
    }

    return func_dct[rule.get('type')](rule)


# region parse rules
def _parse_regex(rule):
    regex_pattern = rule.get('pattern')
    flags = rule.get('flags', [])

    pat_flags = 0
    for f in flags:
        if f is None:
            continue
        pat_flags |= regex_flag_dict.get(f.upper(), 0)

    _regex = re.compile(regex_pattern, pat_flags)
    def f(x): return regex_lint(x, _regex)
    return f


def _parse_range(rule):
    f_value = rule.get('fromValue')
    s_value = rule.get('toValue')
    def f(x): return range_lint(x, f_value, s_value)
    return f


if __name__ == "__main__":
    with open('schema.json', 'r') as fl:
        js = json.loads(fl.read())

    compile_rules(js)
