
import datetime
import calendar

def get_third_friday(year, month):
    """Calculates the date of the 3rd Friday of a given month and year."""
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_cal = c.monthdatescalendar(year, month)
    fridays = [day for week in month_cal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
    return fridays[2] # 3rd Friday (index 2)

def get_last_revision_date():
    """
    Returns the date of the most recent sWIG80 revision.
    Revisions happen on the 3rd Friday of March, June, September, December.
    We assume the data is available the NEXT day (Saturday) or effectively immediately after session.
    """
    now = datetime.date.today()
    current_year = now.year
    
    # Revision months: March (3), June (6), September (9), December (12)
    rev_months = [3, 6, 9, 12]
    
    # Candidates for "last revision"
    candidates = []
    
    # Check current year and previous year to be safe
    for y in [current_year - 1, current_year]:
        for m in rev_months:
            rev_date = get_third_friday(y, m)
            candidates.append(rev_date)
            
    # Filter only dates that are in the past (or today)
    past_revisions = [d for d in candidates if d <= now]
    
    # Return the latest one
    if past_revisions:
        return max(past_revisions)
    return None

def should_update_portfolio(last_update_datetime):
    """
    Determines if portfolio needs update.
    True if:
    1. last_update_datetime is None (never fetched)
    2. last_update_datetime is older than the most recent revision + 1 day buffer.
    """
    if not last_update_datetime:
        return True
        
    last_rev_date = get_last_revision_date()
    
    if not last_rev_date:
        return True # Should not happen unless logic fails
        
    # Convert DB timestamp to date for comparison
    last_db_date = last_update_datetime.date()
    
    # Logic: If the DB update happened BEFORE the last revision, we need to update.
    # Note: We buffer by 1 day because revision applies "after session", so we want to fetch the "next day" or later.
    # If DB date is same as revision date, it might be stale if we fetched morning.
    # Safe bet: If DB date <= Revision Date, update.
    
    if last_db_date <= last_rev_date:
        return True
        
    return False

if __name__ == "__main__":
    # Test
    print(f"Today: {datetime.date.today()}")
    last_rev = get_last_revision_date()
    print(f"Last Revision Date: {last_rev}")
    
    # Test cases
    test_date_old = datetime.datetime(2023, 1, 1)
    print(f"Should update if DB is {test_date_old}? {should_update_portfolio(test_date_old)}")
    
    test_date_new = datetime.datetime.now()
    print(f"Should update if DB is NOW? {should_update_portfolio(test_date_new)}")
