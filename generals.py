from collections import Counter
from multiprocessing import Process
from rpyc.utils.server import ThreadedServer
import random
import rpyc,re


from rpc_handler import RPCHandler


class General(Process):
    global HOST_PORT,HOST
    HOST_PORT = 7779
    HOST = "localhost"

    def __init__(self, port, generals, primary):
        super().__init__()
        self.rpc_handler = RPCHandler(self)
        self.id = port - HOST_PORT
        self.port = port
        self.generals = generals
        self.state = "NF"
        self.primary = primary
        self.order = ""
    
    def run(self):
        ThreadedServer(self.rpc_handler, port=self.port).start()
    
    def init_generals(self, generals):
        self.generals = set(generals)
        if self.port in self.generals:
            self.generals.remove(self.port)

        if self.is_primary():
            for general in self.generals:
                conn = rpyc.connect(HOST, general)
                conn.root.init_generals(self.generals)
                conn.close()

    def add_general(self, generals):
        if self.is_primary():
            for general in generals:
                if general + HOST_PORT not in self.generals:
                    self.generals.add(general + HOST_PORT)
            self.init_generals(self.generals)
            return self.current_state().replace('primary,','').replace('secondary,','')


    def kill_general(self, general_id):
       if self.is_primary() and general_id + HOST_PORT in self.generals:
            self.generals.remove(general_id + HOST_PORT)
            self.init_generals(self.generals)
            return self.current_state().replace('primary,','').replace('secondary,','')
    
    def current_state(self):
        states = [str(self)]
        if self.is_primary():
            for general in sorted(self.generals):
                conn = rpyc.connect(HOST, general)
                states.append(str(conn.root.current_state()))
                conn.close()
            #print(states)
        return "\n".join(states)

    def set_general_state(self, general_id, state):
        if state not in ["NF", "F"]:
            return f"Error setting state {state} for general {general_id}."
        if general_id == self.id:
            self.state = state
            if self.is_primary():
                return self.current_state()
            else:
                return True
        elif self.is_primary() and general_id + HOST_PORT in self.generals:
            conn = rpyc.connect(HOST, general_id + HOST_PORT)
            conn.root.set_general_state(general_id, state)
            conn.close()
            return self.current_state().replace('primary,','').replace('secondary,','')

    
    def all_generals(self, n):
        _g = __ = []
        if self.is_primary():
            _g = [general-HOST_PORT for general in self.generals]
            _g.append(self.id)
            i = 1
            while n > 0:
                if i not in sorted(_g):
                    __.append(i)
                    n -= 1
                i += 1
            return __
        return list()

    def elect_primary(self, primary):
        self.primary = primary
        if self.id == primary:
            for general in self.generals:
                conn = rpyc.connect(HOST, general)
                conn.root.elect_primary(primary)
                conn.close()
            self.init_generals(self.generals)
            return self.current_state().replace('primary,','').replace('secondary,','')
        return True

    def get_results(self,order,g_intent):
        if len(self.generals) == 0:
            return order, self.state == "NF"
        majority = g_intent.most_common(1)
        non_faulty = g_intent.most_common(1)
        #print(majority)
        #print(non_faulty)
        return majority[0][0],non_faulty[0][1]

    def primary_order(self, order):
        if not self.is_primary():
            if self.state == "F":
                order = self.random_order()
            self.order = order
            return True
        return False

    def get_intent_from_generals(self):
        proposed_intent = Counter()
        if not self.is_primary():
            proposed_intent[self.order] += 1
            for general in self.generals:
                conn = rpyc.connect(HOST, general)
                proposed_intent[conn.root.retrieve_order()] += 1
                conn.close()
     
            if proposed_intent["attack"] == proposed_intent["retreat"]:
                majority = "undefined"
            else:
                majority = proposed_intent.most_common(1)[0][0]

            return self.state, majority

    def retrieve_order(self):
        return self.order

    def perform_order(self, order):
        total_generals = 1 + len(self.generals) 
        output = ""
        malicious_general = int(self.state == "F")
        g_intent = Counter()
        if self.is_primary():
            self.order = order
            for general in self.generals:
                if self.state == "F":
                    order = self.random_order()
                conn = rpyc.connect(HOST, general)
                conn.root.primary_order(order)
                conn.close()

            for general in sorted(self.generals):
                g_id = general - HOST_PORT
                conn = rpyc.connect(HOST, general)
                state, majority = conn.root.get_intent_from_generals()
                conn.close()
                malicious_general += int(state == "F") 
                g_intent[majority] += 1
                output += f"G{ g_id }, secondary, majority={ majority }, state={ state }" + "\n"

            majority_order,non_faulty = self.get_results(order,g_intent)

            output = f"G{self.id}, primary, majority={self.order}, state={self.state}\n" + output

            if malicious_general == 0:
                output += f"Execute order: {majority_order}! Non-faulty node{General.pluralize(malicious_general)} in the system - {max(non_faulty-malicious_general,0)} out of {total_generals} quorum suggest {majority_order}"
                return output
            if total_generals == 1 or total_generals < 3*malicious_general + 1 :
                output += f"Execute order: cannot be determined - not enough generals in the system! {malicious_general} faulty node{General.pluralize(malicious_general)} in the system - {total_generals - 1} out of {total_generals} quorum not consistent"
            else:
                output += f"Execute order: {majority_order}! {malicious_general} faulty node{General.pluralize(malicious_general)} in the system - {max(non_faulty-malicious_general,0)} out of {total_generals} quorum suggest {majority_order}"
            return output

    def is_primary(self):
        if self.id == self.primary:
            return True
        return False
            
    def random_order(self):
        if random.randint(0, 1) == 1:
            return "attack"
        return "retreat"
        
    def pluralize(self):
        if self != 1:
            return 's'
        return ''
        
            
    def __repr__(self):
        if self.is_primary():
            label = "primary"
        else:
            label = "secondary"
        return f"G{self.id}, {label}, state={self.state}"


