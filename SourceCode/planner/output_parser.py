import os
import sys
import subprocess


filename = "office_planner_output.txt"
steps = False
time_spent = False
actions = list()
file = open(filename, "r")

for line in file.readlines():
    if "step" in line:
        steps = True

    if steps == True:
        if "time spent" in line:
            steps = False
            continue
        newline = line.split(":",1)[-1].strip()
        actions.append(newline)

file.close()

control, actuator, sensor = actions[0].split(" ")
print(control)
print(actuator)
print(sensor)
