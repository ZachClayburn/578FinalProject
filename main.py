import IFTTTModel

sim = IFTTTModel.Simulation()
sim.view_positions()
sim.run()
sim.view_wait_times()
sim.view_load_over_time()

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
