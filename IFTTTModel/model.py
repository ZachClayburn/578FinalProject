import random
import uuid
from abc import ABC, abstractmethod
from cmath import sqrt
from typing import Tuple, Dict, List, Generator

import simpy


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

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)
        # TODO Make this a list of devices, so one device can control many
        self.connections: Dict[uuid.UUID, CommunicatingDevice] = {}

    def register_controller(self, controller: Controller, device: CommunicatingDevice):
        self.connections[controller.address] = device
        controller.server = self

    def _compute_command(self, controller: CommunicatingDevice):
        yield self.env.timeout(random.random())
        # FIXME Make this a variable dependant on the type of controller and
        #  device, and only let a server handle so many responses at once

    def receive_communication(self, sender: CommunicatingDevice):
        yield from self._compute_command(sender)
        yield from communicate(self, self.connections[sender.address])


def _compute_distance(location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
    return sqrt((location1[0] - location2[0]) ** 2 + (location1[1] - location2[1]) ** 2)


def communicate(device1: CommunicatingDevice, device2: CommunicatingDevice):
    yield device1.env.timeout(random.random())  # FIXME Add controllable range of communication time
    yield from device2.receive_communication(device1)


class User:
    id_counter = 0

    def __init__(self, env: simpy.Environment):
        self.env = env
        self.id_number = User._get_id_num()
        self.controls: List[Controller] = []
        self.devices: List[CommunicatingDevice] = []
        self.wait_times: List[Tuple[int, int]] = []

    @classmethod
    def _get_id_num(cls) -> int:
        num = cls.id_counter
        cls.id_counter += 1
        return num

    def add_device_with_manual_controller(self, device: CommunicatingDevice, controller: Controller):
        self.devices.append(device)
        self.controls.append(controller)

    def run(self):
        while True:
            yield self.env.timeout(random.random())
            # FIXME Make this a variable
            before = self.env.now
            device = random.choice(self.controls)
            yield from communicate(device, device.server)
            after = self.env.now
            wait = after - before
            self.wait_times.append((before, wait))
