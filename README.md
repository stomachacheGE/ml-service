IBM Machine Learning Service
==============

This the prototype for IBM Machine Learning Service application.

Downloading
-----------
You can use git to down the source code of this app
```
git clone https://hub.jazz.net/git/liangchengfu/ml-service
```

Install prereqs
---------------
Go to app root directory. Then you can install all the depedencies using **pip**:

```sh
pip install -r requirements.txt
```

Config your app 
---------------

The folder you download from git should contain everything you needfor deploying a new app instance on your Bluemix space or run locally. But there are few steps before you can run it.

Since the app uses [Cloudant](https://cloudant.com/) as its database, you have to change the Cloudant database credentials in **config.py**:
```python
#Cloudant Database Credentials
CLOUDANT_USER = 'YOUR_CLOUDANT_USERNAME'
CLOUDANT_PWD = 'YOUR_CLOUDANT_PASSWORD'
```
Then you can initialize your Cloudant database. This will create three databases in your Cloudant instance, and at the same time put some indexes into these databases so that the app can make queries to them.

These three databases are: **user_db**, **model_info_db**, **model_history_db**.

To initialize your database, simply run the following code from app root directory:

```sh
python cloudant_db_create.py
```

The above command can also be used when you want to change your databases to another Cloudant instance.

The SECRET KEY in **config.py** is used to generate access key for your app users. You may change it to anything you like and key it secret.

```python
#sercret key used for generating Restful API access key
SECRET_KEY = 'YOUR_SECRET_KEY'
```

Run the app on Bluemix
-----------
In order to tell Bluemix what is your app route, you have to change manifest.yml accordingly:

```
applications:
- path: .
  memory: 512
  instances: 1
  domain: eu-gb.mybluemix.net
  name: ml-service
  host: ml-service
  disk_quota: 1024M
```
This example will ask Bluemix for 512M memory and deploy to [ml-service.eu-gb.mybluemix.net](ml-service.eu-gb.mybluemix.net).

Now you can deploy the app to Bluemix.

Run the app locally:
--------
After you set up your Cloudant database, you can also run it locally.

Go to app root directory. Use the following command to run it in your local machine :

```sh
python run.py local
```
This will run the app at [http://127.0.0.1:5000](http://127.0.0.1:5000)

Have fun !!!



 