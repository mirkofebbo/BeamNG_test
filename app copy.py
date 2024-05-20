import tkinter as tk
from tkinter import ttk
import threading
from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Electrics
import paho.mqtt.client as mqtt
import time

class App:
    def __init__(self, root, loop):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.handlers = []
        self.loop = loop

        # create beamNG instance
        self.beamng = BeamNGpy('localhost', 64256, home='D:\\BeamNG', user='D:\\BeamNG_User')
        self.vehicle = Vehicle('ego', model='etk800', color='Blue', license="connard") 
        self.scenario = Scenario('italy', 'demo_scenario')
        # Simulation and AI status
        self.simulation_running = False
        self.ai_running = False

        # Data to be published
        self.electric = Electrics()
        # Create an MQTT client
        self.client = mqtt.Client()
        self.client.connect("158.223.43.7", 1883)

    def run_simulation(self, status_label, sim_button):
        self.beamng.open()
        
        # Create and set up the scenario
        
        self.vehicle.sensors.attach('electrics', self.electric)
        
        self.scenario.add_vehicle(self.vehicle, pos=(        -1122.145386,
        1649.684448,
        152.4150848), rot_quat=( -0.001342499163,
        -0.0001237737451,
        -0.1021581069,
        0.9947673082))
        self.scenario.make(self.beamng)

        # Load and start the scenario
        self.beamng.load_scenario(self.scenario)
        self.beamng.start_scenario()
        
        # Update status label and button text
        status_label.config(text="Simulation Loaded!")
        sim_button.config(text="Stop Simulation")
        self.simulation_running = True
        # Start the thread to print vehicle data
        data_thread = threading.Thread(target=self.mqtt_connection)
        data_thread.daemon = True
        data_thread.start()

    def start_stop_simulation(self, status_label, sim_button):
        if not self.simulation_running:
            status_label.config(text="Loading simulation...")
            sim_thread = threading.Thread(target=self.run_simulation, args=(status_label, sim_button))
            sim_thread.daemon = True
            sim_thread.start()
        else:
            # Add your code to stop the simulation here
            sim_button.config(text="Start Simulation")
            self.simulation_running = False

    def ai_control(self, ai_button):
        if not self.ai_running:
            self.vehicle.ai.set_mode('span')  # Start AI in span mode
            ai_button.config(text="Stop AI")
            self.ai_running = True
        else:
            self.vehicle.ai.set_mode('disabled')  # Stop the AI
            ai_button.config(text="Start AI")
            self.ai_running = False

    def create_ui(self):
            
        status_label = tk.Label(self.root, text="Press 'Start Simulation' to load.")
        status_label.pack(pady=10)

        sim_button = ttk.Button(self.root, text="Start Simulation", command=lambda: self.start_stop_simulation(status_label, sim_button))
        sim_button.pack(pady=10)

        # Button to control AI
        ai_button = ttk.Button(self.root, text="Start AI", command=lambda: self.ai_control(ai_button))
        ai_button.pack(pady=10)

        self.root.mainloop()

            
    def mqtt_connection(self):
        while self.simulation_running:
            self.vehicle.sensors.poll()
            # Get the data
            fuel = self.vehicle.sensors["electrics"]["fuel"]
            rpm = self.vehicle.sensors["electrics"]["rpm"]
            rpm_tacho = self.vehicle.sensors["electrics"]["rpm_tacho"]
            steering = self.vehicle.sensors["electrics"]["steering"]
            gear = self.vehicle.sensors["electrics"]["gear"]
            # Publish the data
            self.client.publish("topic1", rpm)
            self.client.publish("vehicle/fuel", fuel)
            self.client.publish("vehicle/rpm", rpm)
            self.client.publish("vehicle/rpm_tacho", rpm_tacho)
            self.client.publish("vehicle/steering", steering)
            self.client.publish("vehicle/gear", gear)
            time.sleep(1)


    def close(self):
        self.client.disconnect()
        self.simulation_running = False
        self.beamng.close()
        self.root.quit()
        self.root.destroy()