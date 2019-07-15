

             (define (problem smart-office)
             (:domain office)
             (:objects soundsensor ultrasoundsensor monitor lamp)
             (:init  (sensor soundsensor)
                     (sensor ultrasoundsensor)
                     (actuator monitor)
                     (actuator lamp)
                     (free monitor)
                     (free lamp)
    		         (userpresent soundsensor)       (userpresent ultrasoundsensor)
    		  )
                      (:goal (and (nouserpresent soundsensor) (nouserpresent ultrasoundsensor))))
    	  