'''This version implements High Voltage to Low Voltage losses'''
import os
import pandas as pd
import datetime
import numpy as np

class StorageSimulations:

    def __init__(self, main):
        self.cwd = os.getcwd()
        self.general_input_data_path = self.cwd + "/data/"
        self.generation_input_data_path = self.general_input_data_path + "res_data/calculated/"
        self.demand_input_data_path = self.general_input_data_path + "demand/calculated/"
        self.output_path = self.general_input_data_path + 'results/'
        self.simulation_details = main.simulation_details
        
        self.storage_specifications = {}
        self.storage_technologies = main.simulation_details.loc['storage_technology']['value'].values
        for storage_technology in self.storage_technologies:
            self.storage_specifications[storage_technology] = pd.read_excel(self.general_input_data_path + storage_technology + '_characteristics.xlsx', index_col=0, header=0)
        
        # Prepare "simulation" and "output dataframes"
        self.simulation_frames = 8760 #hours in a year
        self.simulation_columns = ['battery_p_ch', 'battery_p_dis', 'battery_soc', 'battery_stored_energy', 'battery throughput energy (MWh)', 'battery_charge_state', 'phs_p_ch', 'phs_p_dis', 'phs_soc', 'phs_stored_energy', 'phs_charge_state', 'RES penetration', 'curtailment', 'energy shortage', 'modified demand', 'periods since battery state change']
        self.output_columns = ['maximization criterion', 'pv capacity (MW)', 'wind capacity (MW)', 'hydro capacity (MW)', 'battery_capacity (MWh)', 'phs_capacity (MWh)', 'battery_power (MW)', 'battery throughput energy (MWh)', 'degraded_battery_capacity (MWh)', 'Total Potential RES generation (TWh)', 'Total Demand (TWh)','curtailment (%)', 'curtailment (TWh)', 'curtailment with zero storage (%)', 'curtailment with zero storage (TWh)', 'max hourly curtailment (MWh)', 'RES penetration (%)', 'RES penetration (MWh)', 'RES penetration without storage (%)', 'annual missing energy (TWh)', 'annual missing energy without storage (TWh)', 'peak missing energy (MW)', 'peak missing energy without storage (MW)','max periods until state change']
        self.simulations_df = pd.DataFrame(np.nan, index=range(self.simulation_frames), columns=self.simulation_columns)
        return
    
    def convert_to_datetime(self, variable):
        variable.index = variable.index + ' ' + variable.iloc[:,0].values
        variable = variable.drop('hour', axis=1)
        variable.index = pd.to_datetime(variable.index, format='%Y-%m-%d %H:%M:%S')
        return variable
    
    def reset_simulations_df(self, res_generation, demand):
        self.simulations_df.iloc[:,:] = 0
        self.simulations_df.loc[:,'modified demand'] = demand.iloc[:,0]
        if 'hydro' in res_generation.keys():
            self.simulations_df.loc[:,'RES penetration'] = res_generation['hydro'].iloc[:,0]
        else:
            self.simulations_df.loc[:,'RES penetration'] = 0
        return
    
    def update_bess_specifications(self, storage_capacity):
        bess_pdis_max = storage_capacity/self.storage_specifications["battery"].loc['duration']['value'] #in MW
        bess_pch_max = storage_capacity*(self.storage_specifications["battery"].loc['charging rate (%)']['value']/100) #in MW
        bess_min_discharge_level = storage_capacity*((100-self.storage_specifications["battery"].loc['depth_of_discharge']['value'])/100)
        return bess_pch_max, bess_pdis_max, bess_min_discharge_level
    
    def update_phs_specifications(self, storage_capacity):
        phs_pmax_dis = storage_capacity/self.storage_specifications["phs"].loc['duration (h)']['value'] #in MW
        phs_min_discharge_level = storage_capacity*((100-self.storage_specifications["phs"].loc['depth_of_discharge (%)']['value'])/100)
        return phs_pmax_dis, phs_min_discharge_level
    
    def hourly_energy_simulations(self, sampled_res_capacities, res_combination, res_generation, aggregated_res_generation_df, demand, storage_capacity, bess_pch_max, bess_pdis_max, bess_min_discharge_level, phs_pmax_dis, phs_min_discharge_level):
        # calendar year simulations
        date = aggregated_res_generation_df.index[0]
        end = aggregated_res_generation_df.index[-1]
        hour_delta = datetime.timedelta(hours=1)
        while date <= end:
            if date.month==2 and date.day==29:
                self.simulations_df.loc[date, 'RES penetration'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'RES penetration']
                self.simulations_df.loc[date, 'battery_p_ch'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery_p_ch']
                self.simulations_df.loc[date, 'battery_p_dis'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery_p_dis']
                self.simulations_df.loc[date, 'battery_stored_energy'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery_stored_energy']
                self.simulations_df.loc[date, 'battery throughput energy (MWh)'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery throughput energy (MWh)']
                self.simulations_df.loc[date, 'modified demand'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'modified demand']
                self.simulations_df.loc[date, 'curtailment'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'curtailment']
                self.simulations_df.loc[date, 'energy shortage'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'energy shortage']
                self.simulations_df.loc[date, 'battery_soc'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery_soc']
                self.simulations_df.loc[date, 'battery_charge_state'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'battery_charge_state']
                self.simulations_df.loc[date, 'periods since battery state change'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'periods since battery state change']
                self.simulations_df.loc[date, 'phs_p_ch'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'periods since battery state change']
                self.simulations_df.loc[date, 'phs_p_dis'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'phs_p_dis']
                self.simulations_df.loc[date, 'phs_stored_energy'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'phs_stored_energy']
                self.simulations_df.loc[date, 'phs_charge_state'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'phs_charge_state']
                self.simulations_df.loc[date, 'phs_soc'] = self.simulations_df.loc[date - datetime.timedelta(hours=24), 'phs_soc']
                date += hour_delta
                continue
            ''' Εάν υπάρχει περιορισμός ταυτοχρονισμού όπως στο ΑΠΟΛΛΩΝ'''
            if aggregated_res_generation_df.loc[date]['res_generation'] > (self.simulation_details.loc['net_billing_percentage (%)']['value']/100) * sampled_res_capacities.loc[res_combination].sum():
                eligible_res_generation = ((self.simulation_details.loc['net_billing_percentage (%)']['value']/100) * sampled_res_capacities.loc[res_combination].sum())*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
                energy_to_be_stored = aggregated_res_generation_df.loc[date]['res_generation'] - eligible_res_generation/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
            else:
                eligible_res_generation = aggregated_res_generation_df.loc[date]['res_generation']*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
                energy_to_be_stored = 0
            ''' Εάν υπάρχει περιορισμός ταυτοχρονισμού όπως στο ΑΠΟΛΛΩΝ'''
            
            if eligible_res_generation >= demand.loc[date]['demand']:
                # batteries first
                self.simulations_df.loc[date, 'RES penetration'] += demand.loc[date]['demand']
                energy_to_be_stored += (eligible_res_generation - demand.loc[date]['demand'])/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
                if date == aggregated_res_generation_df.index[0]:
                    remaining_capacity = storage_capacity - bess_min_discharge_level
                    remaining_stored_energy = 0
                else:
                    remaining_capacity = storage_capacity - self.simulations_df.loc[date - hour_delta]['battery_soc']
                    remaining_stored_energy = self.simulations_df.loc[date - hour_delta]['battery_soc'] - bess_min_discharge_level
                self.simulations_df.loc[date, 'battery_p_ch'] = min(bess_pch_max, remaining_capacity)
                self.simulations_df.loc[date, 'battery_p_dis'] = min(bess_pdis_max, remaining_stored_energy*(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100))
                self.simulations_df.loc[date, 'battery_stored_energy'] = min(energy_to_be_stored, remaining_capacity, self.simulations_df.loc[date, 'battery_p_ch'])
                self.simulations_df.loc[date, 'battery throughput energy (MWh)'] = abs(self.simulations_df.loc[date, 'battery_stored_energy'])
                self.simulations_df.loc[date, 'modified demand'] += self.simulations_df.loc[date, 'battery_stored_energy']
                self.simulations_df.loc[date, 'curtailment'] = energy_to_be_stored - self.simulations_df.loc[date, 'battery_stored_energy']
                if date == aggregated_res_generation_df.index[0]:
                    self.simulations_df.loc[date, 'battery_soc'] = bess_min_discharge_level + self.simulations_df.loc[date]['battery_stored_energy']
                else:
                    self.simulations_df.loc[date, 'battery_soc'] = self.simulations_df.loc[date - hour_delta, 'battery_soc'] + self.simulations_df.loc[date]['battery_stored_energy']
                self.simulations_df.loc[date, 'battery_charge_state'] = 'Charging!'
                
                if (date-hour_delta) in self.simulations_df.index:
                    if 'Charging!' in self.simulations_df.loc[date - hour_delta, 'battery_charge_state'] and self.simulations_df.loc[date, 'battery_stored_energy']>0:
                        self.simulations_df.loc[date, 'periods since battery state change'] = self.simulations_df.loc[date - hour_delta, 'periods since battery state change'] + 1
                    else:
                        self.simulations_df.loc[date, 'periods since battery state change'] = 1
                else:
                    self.simulations_df.loc[date, 'periods since battery state change'] = 1
                
                #then phs
                if date == aggregated_res_generation_df.index[0]:
                    phs_remaining_capacity = self.storage_specifications["phs"].loc['capacity (MWh)']['value'] - phs_min_discharge_level
                    phs_remaining_stored_energy = 0
                else:
                    phs_remaining_capacity = self.storage_specifications["phs"].loc['capacity (MWh)']['value'] - self.simulations_df.loc[date - hour_delta]['phs_soc']
                    phs_remaining_stored_energy = self.simulations_df.loc[date - hour_delta]['phs_soc'] - phs_min_discharge_level
                self.simulations_df.loc[date, 'phs_p_ch'] = min(self.storage_specifications["phs"].loc['pmax_charge (MW)']['value'], phs_remaining_capacity)
                self.simulations_df.loc[date, 'phs_p_dis'] = min(phs_pmax_dis, phs_remaining_stored_energy*(self.storage_specifications["phs"].loc['round_trip_efficiency (%)']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100))
                if self.simulations_df.loc[date, 'curtailment'] > 0 and "phs" in self.storage_technologies:
                    self.simulations_df.loc[date, 'phs_stored_energy'] = min(self.simulations_df.loc[date, 'curtailment'], phs_remaining_capacity, self.simulations_df.loc[date, 'phs_p_ch'])
                    self.simulations_df.loc[date, 'modified demand'] += self.simulations_df.loc[date, 'phs_stored_energy']
                    self.simulations_df.loc[date, 'curtailment'] -= self.simulations_df.loc[date, 'phs_stored_energy']
                if date == aggregated_res_generation_df.index[0]:
                    self.simulations_df.loc[date, 'phs_soc'] = phs_min_discharge_level + self.simulations_df.loc[date]['phs_stored_energy']
                else:
                    self.simulations_df.loc[date, 'phs_soc'] = self.simulations_df.loc[date - hour_delta, 'phs_soc'] + self.simulations_df.loc[date]['phs_stored_energy']
                    
            
            elif eligible_res_generation < demand.loc[date]['demand']:
                # batteries first
                self.simulations_df.loc[date, 'RES penetration'] += eligible_res_generation
                missing_energy =  demand.loc[date]['demand'] - eligible_res_generation
                if date == aggregated_res_generation_df.index[0]:
                    remaining_capacity = storage_capacity - bess_min_discharge_level
                    remaining_stored_energy = 0
                else:
                    remaining_capacity = storage_capacity - self.simulations_df.loc[date - hour_delta]['battery_soc']
                    remaining_stored_energy = self.simulations_df.loc[date - hour_delta]['battery_soc'] - bess_min_discharge_level
                self.simulations_df.loc[date, 'battery_p_ch'] = min(bess_pch_max, remaining_capacity)
                self.simulations_df.loc[date, 'battery_p_dis'] = min(bess_pdis_max, remaining_stored_energy*(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100))
                self.simulations_df.loc[date, 'battery_stored_energy'] = -(min(missing_energy, remaining_stored_energy*(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100), self.simulations_df.loc[date, 'battery_p_dis']))
                self.simulations_df.loc[date, 'battery throughput energy (MWh)'] = abs((self.simulations_df.loc[date]['battery_stored_energy']/(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100))/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)) # 'stored_energy' is negative so it is added)
                self.simulations_df.loc[date, 'energy shortage'] = missing_energy + self.simulations_df.loc[date, 'battery_stored_energy'] # 'stored_energy' is negative so it is added
                self.simulations_df.loc[date, 'RES penetration'] += abs(self.simulations_df.loc[date, 'battery_stored_energy'])
                self.simulations_df.loc[date, 'modified demand'] -= abs(self.simulations_df.loc[date, 'battery_stored_energy'])
                if date == aggregated_res_generation_df.index[0]:
                    self.simulations_df.loc[date, 'battery_soc'] = bess_min_discharge_level + (self.simulations_df.loc[date]['battery_stored_energy']/(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100))/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100) # 'stored_energy' is negative so it is added
                else:
                    self.simulations_df.loc[date, 'battery_soc'] = self.simulations_df.loc[date - hour_delta, 'battery_soc'] + (self.simulations_df.loc[date]['battery_stored_energy']/(self.storage_specifications["battery"].loc['round_trip_efficiency']['value']/100))/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100) # 'stored_energy' is negative so it is added
                
                self.simulations_df.loc[date, 'battery_charge_state'] = 'Discharging!'
                if (date-hour_delta) in self.simulations_df.index:
                    if 'Discharging!' in self.simulations_df.loc[date - hour_delta, 'battery_charge_state'] and self.simulations_df.loc[date, 'battery_stored_energy']<0:
                        self.simulations_df.loc[date, 'periods since battery state change'] = self.simulations_df.loc[date - hour_delta, 'periods since battery state change'] + 1
                    else:
                        self.simulations_df.loc[date, 'periods since battery state change'] = 1
                else:
                    self.simulations_df.loc[date, 'periods since battery state change'] = 1
                
                '''Αποθήκευση ενέργειας που δεν μπορεί να ταυτοχρονιστεί'''
                remaining_capacity = storage_capacity - self.simulations_df.loc[date, 'battery_soc']
                remaining_stored_energy = self.simulations_df.loc[date, 'battery_soc'] - bess_min_discharge_level
                self.simulations_df.loc[date, 'battery_stored_energy'] = min(energy_to_be_stored, remaining_capacity, self.simulations_df.loc[date, 'battery_p_ch'])
                self.simulations_df.loc[date, 'modified demand'] += self.simulations_df.loc[date, 'battery_stored_energy']
                self.simulations_df.loc[date, 'curtailment'] = energy_to_be_stored - self.simulations_df.loc[date, 'battery_stored_energy']
                self.simulations_df.loc[date, 'battery_soc'] = self.simulations_df.loc[date, 'battery_soc'] + self.simulations_df.loc[date]['battery_stored_energy']
                '''Αποθήκευση ενέργειας που δεν μπορεί να ταυτοχρονιστεί'''
                
                #then phs
                if date == aggregated_res_generation_df.index[0]:
                    phs_remaining_capacity = self.storage_specifications["phs"].loc['capacity (MWh)']['value'] - phs_min_discharge_level
                    phs_remaining_stored_energy = 0
                else:
                    phs_remaining_capacity = self.storage_specifications["phs"].loc['capacity (MWh)']['value'] - self.simulations_df.loc[date - hour_delta]['phs_soc']
                    phs_remaining_stored_energy = self.simulations_df.loc[date - hour_delta]['phs_soc'] - phs_min_discharge_level
                self.simulations_df.loc[date, 'phs_p_ch'] = min(self.storage_specifications["phs"].loc['pmax_charge (MW)']['value'], phs_remaining_capacity)
                self.simulations_df.loc[date, 'phs_p_dis'] = min(phs_pmax_dis, phs_remaining_stored_energy*(self.storage_specifications["phs"].loc['round_trip_efficiency (%)']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100))
                if self.simulations_df.loc[date, 'energy shortage'] > 0 and "phs" in self.storage_technologies:
                    self.simulations_df.loc[date, 'phs_stored_energy'] = -min(self.simulations_df.loc[date, 'energy shortage'], phs_remaining_stored_energy*(self.storage_specifications["phs"].loc['round_trip_efficiency (%)']['value']/100)*(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100), self.simulations_df.loc[date, 'phs_p_dis'])
                    self.simulations_df.loc[date, 'modified demand'] -= abs(self.simulations_df.loc[date, 'phs_stored_energy'])
                    self.simulations_df.loc[date, 'energy shortage'] += self.simulations_df.loc[date, 'phs_stored_energy'] # 'phs_stored_energy' is negative so it is added
                    self.simulations_df.loc[date, 'RES penetration'] += abs(self.simulations_df.loc[date, 'phs_stored_energy'])
                if date == aggregated_res_generation_df.index[0]:
                    self.simulations_df.loc[date, 'phs_soc'] = phs_min_discharge_level + (self.simulations_df.loc[date]['phs_stored_energy']/(self.storage_specifications["phs"].loc['round_trip_efficiency (%)']['value']/100))/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
                else:
                    self.simulations_df.loc[date, 'phs_soc'] = self.simulations_df.loc[date - hour_delta, 'phs_soc'] + (self.simulations_df.loc[date]['phs_stored_energy']/(self.storage_specifications["phs"].loc['round_trip_efficiency (%)']['value']/100))/(1-self.simulation_details.loc['hv_to_lv_losses (%)']['value']/100)
            # else:
            #     self.simulations_df.loc[date, 'battery_charge_state'] = 'Idle...'
            #     self.simulations_df.loc[date, 'periods since battery state change'] = 0
            date += hour_delta
        self.simulations_df = self.simulations_df[~((self.simulations_df.index.month == 2) & (self.simulations_df.index.day == 29))]
        return
    
    def update_bess_capacity_for_self_consumption_maximization (self, storage_capacity, variable_tracking):
        print ('          Updating storage capacity with criterion being RES self-consumption maximization')
        storage_capacity += ((variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity'] - variable_tracking.loc[len(variable_tracking)-2, 'storage_capacity'])/(variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'] - variable_tracking.loc[len(variable_tracking)-2, 'res_penetration (%)']))*(self.simulation_details.loc['target_threshold (%)']['value'] - variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'])
        if storage_capacity < 0:
            import ipdb; ipdb.set_trace()
        return storage_capacity
    
    def update_bess_capacity_for_curtailment_minimization (self, storage_capacity, variable_tracking):
        print ('          Updating storage capacity with criterion being curtailment minimization')
        storage_capacity += ((variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity'] - variable_tracking.loc[len(variable_tracking)-2, 'storage_capacity'])/(variable_tracking.loc[len(variable_tracking)-2, 'curtailment (%)'] - variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']))*(variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)'] - self.simulation_details.loc['target_threshold (%)']['value'])
        if storage_capacity < 0:
            import ipdb; ipdb.set_trace()
        return storage_capacity

    
    def maximize_self_consumption(self, res_combination, res_generation, aggregated_res_generation_df, demand, sampled_res_capacities):
        # initialization of simulation values...
        storage_capacity = 0.0 #in MWh
        curtailment = 100.0 # initialization at maximum % value
        RES_penetration = 0.0 # initialization at minimum penetration

        # tracking variables which are used to end iterations and save the right results
        variable_tracking = pd.DataFrame(columns=['storage_capacity', 'power_capacity', 'curtailment (%)', 'curtailment_TWh', 'max_hourly_curtailment', 'res_penetration (%)', \
                                                  'res_penetration (MWh)', 'annual_missing_energy', 'peak_missing_energy', 'max_periods_until_state_change'])
        
        # Iterations to find required storage capacity in each year
        while RES_penetration < self.simulation_details.loc['target_threshold (%)']['value'] and curtailment > 0:
            self.reset_simulations_df(res_generation, demand)
            # update BESS characteristics
            print("     Trying with storage capacity: " + str(storage_capacity) + "MWh")
            bess_pch_max, bess_pdis_max, bess_min_discharge_level = self.update_bess_specifications(storage_capacity)
            phs_pmax_dis, phs_min_discharge_level = self.update_phs_specifications(self.storage_specifications["phs"].loc['capacity (MWh)']['value'])
            self.hourly_energy_simulations(sampled_res_capacities, res_combination, res_generation, aggregated_res_generation_df, demand, storage_capacity, bess_pch_max, bess_pdis_max, bess_min_discharge_level, phs_pmax_dis, phs_min_discharge_level)
            # update tracking variables with the results of the current storage capacity
            variable_tracking.loc[len(variable_tracking), 'storage_capacity'] = storage_capacity
            variable_tracking.loc[len(variable_tracking)-1, 'power_capacity'] = bess_pdis_max
            variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)'] = (self.simulations_df.loc[:,'curtailment'].sum()/aggregated_res_generation_df.loc[:,'res_generation'].sum())*100
            variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh'] = self.simulations_df.loc[:,'curtailment'].sum()/1000000
            variable_tracking.loc[len(variable_tracking)-1, 'max_hourly_curtailment'] = self.simulations_df.loc[:,'curtailment'].max()
            variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'] = (self.simulations_df.loc[:,'RES penetration'].sum()/demand.loc[:]['demand'].sum().values[0])*100
            variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (MWh)'] = self.simulations_df.loc[:,'RES penetration'].sum()
            variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy'] = self.simulations_df.loc[:,'energy shortage'].sum()/1000000 #in TWh
            variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy'] = self.simulations_df.loc[:,'energy shortage'].max()
            variable_tracking.loc[len(variable_tracking)-1, 'max_periods_until_state_change'] = self.simulations_df.loc[:,'periods since battery state change'].max()
            
            print ('          Power capacity: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'power_capacity']) + str(' MW'))
            print ('          Curtailment: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']) + str('%'))
            print ('          RES penetration: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']) + str('%'))
            
            curtailment = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
            RES_penetration = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
            
            # output values without storage
            if storage_capacity == 0.0:  
                self.output_df.loc[res_combination, 'annual missing energy without storage (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy']
                self.output_df.loc[res_combination, 'peak missing energy without storage (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy']
                self.output_df.loc[res_combination, 'curtailment with zero storage (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
                self.output_df.loc[res_combination, 'curtailment with zero storage (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh']
                self.output_df.loc[res_combination, 'RES penetration without storage (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
            
            
            if variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'] < self.simulation_details.loc['target_threshold (%)']['value'] and \
                abs(self.simulation_details.loc['target_threshold (%)']['value'] - variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']) > self.simulation_details.loc['target_offset (%)']['value']:
                    if len(variable_tracking)>1:
                        if (variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'] - variable_tracking.loc[len(variable_tracking)-2, 'res_penetration (%)']) != 0.0:
                            storage_capacity = self.update_bess_capacity_for_self_consumption_maximization (storage_capacity, variable_tracking)
                        else:
                            variable_tracking = variable_tracking.drop(variable_tracking.index[-1])
                            print ('          RES penetration did not change with capacity change. Exiting loop...')
                            break
                    else:
                        storage_capacity += 0.001
            else:
                print ('          Simulations reached required target accuracy. Exiting loop...')
                break
            
        # output values with storage
        print ("     Found required capacity for res combination " +str(res_combination) + ": " + str(variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity']) + "MWh\n")
        self.output_df.loc[res_combination, 'battery_capacity (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity']
        self.output_df.loc[res_combination, 'battery_power (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'power_capacity']
        if 'phs' in self.storage_technologies:
            self.output_df.loc[res_combination, 'phs_capacity (MWh)'] = self.storage_specifications['phs'].loc['capacity (MWh)']['value']
        self.output_df.loc[res_combination, 'curtailment (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
        self.output_df.loc[res_combination, 'curtailment (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh']
        self.output_df.loc[res_combination, 'max hourly curtailment (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'max_hourly_curtailment']
        self.output_df.loc[res_combination, 'RES penetration (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
        self.output_df.loc[res_combination, 'RES penetration (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (MWh)']
        self.output_df.loc[res_combination, 'annual missing energy (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy']
        self.output_df.loc[res_combination, 'peak missing energy (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy']
        self.output_df.loc[res_combination, 'max periods until state change'] = variable_tracking.loc[len(variable_tracking)-1, 'max_periods_until_state_change']
        
        self.simulations_df.to_excel(self.output_path + 'simulations - res combination ' + str(res_combination) + '.xlsx')
        
        return
    
    def minimize_curtailment (self, res_combination, res_generation, aggregated_res_generation_df, demand, sampled_res_capacities):
        # initialization of simulation values...
        storage_capacity = 0.0 #in MWh
        curtailment = 100.0 # initialization at maximum % value
        RES_penetration = 0.0 # initialization at minimum penetration

        # tracking variables which are used to end iterations and save the right results
        variable_tracking = pd.DataFrame(columns=['storage_capacity', 'power_capacity', 'curtailment (%)', 'curtailment_TWh', 'max_hourly_curtailment', 'res_penetration (%)', \
                                                  'res_penetration (MWh)', 'annual_missing_energy', 'peak_missing_energy', 'max_periods_until_state_change'])
        
        # Iterations to find required storage capacity in each year
        while curtailment > self.simulation_details.loc['target_threshold (%)']['value'] and RES_penetration < 100:
            self.reset_simulations_df(res_generation, demand)
            # update BESS characteristics
            print("     Trying with storage capacity: " + str(storage_capacity) + "MWh")
            bess_pch_max, bess_pdis_max, bess_min_discharge_level = self.update_bess_specifications(storage_capacity)
            phs_pmax_dis, phs_min_discharge_level = self.update_phs_specifications(self.storage_specifications["phs"].loc['capacity (MWh)']['value'])
            self.hourly_energy_simulations(sampled_res_capacities, res_combination, res_generation, aggregated_res_generation_df, demand, storage_capacity, bess_pch_max, bess_pdis_max, bess_min_discharge_level, phs_pmax_dis, phs_min_discharge_level)
        
            # update tracking variables with the results of the current storage capacity
            variable_tracking.loc[len(variable_tracking), 'storage_capacity'] = storage_capacity
            variable_tracking.loc[len(variable_tracking)-1, 'power_capacity'] = bess_pdis_max
            variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)'] = (self.simulations_df.loc[:,'curtailment'].sum()/aggregated_res_generation_df.loc[:,'res_generation'].sum())*100
            variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh'] = self.simulations_df.loc[:,'curtailment'].sum()/1000000
            variable_tracking.loc[len(variable_tracking)-1, 'max_hourly_curtailment'] = self.simulations_df.loc[:,'curtailment'].max()
            variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)'] = (self.simulations_df.loc[:,'RES penetration'].sum()/demand.loc[:]['demand'].sum().values[0])*100
            variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (MWh)'] = self.simulations_df.loc[:,'RES penetration'].sum()
            variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy'] = self.simulations_df.loc[:,'energy shortage'].sum()/1000000 #in TWh
            variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy'] = self.simulations_df.loc[:,'energy shortage'].max()
            variable_tracking.loc[len(variable_tracking)-1, 'max_periods_until_state_change'] = self.simulations_df.loc[:,'periods since battery state change'].max()
            
            print ('          Power capacity: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'power_capacity']) + str(' MW'))
            print ('          Curtailment: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']) + str('%'))
            print ('          RES penetration: ' + str(variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']) + str('%'))
            
            curtailment = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
            RES_penetration = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
            
            # output values without storage
            if storage_capacity == 0.0:  
                self.output_df.loc[res_combination, 'annual missing energy without storage (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy']
                self.output_df.loc[res_combination, 'peak missing energy without storage (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy']
                self.output_df.loc[res_combination, 'curtailment with zero storage (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
                self.output_df.loc[res_combination, 'curtailment with zero storage (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh']
                self.output_df.loc[res_combination, 'RES penetration without storage (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
            
            
            if variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)'] > self.simulation_details.loc['target_threshold (%)']['value'] and \
                abs(self.simulation_details.loc['target_threshold (%)']['value'] - variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']) > self.simulation_details.loc['target_offset (%)']['value']:
                    if len(variable_tracking)>1:
                        if (variable_tracking.loc[len(variable_tracking)-2, 'curtailment (%)'] - variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']) != 0.0:
                            storage_capacity = self.update_bess_capacity_for_curtailment_minimization (storage_capacity, variable_tracking)
                        else:
                            variable_tracking = variable_tracking.drop(variable_tracking.index[-1])
                            print ('          Curtailment did not change with capacity change. Exiting loop...')
                            break
                    else:
                        storage_capacity += 0.001
            else:
                print ('          Simulations reached required target accuracy. Exiting loop...')
                break
            
        # output values with storage
        print ("     Found required capacity for res combination " +str(res_combination) + ": " + str(variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity']) + "MWh\n")
        self.output_df.loc[res_combination, 'battery_capacity (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'storage_capacity']
        self.output_df.loc[res_combination, 'battery_power (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'power_capacity']
        if 'phs' in self.storage_technologies:
            self.output_df.loc[res_combination, 'phs_capacity (MWh)'] = self.storage_specifications['phs'].loc['capacity (MWh)']['value']
        self.output_df.loc[res_combination, 'curtailment (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment (%)']
        self.output_df.loc[res_combination, 'curtailment (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'curtailment_TWh']
        self.output_df.loc[res_combination, 'max hourly curtailment (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'max_hourly_curtailment']
        self.output_df.loc[res_combination, 'RES penetration (%)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (%)']
        self.output_df.loc[res_combination, 'RES penetration (MWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'res_penetration (MWh)']
        self.output_df.loc[res_combination, 'annual missing energy (TWh)'] = variable_tracking.loc[len(variable_tracking)-1, 'annual_missing_energy']
        self.output_df.loc[res_combination, 'peak missing energy (MW)'] = variable_tracking.loc[len(variable_tracking)-1, 'peak_missing_energy']
        self.output_df.loc[res_combination, 'max periods until state change'] = variable_tracking.loc[len(variable_tracking)-1, 'max_periods_until_state_change']
        return
    
    def calculate_battery_capacity(self, year, demand, sampled_res_capacities):
        self.simulations_df.index = demand.index
        self.output_df = pd.DataFrame(None, columns=self.output_columns)
        for res_combination in sampled_res_capacities.index:
            res_generation = {}
            for technology in sampled_res_capacities.columns:    
                input_file_name = technology +' '+ str(round(sampled_res_capacities.loc[res_combination][technology],5))+'MW_generation_' + str(year) + '.csv'
                res_generation[technology] = pd.read_csv(self.generation_input_data_path + input_file_name, index_col=0, header = 0)
                res_generation[technology] = self.convert_to_datetime(res_generation[technology])
            if 'hydro' in res_generation.keys():
                demand.iloc[:,0] -= res_generation['hydro'].iloc[:,0]
            '''Still need to develop:
                    1. Arbitrage
            '''
            aggregated_res_generation_df = pd.DataFrame(0, index=demand.index, columns=['res_generation'])
            for technology in res_generation.keys():    
                aggregated_res_generation_df.iloc[:,0] += res_generation[technology].iloc[:,0]
            if self.simulation_details.loc['target']['value'] == 'demand':
                # import ipdb;ipdb.set_trace()
                if aggregated_res_generation_df.loc[:]['res_generation'].sum() >= (demand.loc[:]['demand'].sum().values[0]*(self.simulation_details.loc['target_threshold (%)']['value']/100)):
                    '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''
                    '''Εδ΄ώ  πρώτα  ελέγχω αν η παραγωγή επαρκεί για να καλυψει την ζήτηση'''
                    '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''
                    print ('Finding required storage capacity to maximize RES consumption for res capacity scenario ' + str(res_combination) + ' in year ' + str(year))
                    self.output_df.loc[res_combination, 'maximization criterion'] =  self.simulation_details.loc['target']['value']
                    self.output_df.loc[res_combination, 'Total Potential RES generation (TWh)'] =  aggregated_res_generation_df.iloc[:,0].sum()/1000000
                    self.output_df.loc[res_combination, 'Total Demand (TWh)'] = demand.loc[:]['demand'].sum().values[0]/1000000
                    if 'solar' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'pv capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['solar']
                    if 'wind' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'wind capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['wind']
                    if 'hydro' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'hydro capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['hydro']
                    
                    self.maximize_self_consumption(res_combination, res_generation, aggregated_res_generation_df, demand, sampled_res_capacities)
                else:
                    print('RES capacity of scenario ' + str(res_combination) + ' in year ' + str(year) +' is not enough to cover the required demand.')
            
            elif self.simulation_details.loc['target']['value'] == 'curtailment':
                if ((aggregated_res_generation_df.loc[:]['res_generation'].sum()-demand.loc[:]['demand'].sum().values[0])/aggregated_res_generation_df.loc[:]['res_generation'].sum())*100 <= self.simulation_details.loc['target_threshold (%)']['value']:
                    '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''
                    '''Εδ΄ώ  πρώτα  ελέγχω αν η παραγωγή είναι υπερβολική για να φτάσουμε τα επιθυμητά επίπεδα curtailment ακόμη και αν καλυφθεί όλη η ζήτηση'''
                    '''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''
                    print ('Finding required storage capacity to minimize curtailment for res capacity scenario ' + str(res_combination) + ' in year ' + str(year))
                    self.output_df.loc[res_combination, 'maximization criterion'] =  self.simulation_details.loc['target']['value']
                    self.output_df.loc[res_combination, 'Total Potential RES generation (TWh)'] =  aggregated_res_generation_df.iloc[:,0].sum()/1000000
                    self.output_df.loc[res_combination, 'Total Demand (TWh)'] = demand.loc[:]['demand'].sum().values[0]/1000000
                    if 'solar' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'pv capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['solar']
                    if 'wind' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'wind capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['wind']
                    if 'hydro' in sampled_res_capacities.columns:
                        self.output_df.loc[res_combination, 'hydro capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['hydro']
                    
                    self.minimize_curtailment(res_combination, res_generation, aggregated_res_generation_df, demand, sampled_res_capacities)
                else:
                    print('RES capacity of scenario ' + str(res_combination) + ' in year ' + str(year) +' is too high to reach the required curtailment levels.')
             
        self.output_df.to_excel(self.output_path + 'res and storage sizing - objective ' + self.simulation_details.loc['target']['value'] +' - '+ str(year) + '.xlsx')
        return

    def get_battery_capacity(self):
        storage_capacities = pd.read_excel(self.general_input_data_path + "(dispatch) storage capacity" +".xlsx", header=0, index_col=0)
        return storage_capacities
    
    def simulate_res_and_storage_dispatch(self, year, demand, sampled_res_capacities, storage_capacities):
        self.simulations_df.index = demand.index
        self.output_df = pd.DataFrame(None, columns=self.output_columns)
        if 'year' in sampled_res_capacities.columns:
            sampled_res_capacities = sampled_res_capacities.drop('year', axis=1)
        for res_combination in sampled_res_capacities.index:
            res_generation = {}
            for technology in sampled_res_capacities.columns:    
                input_file_name = technology +' '+ str(round(sampled_res_capacities.loc[res_combination][technology],5))+'MW_generation_' + str(year) + '.csv'
                res_generation[technology] = pd.read_csv(self.generation_input_data_path + input_file_name, index_col=0, header = 0)
                res_generation[technology] = self.convert_to_datetime(res_generation[technology])
            if 'hydro' in res_generation.keys():
                demand.iloc[:,0] -= res_generation['hydro'].iloc[:,0]
            aggregated_res_generation_df = pd.DataFrame(0, index=demand.index, columns=['res_generation'])
            for technology in res_generation.keys():    
                aggregated_res_generation_df.iloc[:,0] += res_generation[technology].iloc[:,0]
            
            storage_capacity = storage_capacities.loc[res_combination, "battery_capacity (MWh)"]
            bess_pch_max, bess_pdis_max, bess_min_discharge_level = self.update_bess_specifications(storage_capacity)
            phs_pmax_dis, phs_min_discharge_level = self.update_phs_specifications(self.storage_specifications["phs"].loc['capacity (MWh)']['value'])
            
            print ('Simulating RES and storage dispatch for res capacity scenario ' + str(res_combination) + ' in year ' + str(year))
            self.reset_simulations_df(res_generation, demand)
            self.hourly_energy_simulations(sampled_res_capacities, res_combination, res_generation, aggregated_res_generation_df, demand, storage_capacity, bess_pch_max, bess_pdis_max, bess_min_discharge_level, phs_pmax_dis, phs_min_discharge_level)
            
            
            self.output_df.loc[res_combination, 'maximization criterion'] =  None
            self.output_df.loc[res_combination, 'Total Potential RES generation (TWh)'] =  aggregated_res_generation_df.iloc[:,0].sum()/1000000
            self.output_df.loc[res_combination, 'Total Demand (TWh)'] = demand.loc[:]['demand'].sum().values[0]/1000000
            if 'solar' in sampled_res_capacities.columns:
                self.output_df.loc[res_combination, 'pv capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['solar']
            if 'wind' in sampled_res_capacities.columns:
                self.output_df.loc[res_combination, 'wind capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['wind']
            if 'hydro' in sampled_res_capacities.columns:
                self.output_df.loc[res_combination, 'hydro capacity (MW)'] =  sampled_res_capacities.loc[res_combination]['hydro']
            
            self.output_df.loc[res_combination, 'annual missing energy without storage (TWh)'] = None
            self.output_df.loc[res_combination, 'peak missing energy without storage (MW)'] = None
            self.output_df.loc[res_combination, 'curtailment with zero storage (%)'] = None
            self.output_df.loc[res_combination, 'curtailment with zero storage (TWh)'] = None
            self.output_df.loc[res_combination, 'RES penetration without storage (%)'] = None
        
            self.output_df.loc[res_combination, 'battery_capacity (MWh)'] = storage_capacity
            self.output_df.loc[res_combination, 'battery_power (MW)'] = bess_pdis_max
            self.output_df.loc[res_combination, 'battery throughput energy (MWh)'] = self.simulations_df.loc[:, 'battery throughput energy (MWh)'].sum()
            self.output_df.loc[res_combination, 'battery_cycles'] = self.output_df.loc[res_combination, 'battery throughput energy (MWh)']/(self.output_df.loc[res_combination, 'battery_capacity (MWh)']*2) # pollaplasiazw me 2 epeidh enas kuklos antistoixei se fortish kai ekfortish. Ara 2 fores to battery capacity mou kanoyn enan kuklo
            self.output_df.loc[res_combination, 'degraded_battery_capacity (MWh)'] = self.output_df.loc[res_combination, 'battery_capacity (MWh)'] * ((100 - self.output_df.loc[res_combination, 'battery_cycles']*self.storage_specifications["battery"].loc['degradation_rate_per_cycle (%)']['value'])/100)
            if 'phs' in self.storage_technologies:
                self.output_df.loc[res_combination, 'phs_capacity (MWh)'] = self.storage_specifications['phs'].loc['capacity (MWh)']['value']
            self.output_df.loc[res_combination, 'curtailment (%)'] = (self.simulations_df.loc[:,'curtailment'].sum()/aggregated_res_generation_df.loc[:,'res_generation'].sum())*100
            self.output_df.loc[res_combination, 'curtailment (TWh)'] = self.simulations_df.loc[:,'curtailment'].sum()/1000000
            self.output_df.loc[res_combination, 'max hourly curtailment (MWh)'] = self.simulations_df.loc[:,'curtailment'].max()
            self.output_df.loc[res_combination, 'RES penetration (%)'] = (self.simulations_df.loc[:,'RES penetration'].sum()/demand.loc[:]['demand'].sum().values[0])*100
            self.output_df.loc[res_combination, 'annual missing energy (TWh)'] = self.simulations_df.loc[:,'energy shortage'].sum()/1000000 #in TWh
            self.output_df.loc[res_combination, 'peak missing energy (MW)'] = self.simulations_df.loc[:,'energy shortage'].max()
            self.output_df.loc[res_combination, 'max periods until state change'] = self.simulations_df.loc[:,'periods since battery state change'].max()
            
        self.output_df.to_excel(self.output_path + 'res and storage dispatch - objective ' + self.simulation_details.loc['target']['value'] +' - '+ str(year) + '.xlsx')
        return self.output_df.loc[res_combination, 'degraded_battery_capacity (MWh)']