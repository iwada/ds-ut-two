import rpyc

class RPCHandler(rpyc.Service):

    def exposed_init_generals(self, port): return self.general.init_generals(port)

    def exposed_add_general(self, generals): return self.general.add_general(generals)

    def exposed_kill_general(self, general_id): return self.general.kill_general(general_id)

    def exposed_current_state(self): return self.general.current_state()

    def exposed_set_general_state(self, general_id, state): return self.general.set_general_state(general_id, state)

    def exposed_all_generals(self, n): return self.general.all_generals(n)

    def exposed_elect_primary(self, general_id): return self.general.elect_primary(general_id)

    def exposed_primary_order(self, order): return self.general.primary_order(order)

    def exposed_perform_order(self, order):  return self.general.perform_order(order)

    def exposed_get_intent_from_generals(self): return self.general.get_intent_from_generals()

    def exposed_retrieve_order(self): return self.general.retrieve_order()

    def __init__(self, general):
        self.general = general
        super().__init__()
