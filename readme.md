# **ArcLint**

A tool to let you create data validation rules using flexible data patterns with regex and ranges within ArcGIS.

Flexible, repeatable and open, by using regex patterns to apply data validation to your fields, or groups of fields, to help clean and flag data issues in any table readable by ArcGIS

## **Why**

Many of these data checks should be completed with domains. By restricting the input to a fixed domain value, the data should be consistant within that field.

That said, there is cases when a domain is unable to fully match and clean data. Examples of this are fields with blank values, leading or trailing whitespace in text, line returns and so forth. Domains and standard processing is unable to flag these errors, which is where this tool can help improve the data consistancy and structure.

At its root the regex patterns give you flexibility to produce complex rules to flag your data. They must conform to the python spec for the re module for regex [re link](https://docs.python.org/3/library/re.html)

## **Input**

Your patterns and rules should be defined in a .json file with the following specifications. See the example folder for examples of the different types.

## **Structure**

### **Rules**

each rule, as a dictionary, should at minimum contain a "ruleName". If the rule is not a global rule (described below), it should also contain a "type" key indicating what type of rule it is in addition to the type specific fields. 

See below for the various rule types available. Each rule type will expect different values beyond two required below.

    {
        'ruleName': 'sample_rule',
        'type': 'regex'
    }

### **Fields**

within the top level you define which fields you want to capture and apply the rules to. the root level should have a ***"fields"*** key with an array as a value containing the indvidual fields to validate.

    {
        "fields": []
    }

Each value of the array should follow the field structure, specifying the name of the field, and an array of rules to process.

    {
        "fieldName": "some field name" # field name should be a string
        "rules": [] # an array of rules to apply
    }


Here is an example of regex rule that matches the text ***Site A*** within a ***SiteName*** field.

    {
    "fields": [
        { 
            "fieldName": "SiteName",
            "rules": [
                {
                    "ruleName": "site_rule",
                    "type": "regex",
                    "pattern": "(Site A)",
                }
            ]
        }
    ]
    }

Each rule should have a unique rule name for that field. Rules names may be duplicated across different fields, but must be unique for each rule in a single field.

## **Global Rules**

If you would like to apply a rule to many different fields, then you should create a global rule and specify it in the rules array. Like within the field rules, global rules should be unique to its scope.

At the root level of your json file, a "globalRule" should be defined. This should have "globalRules" as the key and an array as the value.

    {
        "globalRules": []
    }

The rules should follow the same structure as above, with a "ruleName", "type" and other required parameters.

To use the global rule, simply specify its ruleName as the ruleName value within your fields rule array. See below for example.

This rule can then be shared across multiple fields simply by specifying it again.

    {
        "globalRules": [
            {
                "ruleName": "build_year",
                "type": "range",
                "fromValue": 1960,
                "toValue": 2000
            }
        ],
        "fields": [
            { 
                "fieldName": "SiteName",
                "rules": [
                    {
                        "ruleName": "site_rule",
                        "type": "regex",
                        "pattern": "(Site A)"
                    }
                ]
            },
            {
                "fieldName": "BuildYear",            
                "rules": [
                    {
                        "ruleName": "build_year"
                    }
                ]
            }
        ]
    }



## **Rule Groups**

Since rules are evaluated on a per-row + per-field basis, rules can be combined into rule groups to validate across many fields of a single row. An example of this would be validating that the site name is "Site A" and it is built between 1960 and 1980. 

Further, you can also specify to require that all items within the rule group match, or any of the items by specifying a "match" parameter.

Like the fields and global rules, a key of ***"ruleGroups"*** is required, with an array of your rule groups. 

Each group should have a ***groupName*** and an array of "rules" specifying which rules apply to that group.

each rule should be a dictionary specifying the field name and the rule within that field. Finally a description can be added to provide details of the rule group.

See examples/rule_groups.json or examples/global_rule_groups.json for a full specification.

    "ruleGroups": [
            {
                "groupName": "site_group_rule",
                "description": "Site A built between 1960 and 2000",
                "rules": [
                    {"fieldName": "SiteName", "ruleName": "site_rule"},
                    {"fieldName": "BuildYear", "ruleName": "build_year"}
                ],
                "match": "all"
            }
        ]


## **Output**

the tool with output a results.json file to the specified folder containing the OID of the rows with errors.

It will specify the individual rows that had field errors as well as the rows that match your group rules.

    {
        "run_datetime": "2020-07-13 14:58:52",
        "fields": {
            "YR_INST": [
                {
                    "ruleName": "1963",
                    "errorIDs": [
                        2,
                        3,
                        4,
                        5,
                        6,
                        9,
                        10,
                        11
                    ]
                }
            ]
        },
        "groups": {
            "facility_test": {
                "errorIDs": [
                    5,
                    6
                ],
                "description": "Is it facility, in zone 2e and outside of range 1960 to 2000"
            }
        }
    }


# Specifications