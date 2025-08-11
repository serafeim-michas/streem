import pandas as pd


class TechnoeconomicCalculations:

    def __init__(self, main):
        
        self.cwd = main.cwd
        self.input_data_path = main.input_data_path
        self.output_data_path = self.input_data_path + 'results/'
        self.technoeconomic_assumptions_file = "technoeconomic_assumptions.xlsx"
        
        self.simulation_details = main.simulation_details
        self.technoeconomic_assumptions = pd.read_excel(self.input_data_path + self.technoeconomic_assumptions_file, index_col=0, header=0)
        
        self.storage_specifications = {}
        self.storage_technologies = main.simulation_details.loc['storage_technology']['value'].values
        for storage_technology in self.storage_technologies:
            self.storage_specifications[storage_technology] = pd.read_excel(self.input_data_path + storage_technology + '_characteristics.xlsx', index_col=0, header=0)
        return
    
    
    def calculate_eac(self, year):
        
        output_file = pd.read_excel(self.output_data_path + 'res and storage sizing - objective ' + self.simulation_details.loc['target']['value'] +' - '+ str(year) + '.xlsx', index_col=0, header=0)
        
        pv_capital_recovery_factor = self.technoeconomic_assumptions.loc['interest']['value']/(1-(1+self.technoeconomic_assumptions.loc['interest']['value'])**(-self.technoeconomic_assumptions.loc['lifetime-pv (years)']['value']))
        wind_capital_recovery_factor = self.technoeconomic_assumptions.loc['interest']['value']/(1-(1+self.technoeconomic_assumptions.loc['interest']['value'])**(-self.technoeconomic_assumptions.loc['lifetime-wind (years)']['value']))
        hydro_capital_recovery_factor = self.technoeconomic_assumptions.loc['interest']['value']/(1-(1+self.technoeconomic_assumptions.loc['interest']['value'])**(-self.technoeconomic_assumptions.loc['lifetime-hydro (years)']['value']))
        bess_capital_recovery_factor = self.technoeconomic_assumptions.loc['interest']['value']/(1-(1+self.technoeconomic_assumptions.loc['interest']['value'])**(-self.technoeconomic_assumptions.loc['lifetime-bess (years)']['value']))
        
        for scenario in output_file.index:
            if not pd.isna(output_file.loc[scenario, 'pv capacity (MW)']):
                pv_capital_cost = output_file.loc[scenario]['pv capacity (MW)'] * self.technoeconomic_assumptions.loc['CC-pv (€/MW)']['value']
                pv_o_m_cost = output_file.loc[scenario]['pv capacity (MW)'] * self.technoeconomic_assumptions.loc['O&M-pv  (€/MW)']['value']
            else:
                pv_capital_cost = 0
                pv_o_m_cost = 0
            
            if not pd.isna(output_file.loc[scenario, 'wind capacity (MW)']):
                wind_capital_cost = output_file.loc[scenario]['wind capacity (MW)'] * self.technoeconomic_assumptions.loc['CC-wind (€/MW)']['value']
                wind_o_m_cost = output_file.loc[scenario]['wind capacity (MW)'] * self.technoeconomic_assumptions.loc['O&M-wind  (€/MW)']['value']
            else:
                wind_capital_cost = 0
                wind_o_m_cost = 0
               
            if not pd.isna(output_file.loc[scenario, 'hydro capacity (MW)']):
                hydro_capital_cost = output_file.loc[scenario]['hydro capacity (MW)'] * self.technoeconomic_assumptions.loc['CC-hydro (€/MW)']['value']
                hydro_o_m_cost = output_file.loc[scenario]['hydro capacity (MW)'] * self.technoeconomic_assumptions.loc['O&M-hydro  (€/MW)']['value']
            else:
                hydro_capital_cost = 0
                hydro_o_m_cost = 0
                
            if not pd.isna(output_file.loc[scenario, 'battery_capacity (MWh)']):
                bess_power_component = max(output_file.loc[scenario]['battery_power (MW)'], output_file.loc[scenario]['battery_capacity (MWh)']/(100/self.storage_specifications["battery"].loc['charging rate (%)']['value']))
                bess_capital_cost = output_file.loc[scenario]['battery_capacity (MWh)'] * self.technoeconomic_assumptions.loc['CC-bess (€/MWh)']['value'] + bess_power_component * self.technoeconomic_assumptions.loc['CC-bess (€/MW)']['value']
                bess_o_m_cost = bess_power_component * self.technoeconomic_assumptions.loc['O&M-bess (€/MW)']['value']
            else:
                bess_capital_cost = 0
                bess_o_m_cost = 0
            
            ''' Αφαίρεση επιδοτήσεων από το capital cost'''
            total_capital_cost = pv_capital_cost + wind_capital_cost + hydro_capital_cost + bess_capital_cost - self.technoeconomic_assumptions.loc['national subsidy (€)']['value']
            ''' Αφαίρεση επιδοτήσεων από το capital cost'''
            total_o_m_cost = pv_o_m_cost + wind_o_m_cost + hydro_o_m_cost + bess_o_m_cost
            total_equivalent_annual_cost = total_capital_cost * pv_capital_recovery_factor + total_o_m_cost
                                           
            eac_per_mwh = total_equivalent_annual_cost / output_file.loc[scenario]['RES penetration (MWh)']
            output_file.loc[scenario, 'Capital Cost (M€)'] = total_capital_cost/1000000
            output_file.loc[scenario, 'EAC (€)'] = total_equivalent_annual_cost
            output_file.loc[scenario, 'EAC/MWh (€/MWh)'] = eac_per_mwh
        
        output_file.to_excel(self.output_data_path + 'res and storage sizing - objective ' + self.simulation_details.loc['target']['value'] +' - '+ str(year) + '_with_EAC.xlsx')
        
        return