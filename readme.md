# ArcLint

## Patterns

### Regex

apply a regex pattern to the field

if the pattern matches, it will flag as an error
if the pattern doesn't match, then it is considered good

    {
        "fieldName": "",
        "type": "regex",
        "pattern": "",
        "flags": []
    }


### Range

checks against a range of values
if value is within range, then good

    {
        "fieldName": "",
        "type": "range",
        "fromValue": 0,
        "toValue": 10
    }


### Domain

checks to see if value exists within a domain (can be any)

### No Blanks

checks to see if value contains a blank.
flag to check if empty text?

### Line Returns

checks to see if the value contains line returns



want to add rule groups to match collections. If any of the rules match then its a flag for example



any?

cast iron, within a range


rule > regex = cast iron
rule > range = 150 to 400

this is applied to two fields

therefore, i need a rule group that tests if all fields are true

could have a rule group, that takes specific rule names and tests for all? 


having many rules for one field.
Can build multiple different regex searchs on a field, and see which one matches or fails. 

then, with rule groups can test collection of rules across multiple fields

Define rules for fields > group fields together

maybe add a "use_all" to rule group



keep same dictionary reference as other rules and just check if row number is in any/all

keep field + rule name and loop each rulegroup/rule after all are processed

i like option 1, but option 2 may be better