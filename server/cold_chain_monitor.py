def evaluate_cold_chain(temperature_readings_24h, recorded_stock):
    """
    Evaluates temperature breaches (> 8.0°C) and computes stock degradation.
    """
    breached_readings = [t for t in temperature_readings_24h if t > 8.0]
    breach_hours = len(breached_readings)

    if breach_hours >= 6:
        decay_rate = 0.70  # 70% thermal degradation
        status = "CRITICAL BREACH"
    elif breach_hours >= 3:
        decay_rate = 0.30  # 30% thermal degradation
        status = "ELEVATED RISK"
    else:
        decay_rate = 0.0
        status = "COMPLIANT"

    usable_stock = int(recorded_stock * (1.0 - decay_rate))
    lost_stock = recorded_stock - usable_stock

    return {
        "status": status,
        "breach_hours": breach_hours,
        "decay_percentage": int(decay_rate * 100),
        "usable_stock": usable_stock,
        "spoiled_stock": lost_stock
    }