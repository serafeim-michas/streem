import pandas as pd
import numpy as np
import os
import calendar
import datetime
import statistics
import random
from lhs import LHS


class RES_Generation_Projections:
    def __init__(self, main):
        print('Pre processing historical res generation data...')
        
        '''DO NOT CHANGE'''
        self.cwd = os.getcwd()
        self.lhs = LHS()
        self.number_of_res_capacity_samples = main.simulation_details.loc['number_of_res_capacity_samples']['value']
        self.input_data_path = "/data/res_data/input/"
        self.output_data_path = "/data/res_data/calculated/"
        self.statistics_header_labels = ['mean', 'volatility']
        
        
        '''CUSTOMIZE AS NECESSARY'''
        self.capacity_file_name = 'historical_capacity.csv'
        self.input_file_name = 'historical_timeseries.csv'
        self.growth_file_name = 'res_capacity_projections.xlsx'
        
        '''NO HARD CODE'''
        self.historical_capacity_df = pd.read_csv(self.cwd + self.input_data_path + self.capacity_file_name, header=0, index_col=0)
        self.data_years = self.historical_capacity_df.index
        
        # Read data
        self.entso_generation_df = pd.read_csv(self.cwd + self.input_data_path + self.input_file_name, header=0)
        self.entso_capacity_df = pd.read_csv(self.cwd + self.input_data_path + self.capacity_file_name, header=0, index_col=0)
        self.res_growth_df = pd.read_excel(self.cwd + self.input_data_path + self.growth_file_name, header=0, index_col=0)
        
        #Pre-process data
        self.assessed_technologies = []
        if "max solar capacity (MW)" in self.res_growth_df.columns:
            self.assessed_technologies.append("solar")
            self.output_header_labels = ['day', 'hour', 'solar generation (MWh)']
            self.column_of_interest = self.output_header_labels[2]
            print ("     Reshaping historical solar data...")
            self.entso_solar_generation_df = self.reshape_data(self.entso_generation_df)
            self.entso_solar_generation_df = self.remove_erroneous_solar_generation_measurement(self.entso_solar_generation_df)
            print ("     Normalizing solar data to latest available year...")
            self.historical_solar_statistics_df_non_leap = self.calculate_data_distribution(self.entso_solar_generation_df, 'solar capacity (MW)')
        
        if "max wind capacity (MW)" in self.res_growth_df.columns:
            self.assessed_technologies.append("wind")
            self.output_header_labels = ['day', 'hour', 'wind generation (MWh)']
            self.column_of_interest = self.output_header_labels[2]
            print ("     Reshaping historical wind data...")
            self.entso_wind_generation_df = self.reshape_data(self.entso_generation_df)
            print ("     Normalizing wind data to latest available year...")
            self.historical_wind_statistics_df_non_leap = self.calculate_data_distribution(self.entso_wind_generation_df, 'wind capacity (MW)')
        
        if "max hydro capacity (MW)" in self.res_growth_df.columns:
            self.assessed_technologies.append("hydro")
            self.output_header_labels = ['day', 'hour', 'hydro generation (MWh) (excluding PHS)']
            self.column_of_interest = self.output_header_labels[2]
            print ("     Reshaping historical hydro data...")
            self.entso_hydro_generation_df = self.reshape_data(self.entso_generation_df)
            print ("     Normalizing hydro data to latest available year...")
            self.historical_hydro_statistics_df_non_leap = self.calculate_data_distribution(self.entso_hydro_generation_df, 'hydro capacity (MW)')
        return
    
    def reshape_data(self, data):
        # Select data of interest
        for column in data.columns:
            if column != self.column_of_interest:
                data = data.drop(column, axis=1)
        
        # Reshape data in BSAM "demand" format
        date = datetime.datetime(self.data_years[0], 1, 1)
        end = datetime.datetime(self.data_years[-1]+1, 1, 1)
        timestep = datetime.timedelta(hours=1)
        reshaped_data = []
        df_index = 0
        while date < end:
            # historical_timeseries.append([date.strftime('%Y-%m-%d'), date.strftime('%H:%M:%S'), entso_df.iloc[df_index][column_of_interest]])
            reshaped_data.append([date, float(data.iloc[df_index][self.column_of_interest])])
            date += timestep
            df_index += 1
        reshaped_data = np.array(reshaped_data)
        reshaped_data_df = pd.DataFrame(reshaped_data[:,1:], index=reshaped_data[:,0], columns=[self.output_header_labels[2]], dtype=None)
        return reshaped_data_df 
    
    def convert_to_datetime(self, variable):
        variable.index = variable.index + ' ' + variable.iloc[:,0].values
        variable = variable.drop('hour', axis=1)
        variable.index = pd.to_datetime(variable.index, format='%Y-%m-%d %H:%M:%S')
        return variable
    
    def remove_erroneous_solar_generation_measurement(self, data):
        print ("     Removing erroneous measurements of Solar generation at hours without sun...")
        date = datetime.datetime(self.data_years[0], 1, 1)
        end = datetime.datetime(self.data_years[-1]+1, 1, 1)
        timestep = datetime.timedelta(hours=1)
        while date < end:
            if date.hour<=5 or date.hour>=21:
                data.loc[date] = 0
            date += timestep
        return data
    
    def calculate_data_distribution(self, data, column):
        # normalize to values of the first year
        for year in self.data_years:
            normalization_factor = self.entso_capacity_df.loc[year][column]/self.entso_capacity_df.iloc[-1][column]
            if normalization_factor != 1:
                print ('          Generation in year ' + str(year) + ' normalized with factor ' + str(normalization_factor))
                date = datetime.datetime(year, 1, 1)
                end = datetime.datetime(year+1, 1, 1)
                timestep = datetime.timedelta(hours=1)
                while date < end:
                    data.loc[date][0] = data.loc[date][0]/normalization_factor
                    date += timestep
            else:
                print ('          Generation in year ' + str(year) + ' did not require normalization because capacity remained constant')
        
        # calculate mean and volatility of each hour of the calendar year
        print ("          Calculating mean and volatility of each hour of the calendar year...")
        historical_statistics_array = []
        date = datetime.datetime(self.data_years[-1], 1, 1)
        end = datetime.datetime(self.data_years[-1]+1, 1, 1)
        timestep = datetime.timedelta(hours=1)
        while date < end:
            temp_list = [data.loc[date][self.output_header_labels[2]]]
            '''can be commented out'''
            temp_date = date
            for other_year in self.data_years[:-1]:
                temp_date = datetime.datetime(other_year, date.month, date.day, date.hour, date.minute)
                if temp_date.month==2 and temp_date.day==29 and not(calendar.isleap(other_year)):
                    continue
                temp_list.append(data.loc[temp_date][self.output_header_labels[2]])
            '''can be commented out'''
            if len(temp_list)>1:
                historical_statistics_array.append([date, statistics.mean(temp_list), statistics.stdev(temp_list)])
            else:
                historical_statistics_array.append([date, temp_list[0], 0])
            date += timestep
        
        historical_statistics_array = np.array(historical_statistics_array)
        historical_statistics_df = pd.DataFrame(historical_statistics_array[:,1:], index=historical_statistics_array[:,0], columns=self.statistics_header_labels, dtype=None)

        historical_statistics_df_non_leap = historical_statistics_df.copy(deep=True)
        historical_statistics_df_non_leap = historical_statistics_df_non_leap[~((historical_statistics_df_non_leap.index.month == 2) & (historical_statistics_df_non_leap.index.day == 29))]
        
        # average_historical_demand_leap = historical_statistics_df.loc[:,'mean'].sum()/1000000.0 #in TWh
        # average_historical_demand_non_leap = historical_statistics_df_non_leap.loc[:,'mean'].sum()/1000000.0 #in TWh
        return historical_statistics_df_non_leap
    
    def get_sampled_res_capacities(self, year):
        sampling_ranges = []
        for technology in self.assessed_technologies:
            if self.res_growth_df.columns.str.contains(technology).any():
                columns_of_technology = self.res_growth_df.columns[self.res_growth_df.columns.str.contains(technology)]
                sampling_ranges.append(self.res_growth_df.loc[:][columns_of_technology].loc[year].values.tolist())
                sampling_ranges[-1].insert(0,technology)
        sampled_res_capacities = self.lhs.sample(self.number_of_res_capacity_samples, sampling_ranges) 
        return sampled_res_capacities
    
    ''' needs fixing'''         
    def calculate_res_generation_profile(self, year, sampled_res_capacities):
        # perform projections by applying growth rates
        if 'year' in sampled_res_capacities.columns:
            sampled_res_capacities = sampled_res_capacities.drop('year', axis=1)
        for technology in sampled_res_capacities.columns:    
            for res_combination in sampled_res_capacities.index:
                output_file_name = technology +' '+ str(round(sampled_res_capacities.loc[res_combination][technology],5))+'MW_generation_' + str(year) + '.csv'
                columns_of_technology = self.entso_capacity_df.columns[self.entso_capacity_df.columns.str.contains(technology)]
                year_growth = sampled_res_capacities.loc[res_combination][technology]/self.entso_capacity_df.loc[:][columns_of_technology].loc[self.data_years[-1]].values[0]
                print ('     Projecting ' + technology + ' generation for year ' + str(year) + ' and scenario ' + str(res_combination) + ' with growth factor ' + str(year_growth))
                
                datetime_generation_projections = []
                date = datetime.datetime(year, 1, 1)
                end = datetime.datetime(year+1, 1, 1)
                timestep = datetime.timedelta(hours=1)
                while date < end:
                    if calendar.isleap(year) and date.month==2 and date.day==29:
                        date += timestep
                        continue
                    if technology == 'solar':
                        current_mean = self.historical_solar_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][0]
                        current_var = self.historical_solar_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][1]
                        output_header_labels = ['day', 'hour', 'solar generation (MWh)']
                    elif technology =='wind':
                        current_mean = self.historical_wind_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][0]
                        current_var = self.historical_wind_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][1]
                        output_header_labels = ['day', 'hour', 'wind generation (MWh)']
                    elif technology == 'hydro':
                        current_mean = self.historical_hydro_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][0]
                        current_var = self.historical_hydro_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][1]
                        output_header_labels = ['day', 'hour', 'hydro generation (MWh) (excluding PHS)']
                    else:
                        print ('Historical data for ' + technology + ' do not exist. Please check!')
                        
                    temp_projection = current_mean*year_growth
                    if temp_projection > sampled_res_capacities.loc[res_combination][technology]:
                        print("           Exceeded solal generation on year: " + str(year))
                        temp_projection = sampled_res_capacities.loc[res_combination][technology]
                    elif temp_projection < 0:
                        print("           Solar generation below zero in year: " + str(year))
                        temp_projection = 0.0
                    datetime_generation_projections.append([date, temp_projection])
                    date += timestep
                datetime_generation_projections = np.array(datetime_generation_projections)
                datetime_generation_projections_df = pd.DataFrame(datetime_generation_projections[:,1:], index=datetime_generation_projections[:,0], columns=[output_header_labels[2:]], dtype=None)
                datetime_generation_projections_df.insert(0,'hour', datetime_generation_projections_df.index.strftime('%H:%M:%S'))
                
                generation_projections_df = pd.DataFrame(datetime_generation_projections_df.values, index=datetime_generation_projections_df.index.strftime('%Y-%m-%d'), columns=[output_header_labels[1:]], dtype=None)
                print ('          Writing to file...')
                generation_projections_df.to_csv(self.cwd+self.output_data_path+output_file_name, index=True, header=output_header_labels[1:])
        return