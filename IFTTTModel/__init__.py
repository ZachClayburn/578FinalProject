import random
import statistics as stat
from typing import List, Callable, Tuple, Union

import simpy

import IFTTTModel.model as model
from IFTTTModel.model import DAYS, HOURS, MINUTES, SECONDS
import IFTTTModel.visualization as vis


class Simulation:

    def __init__(self,
                 num_users: int = 15000,
                 mean_num_devices_per_user: int = 10,
                 user_interaction_mean: float = 20,
                 sim_length_days: int = 3 * DAYS + 1 * MINUTES,
                 server_capacity: int = 30,
                 server_response_mean: float = 1 * SECONDS,
                 signal_slowness: float = 0.01 * SECONDS,
                 num_servers: int = 3,
                 boundary_side_length: float = 100,
                 ):
        # print('Creating Simulations')
        self.num_users = num_users
        self.mean_num_devices_per_user = mean_num_devices_per_user
        self.stdv_num_devices_per_user = mean_num_devices_per_user * 0.2

        self.sim_length_days = sim_length_days

        self.user_interaction_mean = user_interaction_mean
        self.user_interaction_stdv = user_interaction_mean * 0.2

        self.server_capacity = server_capacity
        self.server_response_mean = server_response_mean
        self.server_response_stdv = server_response_mean * 0.2

        model.time_to_distance_ratio = signal_slowness

        self.num_servers = num_servers

        self.boundary_side_length = boundary_side_length

        self.users: List[model.User] = []
        self.servers: List[model.Server] = []

        self.has_run = False
        self.env = simpy.Environment()

        self.build_sim()

    def _get_position(self) -> Tuple[float, float]:
        return self.boundary_side_length * random.random(), self.boundary_side_length * random.random()

    def build_sim(self):

        for _ in range(self.num_servers):
            server_location = self._get_position()
            self.servers.append(model.Server(self.env, server_location, self.server_capacity,
                                             self.server_response_mean, self.server_response_stdv))

        # print('Creating users')
        for _ in range(self.num_users):
            user = model.User(self.env, self.user_interaction_mean, self.user_interaction_stdv)
            location = self._get_position()
            for _ in range(self._get_num_devices_for_user()):
                controller = model.SimpleController(self.env, location)
                device = model.ToggleDevice(self.env, location)
                steps = random.randint(1, self.num_servers)
                pipeline: List[Union[model.CommunicatingDevice, model.Server]] = random.sample(self.servers, steps)
                pipeline.insert(0, controller)
                pipeline.append(device)
                for i in range(1, len(pipeline) - 1):
                    pipeline[i].register_connection(pipeline[i - 1], pipeline[i + 1])
                user.add_device_with_manual_controller(device, controller)

            self.users.append(user)
            self.env.process(user.run())

    def _get_num_devices_for_user(self) -> int:
        num_devices = 0
        while num_devices == 0:
            num_devices = round(random.normalvariate(self.mean_num_devices_per_user, self.stdv_num_devices_per_user))
        return num_devices

    def _post_simulation(fun: Callable):
        def new_method(self: 'Simulation', *args, **kwargs):
            if not self.has_run:
                raise Exception('Simulation must be run first!')
            return fun(self, *args, **kwargs)

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

        # print('Starting Simulation')
        self.env.process(progress_report(self.env))
        self.env.process(minute_report(self.env))
        self.env.run(until=self.sim_length_days)
        self.has_run = True

    @_post_simulation
    def view_wait_times(self) -> None:
        vis.view_wait_times(self.users)

    def view_positions(self):
        vis.show_geographical_distribution(self.servers, self.users)

    def view_load_over_time(self):
        vis.show_loads_over_time(self.servers)

    @_post_simulation
    def get_max_and_mean_wait(self):
        # print('returning max and mean')
        wait_times = []
        for user in self.users:
            wait_times.extend([i for _, i in user.wait_times])
        max_wait = max(wait_times)
        mean_wait = stat.mean(wait_times)
        return max_wait, mean_wait


if __name__ == '__main__':
    sim = Simulation(num_users=1)
    sim.run()
    print(sim.get_max_and_mean_wait())
    sim.view_load_over_time()
    sim.view_wait_times()
