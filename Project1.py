import sys

#rename needs to be in order if no available registers
#garbage collection for writebuffer and used_reg
"""global variables"""
num_registers = 0
issue_width = 0

current_cycle = 0
registers = {}
instructions = []

registers_inst = []
used_register_dict = {}
write_buffer = [] 
load_store_stall_buffer = [] #pointer to a S-type and L-type instruction, a queue used for stalling conservative load-store by keeping track of whuich store word came first
remove_buffer = []

#<FE>,<DE>,<RE>,<DI>,<IS>,<WB>,<CO> buffers
decode_buffer = []
rename_buffer = []
dispatch_buffer = []
issue_buffer = []
writeback_buffer = []
commit_buffer = []
"""global variables"""


class Instruction:
    def __init__(self, type, reg1, reg2, reg3):
        self.type = type
        self.reg1 = reg1
        self.reg2 = reg2
        self.reg3 = reg3
        self.cycles = []
        self.reads = []
        self.write = reg1


#checks if there is a S-type before a L-type instruct
#return true if there is a S-type and false otherwise
def load_store_checker(instruct):
    global load_store_stall_buffer
    
    if(instruct not in load_store_stall_buffer):
        return False
    
    ind = load_store_stall_buffer.index(instruct)
    while ind >= 0:
        if load_store_stall_buffer[ind].type == "S":
            return True
        ind-=1
    return False

def remove_buffer_helper():
    global remove_buffer, registers_inst, used_register_dict
    dic = {}
    for key in used_register_dict:
        dic[used_register_dict[key]] = key

    for instruct in remove_buffer:
        ind = registers_inst.index(instruct)
        registers_inst[ind] = 0
        if ind in dic:
            used_register_dict.pop(dic[ind])

    remove_buffer = []

def find_next_free_register():
    global registers_inst
    for i in range(len(registers_inst)):
        if registers_inst[i] == 0:
            return i
    return -1

def initialize():
    global num_registers, issue_width, load_store_stall_buffer, registers_inst

    """line = sys.stdin.readline().strip()
    ins = line.split(",")
    num_registers = int(ins[0])
    issue_width = int(ins[1])"""

    load_store_stall_buffer = []

    num_registers = 40
    issue_width = 16
    registers_inst = [0] * (num_registers - 32)
    print(num_registers, issue_width)
    if(num_registers < 32):
        return False
    else:
        return True


def createinstructions():
    global instructions
    count = 0
    
    """for line in sys.stdin:
        ins = line.strip().split(",")
        instruct = Instruction(ins[0], ins[1], ins[2], ins[3])
        instructions += [instruct]
        count += 1"""

    instruct = Instruction("L",2,80,4)
    instructions += [instruct]
    instruct = Instruction("L",3,64,5)
    instructions += [instruct]
    instruct = Instruction("R",2,2,3)
    instructions += [instruct]
    instruct = Instruction("S",2,24,29)
    instructions += [instruct]
    instruct = Instruction("I",1,0,8)
    instructions += [instruct]
    instruct = Instruction("R",6,6,1)
    instructions += [instruct]
    instruct = Instruction("R",7,7,1)
    instructions += [instruct]
    instruct = Instruction("L",4,0,6)
    instructions += [instruct]
    instruct = Instruction("L",5,0,7)
    instructions += [instruct]
    instruct = Instruction("L",2,80,4)
    instructions += [instruct]
    instruct = Instruction("L",3,64,5)
    instructions += [instruct]
    instruct = Instruction("R",2,2,3)
    instructions += [instruct]
    instruct = Instruction("S",2,24,29)
    instructions += [instruct]
    count = 13
    print(count)
    return count


#<FE>,<DE>,<RE>,<DI>
def fetch(fetch_index, instruction_count):
    global decode_buffer, current_cycle, issue_width

    count = 0
    while count < issue_width and (fetch_index + count) < instruction_count:
        instruct = instructions[fetch_index + count]
        instruct.cycles = [current_cycle]
        decode_buffer += [instruct]
        count += 1
    fetch_index += count

    return fetch_index


def decode():
    global decode_buffer, rename_buffer, current_cycle

    for instruct in decode_buffer:
        instruct.cycles += [current_cycle]
        rename_buffer.append(instruct)
    
    decode_buffer = []
    

