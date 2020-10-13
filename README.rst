.. aioget documentation master file, created by
   sphinx-quickstart on Fri Oct  2 10:02:04 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

====================================================
Welcome to AIOGET
====================================================

.. image:: https://img.shields.io/badge/python-3.8.5-blue?style=plastic&logo=appveyor
   :target: https://img.shields.io/badge/python-3.8.5-blue?style=plastic&logo=appveyor
   :alt: python 3.8.5 badge

.. image:: https://img.shields.io/badge/coverage-75%25-orange?style=plastic&logo=appveyor
   :target: https://img.shields.io/badge/coverage-75%25-orange?style=plastic&logo=appveyor
   :alt: coverage badge


Asynchronous microservices for search, download, and parsing of webpages in Python, RabbitMQ, and Redis containerized with Docker. Based on Python's asyncio as well as aiohttp, aiofiles, and pika (rabbitmq) libs, most of the functions and methods include Python typing declarations to ease development as well.

Project Goals
=============

Parsing
-------
Focus on **parsing data**, and applying your own Machine Learning or Deep Learning models to the data - or simply just data extraction.
Add a new webpage parser to the parser_scripts and you're on your way.

DRY (Don't Repeat Yourself) - unless its after a few months
-----------------------------------------------------------
The Search and Download microservices retain a Search and Download History in Redis, respectivly so if you don't waste
precious resources and bandwidth searching or downloading the same page again. After a user-configured *refresh_period*
an old webpage will be requested.

Distributed Microservices
-------------------------
Using RabbitMQ and Docker, the services can be distributed on a single or across multiple nodes.

Client-Business Oriented
------------------------
Data can be gathered for specific client or business drivers. Supports adding your own proxy. Current business functions
include non-favorable media, business line, and sanction jurisdiction. Feel free to add your own.

Centralized Logging - Focus on what matters most
------------------------------------------------
Logging Service are built to filter out critical, error, and warning from info and debug logs.

BYO (Build your own)
--------------------
Build your own microservices to digest outputs from the Parser Service! Or play around with your own network/container
configuration.

Some ideas:

- send messages to a Translation Service for text translation
- send messages to an NLP service
- store data in a DB
- create a REST API


Getting Started
===============

Installation
------------

The fastest way to get up and running is using Docker's ``docker-compose up -d --build`` command in the
project root directory.

To stop the services run ``docker-compose down``

Run Sample Scripts
------------------

Run the same scripts provided in the root directory:

- First run ``receiver.py`` in one terminal and
- Second run ``sender.py`` in another terminal

If all goes well, you should see a new ``webpages`` directory populating with webpages.

**Deeper Inspection**

If you have a python console, you can connect to Redis to inspect the entries:

.. code-block::

   # you may need to stop a locally running redis-server to view this (not the redis docker container)
   # with ``sudo service redis-server stop``
   import redis
   search_history = redis.Redis(db=0)
   download_history = redis.Redis(db=1)

   print(search_history.dbsize(), download_history.dbsize())

Running Tests
-------------

Start up the docker containers and run the tests from the ``tests`` directory.

Contributing
============

Write your own tests, and submit a PR, or file an issue.


License
=======

``aioget`` is offered under the Apache 2 license.
