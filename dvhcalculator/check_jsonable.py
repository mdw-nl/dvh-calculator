import json
import logging


def log_unjsonable(plan_out):
    for name, element in get_unjsonable_elements('root object', plan_out):
        error_string = 'not jsonable:\n  at:%s\n  type: %s,\n  value:%s'
        logging.error(error_string % (name, type(element), element))


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except TypeError:
        return False


def get_unjsonable_elements(name, value):
    if type(value) == list:
        for index, element in enumerate(value):
            yield from get_unjsonable_elements((name + ':' + str(index)),
                                               element)
    elif type(value) == dict:
        for index, element in value.items():
            yield from get_unjsonable_elements(name + ':' + str(index),
                                               element)
    else:
        if not is_jsonable(value):
            yield (name, value)
