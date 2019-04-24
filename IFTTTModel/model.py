import random
import uuid
from abc import ABC, abstractmethod
from cmath import sqrt
from typing import Tuple, Dict, List, Generator, Iterable, Union

import simpy
import numpy as np

DAYS = 24
HOURS = 1
MINUTES = 1 / 60
SECONDS = 1 / 3600

time_to_distance_ratio: float = None


class CommunicatingDevice(ABC):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        self.address = uuid.uuid4()
        self.env = env
        self.location = location

    def __repr__(self):
        return f'{self.__class__.__name__}(address={self.address!r}, location={self.location!r})'

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

    def register_connection(self, source: Union[Controller, 'Server'], destination: CommunicatingDevice):
        self.connections[source.address] = destination
        source.server = self

    def _compute_command(self, controller: CommunicatingDevice):
        with self.resources.request() as req:
            current_load = self.resources.count
            self.load.append((self.env.now, current_load))
            yield req
            self.load.append((self.env.now, self.resources.count))
            base_response = -1
            while base_response < 0:
                base_response = random.normalvariate(self.response_mean, self.response_stdev)
            response_time = (1 + current_load / self.resources.capacity) * base_response
            yield self.env.timeout(response_time)
            # TODO Make this a variable dependant on the type of controller and device?

    def receive_communication(self, sender: CommunicatingDevice):
        yield from self._compute_command(sender)
        yield from communicate(self, self.connections[sender.address])


def _compute_distance(location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
    dist = sqrt((location1[0] - location2[0]) ** 2 + (location1[1] - location2[1]) ** 2)
    return dist if not isinstance(dist, complex) else dist.real


def communicate(device1: CommunicatingDevice, device2: CommunicatingDevice):
    dist = _compute_distance(device1.location, device2.location)
    yield device1.env.timeout(dist * time_to_distance_ratio)  # FIXME Add controllable range of communication time
    yield from device2.receive_communication(device1)


class User:
    id_counter = 0

    def __init__(self,
                 env: simpy.Environment,
                 daily_interactions_mean: float,
                 daily_interactions_stdev: float,
                 patience: float = 0):  # TODO Remove default value
        self.daily_interactions_stdev = daily_interactions_stdev
        self.daily_interactions_mean = daily_interactions_mean
        self.env = env
        self.patience = patience
        self.resource = simpy.Resource(env)
        self.id_number = User._get_id_num()
        self.controls: List[Controller] = []
        self.devices: List[CommunicatingDevice] = []
        self.wait_times: List[Tuple[int, int]] = []

    def _action_times(self, day_count: int):
        interaction_count = -1
        while interaction_count < 0:
            interaction_count = random.normalvariate(self.daily_interactions_mean, self.daily_interactions_stdev)
            interaction_count = int(interaction_count)
        interaction_times = self._daily_times(size=int(np.round(interaction_count)))
        for time in interaction_times:
            yield time + day_count * DAYS

    @staticmethod
    def _daily_times(size: int) -> Iterable[float]:
        times = []
        for _ in range(size):
            time = -1
            mu_sigma = (17, 5) if random.random() < 0.65 else (7, 1)
            while time < 0:
                time = random.normalvariate(*mu_sigma)
            times.append(time)
        times.sort()
        return times

    @classmethod
    def _get_id_num(cls) -> int:
        num = cls.id_counter
        cls.id_counter += 1
        return num

    def add_device_with_manual_controller(self, device: CommunicatingDevice, controller: Controller):
        self.devices.append(device)
        self.controls.append(controller)

    def _interact(self, interaction_time):
        scheduled_time = interaction_time - self.env.now
        assert scheduled_time >= 0
        yield self.env.timeout(scheduled_time)
        before = self.env.now
        device = random.choice(self.controls)
        yield from communicate(device, device.server)
        after = self.env.now
        wait = after - before
        self.wait_times.append((before, wait))

    def run(self):
        day_count = 0
        while True:
            for interaction_time in self._action_times(day_count):
                self.env.process(self._interact(interaction_time))
            day_count += 1
            yield self.env.timeout(1 * DAYS)
