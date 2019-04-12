import random
import uuid
from abc import ABC, abstractmethod
from cmath import sqrt
from typing import Tuple, Dict, List, Generator

import simpy
import scipy.stats as st
import numpy as np

DAYS = 24
HOURS = 1
MINUTES = 1 / 60
SECONDS = 1 / 3600


class CommunicatingDevice(ABC):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        self.address = uuid.uuid1()
        self.env = env
        self.location = location

    @abstractmethod
    def receive_communication(self, sender: 'CommunicatingDevice') -> Generator:
        raise NotImplementedError


class Controller(CommunicatingDevice, ABC):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)
        self.server: Server = None


class ToggleDevice(CommunicatingDevice):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)
        self.is_active = False

    def receive_communication(self, sender: CommunicatingDevice) -> Generator:
        self.is_active = not self.is_active
        yield self.env.timeout(0)


class SimpleController(Controller):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)

    def receive_communication(self, sender: CommunicatingDevice) -> Generator:
        # This Doesn't really need to be here, the simple controller will never receive any communication back, so this
        # is a no-op
        yield self.env.timeout(0)


class Server(CommunicatingDevice):

    def __init__(self, env: simpy.Environment,
                 location: Tuple[float, float],
                 capacity: int,
                 response_mean: float,
                 response_stdev: float,
                 ):
        super().__init__(env, location)
        # TODO Make this a list of devices, so one device can control many?
        self.response_mean = response_mean
        self.response_stdev = response_stdev
        self.connections: Dict[uuid.UUID, CommunicatingDevice] = {}
        self.resources = simpy.Resource(self.env, capacity=capacity)
        self.load: List[Tuple[float, int]] = []

    def register_controller(self, controller: Controller, device: CommunicatingDevice):
        self.connections[controller.address] = device
        controller.server = self

    def _compute_command(self, controller: CommunicatingDevice):
        with self.resources.request() as req:
            self.load.append((self.env.now, self.resources.count))
            yield req
            self.load.append((self.env.now, self.resources.count))
            yield self.env.timeout(random.normalvariate(self.response_mean, self.response_stdev))
            # TODO Make this a variable dependant on the type of controller and device?

    def receive_communication(self, sender: CommunicatingDevice):
        yield from self._compute_command(sender)
        yield from communicate(self, self.connections[sender.address])


def _compute_distance(location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
    return sqrt((location1[0] - location2[0]) ** 2 + (location1[1] - location2[1]) ** 2)


def communicate(device1: CommunicatingDevice, device2: CommunicatingDevice):
    yield device1.env.timeout(random.random() * 0.01 * SECONDS)  # FIXME Add controllable range of communication time
    yield from device2.receive_communication(device1)


class UserActionDistribution(st.rv_continuous):
    def __init__(self):
        super().__init__(a=0, b=(1*DAYS))

    def _pdf(self, x, *args):
        return (0.8 * self.normal_pdf(x, 7, 7)) + (2.2 * self.normal_pdf(x, 17, 15))

    @staticmethod
    def normal_pdf(x: float, mean: float, variance: float) -> float:
        return np.exp(- (x - mean)**2 / (2 * variance)) / np.sqrt(2 * np.pi * variance)


class User:
    id_counter = 0

    def __init__(self,
                 env: simpy.Environment,
                 daily_interactions_mean: float,
                 daily_interactions_stdev: float):
        self.daily_interactions_stdev = daily_interactions_stdev
        self.daily_interactions_mean = daily_interactions_mean
        self.env = env
        self.id_number = User._get_id_num()
        self.controls: List[Controller] = []
        self.devices: List[CommunicatingDevice] = []
        self.wait_times: List[Tuple[int, int]] = []
        self.interaction_distribution = UserActionDistribution()

    def _action_times(self):
        day_count = 0
        while True:
            interaction_count = -1
            while interaction_count < 0:
                interaction_count = random.normalvariate(self.daily_interactions_mean, self.daily_interactions_stdev)
                interaction_count = int(interaction_count)
            interaction_times = self.interaction_distribution.rvs(scale=2, size=int(np.round(interaction_count)))
            interaction_times.sort()
            for time in interaction_times:
                yield time + day_count * DAYS
            day_count += 1

    @classmethod
    def _get_id_num(cls) -> int:
        num = cls.id_counter
        cls.id_counter += 1
        return num

    def add_device_with_manual_controller(self, device: CommunicatingDevice, controller: Controller):
        self.devices.append(device)
        self.controls.append(controller)

    def run(self):
        for interaction_time in self._action_times():
            yield self.env.timeout(max(interaction_time - self.env.now, 0))
            print(f'{self.env.now}, {self.id_number}')
            before = self.env.now
            device = random.choice(self.controls)
            yield from communicate(device, device.server)
            after = self.env.now
            wait = after - before
            self.wait_times.append((before, wait))
