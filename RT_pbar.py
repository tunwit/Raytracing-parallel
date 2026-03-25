import progressbar
import time
 
 
# Function to create 
def start_animated_marker(maxbar):
    widgets = [
        "Render ",
        progressbar.Percentage(),
        " | ",
        progressbar.Bar(marker="="),
        " | ",
        progressbar.Counter(format="%(value)d/%(max_value)d tiles"),
        " | ",
        progressbar.Timer(),
        " | ",
        progressbar.ETA(),
        " | ",
        progressbar.Variable("recent"),
        ]
    bar = progressbar.ProgressBar(max_value=maxbar, widgets=widgets).start()  
    return bar
         
