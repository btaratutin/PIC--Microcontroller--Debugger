"""
Boris Taratutin
Sat Apr 24 23:25:25 2010



"""
import sys

sys.path.append("""C:\Users\Boris\Documents\Program Files\Microcontollers - PICs\My Code\Test_Pic\Python\helpers""")
import Continual_Plot

plot = Continual_Plot.ContinualPlot()

plot.addData(5)
plot.addData(10)
plot.addData(2)
print "press enter to exit"
raw_input()
#plot.close()
sys.exit(app.exec_())