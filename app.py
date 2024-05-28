import tkinter as tk
from tkinter import ttk
import threading
from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Electrics
import paho.mqtt.client as mqtt
import time
import logging

class App:
    def __init__(self, root, loop):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.handlers = []
        self.loop = loop

        # create BeamNG instance
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
        try:
            self.beamng.open()
            
            # Create and set up the scenario
            self.vehicle.sensors.attach('electrics', self.electric)
            
            self.scenario.add_vehicle(self.vehicle, pos=(-1122.145386, 1649.684448, 152.4150848), 
                                      rot_quat=(-0.001342499163, -0.0001237737451, -0.1021581069, 0.9947673082))

            self.scenario.make(self.beamng)

            # Load and start the scenario
            self.beamng.load_scenario(self.scenario)
            self.beamng.start_scenario()
            
            # Update status label and button text
            status_label.config(text="Simulation Loaded!")
            sim_button.config(text="Stop Simulation")
            self.simulation_running = True

            # Start the thread to publish vehicle data
            self.start_data_thread()

        except Exception as e:
            logging.exception("Error starting simulation")
            print(f"Error starting simulation: {e}")
            status_label.config(text="Error loading simulation.")

    def start_stop_simulation(self, status_label, sim_button):
        if not self.simulation_running:
            status_label.config(text="Loading simulation...")
            sim_thread = threading.Thread(target=self.run_simulation, args=(status_label, sim_button))
            sim_thread.daemon = True
            sim_thread.start()
        else:
            # Stop the simulation
            self.simulation_running = False
            sim_button.config(text="Start Simulation")
            try:
                self.beamng.stop_scenario()
                self.beamng.close()
            except Exception as e:
                logging.exception("Error stopping simulation")
                print(f"Error stopping simulation: {e}")

    def ai_control(self, ai_button):
        try:
            if not self.ai_running:
                self.vehicle.ai.set_mode('span')  # Start AI in span mode
                ai_button.config(text="Stop AI")
                self.ai_running = True
            else:
                self.vehicle.ai.set_mode('disabled')  # Stop the AI
                ai_button.config(text="Start AI")
                self.ai_running = False
        except Exception as e:
            logging.exception("Error controlling AI")
            print(f"Error controlling AI: {e}")

    def create_ui(self):
        status_label = tk.Label(self.root, text="Press 'Start Simulation' to load.")
        status_label.pack(pady=10)

        sim_button = ttk.Button(self.root, text="Start Simulation", command=lambda: self.start_stop_simulation(status_label, sim_button))
        sim_button.pack(pady=10)

        # Button to control AI
        ai_button = ttk.Button(self.root, text="Start AI", command=lambda: self.ai_control(ai_button))
        ai_button.pack(pady=10)

        # Button to reset the simulation
        reset_button = ttk.Button(self.root, text="Reset Simulation", command=self.reset_simulation)
        reset_button.pack(pady=10)

        self.root.mainloop()

    def reset_simulation(self):
        if self.simulation_running:
            try:
                if self.ai_running:
                    self.vehicle.ai.set_mode('disabled')
                    self.ai_running = False
                    time.sleep(1)  # Allow time for the AI to be properly disabled
                
                self.vehicle.teleport(pos=(-1122.145386, 1649.684448, 152.4150848), 
                                      rot_quat=(-0.001342499163, -0.0001237737451, -0.1021581069, 0.9947673082))

                
                # Ensure the data thread is running after reset
                self.start_data_thread()
            except Exception as e:
                logging.exception("Error resetting simulation")
                print(f"Error resetting simulation: {e}")

    def start_data_thread(self):
        if hasattr(self, 'data_thread') and self.data_thread.is_alive():
            return  # Thread is already running
        self.data_thread = threading.Thread(target=self.mqtt_connection)
        self.data_thread.daemon = True
        self.data_thread.start()

    def mqtt_connection(self):
        while self.simulation_running:
            self.vehicle.sensors.poll()
            # Get the data
            fuel = round(self.vehicle.sensors["electrics"]["fuel"], 2)
            rpm = int(self.vehicle.sensors["electrics"]["rpm"])
            gear = self.vehicle.sensors["electrics"]["gear"]
            gear_a = self.vehicle.sensors["electrics"]["gear_a"]
            running = self.vehicle.sensors["electrics"]["running"]
            turnsignal = self.vehicle.sensors["electrics"]["turnsignal"]
            wheelspeed = self.vehicle.sensors["electrics"]["wheelspeed"]

            # Convert speed to mph and km/h
            speed_kmph = int(wheelspeed * 3.6)
            speed_mph = int(wheelspeed * 2.237)
            match gear:
                case "D":
                    gear = -1
                case "P":
                    gear = 0
                case "R":
                    gear = 1
                case "N":
                    gear = 2

            # Publish the data
            self.client.publish("vehicle/fuel", fuel)
            self.client.publish("vehicle/rpm", rpm)
            self.client.publish("vehicle/gear", gear)
            self.client.publish("vehicle/gear_a", gear_a)
            self.client.publish("vehicle/running", running)
            self.client.publish("vehicle/turnsignal", turnsignal)
            self.client.publish("vehicle/speed_kmph", speed_kmph)
            self.client.publish("vehicle/speed_mph", speed_mph)
            time.sleep(0.15)

    def close(self):
        try:
            self.client.disconnect()
            self.simulation_running = False
            self.beamng.close()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logging.exception("Error closing application")
            print(f"Error closing application: {e}")
