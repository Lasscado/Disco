from pymongo import MongoClient
from os import environ

db = MongoClient(environ.get('DATABASE_URI'))[environ['DATABASE_NAME']]
