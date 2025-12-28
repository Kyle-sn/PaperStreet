Any time new position handler functionality is added, make sure that relevant functions are added/updated in ib_app.py.

All ib_app.py functions need to be called by files that impilement it. All additional logic has to happen lower in the code structure and then eventually be called by the IBApp implementations. 