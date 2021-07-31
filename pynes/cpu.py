from dataclasses import dataclass
from enum import Flag, auto, Enum
from pathlib import Path
from typing import DefaultDict

from hexdump import hexdump
import yaml
from tabulate import tabulate

from pynes.cassette import *
from pynes.ram import *

NES_HSIZE = 0x0010
PROG_ROM_UNIT_SIZE = 0x4000
CHAR_ROM_UNIT_SIZE = 0x2000

WRAM_SIZE = 0xFFFF
END = "little"

class Opcode(Enum):
    ADC = auto() 
    SBC = auto()
    AND = auto()
    ORA = auto()
    EOR = auto()
    ASL = auto() 
    LSR = auto()
    ROL = auto() 
    ROR = auto()
    BCC = auto() 
    BCS = auto()
    BEQ = auto() 
    BNE = auto()
    BVC = auto() 
    BVS = auto()
    BPL = auto() 
    BMI = auto()
    BIT = auto()
    JMP = auto()
    JSR = auto()
    RTS = auto()
    BRK = auto()
    RTI = auto()
    CMP = auto() 
    CPX = auto()
    CPY = auto()
    INC = auto() 
    DEC = auto()
    INX = auto() 
    DEX = auto()
    INY = auto() 
    DEY = auto()
    CLC = auto() 
    SEC = auto()
    CLI = auto() 
    SEI = auto() 
    CLD = auto() 
    SED = auto() 
    CLV = auto()
    LDA = auto() 
    LDX = auto() 
    LDY = auto()
    STA = auto() 
    STX = auto() 
    STY = auto()
    TAX = auto() 
    TXA = auto() 
    TAY = auto() 
    TYA = auto()
    TSX = auto()
    TXS = auto()
    PHA = auto() 
    PLA = auto()
    PHP = auto()
    PLP = auto()
    NOP = auto()
    NOPD = auto()
    NOPI = auto()
    LAX = auto()
    SAX = auto()
    DCP = auto()
    ISB = auto()
    SLO = auto()
    RLA = auto()
    SRE = auto()
    RRA = auto()

opcode_dic = {
    "ADC": Opcode.ADC,
    "SBC": Opcode.SBC,
    "AND": Opcode.AND,
    "ORA": Opcode.ORA,
    "EOR": Opcode.EOR,
    "ASL": Opcode.ASL,
    "LSR": Opcode.LSR,
    "ROL": Opcode.ROL,
    "ROR": Opcode.ROR,
    "BCC": Opcode.BCC,
    "BCS": Opcode.BCS,
    "BEQ": Opcode.BEQ,
    "BNE": Opcode.BNE,
    "BVC": Opcode.BVC,
    "BVS": Opcode.BVS,
    "BPL": Opcode.BPL,
    "BMI": Opcode.BMI,
    "BIT": Opcode.BIT,
    "JMP": Opcode.JMP,
    "JSR": Opcode.JSR,
    "RTS": Opcode.RTS,
    "BRK": Opcode.BRK,
    "RTI": Opcode.RTI,
    "CMP": Opcode.CMP,
    "CPX": Opcode.CPX,
    "CPY": Opcode.CPY,
    "INC": Opcode.INC,
    "DEC": Opcode.DEC,
    "INX": Opcode.INX,
    "DEX": Opcode.DEX,
    "INY": Opcode.INY,
    "DEY": Opcode.DEY,
    "CLC": Opcode.CLC,
    "SEC": Opcode.SEC,
    "CLI": Opcode.CLI,
    "SEI": Opcode.SEI,
    "CLD": Opcode.CLD,
    "SED": Opcode.SED,
    "CLV": Opcode.CLV,
    "LDA": Opcode.LDA,
    "LDX": Opcode.LDX,
    "LDY": Opcode.LDY,
    "STA": Opcode.STA,
    "STX": Opcode.STX,
    "STY": Opcode.STY,
    "TAX": Opcode.TAX,
    "TXA": Opcode.TXA,
    "TAY": Opcode.TAY,
    "TYA": Opcode.TYA,
    "TSX": Opcode.TSX,
    "TXS": Opcode.TXS,
    "PHA": Opcode.PHA,
    "PLA": Opcode.PLA,
    "PHP": Opcode.PHP,
    "PLP": Opcode.PLP,
    "NOP": Opcode.NOP,
    "NOP": Opcode.NOP,
    "NOP": Opcode.NOP,
    "LAX": Opcode.LAX,
    "SAX": Opcode.SAX,
    "DCP": Opcode.DCP,
    "ISB": Opcode.ISB,
    "SLO": Opcode.SLO,
    "RLA": Opcode.RLA,
    "SRE": Opcode.SRE,
    "RRA": Opcode.RRA
}

