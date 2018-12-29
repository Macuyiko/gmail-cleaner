# gmail-cleaner
Code to go with http://blog.macuyiko.com/post/2017/cleaning-up-a-gmail-inbox.html

First run `fill_database.py` to fill / update the emails database. **Warning:** this will take a while with a large inbox, due to the Gmail API being limited in its `list()` and `get()` calls (feel free to let me know if there's a way to speed this up).

Next, use the `flask_app.py` to start cleaning.

You'll need to create a Gmail API in your Google API console and obtain the `client_secret` JSON file.
