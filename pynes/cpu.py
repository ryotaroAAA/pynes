from dataclasses import dataclass
from enum import auto, Enum
from pathlib import Path
import traceback
from typing import DefaultDict

from hexdump import hexdump
from pprint import *
from print_color import print
from tabulate import tabulate
import yaml

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
    
    def set_val(self, p):
        self.CARRY = p & (1 << 0) > 0
        self.ZERO = p & (1 << 1) > 0
        self.INTERRUPT = p & (1 << 2) > 0
        self.DECIMAL = p & (1 << 3) > 0
        self.BREAK = p & (1 << 4) > 0
        self.RESERVED = p & (1 << 5) > 0
        self.OVERFLOW = p & (1 << 6) > 0
        self.NEGATIVE = p & (1 << 7) > 0
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
        self.op_index = 0
        self.reg = Register()
        self.ram = Ram(WRAM_SIZE)
        self.cas = cas
        self.reset()
        self.dump = []

        with Path("opset.yaml").open() as f:
            self.opset = yaml.safe_load(f)

    def reset(self):
        self.reg.reset()
        self.reg.PC = self.wread(0xFFFC)

    def reset_addr(self, addr):
        self.reg.reset()
        self.reg.PC = addr
    
    def load_correct_log(self, path):
        if Path(path).exists():
            with Path(path).open() as f:
                self.correct = yaml.safe_load(f)

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
        assert 0x0000 <= addr <= 0xFFFF, "invalid addr!"
        try:
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
        except NotImplementedError:
            raise NotImplementedError
        except:
            print(traceback.format_exc())
            print(hex(addr), data)
    
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
    
    def branch(self, addr):
        self.reg.PC = addr
        self.has_branched = True

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
            oprand["data"] = addr + self.reg.PC
            oprand["data"] -= 0 if addr < 0x80 else 0xFF
            oprand["add_cycle"] = \
                int((oprand["data"] ^ self.reg.PC) & 0xFF00)
        elif mode == Addrmode.ZPG_X:
            oprand["data"] = (self.reg.X + self.fetch(1)) & 0xFF
        elif mode == Addrmode.ZPG_Y:
            oprand["data"] = (self.reg.X + self.fetch(1)) & 0xFF
        elif mode == Addrmode.ABS:
            oprand["data"] = self.fetch(2)
        elif mode == Addrmode.ABS_X:
            oprand["data"] = (self.reg.X + self.fetch(2)) & 0xFFFF
            oprand["add_cycle"] = \
                int(not oprand["data"] == (self.reg.X & 0xFF00))
        elif mode == Addrmode.ABS_Y:
            oprand["data"] = (self.reg.Y + self.fetch(2)) & 0xFFFF
            oprand["add_cycle"] = \
                int(not oprand["data"] == (self.reg.Y & 0xFF00))
        elif mode == Addrmode.IND_X:
            base = (self.reg.X + self.fetch(1)) & 0xFF
            oprand["data"] = (self.reg.X + self.wread(base)) & 0xFFFF
            oprand["add_cycle"] = \
                int(not oprand["data"] == (self.reg.Y & 0xFF00))
        elif mode == Addrmode.IND_Y:
            base = (self.reg.Y + self.fetch(1)) & 0xFF
            oprand["data"] = (self.reg.Y + self.wread(base)) & 0xFFFF
            oprand["add_cycle"] = \
                int(not oprand["data"] == (self.reg.Y & 0xFF00))
        elif mode == Addrmode.ABS_IND:
            pass
        else:
            raise NotImplementedError
        
        return opset, oprand

    def check_stat(self, opset, oprand, pc):
        self.dump_stat(opset, oprand, pc)
        self.comp_stat()
        self.op_index += 1

    def print_stat(self, op):
        if op["data"] == "":
            op["data"] = 0x00
            
        print(
            f"{op['i']:4d} {op['pc']:04X} {op['opset']:3s} {op['mode']:5s} "
            f"{op['data']:04X} A:{op['A']:02X} X:{op['X']:02X} Y:{op['Y']:02X} "
            f"P:{op['P']:02X} SP:{op['SP']:04X}"
        )

    def dump_stat(self, opset, oprand, pc):
        op = {
            "i" : self.op_index + 1,
            "pc" : pc,
            "opset" : opset['op'],
            "mode" : opset['mode'],
            "data" : oprand['data'],
            "A" :self.reg.A,
            "X" : self.reg.X,
            "Y" : self.reg.Y,
            "P" : self.reg.P.get_val(),
            "SP" : self.reg.SP
        }
        self.print_stat(op)
        self.dump.append(op)
    
    def comp_stat(self):
        # last one
        sample_op = self.dump[-1]
        # load i-th log
        correct_op = self.correct[self.op_index]
        check_items = [
            "i",
            "pc",
            "opset",
            "mode",
            "data",
            "A",
            "X",
            "Y",
            "P",
            "SP"
        ]
        failed = False
        for item in check_items:
            if correct_op[item] == "":
                continue
            if item == "SP" and not correct_op[item] & 0xFF00:
                sample_op[item] &= 0xFF
            if sample_op[item] != correct_op[item]:
                print(f"{item}, sample:{sample_op[item]:X}, "
                    f"correct:{correct_op[item]:X}",
                    tag = "failure", tag_color = "red", color = "white")
                if item == "P":
                    def print_status(p):
                        obj = {}
                        obj["CARRY"] = p & (1 << 0) > 0
                        obj["ZERO"] = p & (1 << 1) > 0
                        obj["INTERRUPT"] = p & (1 << 2) > 0
                        obj["DECIMAL"] = p & (1 << 3) > 0
                        obj["BREAK"] = p & (1 << 4) > 0
                        obj["RESERVED"] = p & (1 << 5) > 0
                        obj["OVERFLOW"] = p & (1 << 6) > 0
                        obj["NEGATIVE"] = p & (1 << 7) > 0
                        return obj
                    print(f"{sample_op[item]:X}",
                        tag = "sample", tag_color = "yellow")
                    pprint(vars(self.reg.P))
                    print(f"{correct_op[item]:X}",
                        tag = "correct", tag_color = "yellow")
                    pprint(print_status(correct_op[item]))
                failed = True
        if failed:
            start, end = max(0, self.op_index - 5), self.op_index + 1
            print("", tag = "sample", tag_color = "yellow", color = "white")
            for s in self.dump[start:end]:
                self.print_stat(s)

            print("", tag = "correct", tag_color = "yellow", color = "white")
            for c in self.correct[start:end]:
                self.print_stat(c)
            assert False, "status check error!"

    def dump_stat_yaml(self, path):
        Path("sample").mkdir(exist_ok = True)
        with Path(path).open("w") as f:
            yaml.dump(self.dump, f)

    def set_flag_for_after_calc(self, result):
        result &= 0xFF
        self.reg.P.NEGATIVE = bool(result & 0x80)
        self.reg.P.ZERO = result == 0

    def push(self, data):
        self.write(self.reg.SP & 0xFF | 0x100, data)
        self.reg.SP -= 1

    def push_PC(self):
        self.push((self.reg.PC >> 8) & 0xFF)
        self.push(self.reg.PC & 0xFF)
    
    def push_reg_status(self):
        self.push(self.reg.P.get_val())

    def pop(self):
        self.reg.SP += 1
        return self.bread(self.reg.SP & 0xFF | 0x100)

    def pop_PC(self):
        self.reg.PC = self.pop()
        self.reg.PC += (self.pop() << 8)
    
    def pop_reg_status(self):
        status = self.pop()
        self.reg.P.set_val(status)

    def exec(self, opset, oprand):
        op = opcode_dic[opset["op"]]
        data = oprand["data"]
        mode = addrmode_dic[opset["mode"]]
        # load
        if op in [Opcode.LDA, Opcode.LDX, Opcode.LDY]:
            data_ = data if mode == Addrmode.IMD else self.bread(data)
            if op == Opcode.LDA:
                self.reg.A = data_
            elif op == Opcode.LDX:
                self.reg.X = data_
            elif op == Opcode.LDY:
                self.reg.Y = data_
            else:
                raise NotImplementedError
            self.set_flag_for_after_calc(data_)
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
            self.reg.SP = self.reg.X + 0x0100
        elif op == Opcode.TYA:
            self.reg.A = self.reg.Y
            self.set_flag_for_after_calc(self.reg.A)
        # op
        elif op == Opcode.ADC:
            data_ = data if mode == Addrmode.IMD else self.bread(data)
            result = self.reg.A + data_ + int(self.reg.P.CARRY)
            # self.reg.P.CARRY = result >= 0
            self.reg.P.CARRY = (result > 0xFF and
                self.reg.A < 0xFF and data_ < 0xFF)
            # print(result, bool(result & 0x80), result > 0xFF)
            self.reg.P.OVERFLOW = bool(
                ((data_ ^ result) & 0x80) and
                ((self.reg.A ^ result) & 0x80))
            self.set_flag_for_after_calc(result)
            self.reg.A = result & 0xFF
        elif op == Opcode.AND:
            data_ = data if mode == Addrmode.IMD else self.bread(data)
            self.reg.A &= data_
            self.set_flag_for_after_calc(self.reg.A) 
        elif op == Opcode.ASL:
            result = self.reg.A if mode == Addrmode.ACM else self.bread(data)
            # print(result, self.reg.A, result & 0x01, bool(result & 0x01)
            self.reg.P.CARRY = bool(result & 0x80)
            result = (result << 1) & 0xFF
            if mode == Addrmode.ACM:
                self.reg.A = result
            else:
                self.write(data, result)
            self.set_flag_for_after_calc(result)
        elif op == Opcode.BIT:
            data_ = self.bread(data)
            self.reg.P.OVERFLOW = bool(data_ & 0x40)
            self.reg.P.NEGATIVE = bool(data_ & 0x80)
            self.reg.P.ZERO = not (data_ & self.reg.A)
        elif op == Opcode.CMP:
            result = data if mode == Addrmode.IMD else self.bread(data)
            comp = self.reg.A - result
            self.reg.P.CARRY = (comp >= 0)
            self.set_flag_for_after_calc(comp)
        elif op == Opcode.CPX:
            result = data if mode == Addrmode.IMD else self.bread(data)
            comp = self.reg.X - result
            self.reg.P.CARRY = (comp >= 0)
            self.set_flag_for_after_calc(comp)
        elif op == Opcode.CPY:
            result = data if mode == Addrmode.IMD else self.bread(data)
            comp = self.reg.Y - result
            self.reg.P.CARRY = (comp >= 0)
            self.set_flag_for_after_calc(comp)
        # inc/dec
        elif op == Opcode.DEC:
            data_ = (self.bread(data) - 1) & 0xFF
            self.write(data, data_)
            self.set_flag_for_after_calc(data_)
        elif op == Opcode.DEX:
            self.reg.X = (self.reg.X - 1) & 0xFF
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.DEY:
            self.reg.Y = (self.reg.Y - 1) & 0xFF
            self.set_flag_for_after_calc(self.reg.Y)
        elif op == Opcode.EOR:
            self.reg.A ^= data if mode == Addrmode.IMD else self.bread(data)
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.INC:
            data_ = (self.bread(data) + 1) & 0xFF
            self.write(data, data_)
            self.set_flag_for_after_calc(data_)
        elif op == Opcode.INX:
            self.reg.X = (self.reg.X + 1) & 0xFF
            self.set_flag_for_after_calc(self.reg.X)
        elif op == Opcode.INY:
            self.reg.Y = (self.reg.Y + 1) & 0xFF
            self.set_flag_for_after_calc(self.reg.Y)
        elif op == Opcode.LSR:
            result = self.reg.A if mode == Addrmode.ACM else self.bread(data)
            self.reg.P.CARRY = result & 0x01
            result = (result >> 1) & 0xFF
            self.reg.P.ZERO = (result == 0)
            if mode == Addrmode.ACM:
                self.reg.A = result
            else:
                self.write(data, result)
            self.reg.P.NEGATIVE = False
        elif op == Opcode.ORA:
            result = data if mode == Addrmode.IMD else self.bread(data)
            self.reg.A |= result
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.ROL:
            raise NotImplementedError
        elif op == Opcode.ROR:
            raise NotImplementedError
        elif op == Opcode.SBC:
            data_ = data if mode == Addrmode.IMD else self.bread(data)
            result = self.reg.A - data_ - int(not self.reg.P.CARRY)
            self.reg.P.CARRY = not(result < 0)
            self.reg.P.OVERFLOW = bool(
                self.reg.P.CARRY and
                (((data_ ^ result) & 0x80) or
                ((self.reg.A ^ result) & 0x80)))
            self.set_flag_for_after_calc(result)
            self.reg.A = result & 0xFF
        elif op == Opcode.PHA:
            self.push(self.reg.A)
        elif op == Opcode.PHP:
            break_ = self.reg.P.BREAK
            self.reg.P.BREAK = True
            self.push_reg_status()
            self.reg.P.BREAK = break_
        elif op == Opcode.PLA:
            self.reg.A = self.pop()
            self.set_flag_for_after_calc(self.reg.A)
        elif op == Opcode.PLP:
            break_ = self.reg.P.BREAK
            self.pop_reg_status()
            self.reg.P.BREAK = break_
            self.reg.P.RESERVED = True
        elif op == Opcode.JMP:
            self.reg.PC = data
        elif op == Opcode.JSR:
            pc = self.reg.PC - 1
            self.push((pc >> 8) & 0xFF)
            self.push(pc & 0xFF)
            self.reg.PC = data
        elif op == Opcode.RTS:
            self.pop_PC()
            self.reg.PC += 1
        elif op == Opcode.RTI:
            break_ = self.reg.P.BREAK
            self.pop_reg_status()
            self.pop_PC()
            self.reg.P.BREAK = break_
            self.reg.P.RESERVED = True
        elif op == Opcode.BCS:
            if self.reg.P.CARRY:
                self.branch(data)
        elif op == Opcode.BCC:
            if not self.reg.P.CARRY:
                self.branch(data)
        elif op == Opcode.BEQ:
            if self.reg.P.ZERO:
                self.branch(data)
        elif op == Opcode.BNE:
            if not self.reg.P.ZERO:
                self.branch(data)
        elif op == Opcode.BMI:
            if self.reg.P.NEGATIVE:
                self.branch(data)
        elif op == Opcode.BPL:
            if not self.reg.P.NEGATIVE:
                self.branch(data)
        elif op == Opcode.BVS:
            if self.reg.P.OVERFLOW:
                self.branch(data)
        elif op == Opcode.BVC:
            if not self.reg.P.OVERFLOW:
                self.branch(data)
        elif op == Opcode.CLD:
            self.reg.P.DECIMAL = False
        elif op == Opcode.CLC:
            self.reg.P.CARRY = False
        elif op == Opcode.CLI:
            self.reg.P.INTERRUPT = False
        elif op == Opcode.CLV:
            self.reg.P.OVERFLOW = False
        elif op == Opcode.SEC:
            self.reg.P.CARRY = True
        elif op == Opcode.SEI:
            self.reg.P.INTERRUPT = True
        elif op == Opcode.SED:
            self.reg.P.DECIMAL = True
        elif op == Opcode.BRK:
            raise NotImplementedError
        elif op == Opcode.NOP:
            pass
        # TODO: unofficial
        elif op == Opcode.NOPI:
            raise NotImplementedError
        elif op == Opcode.NOPD:
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
        self.check_stat(opset, oprand, pc)
        self.exec(opset, oprand)