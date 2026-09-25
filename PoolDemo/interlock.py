# CS 6494
# Caleb Norman
# This code represents the flow interlock system which will halt chemical dosing if it trips
# (too low of flow)

class Interlock:
    """
    The flow interlock, it has a way to evaluate based on a reported flow (what a sensor would give)
    and a tripped state. The trip is important because it stops the chemical feeders from going if
    we hit that min_flow_gpm.
    """

    def __init__(self, min_flow_gpm: float = 5.0):
        self.min_flow_gpm = min_flow_gpm
        self.tripped = False
        self.trip_log = []  # (minute, reported_flow_gpm) for each NEW trip event
        self.restart_log = []  # minutes at which restart() was called while tripped

    def evaluate(self, minute, reported_flow_gpm: float) -> bool:
        """
        Update the interlock state based on the reported flow, this is constantly called when we want
        to dose chemicals
        """
        if reported_flow_gpm < self.min_flow_gpm and not self.tripped:
            self.tripped = True
            self.trip_log.append((minute, reported_flow_gpm))
        return not self.tripped

    def restart(self, minute=None):
        """
        This is what an operator would have to deal with, we are mocking an in person reset of the interlock
        """
        if self.tripped:
            self.restart_log.append(minute)
        self.tripped = False