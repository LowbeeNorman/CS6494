# CS 6494
# Caleb Norman
# This code represents the chemical monitor which samples water and attempts to feed chemicals

class Controller:
    """
    The chemical controller, which monitors some generic chemical, and feeds based on the target range.
    """

    def __init__(
        self,
        interlock,
        target_low: float = 0.9,
        target_high: float = 1.3,
        max_dose_rate_ppm_gal: float = 0.5,
        recheck_interval_min: int = 15,  # how often the controller re-evaluates
        pulse_minutes: int = 15,         # feeder run time once triggered, unchecked
    ):
        self.interlock = interlock
        self.target_low = target_low
        self.target_high = target_high
        self.max_dose_rate_ppm_gal = max_dose_rate_ppm_gal # (ppm_raised * pool volume) / turnover minutes
        self.recheck_interval_min = recheck_interval_min
        self.pulse_minutes = pulse_minutes

        # Internal state for cadence: minutes remaining in an active pulse.
        self._pulse_minutes_remaining = 0

        # Bookkeeping -- useful later for a "bounded dosing per window" property.
        self.total_dosed = 0.0
        self.dose_log = []  # (minute, reported_flow_gpm, sensor_conc, dose, triggered_check, interlock_tripped)

    def decide_dose(self, minute: float, reported_flow_gpm: float, sensor_conc: float) -> float:
        """Return dose mass (ppm-gal) to apply this step, given REPORTED evidence only."""
        triggered_check = False

        # Ask the interlock FIRST, every cycle, even mid-pulse. The
        # controller has no flow logic of its own -- it defers entirely.
        permitted = self.interlock.evaluate(minute, reported_flow_gpm)

        if not permitted:
            self._pulse_minutes_remaining = 0
            dose = 0.0
        elif self._pulse_minutes_remaining > 0:
            # Mid-pulse: keep dosing at max rate WITHOUT rechecking sensor_conc.
            dose = self.max_dose_rate_ppm_gal
            self._pulse_minutes_remaining -= 1
        elif minute % self.recheck_interval_min == 0:
            # Recheck point: decide whether to start a new pulse.
            triggered_check = True
            if sensor_conc < self.target_low:
                self._pulse_minutes_remaining = self.pulse_minutes - 1  # this minute counts as pulse minute 1
                dose = self.max_dose_rate_ppm_gal
            else:
                dose = 0.0
        else:
            dose = 0.0

        self.total_dosed += dose
        self.dose_log.append(
            (minute, reported_flow_gpm, sensor_conc, dose, triggered_check, self.interlock.tripped)
        )
        return dose