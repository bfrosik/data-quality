def add_line_to_file(file, line):
    with open(file, 'a') as f:
        f.write(line+'\n')
    f.close()

def replace_text_in_file(file, find, replace):
    with open(file, 'r+') as f :
        filedata = f.read()
        f.seek(0)
        # Replace the target string
        filedata = filedata.replace(find, replace)
        f.write(filedata)
        f.truncate()
        f.close()

def replace_text_after_in_file(file, after, find, replace):

    def next_after(line):
        match = after[0]
        if line.find(match) >= 0:
            after.remove(match)
            return len(after) == 0
        return False

    with open(file, 'r+') as f :
        lines = f.readlines()
        f.seek(0)
        # Find the after text

        do = False
        for line in lines:
            if not do:
                do = next_after(line)
            else:
                if line.find(find) >= 0:
                    line = line.replace(find, replace)
            f.write(line)
        f.truncate()
        f.close()

def delete_line_in_file(file, linestart):
    with open(file, 'r+') as f :
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if not line.startswith(linestart):
                f.write(line)
        f.truncate()
        f.close()


