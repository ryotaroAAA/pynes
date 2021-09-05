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
    cpu.load_correct_log(f"test_log/nestest.yaml")
    pprint(vars(cpu.reg))

    renderer = Renderer()
    video = Video(cpu)

    # for _ in range(8991):
    while True:
        cycle = cpu.run()
        if not (image := ppu.run(cycle)) == None:
            s = time.time()
            renderer.render(image)
            data = renderer.get_render_result()
            video.update(data)
            e = time.time()
            print(f"[FPS] {1/(e - s):0.1f}")
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
    video = Video(cpu)

    while True:
        cycle = cpu.run()
        if not (image := ppu.run(cycle)) == None:
            s = time.time()
            renderer.render(image)
            data = renderer.get_render_result()
            video.update(data)
            e = time.time()
            print(f"[FPS] {1/(e - s):0.1f}")
    print("success!")

def run(args):
    cas = Cassette(f"rom/{args.rom}")
    wram = Ram(WRAM_SIZE)
    vram = Ram(VRAM_SIZE)
    inter = Interrupts()
    ppu = Ppu(cas, vram, inter)
    cpu = Cpu(cas, wram, ppu, inter)
    pprint(vars(cpu.reg))

    renderer = Renderer()
    video = Video(cpu)

    loop = sys.maxsize if args.loop == -1 else args.loop
    for _ in range(loop):
        cycle = cpu.run()
        if not (image := ppu.run(cycle)) == None:
            s = time.time()
            renderer.render(image)
            data = renderer.get_render_result()
            video.update(data)
            e = time.time()
            print(f"[FPS] {1/(e - s):0.1f}")
    if args.stop:
        while True:
            pass
    print("success!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--loop", type=int, default=-1, help="loop")
    parser.add_argument("-r", "--rom", default="", help="rom")
    parser.add_argument("-s", "--stop", action="store_true", help="stop after num of loop run")
    args = parser.parse_args()
    print(vars(args), tag="args", tag_color="green", color="white")

    run(args)