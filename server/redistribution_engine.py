import pandas as pd
import numpy as np

def calculate_inter_phc_transfers(phc_df, transit_rate_per_km=8.0):
    """
    Identifies surplus and deficit PHCs, then calculates route-optimized transfers.
    """
    # Net Balance = Usable Stock - (Safety Stock + 7-Day Forecast Demand)
    phc_df['net_balance'] = phc_df['usable_stock'] - (phc_df['safety_stock'] + phc_df['forecast_demand'])
    
    surplus = phc_df[phc_df['net_balance'] > 0].copy()
    deficits = phc_df[phc_df['net_balance'] < 0].copy()

    transfers = []

    for _, def_row in deficits.iterrows():
        needed_qty = abs(def_row['net_balance'])
        
        # Calculate Haversine-style planar distance approximation (km)
        surplus['dist_km'] = np.sqrt(
            (surplus['lat'] - def_row['lat'])**2 + 
            (surplus['lon'] - def_row['lon'])**2
        ) * 111.0

        eligible_donors = surplus[
            (surplus['net_balance'] > 0) & 
            (surplus['medicine'] == def_row['medicine'])
        ].sort_values('dist_km')

        for s_idx, donor in eligible_donors.iterrows():
            if needed_qty <= 0:
                break
            
            avail = donor['net_balance']
            transfer_amount = int(min(needed_qty, avail))
            
            if transfer_amount > 0:
                cost = round(donor['dist_km'] * transit_rate_per_km, 2)
                transfers.append({
                    "From PHC": donor['facility_name'],
                    "To PHC": def_row['facility_name'],
                    "Medicine": def_row['medicine'],
                    "Transfer Units": transfer_amount,
                    "Distance (km)": round(donor['dist_km'], 1),
                    "Est. Logistics Cost (INR)": cost,
                    "Priority": "URGENT" if abs(def_row['net_balance']) > def_row['safety_stock'] else "STANDARD"
                })
                
                needed_qty -= transfer_amount
                surplus.loc[s_idx, 'net_balance'] -= transfer_amount

    return pd.DataFrame(transfers)