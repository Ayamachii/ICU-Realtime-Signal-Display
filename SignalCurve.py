from time import perf_counter
import numpy as np


class SignalCurve:
    """" This class represents the signal / curve (plotDataItem in pyQtGraph) that can be drawn on a Graph object (PlotItem in pyQtGraph).
    ...

    Attributes
    ----------
    graph_index : int
        The number of the graph it is drawn on
    signal_path : string
        Path to the file carrying the signal data
    pen_color : string
        Color of the curve, can be changed
    label : string
        Name of SignalCurve to be displayed in legend
    df : pd.DataFrame
        Data of signal curve (y values)
    mainWindow : MyMainWindow
        The window object it belongs to
    interval_value : int
        The interval between the update of the timer scrolling the graph, used to control the speed of scrolling display
    startTime : int
        The time the SignalCurve started (was added)
    space_between_points : float
        Default time step for 1D signals with no information about the sampling period
    ptr_of_signal_values : int
        Carries the index of the point in df that we have drawn
    if_from_multiple_flag : bool
        Whether this SignalCurve comes from a file wih a single or multiple channel signals
    ended_flag : bool
        Whether this particular signalCurve has ended displaying
        
    Methods
    -------
    set_initial_plot_settings
        Sets the initial ranges of axes for the Graph the signal curve is drawn on
    update
        Draws the next point of the curve along with the previous points
    """

    def __init__(self, mainWindow, graph_index, df, signal_path="", pen_color="#ffff", label="", if_from_multiple_flag = False):

        self.graph_index = graph_index 
        self.signal_path = signal_path #file path
        self.pen_color = pen_color
        self.label = label

        self.df = df

        self.mainWindow = mainWindow

        self.interval_value = self.mainWindow.graphs[self.graph_index].interval_value

        self.startTime = perf_counter()

        self.space_between_points = 0.05
        self.ptr_of_signal_values = 0

        self.if_from_multiple_flag = if_from_multiple_flag
        self.ended_flag = False
        
        self.set_initial_plot_settings()

        self.mainWindow.graphs[self.graph_index].curves.append(self)  
        self.mainWindow.signals.append(self)

    def set_initial_plot_settings(self):
        """" Sets the initial ranges of axes for the Graph the signal curve is drawn on """

        graph = self.mainWindow.graphs[self.graph_index]
        self.values = self.df
        self.max = self.df.max()
        self.min = self.df.min()
        graph.plot_item.setYRange(self.min.min(), self.max.max())
        graph.plot_item.setXRange(-50*self.space_between_points, 0)

    def update(self): 
        """ 
        1. Updates the y data on the SignalCurve
        2. handles the first update call setting the initial parameters
        3. Handles pause event
        4. checks if if all signals are done to stop the scrolling graph
        """

        graph = self.mainWindow.graphs[self.graph_index]

        # Default time step for 1D signals with no information about the sampling period
        step = 0.05

        # Case signal has just been added (first call of update)
        if self.ptr_of_signal_values == 0:
            if self.if_from_multiple_flag:
                number_of_points = self.df.shape[0]
            else: 
                number_of_points = self.df.shape[1]
            self.x_values_of_curve = np.arange(0, step * number_of_points, step) 
            self.curve = graph.plot_item.plot(name=self.label, pen=self.pen_color)

        # scroll graph and update SignalCurve unless it is paused or all curves have ended
        if not graph.paused and not self.mainWindow.graphs[self.graph_index].all_done:

            self.x_values_of_curve = self.x_values_of_curve - 0.05
            x = self.x_values_of_curve[:self.ptr_of_signal_values]

            #the signal was drawn on the whole initial x-axis range
            self.mainWindow.graphs[self.graph_index].first_added_signal = self.mainWindow.graphs[self.graph_index].curves[0]

            # set first added_signal
            for signal in self.mainWindow.signals:
                if signal.startTime < self.mainWindow.graphs[self.graph_index].first_added_signal.startTime:
                    self.mainWindow.graphs[self.graph_index].first_added_signal = signal
            
            # prevent scrolling before first_added_signal (done after a chunk of first_added_signal is drawn)
            if self.ptr_of_signal_values > 50:
                self.mainWindow.graphs[self.graph_index].plot_item.setLimits(xMin = self.mainWindow.graphs[self.graph_index].first_added_signal.x_values_of_curve[0])

            # set y data of signal curve to be drawn
            if self.if_from_multiple_flag:
                y = self.df[:self.ptr_of_signal_values]
            else:
                y = self.df.iloc[0, :self.ptr_of_signal_values]

            self.curve.setData(x=x, y=y)

            # increment the ptr to draw a new point the next uodate call
            if (self.if_from_multiple_flag and  not (self.ptr_of_signal_values == len(self.df))) or (not (self.ptr_of_signal_values == self.df.shape[1]) and not self.if_from_multiple_flag):
                self.ptr_of_signal_values += 1

        # Get the total number of points of SignalCurve to check if it has ended 
        if self.if_from_multiple_flag:
            number_of_points = len(self.df)
        else: 
            number_of_points = self.df.shape[1]
        
        # Check if the current SignalCurve is finished
        if self.ptr_of_signal_values == number_of_points:
            self.ended_flag = True #this curve in particular
            self.mainWindow.graphs[self.graph_index].all_done = True

            # Check if all curves are done and set all_done flag  accordingly
            for signal in self.mainWindow.graphs[self.graph_index].curves:
                if not signal.ended_flag:
                    self.mainWindow.graphs[self.graph_index].all_done = False
                    break
            
            # Stop scrolling graph if all curves are done
            if self.mainWindow.graphs[self.graph_index].all_done: 
                    
                    self.mainWindow.resetBtns[self.graph_index].setDisabled(False)
                    self.mainWindow.rewind_btns[self.graph_index].setDisabled(False)
                    
                    if self.mainWindow.graphs[self.graph_index].plot_item.viewRange()[0][1] == 0.01:
                        self.mainWindow.arrow_btns['right'][self.graph_index].setDisabled(True)
                    else:
                        self.mainWindow.arrow_btns['right'][self.graph_index].setDisabled(False)
                    self.mainWindow.play_pause_btns[self.graph_index].setDisabled(True)
