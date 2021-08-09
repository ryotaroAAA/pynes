import argparse

from pynes.cassette import *
from pynes.cpu import *
from pynes.ram import *

def nestest(limit = 1000):
    cas = Cassette("rom/nestest.nes")
    cpu = Cpu(cas)
    cpu.reset_addr(0xc000)
    cpu.load_correct_log(f"log/nestest{limit}.yaml")
    pprint(vars(cpu.reg))
    for _ in range(limit):
        cpu.run()
    cpu.dump_stat_yaml(f"sample/nestest{limit}.yaml")

def hello():
    cas = Cassette("rom/hello.nes")
    cpu = Cpu(cas)
    cpu.load_correct_log("log/hello.yaml")
    pprint(vars(cpu.reg))
    for _ in range(200):
        cpu.run()
    cpu.dump_stat_yaml("sample/hello.yaml")

def run(args):
    cas = Cassette("rom/hello.nes")
    cpu = Cpu(cas)
    pprint(vars(cpu.reg))
    for _ in range(args.loop):
        cpu.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--loop", type=int, default=100, help="")
    parser.add_argument("-m", "--mode", default="run", help="run or test")
    args = parser.parse_args()
    print(vars(args), tag="args", tag_color="green", color="white")

    run(args)