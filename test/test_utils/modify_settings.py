def add_line_to_file(file, line):
    with open(file, 'a') as f:
        f.write('line')
    f.close()

def replace_text_in_file(file, find, replace):
    with open(file, 'r+') as f :
        filedata = f.read()
    f.seek(0)
    # Replace the target string
    filedata = filedata.replace(find, replace)
    f.write(filedata)
    #f.truncate()
    f.close()

def replace_text_after_in_file(file, after, find, replace):
    with open(file, 'r+') as f :
        lines = f.readlines()
    f.seek(0)
    # Find the after text
    for line in lines:
        do = False
        if line.startswith(after):
            do = True
        if line.startswith(find) and do:
            line = line.replace(find, replace)
        f.write(line)
    f.close()

def delete_line_in_file(file, linestart):
    with open(file, 'r+') as f :
        lines = f.readlines()
    f.seek(0)
    for line in lines:
        if not line.startswith(linestart):
            f.write(line)
    f.close()


