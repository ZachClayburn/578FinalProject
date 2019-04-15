import random
from typing import List, Callable, Tuple

import simpy

import IFTTTModel.model as model
from IFTTTModel.model import DAYS, HOURS, MINUTES, SECONDS
import IFTTTModel.visualization as vis


class Simulation:

    def __init__(self,
                 num_users: int = 15000,
                 mean_num_devices_per_user: int = 10,
                 stdv_num_devices_per_user: int = 2,
                 user_interaction_mean: float = 20,
                 user_interaction_stdv: float = 10,
                 sim_length_days: int = 5 * DAYS + 1 * MINUTES,
                 server_capacity: int = 30,
                 server_capacity_mean: int = 30,
                 server_capacity_stdv: int = 4,
                 server_response_mean: float = 1 * SECONDS,
                 server_response_stdv: float = 0.01 * SECONDS,
                 boundary_side_length: float = 100
                 ):
        print('Creating Simulations')
        self.num_users = num_users
        self.mean_num_devices_per_user = mean_num_devices_per_user
        self.stdv_num_devices_per_user = stdv_num_devices_per_user

        self.sim_length_days = sim_length_days

        self.user_interaction_mean = user_interaction_mean
        self.user_interaction_stdv = user_interaction_stdv

        self.server_capacity = server_capacity
        self.server_capacity_mean = server_capacity_mean
        self.server_capacity_stdv = server_capacity_stdv
        self.server_response_mean = server_response_mean
        self.server_response_stdv = server_response_stdv

        self.boundary_side_length = boundary_side_length

        self.users: List[model.User] = []
        self.server: model.Server = None

        self.has_run = False
        self.env = simpy.Environment()

        self.build_sim()

    def _get_position(self) -> Tuple[float, float]:
        return self.boundary_side_length * random.random(), self.boundary_side_length * random.random()

    def build_sim(self):
        capacity = random.normalvariate(self.server_capacity_mean, self.server_capacity_stdv)
        server_location = self._get_position()
        self.server = model.Server(self.env, server_location, capacity,
                                   self.server_response_mean, self.server_response_stdv)
        print('Creating users')
        for i in range(self.num_users):
            user = model.User(self.env, self.user_interaction_mean, self.user_interaction_stdv)
            location = self._get_position()
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
                yield env.timeout(1 * DAYS)
                print(f'Finished day {progress_report.day_number} of {int(self.sim_length_days / DAYS)}')
                progress_report.day_number += 1
        progress_report.day_number = 1

        def minute_report(env: simpy.Environment):
            while True:
                yield env.timeout(1 * SECONDS)
                print(f'Minute {divmod(env.now, DAYS)[1]}')

        print('Starting Simulation')
        self.env.process(progress_report(self.env))
        # self.env.process(minute_report(self.env))
        self.env.run(until=self.sim_length_days)
        self.has_run = True

    @_post_simulation
    def view_wait_times(self) -> None:
        vis.view_wait_times(self.users)

    def view_positions(self):
        vis.show_geographical_distribution([self.server], self.users)

    def view_load_over_time(self):
        vis.show_loads_over_time([self.server])
