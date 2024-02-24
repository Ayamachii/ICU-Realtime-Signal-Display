class Graph():
    """" This class represents the graph (plotItem in pyQtGraph) on which multiple signals can be drawn 
    ...

    Attributes
    ----------
    counter : int
        to give an index for each graph to be accessed with in other classes

    Methods
    -------
    reset_graph
        Resets all graph parameters to their default values
    """

    counter = 0
    
    def __init__(self, plot):
        """
        Parameters
        ----------
        plot_item : PyQtGraph.PlotItem
            Carries the plotItem object of pyQtGraph library
        paused : bool
            Indicates whether the graph is paused or not
        interval_value : int
            The interval between the update of the timer scrolling the graph, used to control the speed of scrolling display
        all_done : flag
            Whether all SignalCurves on this graph have finished or not, used to make the scrolling of the graph stop
        pausedAt : float
            Carries the time stamp at which the graph was paused to sync it back when play is pressed
        curves : list
            The list of SignalCurve objects drawn on thsi graph     
        maxY : float
            Keeps track of the maximum y value in all added SignalCurve objects on this graph to prevent panning up more than this value
        minY : float
            Keeps track of the minimum y value in all added SignalCurve objects on this graph to prevent panning down more than this value
        first_added_signal : SignalCurve
            The graph carries the first signal which was added on it to not allow scrolling past the beginning of this one signal
        index : int
            The number of the graph
        """
        self.plot_item = plot
        self.paused = False
        self.interval_value = None
        self.all_done = False
        self.pausedAt = None
        self.curves = []
        self.maxY = 0
        self.minY = 0
        self.first_added_signal = None
        self.index = Graph.counter
        Graph.counter += 1
    
    def reset_graph(self):
        """ Resets all graph parameters to their default values """

        self.paused = False
        self.all_done = False
        self.pausedAt = None
        self.curves = []
        self.maxY = 0
        self.minY = 0
        self.first_added_signal = None