from configparser import ConfigParser
import os
import pandas as pd

class StorageDispatch:

    def __init__(self):
        self.cwd = os.getcwd()
        config = ConfigParser()
        
        # read config file
        config.read('config.ini')
        self.demand = pd.read_csv(self.cwd+config['storage_dispatch']['demand_path'],index_col=0,header=0)
        self.solar_generation = pd.read_csv(self.cwd+config['storage_dispatch']['solar_generation_path'],index_col=0,header=0)
        self.w_onshore_generation = pd.read_csv(self.cwd+config['storage_dispatch']['wind_onshore_generation_path'],index_col=0,header=0)
        
        import ipdb;ipdb.set_trace()
        return

test = StorageDispatch()