class Addrmode(Enum):
    IMPL = auto()
    ACM = auto()
    IMD = auto()
    ZPG = auto()
    ZPG_X = auto()
    ZPG_Y = auto()
    ABS = auto()
    ABS_X = auto()
    ABS_Y = auto()
    REL = auto()
    IND_X = auto()
    IND_Y = auto()
    ABS_IND = auto()

addrmode_dic = {
    "IMPL" : Addrmode.IMPL, 
    "ACM" : Addrmode.ACM, 
    "IMD" : Addrmode.IMD, 
    "ZPG" : Addrmode.ZPG, 
    "ZPG_X" : Addrmode.ZPG_X, 
    "ZPG_Y" : Addrmode.ZPG_Y, 
    "ABS" : Addrmode.ABS, 
    "ABS_X" : Addrmode.ABS_X, 
    "ABS_Y" : Addrmode.ABS_Y, 
    "REL" : Addrmode.REL, 
    "IND_X" : Addrmode.IND_X, 
    "IND_Y" : Addrmode.IND_Y, 
    "ABS_IND" : Addrmode.ABS_IND
}

@dataclass
class Status:
    CARRY: bool = False
    ZERO: bool = False
    INTERRUPT: bool = True
    DECIMAL: bool = False
    BREAK: bool = False
    RESERVED: bool = True
    OVERFLOW: bool = False
    NEGATIVE: bool = False

    def reset(self):
        self.CARRY = False
        self.ZERO = False
        self.INTERRUPT = True
        self.DECIMAL = False
        self.BREAK = False
        self.RESERVED = True
        self.OVERFLOW = False
        self.NEGATIVE = False

    def get_val(self):
        p = (1 << 0) if self.CARRY else 0
        p += (1 << 1) if self.ZERO else 0
        p += (1 << 2) if self.INTERRUPT else 0
        p += (1 << 3) if self.DECIMAL else 0
        p += (1 << 4) if self.BREAK else 0
        p += (1 << 5) if self.RESERVED else 0
        p += (1 << 6) if self.OVERFLOW else 0
        p += (1 << 7) if self.NEGATIVE else 0
        return p

@dataclass
class Register:
    A: int = 0x00
    X: int = 0x00
    Y: int = 0x00
    SP: int = 0x01FD
    PC: int = 0x00
    P: Status = Status()

    def reset(self):
        self.A = 0x00
        self.B = 0x00
        self.X = 0x00
        self.SP = 0x01FD
        self.P.reset()

