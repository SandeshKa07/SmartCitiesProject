import os
import time
import subprocess
import socket
import time
import json

outputfilename = "office_planner_output.txt"
steps = False
time_spent = False
actions = list()
actions_count = 0

plan_send_status = False
planner_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
planner_socket.bind(('localhost', 6969))

while True:

    print("waiting for userpresence")
    data_received, from_address = planner_socket.recvfrom(1024)
    print("data recevied from office script is ", str(data_received))
    user_presence = str(data_received.decode('utf-8'))

    out = """

             (define (problem smart-office)
             (:domain office)
             (:objects soundsensor ultrasoundsensor monitor lamp)
             (:init  (sensor soundsensor)
                     (sensor ultrasoundsensor)
                     (actuator monitor)
                     (actuator lamp)
                     (free monitor)
                     (free lamp)
    		  """

    if "nouser" in user_presence:
        out += "       ({}present soundsensor)".format(user_presence)
        out += "       ({}present ultrasoundsensor)".format(user_presence)
        out += """
    		  """
        out +=""")
                      (:goal (and (userpresent soundsensor) (userpresent ultrasoundsensor))))
    	  """
    else:
        out += "       ({}present soundsensor)".format(user_presence)
        out += "       ({}present ultrasoundsensor)".format(user_presence)
        out += """
    		  """
        out +=""")
                      (:goal (and (nouserpresent soundsensor) (nouserpresent ultrasoundsensor))))
    	  """

    filename = "smartoffice_problem.pddl"
    with open(filename, "w") as f:
      f.write(out)

    #Extract Steps from outputfile and turn on motor accordingly
    myCmd = './ff -o smartoffice_domain.pddl -f smartoffice_problem.pddl > office_planner_output.txt'
    os.system(myCmd)

    time.sleep(1)

    file = open(outputfilename, "r")

    for line in file.readlines():
        if "step" in line:
            steps = True

        if steps == True:
            if "time spent" in line:
                steps = False
                break
            newline = line.split(":",1)[-1].strip()
            actions.append(newline)
            actions_count = actions_count + 1
            print("Total number of actions to be taken = ", str(actions_count))

        if "FALSE" in line:
            actions_data = json.dumps({"action_1":False, "action_2":False})
            planner_socket.sendto(actions_data.encode(), ("127.0.0.1", 6970))
            plan_send_status = True
            break

        if "True" in line:
            actions_data = json.dumps({"action_1":True, "action_2":True})
            planner_socket.sendto(actions_data.encode(), ("127.0.0.1", 6970))
            plan_send_status = True
            break

    if plan_send_status:
        plan_send_status = False
        continue
    else:
        actions_data = json.dumps({"action_1":actions[0], "action_2":actions[1]})
        planner_socket.sendto(actions_data.encode(), ("127.0.0.1", 6970))

    file.close()
    actions_count = 0
