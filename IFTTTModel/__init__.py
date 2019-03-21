import random
from typing import List, Callable

import simpy

import IFTTTModel.model as model
import IFTTTModel.visualization as vis


class Simulation:

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

        self.has_run = False
        self.env = simpy.Environment()

        self.users: List[model.User] = []
        self.server = model.Server(self.env, (0., 0.))

        for i in range(self.num_users):
            user = model.User(self.env)
            location = (0., 0.)
            for j in range(self._get_num_devices_for_user()):
                controller = model.SimpleController(self.env, location)
                device = model.ToggleDevice(self.env, location)
                self.server.register_controller(controller, device)
                user.add_device_with_manual_controller(device, controller)

            self.users.append(user)
            self.env.process(user.run())

    def _get_num_devices_for_user(self) -> int:
        return round(random.normalvariate(self.mean_num_devices_per_user, self.stdv_num_devices_per_user))

    def _post_simulation(fun: Callable):
        def new_method(self: 'Simulation', *args, **kwargs):
            if not self.has_run:
                raise Exception('Simulation must be run first!')
            fun(self, *args, **kwargs)

        return new_method

    def run(self):
        if self.has_run:
            return  # Only allow one run

        def progress_report(env: simpy.Environment):
            while True:
                yield env.timeout(24)
                print(f'Finished day {progress_report.day_number} of {self.sim_length_days}')
                progress_report.day_number += 1
        progress_report.day_number = 1

        self.env.process(progress_report(self.env))
        self.env.run(until=self.sim_length_days * 24 + 1/24)  # FIXME Add constants for time stuff
        self.has_run = True

    @_post_simulation
    def view_wait_times(self) -> None:
        vis.view_wait_times(self.users)
