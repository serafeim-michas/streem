import pandas as pd
import os
import datetime
from tqdm import tqdm
from demand_projections import Demand_Projections
from res_generation_projections import RES_Generation_Projections
from storage_v02 import StorageSimulations
from technoeconomic_calculations import TechnoeconomicCalculations

class Main:
    
    def __init__(self):
        '''Define in what mode should the model run'''
        # Options:
        #   1. res_and_storage_dispatch - DONE
        #   2. res_and_storage_sizing - DONE
        self.streem_mode = "res_and_storage_sizing"

        self.cwd = os.getcwd()
        self.input_data_path = self.cwd+'/data/'
        self.output_data_path = "/data/res_data/calculated/"
        self.simulation_years_file_name = 'simulation_years.xlsx'
        self.simulation_customization_file_name = 'simulation_customization.xlsx'
        
        self.simulation_years = pd.read_excel(self.input_data_path + self.simulation_years_file_name, header=0, index_col=None).loc[:]['simulation years'].tolist()
        self.simulation_details = self.get_simulation_details()
        return

    def get_simulation_details(self):
        simulation_details = pd.read_excel(self.input_data_path + self.simulation_customization_file_name, header=0, index_col=0)
        return simulation_details
    
    def get_capacity_samples(self, year):
        sampled_res_capacities = res_generation_projections.get_sampled_res_capacities(year)
        sampled_res_capacities.to_excel(self.input_data_path + "res_data/calculated/" + "sampled res capacities " + str(year) +".xlsx")
        return sampled_res_capacities
    

if __name__ == "__main__":
    main = Main()
    demand_projections = Demand_Projections() # On instance initiation calculates the statistics of historical demand
    res_generation_projections = RES_Generation_Projections(main) # On instance initiation calculates the statistics of historical generation per technology (solar, wind and hydro)
    storage = StorageSimulations(main) # On instance initiation creates the "simulations" and "output" dataframes
    technoeconomic_calculations = TechnoeconomicCalculations(main)
    print ('\nPre-processing completed succesfully!\n\n')
    if main.streem_mode == "res_and_storage_sizing":
        for year in main.simulation_years:
            print ("Starting simulations for year " + str(year))
            demand = demand_projections.calculate_demand(year) # projects demand timeseries for current simulated year
            demand = demand[~((demand.index.month == 2) & (demand.index.day == 29))]
            sampled_res_capacities = main.get_capacity_samples(year) # uses LHS to sample RES capacities for current simulated year
            res_generation_projections.calculate_res_generation_profile(year, sampled_res_capacities) # projects generation timeseries for each sampled RES capacity for the current simulated year
            storage.calculate_battery_capacity(year, demand, sampled_res_capacities)
            technoeconomic_calculations.calculate_eac(year)
    elif main.streem_mode == "res_and_storage_dispatch":
        sampled_res_capacities = pd.read_excel(main.input_data_path + "res_data/input/" + "(dispatch) sampled res capacities" + ".xlsx", header=0, index_col=0)
        storage_capacities = storage.get_battery_capacity()
        for year in main.simulation_years:
            print ("Starting simulations for year " + str(year))
            demand = demand_projections.calculate_demand(year) # projects demand timeseries for current simulated year
            demand = demand[~((demand.index.month == 2) & (demand.index.day == 29))]
            yearly_sampled_res_capacities = sampled_res_capacities.loc[sampled_res_capacities['year']==year]
            yearly_storage_capacity = storage_capacities.loc[storage_capacities['year']==year]
            res_generation_projections.calculate_res_generation_profile(year, yearly_sampled_res_capacities) # projects generation timeseries for each sampled RES capacity for the current simulated year
            degraded_storage_capacity = storage.simulate_res_and_storage_dispatch(year, demand, yearly_sampled_res_capacities, yearly_storage_capacity)
            storage_capacities.loc[storage_capacities.shape[0],'year'] = year+1
            storage_capacities.loc[len(storage_capacities)-1, 'battery_capacity (MWh)'] = degraded_storage_capacity
    import ipdb;ipdb.set_trace()