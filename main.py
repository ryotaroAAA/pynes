import argparse

from pynes.cassette import *
from pynes.cpu import *
from pynes.interrupts import *
from pynes.ppu import *
from pynes.ram import *
from pynes.renderer import *
from pynes.video import *

def nestest():
    cas = Cassette("rom/nestest.nes")
    wram = Ram(WRAM_SIZE)
    vram = Ram(VRAM_SIZE)
    inter = Interrupts()
    ppu = Ppu(cas, vram, inter)
    cpu = Cpu(cas, wram, ppu, inter)
    # cpu.reset_addr(0xc000)
    cpu.load_correct_log(f"log/nestest.yaml")
    pprint(vars(cpu.reg))

    renderer = Renderer()
    video = Video()

    for _ in range(10000):
        cycle = cpu.run()
        if not (image := ppu.run(3 * cycle)) == None:
            print("image created")
            renderer.render(image)
            data = renderer.get_render_result()
            video.update(data)
            print("video enable!")
            time.sleep(30)
    cpu.dump_stat_yaml(f"sample/nestest.yaml")
    print("success!")

def hello():
    cas = Cassette("rom/hello.nes")
    wram = Ram(WRAM_SIZE)
    vram = Ram(VRAM_SIZE)
    inter = Interrupts()
    ppu = Ppu(cas, vram, inter)
    cpu = Cpu(cas, wram, ppu, inter)
    cpu.load_correct_log("log/hello.yaml")
    pprint(vars(cpu.reg))

    renderer = Renderer()
    video = Video()

    for _ in range(10000):
        cycle = cpu.run()
        if not (image := ppu.run(3 * cycle)) == None:
            print("image created")
            renderer.render(image)
            data = renderer.get_render_result()
            video.update(data)
            print("video enable!")
            time.sleep(30)
    cpu.dump_stat_yaml("sample/hello.yaml")
    print("success!")

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