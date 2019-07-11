import os
import time
import subprocess

out = """

             (define (problem smart-office)
             (:domain office)
             (:objects soundsensor ultrasoundsensor monitor lamp)
             (:init  (sensor soundsensor)
                     (sensor ultrasoundsensor)
                     (nouserpresent soundsensor)
                     (nouserpresent ultrasoundsensor)
                     (actuator monitor)
                     (actuator lamp)
                     (free monitor)
                     (free lamp)
    		  """

out += "       ({}present soundsensor)".format("nouser")
out += """
    		  """
out +=""")
                      (:goal (and (userpresent soundsensor) (userpresent ultrasoundsensor))))
    	  """
filename = "smartoffice_problem.pddl"
with open(filename, "w") as f:
  f.write(out)

#Extract Steps from outputfile and turn on motor accordingly
myCmd = './ff -o smartoffice_domain.pddl -f smartoffice_problem.pddl > /home/sandeshashok/Desktop/office_planner_output.txt'
os.system(myCmd)










