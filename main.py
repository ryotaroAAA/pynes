from pprint import *

from pynes.cassette import *
from pynes.cpu import *
from pynes.ram import *

def run():
    cas = Cassette("hello.nes")
    # print(vars(cas))
    # print(cas.prog_size, cas.char_size)
    cpu = Cpu(cas)
    pprint(vars(cpu.reg))
    # pprint(cpu.opset)
    for _ in range(200):
        cpu.run()
    # print(cpu.fetch(2))
    # print(cpu.fetch(2))
    # print(cpu.fetch(2))
    # print(cpu.fetch(2))
    # data = None
    # with Path("opeset.yaml").open("r") as f:
    #     data = yaml.safe_load(f)
    #     for k, v in data.items():
    #         v["cycle"] = cycles[k]
    #     pprint(data)
    # with Path("opeset.yaml").open("w") as f:
    #     yaml.dump(data, f, default_flow_style=False)
# pprint(opeset_dic)