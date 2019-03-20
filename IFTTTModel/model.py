import random
import uuid
from abc import ABC, abstractmethod
from cmath import sqrt
from typing import Tuple, Dict, List

import simpy


class CommunicatingDevice(ABC):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        self.address = uuid.uuid1()
        self.env = env
        self.location = location

    @abstractmethod
    def receive_communication(self, sender: 'CommunicatingDevice'):
        pass


class ToggleDevice(CommunicatingDevice):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)
        self.is_active = False

    def receive_communication(self, sender: CommunicatingDevice):
        self.is_active = not self.is_active


class SimpleController(CommunicatingDevice):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)

    def receive_communication(self, sender: CommunicatingDevice):
        # This Doesn't really need to be here, the simple controller will never receive any communication back, so this
        # is a no-op
        pass


class Server(CommunicatingDevice):

    def __init__(self, env: simpy.Environment, location: Tuple[float, float]):
        super().__init__(env, location)
        # TODO Make this a list of devices, so one device can control many
        self.connections: Dict[uuid.UUID, CommunicatingDevice] = {}

    def register_controller(self, controller: CommunicatingDevice, device: CommunicatingDevice):
        self.connections[controller.address] = device

    def _compute_command(self, controller: CommunicatingDevice):
        yield self.env.timeout(random.random)
        # FIXME Make this a variable dependant on the type of controller and
        #  device, and only let a server handle so many responses at once

    def receive_communication(self, sender: CommunicatingDevice):
        yield self._compute_command(sender)
        yield communicate(self, self.connections[sender.address])


def _compute_distance(location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
    return sqrt((location1[0] - location2[0]) ** 2 + (location1[1] - location2[1]) ** 2)


def communicate(device1: CommunicatingDevice, device2: CommunicatingDevice):
    yield device1.env.timeout(random.random())  # FIXME Add controllable range of communication time
    yield device2.receive_communication(device1)


class User:

    def __init__(self, env: simpy.Environment):
        self.env = env
        self.controls: List[CommunicatingDevice] = []
        self.devices: List[CommunicatingDevice] = []

    def add_device_with_manual_controller(self, device: CommunicatingDevice, controller: CommunicatingDevice):
        self.devices.append(device)
        self.controls.append(controller)
