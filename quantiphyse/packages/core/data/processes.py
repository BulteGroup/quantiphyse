"""
Quantiphyse - Processes for the data manipulation package

Copyright (c) 2013-2018 University of Oxford
"""

from quantiphyse.utils import debug, QpException

from quantiphyse.processes import Process

class ResampleProcess(Process):
    """ 
    Resample data 
    """

    PROCESS_NAME = "Resample"
    
    def run(self, options):
        data = self.get_data(options)
        order = options.pop("order", 1)
        output_name = options.pop("output-name", "%s_res" % data.name)
        grid_data = options.pop("grid", None)

        if grid_data is None:
            raise QpException("Must provide 'grid' option to specify data item to get target grid from")
        elif grid_data not in self.ivm.data:
            raise QpException("Data item '%s' not found" % grid_data)
        
        grid = self.ivm.data[grid_data].grid
        output_data = data.resample(grid, order=order)
        output_data.name = output_name
        self.ivm.add_data(output_data, make_current=True)
        self.status = Process.SUCCEEDED
