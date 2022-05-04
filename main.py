
import rpyc, time, sys
from generals import General 


def main():

    INFO = """commands: 
    actual-order <attack|retreat> 
    g-state <id> <faulty|non-faulty> 
    g-state 
    g-kill <id_of_general> 
    g-add <k_no_of_generals>
    exit
    info
    """
    global HOST_PORT, HOST
    HOST_PORT = 7779
    HOST = "localhost"
    generals = {}
    primary = " "

    if len(sys.argv) != 2 or not sys.argv[1].isnumeric() or int(sys.argv[1]) < 1:
        print("usage: general_byzantine_program.sh [N]\n\tN must be a number > 0")
        exit(1)

    number_of_generals = int(sys.argv[1])

    for n in range(1, number_of_generals + 1):
        if primary == " " : primary = n
        generals[n] = General(HOST_PORT + n, [], primary)

    for n in generals:
        generals[n].start()
    time.sleep(0.5)
    conn = rpyc.connect("localhost", generals[primary].port)
    conn.root.init_generals(set(range(HOST_PORT + 1, HOST_PORT + number_of_generals + 1)))
    conn.close()

    running = True
    while running:
        command = input("\n$ ")
        args = None
        value = None
        command = command.split(' ')
        if(len(command) == 2):
            args = command[1]
        if(len(command) == 3):
            args = command[1]
            value = command[2]
        striped_command = command[0].rstrip()
        if striped_command == "actual-order":
            if validate_order(args):
                conn = rpyc.connect(HOST, primary + HOST_PORT)
                print(conn.root.execute_order(str(args)))
                conn.close()
            else:
                print(f"Wrong order given - {args}")
        elif striped_command == "g-state" and len(command) == 3:
            if validate_state(value):
                general_state = "NF" if value == "non-faulty" else "F"
                conn = rpyc.connect(HOST, primary + HOST_PORT)
                print(conn.root.set_general_state(int(args), general_state))
                conn.close()
            else:
                print(f"Wrong state given - {value}")

        elif striped_command == "g-state":
            conn = rpyc.connect(HOST, primary + HOST_PORT)
            print(str(conn.root.current_state()))
            conn.close()

        elif striped_command == "g-kill" and len(command) == 2:
             general_id = int(args)
             if is_gen_gt_2(generals):
                is_new_leader_avaliable,primary = is_leader_dead(general_id,generals,primary)
                conn = rpyc.connect(HOST, primary + HOST_PORT)
                if is_new_leader_avaliable:
                    print(conn.root.elect_primary(primary))
                else:
                    print(conn.root.kill_general(general_id))
                conn.close()
                generals.pop(general_id).terminate() if general_id in generals else ''
             else:
                 print(f"Error killing general with id {general_id}")

        elif striped_command == "g-add" and len(command) == 2:
           add_general(generals,primary,args)

        elif striped_command == "exit":
            print("Program exited.")
            running = False
            for n in generals: generals[n].terminate()

        elif striped_command == "info":
            print(INFO)
        else:
            print(f"Invalid Command: {striped_command}. type info for avaliable commands")

def add_general(generals,primary,args):
    conn = rpyc.connect(HOST, primary + HOST_PORT)
    generals_ids = conn.root.all_generals(int(args))
    for n in generals_ids:
        general = General(HOST_PORT + n, [], primary)
        generals[n] = general
        general.start()
    time.sleep(0.5)
    print(conn.root.add_general(generals_ids))
    conn.close()

def validate_state(value):
    if str(value.lower()) not in ["faulty","non-faulty"]:
        return False
    return True

def validate_order(args):
    if str(args.lower()) not in ["attack","retreat"]:
        return False
    return True

def is_leader_dead(general_id,generals,primary):
    if general_id == primary:
        for node in sorted(generals):
            if node != primary:
                primary = node
                return True, primary
    return False, primary

def is_gen_gt_2(generals):
    if len(generals) <= 2:
       return False
    return True


if __name__ == '__main__':
    main()