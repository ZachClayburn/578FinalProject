import random
from typing import List

import simpy

import IFTTTModel.model as model
import IFTTTModel.visualization as vis


class SimParams:

    def __init__(self,
                 num_users: int = 15000,
                 mean_num_devices_per_user: int = 10,
                 stdv_num_devices_per_user: int = 2,
                 sim_length_days: int = 5,
                 ):
        self.num_users = num_users
        self.mean_num_devices_per_user = mean_num_devices_per_user
        self.stdv_num_devices_per_user = stdv_num_devices_per_user
        self.sim_length_days = sim_length_days


class Simulation:

    def __init__(self, params: SimParams = SimParams()):
        self.params = params
        self.env = simpy.Environment()
        self.users: List[model.User] = []
        self.server = model.Server(self.env, (0., 0.))

        for i in range(self.params.num_users):
            user = model.User(self.env)
            location = (0., 0.)
            for j in range(self._get_num_devices_for_user()):
                controller = model.SimpleController(self.env, location)
                device = model.ToggleDevice(self.env, location)
                self.server.register_controller(controller, device)
                user.add_device_with_manual_controller(device, controller)

            self.users.append(model.User(self.env))
            self.env.process(user.run())

    def _get_num_devices_for_user(self) -> int:
        return round(random.normalvariate(self.params.mean_num_devices_per_user, self.params.stdv_num_devices_per_user))

    def run(self):
        self.env.run(until=self.params.sim_length_days * 24)
