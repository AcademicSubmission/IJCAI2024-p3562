from ConfigSpace import Configuration
from os import system,remove,getcwd
from os.path import basename,exists,join
import random,time
import numpy as np

current_path = getcwd()
def format_instance(config: Configuration):
    return f'-bms_num {config["bms_num"]} -lambda_ {config["lambda_"]} -gamma {config["gamma"]} \
            -armnum {config["armnum"]} -backward_step {config["backward_step"]}' 

def set_cpu_time(c):
    global cpu_time
    cpu_time = c
  
def set_target_folder(folder):
    global target_folder
    target_folder = folder

def read_targets(target_file,output_file):
    if not exists(join(current_path,target_file)):
        f = open(join(current_path,output_file))
        lines = f.readlines()
        max_f = int(lines[0].strip().split(' ')[0])
        min_f = int(lines[len(lines) - 1].strip().split(' ')[0])

        if max_f - min_f < 5:
            targets = list(range(min_f, max_f + 1))[::-1]
        else:
            targets = list(np.linspace(max_f,min_f,5))
            targets = [int(t) for t in targets]

        f.close()
        f = open(join(current_path,target_file),'w+')
        for t in targets:
            f.write(f'{t}\n')
        f.close()
        return targets
    else:
        f = open(join(current_path,output_file))
        f1 = open(join(current_path,target_file),"a+")
        lines = f.readlines()
        f1.seek(0)
        lines1 = f1.readlines()
        targets = [int(line1) for line1 in lines1]
        best_found =  int(lines[len(lines)-1].strip().split(' ')[0])
        if best_found < targets[len(targets) - 1]:
            targets.append(best_found)
            f1.write(f'{best_found}\n')
        f.close()
        f1.close()
        return targets

def ecdf(config: Configuration, ins: str, seed: int = 0):
    ''' target_file: target/ins.target
        output_file tmp_{random_number}.out'''
    random.seed(time.time())
    random_number = random.randint(1, 100000)
    system(f"./BandMaxSAT {ins} 1 -cpu_time {cpu_time} {format_instance(config)} > ./tmp_{random_number}.out" )

    out_file = open(join(current_path,f'./tmp_{random_number}.out'))
    lines = out_file.readlines()
    if len(lines) == 0:
        remove(join(current_path,f"./tmp_{random_number}.out"))
        return 0

    targets = read_targets(f'{target_folder}/{basename(ins)}-{cpu_time}.target',f'./tmp_{random_number}.out')
    budgets =  np.logspace(np.log(0.1),np.log(cpu_time),50,base=np.e)
    budgets = [cpu_time + 0.1 - b for b in budgets]
    budgets.sort()
    ecdf = 0
    index = 0
    f, t = lines[index].strip().split(' ')
    f = int(f)
    t = float(t)
    for b in budgets:
        if t < b:
            while(True):
                index += 1
                if index >= len(lines):
                    break
                f, t = lines[index].strip().split(' ')
                f = int(f)
                t = float(t)
                if t >= b:
                    break
        for target in targets:
            if f <= target:
                ecdf += 1
    out_file.close()
    remove(join(current_path,f"./tmp_{random_number}.out"))
    return -ecdf


def multi_ecdf(config: Configuration, ins: str, seed: int = 0):
    ''' target_file: target/ins.target
        output_file tmp_{random_number}.out'''
    instances = ins.split('|')
    result = 0
    for i in instances:
        result += ecdf(config, i, seed)
    return result