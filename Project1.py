import sys

"""global variables"""
num_registers = 0
issue_width = 0

current_cycle = 0
registers = {}
instructions = []

used_register_buffer = []
used_register_dict = {}
write_buffer = [] 

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


def init_numreg_issuewidth():
    global num_registers, issue_width

    line = sys.stdin.readline().strip()
    ins = line.split(",")
    num_registers = int(ins[0])
    issue_width = int(ins[1])

    """num_registers = 40
    issue_width = 16
    print(num_registers, issue_width)"""
    if(num_registers < 32):
        return False
    else:
        return True


def createinstructions():
    global instructions
    count = 0
    
    for line in sys.stdin:
        ins = line.strip().split(",")
        instruct = Instruction(ins[0], ins[1], ins[2], ins[3])
        instructions += [instruct]
        count += 1

    """"instruct = Instruction("L",2,80,4)
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
    count = 9
    print(count)"""
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
    global rename_buffer, dispatch_buffer, num_registers, current_cycle, used_register_buffer, used_register_dict
    free_registers = num_registers - 32
    new_list = []

    for instruct in rename_buffer:
        #checks if are available and renames, else stall
        if(free_registers - len(used_register_buffer) > 0):
            
            if(instruct.type == "R"):
                if(instruct.reg2 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg2]]
                if(instruct.reg3 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg3]]
                used_register_buffer.append(instruct)
                used_register_dict[instruct.reg1] = used_register_buffer.index(instruct)
                instruct.write = 32 + used_register_buffer.index(instruct)

            elif(instruct.type == "I"):
                if(instruct.reg2 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg2]]
                used_register_buffer.append(instruct)
                used_register_dict[instruct.reg1] = used_register_buffer.index(instruct)
                instruct.write = 32 + used_register_buffer.index(instruct)

            elif(instruct.type == "L"):
                if(instruct.reg3 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg3]]
                used_register_buffer.append(instruct)
                used_register_dict[instruct.reg1] = used_register_buffer.index(instruct)
                instruct.write = 32 + used_register_buffer.index(instruct)

            elif(instruct.type == "S"):
                if(instruct.reg1 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg1]]
                if(instruct.reg3 in used_register_dict):
                    instruct.reads += [32 + used_register_dict[instruct.reg3]]

            instruct.cycles += [current_cycle]
            dispatch_buffer.append(instruct)
        else:
            new_list += [instruct]
    rename_buffer = new_list
    
    
def dispatch():
    global dispatch_buffer, issue_buffer

    for instruct in dispatch_buffer:
        instruct.cycles += [current_cycle]
        issue_buffer.append(instruct)
    
    dispatch_buffer = []


def issue():
    global issue_buffer, writeback_buffer, write_buffer, current_cycle

    new_list = []
    
    count = 0
    for instruct in issue_buffer:
        if (count < issue_width):

            #check if all read register dependencies are met
            if(set(instruct.reads).issubset(set(write_buffer))):
                instruct.cycles += [current_cycle]
                writeback_buffer.append(instruct)
                count += 1
            else:
                new_list += [instruct]
            """if(instruct.type == "R"):
                if(instruct.reg2 not in write_buffer and instruct.reg3 not in write_buffer):
                    instruct.cycles += [current_cycle]
                    writeback_buffer.append(instruct)
                    write_buffer += [instruct.reg1]
                    count += 1
                else:
                    new_list += [instruct] 
                    
            if(instruct.type == "I"):
                if(instruct.reg2 not in write_buffer):
                    instruct.cycles += [current_cycle]
                    writeback_buffer.append(instruct)
                    write_buffer += [instruct.reg1]
                    count += 1
                else:
                    new_list += [instruct] 
                    
            if(instruct.type == "L"):
                if(instruct.reg3 not in write_buffer):
                    instruct.cycles += [current_cycle]
                    writeback_buffer.append(instruct)
                    write_buffer += [instruct.reg1]
                    count += 1
                else:
                    new_list += [instruct] 
                    
            if(instruct.type == "S"):
                if(instruct.reg1 not in write_buffer and instruct.reg3 not in write_buffer):
                    instruct.cycles += [current_cycle]
                    writeback_buffer.append(instruct)
                    count += 1
                else:
                    new_list += [instruct]        
                    """
        else:
            new_list += [instruct]
    issue_buffer = new_list

def writeback():
    global writeback_buffer, commit_buffer, write_buffer, used_register_buffer, current_cycle

    new_list = []

    count = 0
    for instruct in writeback_buffer:
        if(count < issue_width):
            if(instruct.type != "S"):
                write_buffer.append(instruct.write)
            instruct.cycles += [current_cycle]
            commit_buffer.append(instruct)

            count += 1
        else: 
            new_list += [instruct]

    writeback_buffer = new_list
    

#removes from the instruction buffer
#frees any registers
def commit(committed_count):
    global commit_buffer, used_register_buffer, instructions,current_cycle, issue_width

    new_list = []
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
                used_register_buffer.remove(instruct)
            commit_buffer.remove(instruct)
            count += 1
    

    """for instruct in commit_buffer:
        if(count < issue_width):
            instruct.cycles += [current_cycle]
            used_register_buffer.remove(instruct)
            count += 1
        else:
            new_list += [instruct]"""

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
    init_numreg_issuewidth()
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
        current_cycle += 1

    toString()
        

if __name__ == "__main__":
    main()