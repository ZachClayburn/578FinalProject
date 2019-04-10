from typing import List

import matplotlib.pyplot as plt

import IFTTTModel.model


def view_wait_times(users: List[IFTTTModel.model.User]) -> None:
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

