# CS 6494
# Caleb Norman
# This code connects the pool, interlock, and controller to make a fake scenario

from pool import Pool
from PoolDemo.controller import Controller
from interlock import Interlock


def run_scenario():

    # Size the feeder the way a real spec sheet would: enough dose rate to
    # swing the WHOLE declared pool volume across the controller's target
    # band within one turnover period. This is what makes the attack
    # dramatic -- the feeder is not "weak," it's correctly sized for the
    # pool it's SUPPOSED to be treating. The hazard is that a flow-spoofed
    # pulse lands in a ~75-gallon feed pocket instead of the full
    # 15,000-gallon pool.

    pool = Pool("Scenario Pool")
    interlock = Interlock()
    controller = Controller(interlock)
    band_width = controller.target_high - controller.target_low
    controller.max_dose_rate_ppm_gal = (band_width * pool.gallons) / (pool.turnover_hours * 60)
    print(f"(Feeder sized at {controller.max_dose_rate_ppm_gal:.2f} ppm-gal/min, "
          f"calibrated to the full {pool.gallons:.0f}-gallon pool)\n")

    # --- Phase 1: pool truly off (e.g. off-season / under repair), but the
    # flow sensor is SPOOFED to report normal flow. Controller sees
    # reported_flow = target and reads the sensor -- which reports rest_concentration
    # only. rest_concentration just decays normally, so the controller "corrects" a
    # perfectly ordinary-looking low reading over and over, never seeing
    # that its dosing is landing entirely in the isolated feed pocket.
    pool.set_pump_state(running=False)
    spoofed_reported_flow = pool.target_gpm

    print("=== Phase 1: true flow = 0, SPOOFED reported flow = target_gpm ===")
    for minute in range(1440):
        dose = controller.decide_dose(minute, spoofed_reported_flow, pool.sensor_reading())
        pool.dose(dose)
        pool.step(minutes=1)
        if minute % 200 == 0:
            print(
                f"t={minute + 1} min | dose={dose} ppm-gal | "
                f"sensor(rest)={pool.sensor_reading()} | feed={pool.feed_concentration} | "
                f"total_dosed={controller.total_dosed} ppm-gal"
            )

    print(
        f"\nEnd of Phase 1: sensor(rest)={pool.sensor_reading()}, feed={pool.feed_concentration}, "
        f"total_dosed={controller.total_dosed} ppm-gal\n"
    )

    # --- Phase 2: true flow is restored (maintenance ends / spoof stops).
    # The over-dosed slug in the feed pocket now mixes into the real pool.
    print("=== Phase 2: true flow restored, reporting goes back to honest ===")
    pool.set_pump_state(running=True)
    peak_bulk = pool.rest_concentration
    for minute in range(1440, 1500):
        reported_flow = pool.true_flow_gpm  # honest now
        dose = controller.decide_dose(minute, reported_flow, pool.sensor_reading())
        pool.dose(dose)
        pool.step(minutes=1)
        peak_bulk = max(peak_bulk, pool.rest_concentration)
        if minute % 10 == 9:
            print(
                f"t={minute + 1:>3} min | dose={dose:.2f} ppm-gal | "
                f"sensor(rest)={pool.sensor_reading():.3f} | feed={pool.feed_concentration:.3f}"
            )

    print(f"\nEnd of Phase 2: sensor(rest)={pool.sensor_reading():.3f}, feed={pool.rest_concentration:.3f}")
    print(f"Peak rest concentration during release: {peak_bulk:.3f}")
    print(f"Total chemical dosed while truly unflowed: {controller.total_dosed:.2f} ppm-gal")


if __name__ == "__main__":
    run_scenario()