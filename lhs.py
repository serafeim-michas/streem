import pandas as pd
from pyDOE import lhs


class LHS:
    
    def __init__(self):
        
        return
    
    def rescale(self, column, params, index):
        interval = params[index]
        return column * (max(interval[1:]) - min(interval[1:])) + min(interval[1:])
    
    def sample(self, number_of_samples, sampling_ranges):
        num_samples = number_of_samples #Set parametrwn pou theloume
        params = sampling_ranges

        design = lhs(len(params), samples=num_samples, criterion='maximin') #Latin-Hypercube me maximin criterion
        
        for i in range(len(params)):
            design[:, i] = self.rescale(design[:, i], params, i)
        
        output_df = pd.DataFrame(design, columns=[sublist[0] for sublist in params])
        # output_df.to_csv('res_capacity_sampling.csv', sep=',')
        return output_df