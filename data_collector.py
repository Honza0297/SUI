
from subprocess import Popen, PIPE
import json, csv
import re
import sys

num_of_features = 5
AIs = ["dt.sdc", "dt.ste", "dt.stei", "dt.wpm_c"]


def log_results(winner):
    for AI in AIs:
        print("AI is " + AI)
        buffer = []
        block = []
        with open("./log/client-{}.log".format(AI)) as f:
            line = "dummy"

            file = "positives" if AI == winner else "negatives"
            print("File for " + AI + " is " + file)
            while line:
                for i in range(num_of_features + 2):
                    line = f.readline()
                    block.append(line)
                if not block[0]: break

                for i in range(1, num_of_features + 1):
                    buffer.append(float(block[i].split(":")[2]))

                with open(file, "a", newline="", encoding='utf-8') as pos:
                    write = csv.writer(pos, lineterminator="\n")
                    write.writerow(buffer)
                    buffer = []
                block = []


if __name__ == '__main__':
    for i in range(int(sys.argv[1])):

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
        print("winner is: {}".format(winner))
        log_results(winner)





    """V out_dict je ted vyhravajici AI
    TODO: z logu vysmazit cisla a ulozit je jako csv: pos pro tu co vyhrala a  neg pro ostatni"""
    pass