import IFTTTModel
import multiprocessing as mp
import csv
import sys
from dataclasses import dataclass
from pprint import pprint


@dataclass(repr=True)
class Experiment:
    run_number: int
    pattern: str
    num_users: int
    devices_per_user: int
    daily_interaction: int
    server_capacity: int
    server_response_time: float
    signal_slowness: float
    num_servers: int
    max_wait: float = -1
    mean_wait: float = -1

    def __str__(self):
        return f'{self.run_number}'


def run(e: Experiment):
    e.max_wait = 100
    return e


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        experiments = []
        for row in reader:
            experiment = Experiment(
                run_number=int(round(float(row[0]))),
                pattern=row[1],
                num_users=int(round(float(row[2]))),
                devices_per_user=int(round(float(row[3]))),
                daily_interaction=int(round(float(row[4]))),
                server_capacity=int(round(float(row[5]))),
                server_response_time=float(float(row[6])),
                signal_slowness=float(row[7]),
                num_servers=int(round(float(row[8])))
            )
            experiments.append(experiment)

    with mp.Pool(processes=4) as pool:
        res = pool.map(run, experiments)
    with open('out.csv', 'w', encoding='utf-8') as f:
        for item in res:
            print(item, file=f)

# sim = IFTTTModel.Simulation()
# sim.view_positions()
# sim.run()
# sim.view_wait_times()
# sim.view_load_over_time()

# # # This was just to test the custom PDF function
# from IFTTTModel.model import UserActionDistribution
# import numpy as np
# import matplotlib.pyplot as plt
# pdf = UserActionDistribution(a=0, b=24)
# t = np.linspace(start=0, stop=24)
# plt.plot(t, pdf.pdf(t))
# plt.show()
# for i in range(25):
#     print(i, pdf.pdf(i))
#
