import os
import sys
from app import db_account, login, app
import app.exceptions as e

#if database connection is not successful
if login.status_code != 200:
	raise e.DatabaseConnectError("Connect to Cloudant failed with reason: " + login.text)
else:
	if len(sys.argv) == 2 and sys.argv[1] == 'local':
		#if 'local' in the argument, then run it locally
		if __name__ == "__main__":
			app.run()
	else:
		port = os.getenv('VCAP_APP_PORT', '5000')
		if __name__ == "__main__":
			app.run(host='0.0.0.0', port=int(port))