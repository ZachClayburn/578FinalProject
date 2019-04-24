from typing import List

import IFTTTModel
import multiprocessing as mp
import logging
import traceback
import csv
import sys
import json
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Emailer:
    def __init__(self, credentials: dict):
        self.u_name = credentials['email']
        self.password = credentials['password']
        self.server: smtplib.SMTP = None

    def __enter__(self) -> 'Emailer':
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.u_name, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.quit()

    def send(self, to: str, message: str, subject: str = None):
        msg = self._build_message_string(to, message, subject)
        self.server.sendmail(self.u_name, to, msg)

    def _build_message_string(self,to: str, message: str, subject: str) -> str:
        msg = MIMEMultipart()
        msg['From'] = self.u_name
        msg['To'] = to
        msg['Subject'] = subject if subject else 'Message from Python'
        msg.attach(MIMEText(message, 'plain'))
        return msg.as_string()


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
        return ','.join(str(x) for x in self.__dict__.values())


def run(e: Experiment):
    try:
        sim = IFTTTModel.Simulation(
            num_users=e.num_users,
            mean_num_devices_per_user=e.devices_per_user,
            user_interaction_mean=e.daily_interaction,
            server_capacity=e.server_capacity,
            server_response_mean=e.server_response_time,
            signal_slowness=e.signal_slowness,
            num_servers=e.num_servers,
        )
        sim.run()
        e.max_wait, e.mean_wait = sim.get_max_and_mean_wait()

        return e
    except Exception as ex:
        print(f'{e.run_number} Failed!', file=sys.stderr)
        traceback.print_exc()


if __name__ == '__main__':

    # with open('out.csv', 'r', encoding='utf-8') as f:
    #     reader = csv.reader(f)
    #     header = next(reader)
    #     done_jobs: List[int] = []
    #     for row in reader:
    #         done_jobs.append(int(row[0]))

    with open("credentials.json") as f:
        email_dict = json.load(f)
    to_address = email_dict['send to']
    with Emailer(email_dict) as emailer:
        try:

            with open(sys.argv[1], encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                header = next(reader)
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
                    if experiment.run_number > 80:
                        experiments.append(experiment)
            num_jobs = len(experiments)

            with mp.Pool(processes=mp.cpu_count()//2, maxtasksperchild=1) as pool:
                # results = pool.imap(run, experiments)
                # print(f"{num_jobs} Jobs started!")
                with open('out.csv', 'a', encoding='utf-8') as f:
                    print(experiments[0])
                    r = run(experiments[0])
                    print(r)
                    print(r, file=f)
                    # print(header, file=f)
                    # for _ in range(num_jobs):
                        # res = results.next()
                        # print(res)
                        # print(res, file=f)
                        # f.flush()

            emailer.send(to_address, 'Process completed!', 'Success')
        except Exception as ex:
            emailer.send(to_address, 'Process failed!', 'Failure')
            print(ex, file=sys.stderr)


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
