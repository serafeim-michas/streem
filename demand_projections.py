import pandas as pd
import numpy as np
import os
import calendar
import datetime
import statistics
import random

class Demand_Projections:
    
    def __init__(self):
        
        print('Pre processing historical demand data...')
        
        '''DO NOT CHANGE'''
        self.cwd = os.getcwd()
        self.input_data_path = "/data/demand/input/"
        self.output_data_path = "/data/demand/calculated/"
        self.output_header_labels = ['day', 'hour', 'demand']
        self.statistics_header_labels = ['mean', 'volatility']
        
        '''CUSTOMIZE AS NECESSARY'''
        self.capacity_file_name = 'historical_annual_demand.csv'
        self.input_file_name = 'historical_timeseries.csv'
        self.growth_file_name = 'demand_projections.xlsx'
        self.column_of_interest = "Actual Total Load [MW] - Greece (GR)"
        
        '''NO HARD CODE'''
        self.historical_capacity_df = pd.read_csv(self.cwd + self.input_data_path + self.capacity_file_name, header=0, index_col=0)
        self.data_years = self.historical_capacity_df.index
        
        # Read data
        self.entso_demand_df = pd.read_csv(self.cwd + self.input_data_path + self.input_file_name, header=0)
        self.entso_capacity_df = pd.read_csv(self.cwd + self.input_data_path + self.capacity_file_name, header=0, index_col=0)
        self.demand_growth_df = pd.read_excel(self.cwd + self.input_data_path + self.growth_file_name, header=0, index_col=0)
        
        #Pre-process data
        self.entso_demand_df = self.reshape_data(self.entso_demand_df)
        self.historical_statistics_df_non_leap = self.calculate_data_distribution(self.entso_demand_df)
        return
        
    def reshape_data(self, data):
        # Select data of interest
        for column in data.columns:
            if column != self.column_of_interest:
                data = data.drop(column, axis=1)
        
        # Reshape data in BSAM "demand" format
        print ("     Reshaping historical data...")
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
        
    def calculate_data_distribution(self, data):
        # normalize to values of the first year
        print ("     Normalizing data to latest available year...")
        for year in self.data_years:
            normalization_factor = self.entso_capacity_df.loc[year]/self.entso_capacity_df.iloc[-1]
            if normalization_factor[0] != 1:
                print ('          Demand in year ' + str(year) + ' normalized with factor ' + str(normalization_factor[0]))
                date = datetime.datetime(year, 1, 1)
                end = datetime.datetime(year+1, 1, 1)
                timestep = datetime.timedelta(hours=1)
                while date < end:
                    data.loc[date][0] = data.loc[date][0]/normalization_factor[0]
                    date += timestep
            else:
                print ('          Demand in year ' + str(year) + ' did not require normalization because annual demand remained constant')
        
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
        
    def calculate_demand(self, year):
        print ('     Projecting demand for year ' + str(year) + ' with growth factor ' + str(self.demand_growth_df.loc[year]['annual demand growth (%)']) + '%')
        # perform projections by applying growth rates
        output_file_name = self.output_header_labels[2] + '_' + str(year) + '.csv'
        year_growth = 1 + self.demand_growth_df.loc[year]['annual demand growth (%)']/100
        
        projections = []
        date = datetime.datetime(year, 1, 1)
        end = datetime.datetime(year+1, 1, 1)
        timestep = datetime.timedelta(hours=1)
        
        while date < end:
            if calendar.isleap(year) and date.month==2 and date.day==29:
                date += timestep
                continue
            current_mean = self.historical_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][0]
            current_var = self.historical_statistics_df_non_leap.loc[datetime.datetime(self.data_years[-1], date.month, date.day, date.hour, date.minute)][1]
            '''Option 1'''
            # temp_projection = current_mean*year_growth + random.uniform(-1,1)*current_var
            # if temp_projection < 0:
            #     import ipdb; ipdb.set_trace()
            # generation_projections.append([date.strftime('%Y-%m-%d'), date.strftime('%H:%M:%S'), temp_projection])
            '''Option 1 end'''
    
            '''Option 2'''
            temp_projection = current_mean*year_growth
            projections.append([date.strftime('%Y-%m-%d'), date.strftime('%H:%M:%S'), temp_projection])
            '''Option 2 end'''
    
            date += timestep
        
        
        projections = np.array(projections)
        projections_df = pd.DataFrame(projections[:,1:], index=projections[:,0], columns=[self.output_header_labels[1:]], dtype=None)
        print ('          Writing demand to file...')
        projections_df.to_csv(self.cwd+self.output_data_path + output_file_name, index=True, header=self.output_header_labels[1:])
        projections_datetime = self.convert_to_datetime(projections_df)

        return projections_datetime.astype(float)
