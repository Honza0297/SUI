import csv
from  subprocess import Popen, PIPE
import json
import re

if __name__ == '__main__':
    process = Popen(["python3", "./scripts/dicewars-ai-only.py", "-r", "-n", "1", "-l", "log", "--ai", "dt.sdc", "dt.ste", "dt.stei", "dt.wpm_c"], stdout=PIPE)

    (output, err) = process.communicate()
    exit_code = process.wait()
    out = output.decode("utf-8").split("\n")
    out_dict = {}
    p = re.compile('(?<!\\\\)\'')

    for line in out:
        if line.startswith("\r0\rWin counts"):
            d = line[14::]
            d= p.sub('\"', d)
            out_dict = json.loads(d)
    winner = list(out_dict.keys())[0].split(" ")[0]
    with open("./log/client-{}.log".format(winner)) as f:
        print(f)
    """V out_dict je ted vyhravajici AI
    TODO: z logu vysmazit cisla a ulozit je jako csv: pos pro tu co vyhrala a  neg pro ostatni"""
    pass