from typing import List

import matplotlib.pyplot as plt

import IFTTTModel.model as model


def view_wait_times(users: List[model.User]) -> None:
    wait_time_tuples = []
    for user in users:
        wait_time_tuples.extend(user.wait_times)
    wait_time_tuples.sort(key=lambda x: x[0])

    times, wait_times = zip(*wait_time_tuples)
    plt.figure(1)
    plt.plot(times, wait_times)
    plt.xlabel('Time')
    plt.ylabel('Wait time')
    plt.title('Wait times over time')

    plt.figure(2)
    plt.hist(wait_times)
    plt.xlabel('Wait Time')
    plt.title('Distributions of wait times')

    plt.show()


def show_geographical_distribution(servers: List[model.Server], users: List[model.User]) -> None:
    server_x = []
    server_y = []

    for server in servers:
        x_pos, y_pos = server.location
        server_x.append(x_pos)
        server_y.append(y_pos)

    user_x = []
    user_y = []

    for users in users:
        x_pos, y_pos = users.devices[0].location
        user_x.append(x_pos)
        user_y.append(y_pos)

    plt.figure()

    plt.scatter(user_x, user_y, s=5, c=[[0, 0, 0]])
    plt.scatter(server_x, server_y, s=20, c=[[1, 0, 0]])

    plt.axis('equal')
    plt.show()


def show_loads_over_time(servers: List[model.Server]):
    server_loads = []
    for server in servers:
        server_loads.extend(server.load)

    server_loads.sort(key=lambda x: x[0])

    time, loads = zip(*server_loads)
    plt.figure()
    plt.plot(time, loads)
    plt.title('Server load over time')
    plt.xlabel('time (hours)')
    plt.ylabel('load (# of connected devices)')
    plt.show()