class Cpu:
    def __init__(self, cas):
        self.reg = Register()
        self.ram = Ram(WRAM_SIZE)
        self.cas = cas
        self.reset()

        with Path("opset.yaml").open() as f:
            self.opset = yaml.safe_load(f)

    def reset(self):
        self.reg.reset()
        self.reg.PC = self.wread(0xFFFC)

    def bread(self, addr):
        return self._read(addr)

    def wread(self, addr):
        return self._read(addr) + (self._read(addr + 1) << 8)

    def _read(self, addr):
        assert 0x0000 <= addr <= 0xFFFF, "invalid addr!"
        # print(hex(addr))
        if addr < 0x0800:
            # wram
            return self.ram.data[addr]
        elif addr < 0x2000:
            # mirror
            return self.ram.data[addr - 0x0800]
        elif addr < 0x4000:
            # PPU
            pass
            # return self.ram[(addr - 0x2000) % 8] 
        elif addr < 0x4020:
            if addr == 0x4014:
                # DMA
                pass
            elif addr == 0x4016:
                # keypad
                pass
            else:
                # APU I/O
                pass
            raise NotImplementedError
        elif addr < 0x6000:
            # ext rom
            pass
        elif addr < 0x8000:
            # ext ram
            pass
        elif addr < 0xC000:
            # prog rom
            return self.cas.prog_rom[addr - 0x8000]
        elif addr < 0xFFFF:
            # prog rom
            if self.cas.prog_size <= 0x4000:
                return self.cas.prog_rom[addr - 0xC000]
            else:
                return self.cas.prog_rom[addr - 0x8000]
        else:
            raise NotImplementedError

    def write(self, addr, data):
        # print(hex(addr), data)
        assert 0x0000 <= addr <= 0xFFFF, "invalid addr!"
        if addr < 0x0800:
            # wram
            self.ram.data[addr] = data
        elif addr < 0x2000:
            # mirror
            self.ram.data[addr - 0x0800] = data
        elif addr < 0x2008:
            # PPU
            pass
        elif 0x4000 <= addr < 0x4020:
            if addr == 0x4014:
                # DMA
                pass
            elif addr == 0x4016:
                # keypad
                pass
            else:
                # APU I/O
                pass 
        else:
            raise NotImplementedError
    
    def fetch(self, size):
        if size in [1, 2]:
            data = None
            if size == 1:
                data = self.bread(self.reg.PC)
            else:
                data = self.wread(self.reg.PC)
            self.reg.PC += size
            # print(type(data), data, hex(data))
            return data
        else:
            raise NotImplementedError

    def get_op(self, opcode):
        opset = self.opset[opcode]
        mode = addrmode_dic[opset["mode"]]
        oprand = DefaultDict(int)
        if mode in [Addrmode.ACM, Addrmode.IMPL]:
            pass
        elif mode in [Addrmode.IMD, Addrmode.ZPG]:
            oprand["data"] = self.fetch(1)
        elif mode == Addrmode.REL:
            addr = self.fetch(1)
            oprand["data"] = addr + self.reg.PC % 0xFF
            oprand["add_cycle"] = \
                1 if (oprand["data"] ^ self.reg.PC) & 0xFF00 else 0
        elif mode == Addrmode.ZPG_X:
            oprand["data"] = (self.reg.X + self.fetch(1)) & 0xFF
        elif mode == Addrmode.ZPG_Y:
            oprand["data"] = (self.reg.X + self.fetch(1)) & 0xFF
        elif mode == Addrmode.ABS:
            oprand["data"] = self.fetch(2)
        elif mode == Addrmode.ABS_X:
            oprand["data"] = (self.reg.X + self.fetch(2)) & 0xFFFF
            oprand["add_cycle"] = \
                1 if not oprand["data"] == (self.reg.X & 0xFF00) else 0
        elif mode == Addrmode.ABS_Y:
            oprand["data"] = (self.reg.Y + self.fetch(2)) & 0xFFFF
            oprand["add_cycle"] = \
                1 if not oprand["data"] == (self.reg.Y & 0xFF00) else 0
        elif mode == Addrmode.IND_X:
            base = (self.reg.X + self.fetch(1)) & 0xFF
            oprand["data"] = self.wread(base)
            oprand["data"] = (self.reg.X + self.fetch(2)) & 0xFFFF
            oprand["add_cycle"] = \
                1 if not oprand["data"] == (self.reg.X & 0xFF00) else 0
        elif mode == Addrmode.IND_Y:
            pass
        elif mode == Addrmode.ABS_IND:
            pass
        else:
            raise NotImplementedError
        
        return opset, oprand

    def op_dump(self, opset, oprand, pc):
        r = self.reg
        print(
            f"{pc:04X} {opset['op']:3s} {opset['mode']:5s} "
            f"{oprand['data']:04X} A:{r.A:02X} X:{r.X:02X} Y:{r.Y:02X} "
            f"P:{r.P.get_val():02X} SP:{r.SP:04X}"
        )

    def set_flag_for_after_calc(self, result):
        self.reg.P.NEGATIVE = not not (result & 0x80)
        self.reg.P.ZERO = not result

    def exec(self, opset, oprand):
        op = opcode_dic[opset["op"]]
        data = oprand["data"]
        mode = addrmode_dic[opset["mode"]]
        # load
        if op == Opcode.LDA:
            self.reg.A = data if mode == Addrmode.IMD else self.bread(data)
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.LDX:
            self.reg.X = data if mode == Addrmode.IMD else self.bread(data)
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.LDY:
            self.reg.Y = data if mode == Addrmode.IMD else self.bread(data)
            self.set_flag_for_after_calc(self.reg.Y)
        # store
        elif op == Opcode.STA:
            self.write(data, self.reg.A)
        elif op == Opcode.STX:
            self.write(data, self.reg.X)
        elif op == Opcode.STY:
            self.write(data, self.reg.Y)
        # transfer
        elif op == Opcode.TAX:
            self.reg.X = self.reg.A
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.TAY:
            self.reg.Y = self.reg.A
            self.set_flag_for_after_calc(self.reg.Y)
        elif op == Opcode.TSX:
            self.reg.X = self.reg.SP & 0xFF
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.TXA:
            self.reg.A = self.reg.X
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.TXS:
            self.reg.SP = self.reg.X & 0x0100
        elif op == Opcode.TYA:
            self.reg.A = self.reg.Y
            self.set_flag_for_after_calc(self.reg.A)
        # op
        elif op == Opcode.ADC:
            raise NotImplementedError
        elif op == Opcode.AND:
            raise NotImplementedError
        elif op == Opcode.ASL:
            raise NotImplementedError
        elif op == Opcode.BIT:
            raise NotImplementedError
        elif op == Opcode.CMP:
            raise NotImplementedError
        elif op == Opcode.CPX:
            raise NotImplementedError
        elif op == Opcode.CPY:
            raise NotImplementedError
        elif op == Opcode.DEC:
            raise NotImplementedError
        elif op == Opcode.DEX:
            raise NotImplementedError
        elif op == Opcode.DEY:
            raise NotImplementedError
        elif op == Opcode.EOR:
            self.reg.A ^= data if mode == Addrmode.IMD else self.bread(data)
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.INC:
            data_ = self.read(data) + 1
            self.write(data, data_)
            self.set_flag_for_after_calc(data_)
        elif op == Opcode.INX:
            self.reg.X += 1
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.INY:
            self.reg.Y += 1
            self.set_flag_for_after_calc(self.reg.Y)
        elif op == Opcode.LSR:
            raise NotImplementedError
        elif op == Opcode.ORA:
            raise NotImplementedError
        elif op == Opcode.ROL:
            raise NotImplementedError
        elif op == Opcode.ROR:
            raise NotImplementedError
        elif op == Opcode.SBC:
            raise NotImplementedError
        elif op == Opcode.PHA:
            raise NotImplementedError
        elif op == Opcode.PHP:
            raise NotImplementedError
        elif op == Opcode.PLA:
            raise NotImplementedError
        elif op == Opcode.PLP:
            raise NotImplementedError
        elif op == Opcode.JMP:
            raise NotImplementedError
        elif op == Opcode.JSR:
            raise NotImplementedError
        elif op == Opcode.RTS:
            raise NotImplementedError
        elif op == Opcode.RTI:
            raise NotImplementedError
        elif op == Opcode.BCC:
            raise NotImplementedError
        elif op == Opcode.BCS:
            raise NotImplementedError
        elif op == Opcode.BEQ:
            raise NotImplementedError
        elif op == Opcode.BMI:
            raise NotImplementedError
        elif op == Opcode.BNE:
            raise NotImplementedError
        elif op == Opcode.BPL:
            raise NotImplementedError
        elif op == Opcode.BVS:
            raise NotImplementedError
        elif op == Opcode.BVC:
            raise NotImplementedError
        elif op == Opcode.CLD:
            self.reg.P.DECIMAL = False
        elif op == Opcode.CLC:
            self.reg.P.CARRY = False
        elif op == Opcode.CLI:
            self.reg.P.INTERRUPT = False
        elif op == Opcode.CLV:
            self.reg.P.OVERFLOW = True
        elif op == Opcode.SEC:
            self.reg.P.CARRY = True
        elif op == Opcode.SEI:
            self.reg.P.INTERRUPT = True
        elif op == Opcode.SED:
            self.reg.P.DECIMAL = True
        elif op == Opcode.BRK:
            raise NotImplementedError
        elif op == Opcode.NOP:
            raise NotImplementedError
        # TODO: unofficial
        elif op == Opcode.NOP:
            raise NotImplementedError
        elif op == Opcode.NOP:
            raise NotImplementedError
        elif op == Opcode.LAX:
            raise NotImplementedError
        elif op == Opcode.SAX:
            raise NotImplementedError
        elif op == Opcode.DCP:
            raise NotImplementedError
        elif op == Opcode.ISB:
            raise NotImplementedError
        elif op == Opcode.SLO:
            raise NotImplementedError
        elif op == Opcode.RLA:
            raise NotImplementedError
        elif op == Opcode.SRE:
            raise NotImplementedError
        elif op == Opcode.RRA:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def run(self):
        pc = self.reg.PC
        opset, oprand = self.get_op(self.fetch(1))
        self.op_dump(opset, oprand, pc)
        # print(opset, oprand)
        # pass
        self.exec(opset, oprand)