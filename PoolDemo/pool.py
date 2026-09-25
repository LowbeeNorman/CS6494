# CS 6494
# Caleb Norman
# This code represents a simple pool model, which I intend to model spoofing sensors of.


class Pool:
    """
    A pool model, takes pool specifications as parameters, models water and chemical flow, and gives
    us a time step function
    """

    def __init__(
        self,
        name: str,
        gallons: float = 15000,      # total pool volume, gallons
        turnover_hours: float = 10,  # hours to circulate all water once
        feed_fraction: float = 0.005,  # fraction of total volume treated as the feed pocket
    ):
        self.name = name
        self.gallons = gallons
        self.turnover_hours = turnover_hours

        # Gallons per minute needed to hit the target turnover rate.
        self.target_gpm = self.gallons / (self.turnover_hours * 60)

        # Split total volume into feed pocket of water, and the rest of the water
        self.feed_gallons = self.gallons * feed_fraction
        self.rest_gallons = self.gallons - self.feed_gallons

        # True dynamic state (updated over time)
        self.pump_running = True
        self.true_flow_gpm = self.target_gpm  # actual current flow, may differ from target

        # Chemical concentration, e.g. ppm free chlorine.
        self.feed_concentration = 1.0   # post-injection pocket; NOT visible to the sensor
        self.rest_concentration = 1.0   # pool + sample line; this IS what the sensor reads

        # Estimate of natural decay of chemicals in water
        self.decay_rate = 0.002

    def set_pump_state(self, running: bool, flow_gpm: float | None = None):
        """
        Set the pool pump to True or False, along with our flow rate (how many gallons per minute)
        """
        self.pump_running = running
        if not running:
            self.true_flow_gpm = 0.0
        else:
            self.true_flow_gpm = flow_gpm if flow_gpm is not None else self.target_gpm

    def dose(self, dose_mass_ppm_gal: float):
        """
        Forcefully dose the feed pocket of water with the amount to raise does_mass_ppm_gal by 1 ppm
        The unit is a bit odd here but our idea is that if we read low ppm, we are moderating the amount
        of chemical we put in so it will spread to the rest of the pool.
        """
        if self.feed_gallons <= 0:
            return
        self.feed_concentration += dose_mass_ppm_gal / self.feed_gallons

    def sensor_reading(self) -> float:
        """
        Reporting the value read by the sensor, this is part of what we are attacking
        """
        return self.rest_concentration

    def step(self, minutes: float = 1.0):
        """
        The step function moves time forward, it lets us simulate how the water would mix and chemical decay
        """
        self.feed_concentration *= (1 - self.decay_rate) ** minutes
        self.rest_concentration *= (1 - self.decay_rate) ** minutes

        # Mixing between feed and the rest, driven by TRUE flow only.
        # Gallons exchanged this step:
        exchanged = self.true_flow_gpm * minutes
        exchanged = min(exchanged, self.feed_gallons, self.rest_gallons)

        if exchanged > 0:
            # Water (and its chemical load) swaps between zones.
            feed_out = exchanged * self.feed_concentration
            bulk_out = exchanged * self.rest_concentration

            self.feed_concentration += (bulk_out - feed_out) / self.feed_gallons
            self.rest_concentration += (feed_out - bulk_out) / self.rest_gallons
        # If exchanged == 0 (no true flow), zones do NOT mix -- this is the
        # condition where dosing the feed pocket stops ever reaching the
        # pool, and the sensor (reading rest_concentrate only) has no way to see
        # what's happening in the feed pocket.

    def true_state(self) -> dict:
        """
        The real snapshot of what is going on
        """
        return {
            "pump_running": self.pump_running,
            "true_flow_gpm": self.true_flow_gpm,
            "feed_conc": self.feed_concentration,
            "bulk_conc": self.rest_concentration,
        }

    def __repr__(self):
        return (
            f"Pool({self.name!r}, gal={self.gallons}, target_gpm={self.target_gpm:.1f}, "
            f"pump_running={self.pump_running}, feed_conc={self.feed_concentration:.3f}, "
            f"bulk_conc={self.rest_concentration:.3f})"
        )


if __name__ == "__main__":
    # This is just a simple test, not the real experiment we perform

    pool = Pool("Baseline Pool")
    band_width = 0.4
    dose_rate = (band_width * pool.gallons) / (pool.turnover_hours * 60)
    print(f"(Using a feeder sized at {dose_rate:.2f} ppm-gal/min for this pool)\n")

    pool.set_pump_state(running=False)

    print("Start: ", pool)
    for minute in range(30):
        pool.dose(dose_mass_ppm_gal=dose_rate)  # feeder keeps dosing despite no flow
        pool.step(minutes=1)
        if minute % 10 == 9:
            print(f"t={minute + 1:>2} min:", pool)

    print("\nWith the pump truly off, feed_conc keeps climbing from dosing")
    print("while bulk_conc (what the sensor actually reads) just decays")
    print("normally -- the sensor has no visibility into the feed pocket,")
    print("so nothing about the sensor reading looks anomalous at all.")