#set the free registers
def rename():
    global rename_buffer, dispatch_buffer, num_registers, current_cycle, registers_inst, used_register_dict, load_store_stall_buffer, write_buffer
    remove_list = []

    for instruct in rename_buffer:

        free_reg_index = find_next_free_register()
        if (instruct.type == "S"): #S-types don't need a free register to perform
            if(instruct.reg1 in used_register_dict):
                instruct.reads += [32 + used_register_dict[instruct.reg1]]
            if(instruct.reg3 in used_register_dict):
                instruct.reads += [32 + used_register_dict[instruct.reg3]]
            load_store_stall_buffer += [instruct]
            instruct.cycles += [current_cycle]
            dispatch_buffer.append(instruct)
            remove_list.append(instruct)

        elif(free_reg_index != -1): #evokes only when there are free registers
            
            if(instruct.type == "R"):
                if(instruct.reg2 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg2]]
                if(instruct.reg3 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg3]]
                registers_inst[free_reg_index] = instruct
                used_register_dict[instruct.reg1] = registers_inst.index(instruct)
                instruct.write = 32 + registers_inst.index(instruct)
                write_buffer.append(instruct.write)

            elif(instruct.type == "I"):
                if(instruct.reg2 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg2]]
                registers_inst[free_reg_index] = instruct
                used_register_dict[instruct.reg1] = registers_inst.index(instruct)
                instruct.write = 32 + registers_inst.index(instruct)
                write_buffer.append(instruct.write)

            elif(instruct.type == "L"):
                if(instruct.reg3 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg3]]
                registers_inst[free_reg_index] = instruct
                used_register_dict[instruct.reg1] = registers_inst.index(instruct)
                instruct.write = 32 + registers_inst.index(instruct)
                write_buffer.append(instruct.write)
                load_store_stall_buffer += [instruct]

            instruct.cycles += [current_cycle]
            dispatch_buffer.append(instruct)
            remove_list.append(instruct)
        else:
            for instruct in remove_list:
                rename_buffer.remove(instruct)
            return
        
    for instruct in remove_list:
                rename_buffer.remove(instruct)
    
    
def dispatch():
    global dispatch_buffer, issue_buffer

    for instruct in dispatch_buffer:
        instruct.cycles += [current_cycle]
        issue_buffer.append(instruct)
    
    dispatch_buffer = []


def issue():
    global issue_buffer, writeback_buffer, write_buffer, current_cycle, load_store_stall_buffer

    new_list = []
    
    count = 0
    for instruct in issue_buffer:

        if (count >= issue_width):
            new_list += [instruct]
        elif(set(instruct.reads).issubset(set(write_buffer)) and len(instruct.reads)!=0):
            new_list += [instruct]
        elif(instruct.type == "L" and load_store_checker(instruct)):    #stall load-store
            new_list += [instruct]
        else:
            instruct.cycles += [current_cycle]
            writeback_buffer.append(instruct)
            count += 1
        """if (count < issue_width):
            #check if all read register dependencies are met
            if(set(instruct.reads).issubset(set(write_buffer))):
                if(instruct.type != "L" or load_store_stall == None):
                    instruct.cycles += [current_cycle]
                    writeback_buffer.append(instruct)
                    count += 1
            else:
                new_list += [instruct]
        else:
            new_list += [instruct]"""
    issue_buffer = new_list

def writeback():
    global writeback_buffer, commit_buffer, write_buffer, registers_inst, current_cycle, load_store_stall_buffer

    new_list = []

    count = 0
    for instruct in writeback_buffer:
        if(count < issue_width):
            if(instruct.type != "S"):
                write_buffer.remove(instruct.write)
            if(instruct.type == "S" or instruct.type == "L"):
                load_store_stall_buffer.remove(instruct)
            instruct.cycles += [current_cycle]
            commit_buffer.append(instruct)

            count += 1
        else: 
            new_list += [instruct]

    writeback_buffer = new_list
    

#removes from the instruction buffer
#frees any registers
def commit(committed_count):
    global commit_buffer, registers_inst, instructions,current_cycle, remove_buffer, issue_width, write_buffer

    count = 0
    inorder_flag = True
    while(inorder_flag and committed_count+count < len(instructions)):
        instruct = instructions[committed_count+count]
        if(count == issue_width or len(commit_buffer) == 0):
            inorder_flag = False
        elif(instruct not in commit_buffer):
            inorder_flag = False
        else:
            instruct.cycles += [current_cycle]
            if(instruct.type != "S"):
                remove_buffer.append(instruct)
            commit_buffer.remove(instruct)
            count += 1

    return committed_count + count


#prints out the instruction cycles
def toString():
    global instructions

    for instruct in instructions:
        print(str(instruct.cycles[0])+","+str(instruct.cycles[1])+","+str(instruct.cycles[2])+","+str(instruct.cycles[3])+","+str(instruct.cycles[4])+","+str(instruct.cycles[5])+","+str(instruct.cycles[6]))


def main():
    global current_cycle
    instruction_count = 0
    fetch_index = 0
    committed_count = 0
    
    #Init
    initialize()
    instruction_count = createinstructions()

    #scheduling
    while(committed_count < instruction_count):
        committed_count = commit(committed_count)
        writeback()
        issue()
        dispatch()
        rename()
        decode()
        fetch_index = fetch(fetch_index, instruction_count)
        remove_buffer_helper()
        current_cycle += 1

    toString()
        

if __name__ == "__main__":
    main()