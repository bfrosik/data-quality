import json

def is_text_in_file(file, text):
    return text in open(file).read()

def equals(struct_1, struct_2):
    return json.dumps(struct_1) == json.dumps(struct_2)
