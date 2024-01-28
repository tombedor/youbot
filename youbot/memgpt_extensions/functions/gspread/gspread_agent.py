# IN PROGRESS

import gspread

# TODO: read creds from env var
gc = gspread.service_account()

# Open a sheet from a spreadsheet in one go
wks = gc.open("Where is the money Lebowski?")