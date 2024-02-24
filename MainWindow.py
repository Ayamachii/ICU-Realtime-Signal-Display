from fpdf import FPDF
from functools import partial
from time import perf_counter
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtWidgets
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QColorDialog, QInputDialog, QMessageBox

from SignalCurve import SignalCurve
from Graph import Graph
from ui.SignalViewer_ui import Ui_MainWindow


class MyMainWindow(QMainWindow, Ui_MainWindow):
    """" This class represents the MainWindow on which the graphs and controls will be diplayed
    ...

    Methods
    -------
    get_timer_interval_from_slider_value
        Calculate the timer interval based on the slider value
    setup_graph
        Setup the graph with initial settings
    connect_signals_slots(self):
        Connect signals to their corresponding slots
    setup_pan_signals(self):
        Setup panning functionality for the graphs
    set_shortcuts(self):
        Set keyboard shortcuts for specific actions
    zoom
        Zoom in or out on the specified graph
    reset_graph
        Reset the specified graph to its initial state
    change_signal_speed
        Change the speed of the signal on the specified graph
    pan
        Pan the specified graph left, right, up, or down
    toggle_pause
        Toggle the pause state of the specified graph
    link_graphs
        Link or unlink the two graphs
    toggle_btns
        Toggle the state of buttons based on the flag
    update_plot
        Update the plot on the specified grap
    insert_signa;
        Insert a signal into the specified graph.
    add_one_channel_signal
        Add a single channel signal to the specified graph.
    add_multiple_channel_signal
        Add multiple channel signals to the specified graph
    show_input_dialog
        Display an input dialog to get a signal label.
    populate_combobox
        Populate the drop-down boxes with available signal labels
    take_screenshot
        Take a screenshot of the specified graph
    save_As_pdf
        Save the screenshots as a PDF file
    add_table_to_pdf
        Add a table to the PDF document.
    change_signal_color
        Change the color of the selected signal on the specified graph
    delete_selected_signal
        Delete the selected signal from the specified graph
    move_signal_to_other_graph
        Move the selected signal to the other graph
    """
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.GLWs = [self.Plot_2, self.Plot_3]
        self.plot_items = [self.Plot_2.addPlot(row=0, col=0, name="plot1"), self.Plot_3.addPlot(row=0, col=1, name="plot2")]
        self.play_pause_btns = [self.PausePlayBtn, self.PausePlayBtn_2]
        self.rewind_btns = [self.RewindBtn1, self.RewindBtn2]
        self.resetBtns = [self.ResetBtn, self.ResetBtn_2]
        self.deleteBtns = [self.DeleteBtnCh1, self.DeleteBtnCh2]

        self.play_pause_icons = [QIcon("Resources/icons8-play-40.png"), QIcon("Resources/icons8-pause-40.png")]

        self.arrow_btns = {
            'left':(self.leftBtn_1, self.leftBtn_2),
            'right':(self.rightBtn_1, self.rightBtn_2),
            'up':(self.upBtn_1, self.upBtn_2),
            'down':(self.downBtn_1, self.downBtn_2)
        }

        self.graphs = [Graph(self.plot_items[0]), Graph(self.plot_items[1])]
        self.drop_boxes = [self.SelectChannelDropBox1, self.SelectChannelDropBox2]

        self.timers = [pg.QtCore.QTimer(), pg.QtCore.QTimer()]
        self.sliders = [self.SpeedSlider_2, self.SpeedSlider]

        self.supported_formats = ["csv", "txt", "xls", 'xlsx', "xlsm", "xlsb", "odf", "ods", "odt"]

        self.screenshots = []  # List to store screenshots
        self.signals = []

        self.link = False

        for timer_index, timer in enumerate(self.timers):
            new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.sliders[timer_index].value())
            timer.setInterval(new_interval)
            timer.start()

        # Default button settings
        self.RewindBtn1.setDisabled(True)
        self.ResetBtn.setDisabled(True)
        self.RewindBtn2.setDisabled(True)
        self.ResetBtn_2.setDisabled(True)

        for plot in self.plot_items:
            plot.setLimits(xMax=0.01)
            plot.addLegend()
            plot.setLabel('bottom', 'Time', 's')
            plot.setXRange(-5, 0.01)
    
        self.connect_signals_slots()

    @staticmethod
    def get_timer_interval_from_slider_value(slider_value):
        """Calculate the timer interval based on the slider value by mapping ranges
        
        Args:
            slider_value (int): The value of the slider.
        
        Returns:
            int: The calculated timer interval.
        """
        return int(((-4 / 11) * slider_value) + (1420 / 11))

    # at the end of a signal (stop and reset graph functionality)
    def setup_graph(self, graph_index:int):
        """Setup the graph with initial settings, connect specific signals to slots, add labels on axes, set axes limits, set timer interval, 
        enable and disable buttons 
        
        Args:
            graph_index (int): The index of the graph to be set up.
        """

        # Connect the timer of the graph to the update_plot function to update the SignalCurves drawn on it
        self.timers[graph_index].timeout.connect(partial(self.update_plot, graph_index))
        # Map interval value form slider value
        interval_value = MyMainWindow.get_timer_interval_from_slider_value(self.sliders[graph_index].value())
        # Set interval and start timer
        self.timers[graph_index].setInterval(interval_value)
        self.timers[graph_index].start()

        # Add a new GraphicsLayoutWidget to remove the old signals that have ended
        self.GLWs[graph_index].removeItem(self.plot_items[graph_index])  
        # Add a plotItem to the new GLW          
        self.plot_items[graph_index] = self.Plot_2.addPlot(row=0, col=0, name="plot1")
        # Enable Legend
        self.plot_items[graph_index].addLegend()
        
        # Set axes labels and limits for panning
        self.plot_items[graph_index].setLabel('bottom', 'Time', 's')
        self.plot_items[graph_index].setLimits(xMax=0.01)
        
        # Disable buttons until the signal is finished 
        self.play_pause_btns[graph_index].setDisabled(True)
        self.resetBtns[graph_index].setDisabled(True)
        self.rewind_btns[graph_index].setDisabled(True)

        # Remove signals of the removed plot from global list signals 
        temp_signals = self.signals.copy()
        for signal in temp_signals:
            if signal.graph_index == graph_index:
                self.signals.remove(signal)

        # refresh graph object and reset parameters
        self.graphs[graph_index].reset_graph()
        
        self.arrow_btns['right'][graph_index].setDisabled(False)
        # populate combobox to refresh and remove old finished signals    
        self.populate_combobox()

    def connect_signals_slots(self):
        """Connect signals to their corresponding slots."""

        # Zoom in and out , adjusting the zoom factor
        self.ZoomIn.clicked.connect(partial(self.zoom, 0, 0.5))
        self.ZoomOut.clicked.connect(partial(self.zoom, 0, 2))

        self.ZoomIn_2.clicked.connect(partial(self.zoom, 1, 0.5))
        self.ZoomOut_2.clicked.connect(partial(self.zoom, 1, 2))

        # Add a new SignalCurve and specify to which Graph
        self.AddSignal1.clicked.connect(partial(self.insert_signal, 0))
        self.AddSignal2.clicked.connect(partial(self.insert_signal, 1))

        # Save snapshot for one of the Graphs
        self.SaveSnapsotButton_1.clicked.connect(partial(self.take_screenshot, 0))
        self.SaveSnapsotButton_2.clicked.connect(partial(self.take_screenshot, 1))

        # Save as pdf button to save a report with statistics of the included curves
        self.pushButton.clicked.connect(partial(self.save_as_pdf))

        # Link axes of graphs together when checked
        self.LinkCheckBox.toggled.connect(self.link_graphs)

        # Reset selected Graph (start the graph which has finished from the beginning with no SignalCrves)
        for btn_index, btn in enumerate(self.resetBtns):
            btn.clicked.connect(partial(self.reset_graph, btn_index))

        # Delete selected SginalCurve in the combobox
        for btn_index, btn in enumerate(self.deleteBtns):
            btn.clicked.connect(partial(self.delete_selected_signal, btn_index))
        
        # Toggle play and pause buttons for the 2 graphs
        for btn_index, btn in enumerate(self.play_pause_btns):
            btn.clicked.connect(partial(self.toggle_pause, btn_index))
        
        # Rewind he finished SignalCurves on one graph from the beginning (Replay)
        for btn_index, btn in enumerate(self.rewind_btns):
            btn.clicked.connect(partial(self.setup_graph, btn_index))

        # Change the color of a SignalCurve
        self.SelectColorButton1.clicked.connect(partial(self.change_signal_color, 0))
        self.SelectColorButton2.clicked.connect(partial(self.change_signal_color, 1))

        # Switch graphs of a SignalCurve 
        self.moveToRight.clicked.connect(partial(self.move_signal_to_other_graph, 0))
        self.moveToLeft.clicked.connect(partial(self.move_signal_to_other_graph, 1))

        # Change display speed (scrolling speed of a graph)
        for slider_index, slider in enumerate(self.sliders):
            slider.valueChanged.connect(partial(self.change_signal_speed, slider_index))
        
        # Connect a timer to each scrolling graph 
        for timer_index, timer in enumerate(self.timers):
            timer.timeout.connect(partial(self.update_plot, timer_index))

        self.set_shortcuts()

        # Connect pan signals with arrow buttons
        self.setup_pan_signals()
        
    def setup_pan_signals(self):
        """Setup panning functionality for the graphs."""
        # graph_index then left_right value then up_down value
        self.rightBtn_1.clicked.connect(partial(self.pan, 0, 1, 0))
        self.rightBtn_2.clicked.connect(partial(self.pan, 1, 1, 0))
        self.leftBtn_1.clicked.connect(partial(self.pan, 0, -1, 0))
        self.leftBtn_2.clicked.connect(partial(self.pan, 1, -1, 0))
        self.upBtn_1.clicked.connect(partial(self.pan, 0, 0, 1))
        self.upBtn_2.clicked.connect(partial(self.pan, 1, 0, 1))
        self.downBtn_1.clicked.connect(partial(self.pan, 0, 0, -1))
        self.downBtn_2.clicked.connect(partial(self.pan, 1, 0, -1))

    def set_shortcuts(self):
        self.leftBtn_1.setShortcut(QKeySequence("Left"))
        self.downBtn_1.setShortcut(QKeySequence("Down"))
        self.rightBtn_1.setShortcut(QKeySequence("Right"))
        self.AddSignal1.setShortcut(QKeySequence("Ctrl+B"))
        self.DeleteBtnCh1.setShortcut(QKeySequence("Ctrl+D"))
        self.SelectColorButton1.setShortcut(QKeySequence("Ctrl+C"))
        self.SaveSnapsotButton_1.setShortcut(QKeySequence("Ctrl+S"))
        self.upBtn_1.setShortcut(QKeySequence("Up"))

    def zoom(self, graph_index, factor):
        """Zoom in or out on the specified graph.
        
        Args:
            graph_index (int): The index of the graph to zoom.
            factor (float): The zoom factor, zoom in -> 0.5, zoom out -> 2
        """
        graph = self.graphs[graph_index].plot_item
        graph.getViewBox().scaleBy((factor, factor))

    def reset_graph(self, graph_index):
        """Reset the specified graph to its initial state.
        
        Args:
            graph_index (int): The index of the graph to reset.
        """

        older_signals = []
        temp_signals = self.signals.copy()

        self.setup_graph(graph_index)

        for signal in temp_signals:
            # only for signalCurves belonging to this Graph
            if signal.graph_index == graph_index:
                
                # Reset SignalCurve attributes
                signal.ptr_of_signal_values = 0

                signal.ended_flag = False
                older_signals.append(signal)

                self.signals.append(signal)
                self.graphs[graph_index].curves.append(signal)

                signal.set_initial_plot_settings()
        # No scrolling past the max point of the signal
        self.arrow_btns['right'][graph_index].setDisabled(False)
        # Refresh signal labels in combobox
        self.populate_combobox()

    def change_signal_speed(self, graph_index):
        """Change the speed of the signal on the specified graph.
        
        Args:
            graph_index (int): The index of the graph to change signal speed.
        """
        temp_signals = self.signals.copy()

        for signal in temp_signals:
            new_speed = self.sliders[signal.graph_index].value()
            new_interval = MyMainWindow.get_timer_interval_from_slider_value(new_speed)
            self.graphs[graph_index].interval_value = new_interval
            self.timers[signal.graph_index].setInterval(new_interval)

        if self.link:
            for timer in self.timers:
                new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.SpeedSlider_2.value())
                timer.setInterval(new_interval)

    def pan(self, graph_index, left_right_flag, up_down_flag):
        """Pan the specified graph left, right, up, or down.
        
        Args:
            graph_index (int): The index of the graph to pan.
            left_right_flag (int): Flag indicating left (-1) or right (1) pan direction.
            up_down_flag (int): Flag indicating up (1) or down (-1) pan direction.
        """
        graph = self.graphs[graph_index].plot_item
        view_box = graph.getViewBox()
        # 0.05 is used to tune how much pan is applied
        view_box.translateBy(x=left_right_flag*0.05*5, y=up_down_flag * 0.05*5)

    def toggle_pause(self, graph_index):
        """Toggle the pause state of the specified graph.
        
        Args:
            graph_index (int): The index of the graph to toggle pause.
        """
        #to pause together when linked
        if self.link:
            graphs_to_toggle_pause = [0, 1]
            for timer in self.timers:
                new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.SpeedSlider_2.value())
                timer.setInterval(new_interval)
        else:
            graphs_to_toggle_pause = [graph_index]

            for i in range(2):
                new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.sliders[i].value())
                self.timers[i].setInterval(new_interval)
        
        for graph_ind in graphs_to_toggle_pause:
            if not self.graphs[graph_ind].paused:
                self.graphs[graph_ind].pausedAt = perf_counter()

            self.graphs[graph_ind].paused = not self.graphs[graph_ind].paused

            if self.graphs[graph_ind].paused: # apply pause
                self.timers[graph_ind].stop()
            else: # remove pause
                self.timers[graph_ind].start()
            self.play_pause_btns[graph_ind].setIcon(self.play_pause_icons[not self.graphs[graph_ind].paused]) 
    
    def link_graphs(self): 
        """Link or unlink the two graphs."""
        # Change flag state
        self.link = not self.link

        if self.link: #apply link
            self.graphs[1].plot_item.setYLink("plot1")
            self.graphs[1].plot_item.setXLink("plot1")

            for timer in self.timers:
                new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.SpeedSlider_2.value())
                timer.setInterval(new_interval)

        else: #remove link
            for i in range(2):
                new_interval = MyMainWindow.get_timer_interval_from_slider_value(self.sliders[i].value())
                self.timers[i].setInterval(new_interval)

            self.graphs[1].plot_item.setYLink(None)
            self.graphs[1].plot_item.setXLink(None)

        #set pause state to be the same
        self.graphs[1].paused = self.graphs[0].paused
        self.toggle_btns(self.link) # true enable buttons if linked and vice versa
            
    def toggle_btns(self, flag):
        """Toggle the state of buttons based on the parameter."""
        self.PausePlayBtn_2.setDisabled(flag)
        self.ResetBtn_2.setDisabled(flag)
        self.RewindBtn2.setDisabled(flag)
        self.upBtn_2.setDisabled(flag)
        self.downBtn_2.setDisabled(flag)
        self.leftBtn_2.setDisabled(flag)
        self.rightBtn_2.setDisabled(flag)
        self.ZoomIn_2.setDisabled(flag)
        self.ZoomOut_2.setDisabled(flag)
        self.SpeedSlider.setDisabled(flag)

    def update_plot(self, graph_index):
        """Update the plot on the specified graph.
        
        Args:
            graph_index (int): The index of the graph to update.
        """
        for signal in self.signals:
            if signal.graph_index == graph_index:
                signal.update()

    def insert_signal(self, graph_index):
        """Insert a signal into the specified graph.
        
        Args:
            graph_index (int): The index of the graph to insert the signal.
        """

        # Load dataframe
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "",
                                                "All Files ();;Text Files (.txt);;CSV Files (*.csv)")

        if not file_path:
            return

        filetype = file_path.split('.')[-1].lower()

        if filetype in self.supported_formats:
            try:
                if filetype == "csv":
                    self.df = pd.read_csv(file_path).T

                elif filetype == "txt":
                    self.df = pd.read_csv(file_path, delimiter='\t').T
                
                elif filetype in ['xls', 'xlsx', "xlsm", "xlsb", "odf", "ods", "odt"]:
                    self.df = pd.read_excel(file_path).T
    
            except Exception as e:
                print(f"Error: {e}")
                QtWidgets.QMessageBox.warning(self, 'Error', f'Error reading file: {e}')
                return
        else:
            print("Unsupported extension")
            QtWidgets.QMessageBox.warning(
                self, 'Unsupported extension', 'Choose a suitable file')
            return
        
        if self.df.shape[0] > 2:
            self.add_multiple_channel_signal(graph_index, file_path)
        else:
            self.add_one_channel_signal(graph_index, file_path)

    def add_one_channel_signal(self, graph_index, file_path):
        """Add a single channel signal to the specified graph.
        
        Args:
            graph_index (int): The index of the graph to add the signal.
            file_path (str): The path of the file containing signal data.
        """

        label = file_path.split('/')[-1].split('.')[-2]

        SignalCurve(
            mainWindow=self,
            graph_index=graph_index,
            signal_path=file_path,
            label=label,
            df=self.df
        )

        #adjust the max and min Y for multiple signals
        if self.df.min().min() < self.graphs[graph_index].minY:
            self.graphs[graph_index].minY = self.df.min().min()

        if self.df.max().max() > self.graphs[graph_index].maxY:
            self.graphs[graph_index].maxY = self.df.max().max()

        self.graphs[graph_index].plot_item.setYRange(self.graphs[graph_index].minY, self.graphs[graph_index].maxY)

        self.populate_combobox()

    def add_multiple_channel_signal(self, graph_index, file_path):
        """Add multiple channel signals to the specified graph.
        
        Args:
            graph_index (int): The index of the graph to add the signals.
            file_path (str): The path of the file containing signal data.
        """
        # display 3 channels of all channels
        max_signals = 3
        reduced_dataframe = self.df.iloc[:max_signals]
        
        signals_to_be_added = []
        
        for signal_index in range(max_signals):
            label = file_path.split('/')[-1].split('.')[-2] + "_" +str(signal_index)

            self.df = reduced_dataframe.iloc[signal_index]

            signal_dict = {
                'graph_index':graph_index,
                'signal_path':file_path,
                'label':label,
                'df':self.df,
                'if_from_multiple_flag':True
            }
            
            signals_to_be_added.append(signal_dict)

            #adjust the max and min Y for multiple signals
            if self.df.min().min() < self.graphs[graph_index].minY:
                self.graphs[graph_index].minY = self.df.min().min()

            if self.df.max().max() > self.graphs[graph_index].maxY:
                self.graphs[graph_index].maxY = self.df.max().max()

            self.graphs[graph_index].plot_item.setYRange(self.graphs[graph_index].minY, self.graphs[graph_index].maxY)

        for signal in signals_to_be_added:
            SignalCurve(
                mainWindow=self,
                graph_index=signal['graph_index'],
                signal_path=signal['signal_path'],
                label=signal['label'],
                df=signal['df'],
                if_from_multiple_flag=signal['if_from_multiple_flag'],
            )
            
        self.populate_combobox()
            
    def show_input_dialog(self, graph_index):
        """Display an input dialog to get a signal label.
        
        Args:
            graph_index (int): The index of the graph for which the label is needed.
        
        Returns:
            str: The label entered by the user.
        """
        icon = QIcon("Resources/icons8-ecg-48-2.png")

        dialog = QInputDialog()
        dialog.setWindowIcon(icon)

        while True:
            label, ok = dialog.getText(
                self, "Signal Label", "Enter a signal label:"
            )

            # if the user clicked cancel, return
            if not ok:
                return None

            if not label:
                QMessageBox.warning(self, "Warning", "Please enter a signal label.")
                continue

            # check if the label already exists
            for signal in self.signals:
                if signal.label == label:
                    QMessageBox.warning(self, "Warning", "Signal label already exists.")
                    break
            else:
                return label

    def populate_combobox(self):
        """Populate the drop-down boxes with available signal labels, also used as a refresh function after adding or removing signals"""
        # For each of the 2 Graphs
        for i in range(2):
            self.drop_boxes[i].clear()
            self.drop_boxes[i].addItem("Select Signal")

        for signal in self.signals:
                self.drop_boxes[signal.graph_index].addItem(signal.label)
    
    def take_screenshot(self, graph_index):
        """Take a screenshot of the specified graph.
        
        Args:
            graph_index (int): The index of the graph to take a screenshot of.
        """
        signals_ = [signal for signal in self.signals if signal.graph_index == graph_index]
        if signals_ == []:
            QtWidgets.QMessageBox.warning(
                self, 'NO Signal ', 'You must display signal first')
        else: 
            plot = self.GLWs[graph_index]

            screenshot = QApplication.primaryScreen().grabWindow(plot.winId())

            # Capture screenshot of the widget
            self.screenshots.append(screenshot)
            print('Screenshot taken.')

    def save_as_pdf(self):
        """Save the screenshots as a PDF file along with SignalCurve statistics"""

        if not self.screenshots:
            print('No screenshots to save.')
            QtWidgets.QMessageBox.warning(
                self, 'NO Screenshot ', 'You must take screenshots first')
            return

        pdf_path, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf)")
        if pdf_path:

            pdf = FPDF()

            # Add screenshots as separate pages
            for index, screenshot in enumerate(self.screenshots, start=1):
                screenshot_path = f"Screenshots/screenshot_{index}.png"
                screenshot.save(screenshot_path)
                pdf.add_page()

                # Add logo to the top left corner of each page
                logo_path = 'Resources/download.png'  # Path to your logo image file
                pdf.image(logo_path, x=10, y=10, w=30)  # Adjust x, y, and w as needed
                pdf.image('Resources/download.jpg', x=pdf.w - 40, y=10, w=30) 
                
                print(f'Saved screenshot {index} as {screenshot_path}')
                y = 45
                for signal in self.signals:
                    pdf.set_font("Arial", size=12)
                    pdf.set_xy(5,y)
                    pdf.cell(0, 10, txt=signal.label, ln=True, align='C')
                    
                    #.describe returns 2 columns .T -> 2 rows
                    statistics = signal.df.T.describe().T #(8,) describe
                
                    self.add_table_to_pdf(statistics, pdf, y+10)
                    #increment each row
                    y = y + 30

                pdf.image(screenshot_path, x=35, w=pdf.w - 70, h = 100)
            pdf.output(pdf_path)
            print(f'PDF saved at {pdf_path}')   
            
            self.screenshots = []

    def add_table_to_pdf(self, df, pdf, y):
        """Add a table to the PDF document.
        
        Args:
            df (pandas.DataFrame): The DataFrame containing table data.
            pdf (FPDF): The FPDF object representing the PDF document.
            y (int): The vertical position to start adding the table.
        """
        # Set font for table header
        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(5, y)

        if df.shape[0] > 2:
            headers = df.index  #(8,) 
        else:
            headers = list(df.columns)
    
        # Add table headers
        for header in headers:
            pdf.cell(25, 10, txt=header, border=1)
        pdf.ln()

        pdf.set_xy(5, y + 10)
        # Set font for table data
        pdf.set_font("Arial", size=10)

        # Add table data
        if df.shape[0] > 2:
            headers = df.index  #(8,)
            for i in range(8):
            
                pdf.cell(25, 10, txt=str(round((df[i]),2)), border=1)
        else:
            for _, row in df.iterrows():
                for header in headers:
                    pdf.cell(25, 10, txt=str(round((row[header]),2)), border=1)
                # New line
                pdf.ln()
            pdf.ln()
        
    def change_signal_color(self, graph_index):
        """Change the color of the selected signal on the specified graph.
        
        Args:
            graph_index (int): The index of the graph containing the signal.
        """
    
        selected_item = self.drop_boxes[graph_index]
        color = QColorDialog.getColor()

        for signal in self.signals:
            if selected_item == signal.label:
                new_pen = pg.mkPen(color.name())  # Create a new pen with the selected color
                signal.curve.setPen(new_pen)  # Set the new pen as the curve's pen
                break

    def delete_selected_signal(self, graph_index):
        """Delete the selected signal in the combobox from the specified graph.
        
        Args:
            graph_index (int): The index of the graph containing the signal to delete.
        """

        selected_item = self.drop_boxes[graph_index]
        temp_signals = self.signals.copy()

        for signal in temp_signals:
            if selected_item == signal.label:
                self.graphs[graph_index].plot_item.removeItem(signal.curve)
                self.graphs[graph_index].curves.remove(signal)
                self.signals.remove(signal)
                # Refresh signals in combobox
                self.populate_combobox()
                break

    # to_graph_index: 0 to right, 1 to left
    def move_signal_to_other_graph(self, to_graph_index):
        """Move the selected signal to the other graph.
        
        Args:
            to_graph_index (int): The index of the graph to move the signal to.
        """
        selected_item = self.drop_boxes[to_graph_index].currentText()
        for sig in self.signals:
            if selected_item == sig.label:   
                sig.graph_index = not to_graph_index
                self.graphs[not to_graph_index].curves.append(sig)
                self.graphs[to_graph_index].curves.remove(sig)

                self.graphs[to_graph_index].plot_item.removeItem(sig.curve)
                self.graphs[not to_graph_index].plot_item.addItem(sig.curve)
                break

        self.populate_combobox()
