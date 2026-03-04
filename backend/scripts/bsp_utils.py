def calculate_bsp_metrics(bet_type, avg_price_matched, bsp):
    """
    Calculate BSP comparison metrics.
    
    For BACK bets: Better if we got higher odds than BSP
    For LAY bets: Better if we got lower odds than BSP
    
    Returns: (absolute_diff, percentage_diff, probability_diff)
    """
    if not avg_price_matched or not bsp or avg_price_matched == 0 or bsp == 0:
        return None, None, None
    
    # Absolute difference
    absolute_diff = avg_price_matched - bsp
    
    # Percentage difference
    percentage_diff = ((avg_price_matched - bsp) / bsp) * 100
    
    # Probability difference (implied probability)
    # Probability = 1 / odds
    # For probability: lower is better for BACK, higher is better for LAY
    # So we invert the calculation to make positive = better for both
    prob_matched = (1 / avg_price_matched) * 100
    prob_bsp = (1 / bsp) * 100
    probability_diff = prob_bsp - prob_matched  # Inverted so positive = better for both BACK and LAY
    
    # For LAY bets, invert the sign so positive = better
    if bet_type == 'LAY':
        absolute_diff = -absolute_diff
        percentage_diff = -percentage_diff
        probability_diff = -probability_diff
    
    return absolute_diff, percentage_diff, probability_diff
